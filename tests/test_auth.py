from pathlib import Path
import unittest

from hair_salon_management.application.auth import AuthService, RegisterCommand, UpdateProfileCommand
from hair_salon_management.domain.errors import AuthenticationError, DomainError, DuplicateEmailError, RecoveryError
from hair_salon_management.infrastructure.database import Database


def service(tmp_path: Path) -> AuthService:
    database = Database(tmp_path / "test.db"); database.migrate()
    return AuthService(database)


def command(**changes: str) -> RegisterCommand:
    data = dict(email="GESTOR@ejemplo.es", password="Clave-Segura-2026", password_confirmation="Clave-Segura-2026",
                first_name="Ana", last_name="García", tax_identifier="12345678Z", address="Calle Mayor 1",
                postal_code="28001", country="España", phone="+34600111222")
    data.update(changes)
    return RegisterCommand(**data)


class AuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = self.enterContext(__import__("tempfile").TemporaryDirectory())
        self.auth = service(Path(self.temporary_directory))

    def test_register_and_authenticate(self) -> None:
        code = self.auth.register(command())
        self.assertGreaterEqual(len(code.replace("-", "")), 20)
        self.assertGreater(self.auth.authenticate("gestor@EJEMPLO.es", "Clave-Segura-2026"), 0)

    def test_duplicate_email_and_weak_password_are_rejected(self) -> None:
        self.auth.register(command())
        with self.assertRaises(DuplicateEmailError): self.auth.register(command(email="gestor@ejemplo.es"))
        with self.assertRaises(DomainError):
            self.auth.register(command(email="otro@ejemplo.es", password="corta", password_confirmation="corta"))

    def test_login_uses_generic_error(self) -> None:
        self.auth.register(command())
        with self.assertRaisesRegex(AuthenticationError, "Email o contraseña incorrectos"):
            self.auth.authenticate("gestor@ejemplo.es", "incorrecta")

    def test_recovery_is_single_use(self) -> None:
        code = self.auth.register(command())
        self.auth.reset_password("gestor@ejemplo.es", code, "Otra-Clave-2026", "Otra-Clave-2026")
        self.assertTrue(self.auth.authenticate("gestor@ejemplo.es", "Otra-Clave-2026"))
        with self.assertRaises(RecoveryError):
            self.auth.reset_password("gestor@ejemplo.es", code, "Una-Clave-2026", "Una-Clave-2026")

    def test_profile_update_and_password_change_require_valid_data(self) -> None:
        self.auth.register(command()); account_id = self.auth.authenticate("gestor@ejemplo.es", "Clave-Segura-2026")
        self.auth.update_profile(account_id, UpdateProfileCommand("Ana María", "García", "ana.maria@ejemplo.es", "+34600111222"))
        self.assertEqual(self.auth.profile_summary(account_id)["email"], "ana.maria@ejemplo.es")
        self.auth.change_password(account_id, "Clave-Segura-2026", "Nueva-Clave-2026", "Nueva-Clave-2026")
        self.assertTrue(self.auth.authenticate("ana.maria@ejemplo.es", "Nueva-Clave-2026"))
        with self.assertRaises(AuthenticationError): self.auth.change_password(account_id, "incorrecta", "Otra-Clave-2026", "Otra-Clave-2026")
