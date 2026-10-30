from __future__ import annotations

import os
from pathlib import Path

from hair_salon_management.application.auth import AuthService
from hair_salon_management.application.management import ManagementService
from hair_salon_management.infrastructure.database import Database


def default_data_path() -> Path:
    configured_directory = os.environ.get("HAIR_SALON_MANAGER_DATA_DIR")
    if configured_directory:
        return Path(configured_directory) / "hair-salon.db"
    return Path.home() / ".local" / "share" / "hair-salon-management" / "hair-salon.db"


def build_auth_service(path: Path | None = None) -> AuthService:
    database = Database(path or default_data_path())
    database.migrate()
    return AuthService(database)


def build_management_service(path: Path | None = None) -> ManagementService:
    database = Database(path or default_data_path())
    database.migrate()
    return ManagementService(database)
