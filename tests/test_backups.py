from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from hair_salon_management.application.auth import AuthService, RegisterCommand
from hair_salon_management.infrastructure.backups import BackupError, BackupService
from hair_salon_management.infrastructure.database import Database


class BackupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(self.enterContext(TemporaryDirectory()))
        self.database = Database(self.directory / "app.db"); self.database.migrate()
        self.auth = AuthService(self.database); self.backups = BackupService(self.database)

    def register(self, email: str) -> None:
        self.auth.register(RegisterCommand(email, "Clave-Segura-2026", "Clave-Segura-2026", "Ana", "García", "12345678Z", "Calle 1", "28001", "España"))

    def test_backup_and_restore_are_consistent(self) -> None:
        self.register("primera@ejemplo.es")
        copy_path = self.backups.create_backup(self.directory / "backup.db")
        self.register("segunda@ejemplo.es")
        self.backups.restore_backup(copy_path)
        self.assertGreater(self.auth.authenticate("primera@ejemplo.es", "Clave-Segura-2026"), 0)
        with self.assertRaises(Exception): self.auth.authenticate("segunda@ejemplo.es", "Clave-Segura-2026")

    def test_active_database_cannot_be_used_as_backup(self) -> None:
        with self.assertRaises(BackupError): self.backups.create_backup(self.database.path)

    def test_restore_rejects_unrelated_sqlite_file(self) -> None:
        unrelated = self.directory / "other.db"
        import sqlite3
        with sqlite3.connect(unrelated) as connection:
            connection.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY)")
        with self.assertRaisesRegex(BackupError, "no pertenece"):
            self.backups.restore_backup(unrelated)
