from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from hair_salon_management.application.auth import AuthService, RegisterCommand
from hair_salon_management.application.management import CustomerCommand, ManagementService
from hair_salon_management.infrastructure.database import Database
from hair_salon_management.infrastructure.exports import ExportService


class ExportTests(unittest.TestCase):
    def test_customer_export_is_account_scoped_and_has_headers(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory); database = Database(root / "app.db"); database.migrate(); auth = AuthService(database)
            auth.register(RegisterCommand("ana@ejemplo.es", "Clave-Segura-2026", "Clave-Segura-2026", "Ana", "García", "12345678Z", "Calle 1", "28001", "España")); account = auth.authenticate("ana@ejemplo.es", "Clave-Segura-2026")
            ManagementService(database).create_customer(account, CustomerCommand("Lucía", "López", "+34600111222"))
            path = ExportService(database).export_customers(account, root / "clientes")
            content = path.read_text(encoding="utf-8-sig")
            self.assertTrue(path.name.endswith(".csv")); self.assertIn("nombre,apellidos", content); self.assertIn("Lucía,López", content); self.assertNotIn("password_hash", content)
