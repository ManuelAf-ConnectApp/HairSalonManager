from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from hair_salon_management.domain.errors import DomainError
from hair_salon_management.infrastructure.database import Database

CENT = Decimal("0.01")
ZERO = Decimal("0")


@dataclass(frozen=True)
class InvoiceLineCommand:
    description: str; quantity: str; unit_price: str; discount_percentage: str = "0"; tax_rate: str = "21"


@dataclass(frozen=True)
class CreateDraftCommand:
    salon_id: int; customer_id: int; lines: list[InvoiceLineCommand]


@dataclass(frozen=True)
class UpdateDraftCommand:
    salon_id: int; customer_id: int; lines: list[InvoiceLineCommand]


@dataclass(frozen=True)
class CalculatedLine:
    description: str; quantity: Decimal; unit_price: Decimal; discount_percentage: Decimal; tax_rate: Decimal
    taxable_base: Decimal; tax_amount: Decimal; total: Decimal


class InvoicingService:
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def _decimal(value: str, label: str) -> Decimal:
        try: return Decimal(value.strip())
        except (InvalidOperation, AttributeError) as error: raise DomainError(f"{label} no es válido.") from error

    def calculate_line(self, command: InvoiceLineCommand) -> CalculatedLine:
        if not command.description.strip(): raise DomainError("La descripción de la línea es obligatoria.")
        quantity = self._decimal(command.quantity, "La cantidad")
        unit_price = self._decimal(command.unit_price, "El precio unitario")
        discount = self._decimal(command.discount_percentage, "El descuento")
        tax_rate = self._decimal(command.tax_rate, "El tipo de IVA")
        if quantity <= ZERO or unit_price < ZERO or not ZERO <= discount <= Decimal("100") or tax_rate < ZERO:
            raise DomainError("Revisa cantidad, precio, descuento y tipo de IVA.")
        base = (quantity * unit_price * (Decimal("1") - discount / Decimal("100"))).quantize(CENT, ROUND_HALF_UP)
        tax = (base * tax_rate / Decimal("100")).quantize(CENT, ROUND_HALF_UP)
        return CalculatedLine(command.description.strip(), quantity, unit_price, discount, tax_rate, base, tax, base + tax)

    def create_draft(self, account_id: int, command: CreateDraftCommand) -> int:
        lines = self._calculate_lines(command.lines)
        with self.database.session() as connection:
            salon = connection.execute("SELECT legal_entity_id FROM salons WHERE id=? AND account_id=? AND active=1", (command.salon_id, account_id)).fetchone()
            if not salon: raise DomainError("Selecciona una peluquería activa de esta cuenta.")
            if not connection.execute("SELECT id FROM customers WHERE id=? AND account_id=? AND active=1", (command.customer_id, account_id)).fetchone():
                raise DomainError("Selecciona un cliente activo de esta cuenta.")
            subtotal = sum((line.taxable_base for line in lines), ZERO).quantize(CENT)
            tax_total = sum((line.tax_amount for line in lines), ZERO).quantize(CENT)
            total = subtotal + tax_total
            result = connection.execute("""INSERT INTO invoices(account_id,salon_id,legal_entity_id,customer_id,subtotal,tax_total,total)
              VALUES (?,?,?,?,?,?,?)""", (account_id, command.salon_id, salon["legal_entity_id"], command.customer_id,
              str(subtotal), str(tax_total), str(total)))
            invoice_id = int(result.lastrowid)
            self._insert_lines(connection, invoice_id, lines)
            return invoice_id

    def update_draft(self, account_id: int, draft_id: int, command: UpdateDraftCommand) -> None:
        lines = self._calculate_lines(command.lines)
        with self.database.session() as connection:
            draft = connection.execute("SELECT id FROM invoices WHERE id=? AND account_id=? AND fiscal_status='DRAFT'", (draft_id, account_id)).fetchone()
            if not draft:
                raise DomainError("El borrador no existe o ya no se puede modificar.")
            salon = connection.execute("SELECT legal_entity_id FROM salons WHERE id=? AND account_id=? AND active=1", (command.salon_id, account_id)).fetchone()
            if not salon:
                raise DomainError("Selecciona una peluquería activa de esta cuenta.")
            if not connection.execute("SELECT id FROM customers WHERE id=? AND account_id=? AND active=1", (command.customer_id, account_id)).fetchone():
                raise DomainError("Selecciona un cliente activo de esta cuenta.")
            subtotal = sum((line.taxable_base for line in lines), ZERO).quantize(CENT)
            tax_total = sum((line.tax_amount for line in lines), ZERO).quantize(CENT)
            total = subtotal + tax_total
            connection.execute("""UPDATE invoices SET salon_id=?, legal_entity_id=?, customer_id=?, subtotal=?, tax_total=?, total=?,
              updated_at=CURRENT_TIMESTAMP WHERE id=?""", (command.salon_id, salon["legal_entity_id"], command.customer_id,
              str(subtotal), str(tax_total), str(total), draft_id))
            connection.execute("DELETE FROM invoice_lines WHERE invoice_id=?", (draft_id,))
            self._insert_lines(connection, draft_id, lines)

    def discard_draft(self, account_id: int, draft_id: int) -> None:
        with self.database.session() as connection:
            result = connection.execute("DELETE FROM invoices WHERE id=? AND account_id=? AND fiscal_status='DRAFT'", (draft_id, account_id))
            if result.rowcount != 1:
                raise DomainError("El borrador no existe o ya no se puede descartar.")

    def get_draft(self, account_id: int, draft_id: int) -> dict[str, object]:
        with self.database.session() as connection:
            draft = connection.execute("SELECT id, salon_id, customer_id FROM invoices WHERE id=? AND account_id=? AND fiscal_status='DRAFT'", (draft_id, account_id)).fetchone()
            if not draft:
                raise DomainError("El borrador no existe o ya no se puede modificar.")
            lines = connection.execute("""SELECT description, quantity, unit_price, discount_percentage, tax_rate
              FROM invoice_lines WHERE invoice_id=? ORDER BY position""", (draft_id,)).fetchall()
        result = dict(draft)
        result["lines"] = [dict(line) for line in lines]
        return result

    def _calculate_lines(self, commands: list[InvoiceLineCommand]) -> list[CalculatedLine]:
        if not commands:
            raise DomainError("Añade al menos una línea de servicio.")
        return [self.calculate_line(line) for line in commands]

    @staticmethod
    def _insert_lines(connection: object, invoice_id: int, lines: list[CalculatedLine]) -> None:
        connection.executemany("""INSERT INTO invoice_lines(invoice_id,position,description,quantity,unit_price,discount_percentage,tax_rate,taxable_base,tax_amount,total)
          VALUES (?,?,?,?,?,?,?,?,?,?)""", [(invoice_id, index, line.description, str(line.quantity), str(line.unit_price),
          str(line.discount_percentage), str(line.tax_rate), str(line.taxable_base), str(line.tax_amount), str(line.total))
          for index, line in enumerate(lines, start=1)])

    def list_drafts(self, account_id: int) -> list[dict[str, object]]:
        with self.database.session() as connection:
            rows = connection.execute("""SELECT invoices.id, invoices.total, invoices.created_at, salons.name AS salon_name,
              customers.first_name || ' ' || customers.last_name AS customer_name FROM invoices
              JOIN salons ON salons.id=invoices.salon_id JOIN customers ON customers.id=invoices.customer_id
              WHERE invoices.account_id=? AND invoices.fiscal_status='DRAFT' ORDER BY invoices.id DESC""", (account_id,)).fetchall()
        return [dict(row) for row in rows]
