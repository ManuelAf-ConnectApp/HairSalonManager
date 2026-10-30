from __future__ import annotations

import sqlite3
from pathlib import Path

from hair_salon_management.domain.errors import DomainError
from hair_salon_management.infrastructure.database import Database


class BackupError(DomainError):
    """Error seguro de una copia o restauración local."""


class BackupService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create_backup(self, destination: Path) -> Path:
        destination = destination.expanduser().resolve()
        if destination == self.database.path.expanduser().resolve():
            raise BackupError("La copia debe guardarse en un archivo distinto de la base de datos activa.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = self.database.connect()
        target = sqlite3.connect(destination)
        try:
            source.backup(target)
        finally:
            target.close(); source.close()
        return destination

    def restore_backup(self, source_path: Path) -> None:
        source_path = source_path.expanduser().resolve()
        if not source_path.is_file():
            raise BackupError("No se encontró el archivo de copia seleccionado.")
        if source_path == self.database.path.expanduser().resolve():
            raise BackupError("Selecciona una copia distinta de la base de datos activa.")
        source = sqlite3.connect(source_path)
        target = self.database.connect()
        try:
            integrity = source.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok": raise BackupError("La copia seleccionada no supera la comprobación de integridad.")
            tables = {row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            required_tables = {"schema_migrations", "operator_accounts", "customers", "invoices"}
            if not required_tables.issubset(tables):
                raise BackupError("La copia seleccionada no pertenece a Hair Salon Management.")
            source.backup(target)
        finally:
            target.close(); source.close()
        self.database.migrate()
