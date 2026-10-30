from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from hair_salon_management.domain.errors import DomainError
from hair_salon_management.domain.validation import normalize_email
from hair_salon_management.infrastructure.database import Database


@dataclass(frozen=True)
class LegalEntityCommand:
    tax_identifier: str; legal_name: str; address: str; postal_code: str; locality: str
    province: str; country: str; email: str = ""; phone: str = ""


@dataclass(frozen=True)
class SalonCommand:
    legal_entity_id: int; name: str; address: str; postal_code: str; locality: str
    province: str; country: str; email: str = ""; phone: str = ""


@dataclass(frozen=True)
class CustomerCommand:
    first_name: str; last_name: str; phone: str; address: str = ""; email: str = ""; notes: str = ""


class ManagementService:
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def _required(*values: str) -> None:
        if not all(value.strip() for value in values):
            raise DomainError("Completa todos los campos obligatorios.")

    def create_legal_entity(self, account_id: int, command: LegalEntityCommand) -> int:
        self._required(command.tax_identifier, command.legal_name, command.address, command.postal_code, command.locality, command.province, command.country)
        email = normalize_email(command.email) if command.email.strip() else None
        try:
            with self.database.session() as connection:
                result = connection.execute("""INSERT INTO legal_entities (account_id,tax_identifier,legal_name,address,postal_code,locality,province,country,email,phone) VALUES (?,?,?,?,?,?,?,?,?,?)""", (account_id, command.tax_identifier.strip().upper(), command.legal_name.strip(), command.address.strip(), command.postal_code.strip(), command.locality.strip(), command.province.strip(), command.country.strip(), email, command.phone.strip() or None))
                return int(result.lastrowid)
        except Exception as error:
            if "UNIQUE constraint failed: legal_entities.account_id, legal_entities.tax_identifier" in str(error):
                raise DomainError("Ya existe un emisor con ese CIF/NIF.") from error
            raise

    def create_salon(self, account_id: int, command: SalonCommand) -> int:
        self._required(command.name, command.address, command.postal_code, command.locality, command.province, command.country)
        email = normalize_email(command.email) if command.email.strip() else None
        with self.database.session() as connection:
            entity = connection.execute("SELECT id FROM legal_entities WHERE id=? AND account_id=? AND active=1", (command.legal_entity_id, account_id)).fetchone()
            if not entity: raise DomainError("Selecciona un emisor fiscal activo de esta cuenta.")
            result = connection.execute("""INSERT INTO salons (account_id,legal_entity_id,name,address,postal_code,locality,province,country,email,phone) VALUES (?,?,?,?,?,?,?,?,?,?)""", (account_id, command.legal_entity_id, command.name.strip(), command.address.strip(), command.postal_code.strip(), command.locality.strip(), command.province.strip(), command.country.strip(), email, command.phone.strip() or None))
            return int(result.lastrowid)

    def update_legal_entity(self, account_id: int, entity_id: int, command: LegalEntityCommand) -> None:
        self._required(command.tax_identifier, command.legal_name, command.address, command.postal_code, command.locality, command.province, command.country)
        email = normalize_email(command.email) if command.email.strip() else None
        try:
            with self.database.session() as connection:
                result = connection.execute("""UPDATE legal_entities SET tax_identifier=?,legal_name=?,address=?,postal_code=?,
                  locality=?,province=?,country=?,email=?,phone=? WHERE id=? AND account_id=? AND active=1""", (command.tax_identifier.strip().upper(), command.legal_name.strip(), command.address.strip(), command.postal_code.strip(), command.locality.strip(), command.province.strip(), command.country.strip(), email, command.phone.strip() or None, entity_id, account_id))
                if result.rowcount != 1: raise DomainError("El emisor seleccionado no está disponible.")
        except Exception as error:
            if "UNIQUE constraint failed: legal_entities.account_id, legal_entities.tax_identifier" in str(error): raise DomainError("Ya existe un emisor con ese CIF/NIF.") from error
            raise

    def archive_legal_entity(self, account_id: int, entity_id: int) -> None:
        with self.database.session() as connection:
            active_salons = connection.execute("SELECT COUNT(*) FROM salons WHERE legal_entity_id=? AND account_id=? AND active=1", (entity_id, account_id)).fetchone()[0]
            if active_salons: raise DomainError("Archiva antes las peluquerías activas asociadas a este emisor.")
            result = connection.execute("UPDATE legal_entities SET active=0 WHERE id=? AND account_id=? AND active=1", (entity_id, account_id))
            if result.rowcount != 1: raise DomainError("El emisor seleccionado no está disponible.")

    def update_salon(self, account_id: int, salon_id: int, command: SalonCommand) -> None:
        self._required(command.name, command.address, command.postal_code, command.locality, command.province, command.country)
        email = normalize_email(command.email) if command.email.strip() else None
        with self.database.session() as connection:
            if not connection.execute("SELECT id FROM legal_entities WHERE id=? AND account_id=? AND active=1", (command.legal_entity_id, account_id)).fetchone(): raise DomainError("Selecciona un emisor fiscal activo de esta cuenta.")
            result = connection.execute("""UPDATE salons SET legal_entity_id=?,name=?,address=?,postal_code=?,locality=?,province=?,country=?,email=?,phone=? WHERE id=? AND account_id=? AND active=1""", (command.legal_entity_id, command.name.strip(), command.address.strip(), command.postal_code.strip(), command.locality.strip(), command.province.strip(), command.country.strip(), email, command.phone.strip() or None, salon_id, account_id))
            if result.rowcount != 1: raise DomainError("La peluquería seleccionada no está disponible.")

    def archive_salon(self, account_id: int, salon_id: int) -> None:
        with self.database.session() as connection:
            result = connection.execute("UPDATE salons SET active=0 WHERE id=? AND account_id=? AND active=1", (salon_id, account_id))
            if result.rowcount != 1: raise DomainError("La peluquería seleccionada no está disponible.")
            connection.execute("UPDATE account_preferences SET active_salon_id=NULL,updated_at=CURRENT_TIMESTAMP WHERE account_id=? AND active_salon_id=?", (account_id, salon_id))

    def set_opening_intervals(self, account_id: int, salon_id: int, weekday: int, intervals: list[tuple[str, str]]) -> None:
        if weekday not in range(7): raise DomainError("El día de la semana no es válido.")
        normalized = sorted((self._valid_time(start), self._valid_time(end)) for start, end in intervals)
        if any(start >= end for start, end in normalized): raise DomainError("Cada tramo debe terminar después de empezar.")
        if any(normalized[index][1] > normalized[index + 1][0] for index in range(len(normalized) - 1)): raise DomainError("Los tramos horarios no pueden solaparse.")
        with self.database.session() as connection:
            if not connection.execute("SELECT id FROM salons WHERE id=? AND account_id=?", (salon_id, account_id)).fetchone(): raise DomainError("La peluquería seleccionada no está disponible.")
            connection.execute("DELETE FROM opening_intervals WHERE salon_id=? AND weekday=?", (salon_id, weekday))
            connection.executemany("INSERT INTO opening_intervals(salon_id,weekday,starts_at,ends_at) VALUES (?,?,?,?)", [(salon_id, weekday, start, end) for start, end in normalized])

    def opening_intervals(self, account_id: int, salon_id: int, weekday: int) -> list[tuple[str, str]]:
        if weekday not in range(7): raise DomainError("El día de la semana no es válido.")
        with self.database.session() as connection:
            if not connection.execute("SELECT id FROM salons WHERE id=? AND account_id=?", (salon_id, account_id)).fetchone(): raise DomainError("La peluquería seleccionada no está disponible.")
            rows = connection.execute("SELECT starts_at,ends_at FROM opening_intervals WHERE salon_id=? AND weekday=? ORDER BY starts_at", (salon_id, weekday)).fetchall()
        return [(str(row["starts_at"]), str(row["ends_at"])) for row in rows]

    @staticmethod
    def _valid_time(value: str) -> str:
        try: return time.fromisoformat(value).strftime("%H:%M")
        except ValueError as error: raise DomainError("La hora debe tener formato HH:MM.") from error

    def create_customer(self, account_id: int, command: CustomerCommand) -> int:
        self._required(command.first_name, command.last_name, command.phone)
        email = normalize_email(command.email) if command.email.strip() else None
        with self.database.session() as connection:
            result = connection.execute("INSERT INTO customers(account_id,first_name,last_name,address,email,phone,notes) VALUES (?,?,?,?,?,?,?)", (account_id, command.first_name.strip(), command.last_name.strip(), command.address.strip() or None, email, command.phone.strip(), command.notes.strip() or None))
            return int(result.lastrowid)

    def list_customers(self, account_id: int, search: str = "") -> list[dict[str, object]]:
        term = f"%{search.strip()}%"
        with self.database.session() as connection:
            rows = connection.execute("""SELECT id, first_name, last_name, phone, email, active FROM customers WHERE account_id=? AND (first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR COALESCE(email,'') LIKE ?) ORDER BY active DESC, last_name, first_name""", (account_id, term, term, term, term)).fetchall()
        return [dict(row) for row in rows]

    def update_customer(self, account_id: int, customer_id: int, command: CustomerCommand) -> None:
        self._required(command.first_name, command.last_name, command.phone)
        email = normalize_email(command.email) if command.email.strip() else None
        with self.database.session() as connection:
            result = connection.execute("""UPDATE customers SET first_name=?,last_name=?,address=?,email=?,phone=?,notes=?,
              updated_at=CURRENT_TIMESTAMP WHERE id=? AND account_id=? AND active=1""", (command.first_name.strip(),
              command.last_name.strip(), command.address.strip() or None, email, command.phone.strip(),
              command.notes.strip() or None, customer_id, account_id))
            if result.rowcount != 1: raise DomainError("El cliente seleccionado no está disponible.")

    def archive_customer(self, account_id: int, customer_id: int) -> None:
        with self.database.session() as connection:
            result = connection.execute("UPDATE customers SET active=0, updated_at=CURRENT_TIMESTAMP WHERE id=? AND account_id=?", (customer_id, account_id))
            if result.rowcount != 1: raise DomainError("El cliente seleccionado no está disponible.")

    def list_legal_entities(self, account_id: int) -> list[dict[str, object]]:
        with self.database.session() as connection:
            rows = connection.execute("SELECT id, tax_identifier, legal_name FROM legal_entities WHERE account_id=? AND active=1 ORDER BY legal_name", (account_id,)).fetchall()
        return [dict(row) for row in rows]

    def list_salons(self, account_id: int) -> list[dict[str, object]]:
        with self.database.session() as connection:
            rows = connection.execute("""SELECT salons.id, salons.name, salons.active, legal_entities.legal_name
              FROM salons JOIN legal_entities ON legal_entities.id=salons.legal_entity_id
              WHERE salons.account_id=? ORDER BY salons.active DESC, salons.name""", (account_id,)).fetchall()
        return [dict(row) for row in rows]

    def set_active_salon(self, account_id: int, salon_id: int) -> None:
        with self.database.session() as connection:
            if not connection.execute("SELECT id FROM salons WHERE id=? AND account_id=? AND active=1", (salon_id, account_id)).fetchone():
                raise DomainError("La peluquería seleccionada no está disponible.")
            connection.execute("""INSERT INTO account_preferences(account_id,active_salon_id,updated_at) VALUES (?,?,CURRENT_TIMESTAMP)
              ON CONFLICT(account_id) DO UPDATE SET active_salon_id=excluded.active_salon_id, updated_at=CURRENT_TIMESTAMP""", (account_id, salon_id))

    def active_salon(self, account_id: int) -> dict[str, object] | None:
        with self.database.session() as connection:
            row = connection.execute("""SELECT salons.id, salons.name, legal_entities.legal_name
              FROM account_preferences JOIN salons ON salons.id=account_preferences.active_salon_id
              JOIN legal_entities ON legal_entities.id=salons.legal_entity_id
              WHERE account_preferences.account_id=? AND salons.active=1""", (account_id,)).fetchone()
        return dict(row) if row else None

    def preferences(self, account_id: int) -> dict[str, object]:
        with self.database.session() as connection:
            row = connection.execute("""SELECT language, date_format, export_directory FROM account_preferences
              WHERE account_id=?""", (account_id,)).fetchone()
        return dict(row) if row else {"language": "es-ES", "date_format": "DD/MM/YYYY", "export_directory": None}

    def update_preferences(self, account_id: int, language: str, date_format: str, export_directory: str) -> None:
        if language != "es-ES" or date_format not in {"DD/MM/YYYY", "YYYY-MM-DD"}:
            raise DomainError("La preferencia seleccionada no es válida.")
        directory = export_directory.strip() or None
        with self.database.session() as connection:
            connection.execute("""INSERT INTO account_preferences(account_id, language, date_format, export_directory, updated_at)
              VALUES (?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(account_id) DO UPDATE SET language=excluded.language,
              date_format=excluded.date_format, export_directory=excluded.export_directory, updated_at=CURRENT_TIMESTAMP""",
              (account_id, language, date_format, directory))

    def dashboard_metrics(self, account_id: int) -> dict[str, int]:
        with self.database.session() as connection:
            customers = connection.execute("SELECT COUNT(*) FROM customers WHERE account_id=? AND active=1", (account_id,)).fetchone()[0]
            salons = connection.execute("SELECT COUNT(*) FROM salons WHERE account_id=? AND active=1", (account_id,)).fetchone()[0]
            drafts = connection.execute("SELECT COUNT(*) FROM invoices WHERE account_id=? AND fiscal_status='DRAFT'", (account_id,)).fetchone()[0]
        return {"customers": customers, "salons": salons, "drafts": drafts, "invoices": 0, "pending_invoices": 0}
