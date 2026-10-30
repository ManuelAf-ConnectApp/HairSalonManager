from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from hair_salon_management.domain.errors import AuthenticationError, DuplicateEmailError, RecoveryError
from hair_salon_management.domain.validation import normalize_email, validate_password
from hair_salon_management.infrastructure.database import Database
from hair_salon_management.infrastructure.security import PasswordHasher, generate_recovery_code


@dataclass(frozen=True)
class RegisterCommand:
    email: str; password: str; password_confirmation: str; first_name: str; last_name: str
    tax_identifier: str; address: str; postal_code: str; country: str; phone: str = ""


@dataclass(frozen=True)
class UpdateProfileCommand:
    first_name: str; last_name: str; email: str; phone: str = ""


class AuthService:
    def __init__(self, database: Database, hasher: PasswordHasher | None = None) -> None:
        self.database, self.hasher = database, hasher or PasswordHasher()

    def register(self, command: RegisterCommand) -> str:
        email = normalize_email(command.email)
        if command.password != command.password_confirmation:
            raise AuthenticationError("Las contraseñas no coinciden.")
        validate_password(command.password)
        required = (command.first_name, command.last_name, command.tax_identifier, command.address,
                    command.postal_code, command.country)
        if not all(field.strip() for field in required):
            raise AuthenticationError("Completa todos los campos obligatorios.")
        code = generate_recovery_code()
        try:
            with self.database.session() as connection:
                cursor = connection.execute("""INSERT INTO operator_accounts
                  (email,password_hash,first_name,last_name,tax_identifier,address,postal_code,country,phone)
                  VALUES (?,?,?,?,?,?,?,?,?)""", (email, self.hasher.hash(command.password), command.first_name.strip(),
                  command.last_name.strip(), command.tax_identifier.strip(), command.address.strip(),
                  command.postal_code.strip(), command.country.strip(), command.phone.strip() or None))
                account_id = cursor.lastrowid
                connection.execute("INSERT INTO recovery_credentials(account_id,code_hash) VALUES (?,?)",
                                   (account_id, self.hasher.hash(code)))
                connection.execute("INSERT INTO audit_events(account_id,event_type) VALUES (?,?)", (account_id, "registered"))
        except Exception as error:
            if "UNIQUE constraint failed: operator_accounts.email" in str(error):
                raise DuplicateEmailError("Ya existe una cuenta con ese correo.") from error
            raise
        return code

    def authenticate(self, email_value: str, password: str) -> int:
        email = normalize_email(email_value)
        now = datetime.now(UTC)
        with self.database.session() as connection:
            account = connection.execute("SELECT * FROM operator_accounts WHERE email = ?", (email,)).fetchone()
            if not account or not account["active"]:
                raise AuthenticationError("Email o contraseña incorrectos.")
            locked_until = account["locked_until"]
            if locked_until and datetime.fromisoformat(locked_until) > now:
                raise AuthenticationError("Email o contraseña incorrectos.")
            if not self.hasher.verify(password, account["password_hash"]):
                attempts = account["failed_attempts"] + 1
                lock = (now + timedelta(seconds=min(30 * attempts, 300))).isoformat() if attempts >= 5 else None
                connection.execute("UPDATE operator_accounts SET failed_attempts=?, locked_until=? WHERE id=?",
                                   (attempts, lock, account["id"]))
                connection.execute("INSERT INTO audit_events(account_id,event_type) VALUES (?,?)", (account["id"], "login_failed"))
                raise AuthenticationError("Email o contraseña incorrectos.")
            connection.execute("UPDATE operator_accounts SET failed_attempts=0, locked_until=NULL WHERE id=?", (account["id"],))
            connection.execute("INSERT INTO audit_events(account_id,event_type) VALUES (?,?)", (account["id"], "login_succeeded"))
            return int(account["id"])

    def reset_password(self, email_value: str, code: str, new_password: str, confirmation: str) -> None:
        email = normalize_email(email_value)
        if new_password != confirmation:
            raise RecoveryError("Las contraseñas no coinciden.")
        validate_password(new_password)
        with self.database.session() as connection:
            account = connection.execute("SELECT id FROM operator_accounts WHERE email=?", (email,)).fetchone()
            if not account:
                raise RecoveryError("No se ha podido restablecer la contraseña.")
            credentials = connection.execute("""SELECT * FROM recovery_credentials
                WHERE account_id=? AND used_at IS NULL AND revoked_at IS NULL""", (account["id"],)).fetchall()
            credential = next((item for item in credentials if self.hasher.verify(code.strip(), item["code_hash"])), None)
            if not credential:
                raise RecoveryError("No se ha podido restablecer la contraseña.")
            connection.execute("UPDATE recovery_credentials SET used_at=CURRENT_TIMESTAMP WHERE id=?", (credential["id"],))
            connection.execute("UPDATE operator_accounts SET password_hash=?, failed_attempts=0, locked_until=NULL WHERE id=?",
                               (self.hasher.hash(new_password), account["id"]))
            connection.execute("INSERT INTO audit_events(account_id,event_type) VALUES (?,?)", (account["id"], "password_reset"))

    def profile_summary(self, account_id: int) -> dict[str, str]:
        with self.database.session() as connection:
            row = connection.execute("""SELECT first_name, last_name, email, tax_identifier, phone
              FROM operator_accounts WHERE id=? AND active=1""", (account_id,)).fetchone()
        if not row:
            raise AuthenticationError("La sesión no está disponible.")
        return {key: str(value or "") for key, value in dict(row).items()}

    def update_profile(self, account_id: int, command: UpdateProfileCommand) -> None:
        if not command.first_name.strip() or not command.last_name.strip():
            raise AuthenticationError("El nombre y los apellidos son obligatorios.")
        email = normalize_email(command.email)
        try:
            with self.database.session() as connection:
                result = connection.execute("""UPDATE operator_accounts SET first_name=?, last_name=?, email=?, phone=?
                  WHERE id=? AND active=1""", (command.first_name.strip(), command.last_name.strip(), email,
                  command.phone.strip() or None, account_id))
                if result.rowcount != 1: raise AuthenticationError("La sesión no está disponible.")
                connection.execute("INSERT INTO audit_events(account_id,event_type) VALUES (?,?)", (account_id, "profile_updated"))
        except Exception as error:
            if "UNIQUE constraint failed: operator_accounts.email" in str(error):
                raise DuplicateEmailError("Ya existe una cuenta con ese correo.") from error
            raise

    def change_password(self, account_id: int, current_password: str, new_password: str, confirmation: str) -> None:
        if new_password != confirmation: raise AuthenticationError("Las contraseñas no coinciden.")
        validate_password(new_password)
        with self.database.session() as connection:
            account = connection.execute("SELECT password_hash FROM operator_accounts WHERE id=? AND active=1", (account_id,)).fetchone()
            if not account or not self.hasher.verify(current_password, account["password_hash"]):
                raise AuthenticationError("No se ha podido actualizar la contraseña.")
            connection.execute("UPDATE operator_accounts SET password_hash=? WHERE id=?", (self.hasher.hash(new_password), account_id))
            connection.execute("INSERT INTO audit_events(account_id,event_type) VALUES (?,?)", (account_id, "password_changed"))
