from __future__ import annotations

import csv
from pathlib import Path

from hair_salon_management.domain.errors import DomainError
from hair_salon_management.infrastructure.database import Database


class ExportError(DomainError):
    """Error seguro de exportación local."""


class ExportService:
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def _writer(destination: Path, headers: list[str], rows: list[tuple[object, ...]]) -> Path:
        destination = destination.expanduser().resolve()
        if destination.suffix.lower() != ".csv": destination = destination.with_suffix(".csv")
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with destination.open("w", newline="", encoding="utf-8-sig") as output:
                writer = csv.writer(output); writer.writerow(headers); writer.writerows(rows)
        except OSError as error:
            raise ExportError("No se ha podido escribir el archivo de exportación.") from error
        return destination

    def export_customers(self, account_id: int, destination: Path) -> Path:
        with self.database.session() as connection:
            records = connection.execute("""SELECT id,first_name,last_name,phone,email,address,notes,active,created_at,updated_at
              FROM customers WHERE account_id=? ORDER BY last_name,first_name""", (account_id,)).fetchall()
        rows = [tuple(record) for record in records]
        return self._writer(destination, ["id", "nombre", "apellidos", "telefono", "email", "direccion", "notas", "activo", "creado_en", "actualizado_en"], rows)

    def export_drafts(self, account_id: int, destination: Path) -> Path:
        with self.database.session() as connection:
            records = connection.execute("""SELECT invoices.id, invoices.created_at, salons.name,
              customers.first_name || ' ' || customers.last_name, invoices.subtotal, invoices.tax_total, invoices.total,
              invoices.fiscal_status, invoices.payment_status FROM invoices JOIN salons ON salons.id=invoices.salon_id
              JOIN customers ON customers.id=invoices.customer_id WHERE invoices.account_id=? ORDER BY invoices.id""", (account_id,)).fetchall()
        return self._writer(destination, ["id", "creado_en", "peluqueria", "cliente", "base", "iva", "total", "estado_fiscal", "estado_cobro"], [tuple(record) for record in records])
