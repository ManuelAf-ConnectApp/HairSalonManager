from __future__ import annotations

from pathlib import Path

from hair_salon_management.domain.errors import DomainError
from hair_salon_management.infrastructure.database import Database


class PdfExportService:
    """Exporta una representación de un borrador; no crea una factura fiscal."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def export_draft(self, account_id: int, draft_id: int, destination: Path) -> Path:
        destination = destination.expanduser().resolve()
        if destination.suffix.lower() != ".pdf":
            destination = destination.with_suffix(".pdf")
        with self.database.session() as connection:
            draft = connection.execute("""SELECT invoices.id, invoices.created_at, invoices.subtotal, invoices.tax_total, invoices.total,
              salons.name AS salon_name, salons.address AS salon_address, legal_entities.legal_name, legal_entities.tax_identifier,
              legal_entities.address AS entity_address, legal_entities.postal_code AS entity_postal_code,
              legal_entities.locality AS entity_locality, customers.first_name, customers.last_name, customers.address AS customer_address,
              customers.email AS customer_email, customers.phone AS customer_phone FROM invoices
              JOIN salons ON salons.id=invoices.salon_id JOIN legal_entities ON legal_entities.id=invoices.legal_entity_id
              JOIN customers ON customers.id=invoices.customer_id WHERE invoices.id=? AND invoices.account_id=?
              AND invoices.fiscal_status='DRAFT'""", (draft_id, account_id)).fetchone()
            if not draft:
                raise DomainError("El borrador no existe o no puede exportarse.")
            invoice_lines = connection.execute("""SELECT description, quantity, unit_price, discount_percentage, tax_rate,
              taxable_base, tax_amount, total FROM invoice_lines WHERE invoice_id=? ORDER BY position""", (draft_id,)).fetchall()
        text_lines = self._document_lines(dict(draft), [dict(line) for line in invoice_lines])
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(_simple_pdf(text_lines))
        except OSError as error:
            raise DomainError("No se ha podido guardar el PDF de prueba.") from error
        return destination

    @staticmethod
    def _document_lines(draft: dict[str, object], invoice_lines: list[dict[str, object]]) -> list[str]:
        customer_name = f"{draft['first_name']} {draft['last_name']}"
        result = [
            "BORRADOR DE PRUEBA — NO ES UNA FACTURA NI DOCUMENTO FISCAL",
            f"Borrador #{draft['id']} · creado: {draft['created_at']}",
            "",
            f"Establecimiento: {draft['salon_name']}",
            f"Emisor: {draft['legal_name']} · NIF/CIF: {draft['tax_identifier']}",
            f"Dirección emisor: {draft['entity_address']}, {draft['entity_postal_code']} {draft['entity_locality']}",
            f"Cliente: {customer_name}",
            f"Contacto cliente: {draft['customer_phone']} · {draft['customer_email'] or 'sin email'}",
            "",
            "Servicio | Cantidad | Precio sin IVA | Desc. | IVA | Total",
        ]
        for line in invoice_lines:
            result.append(f"{line['description']} | {line['quantity']} | {line['unit_price']} EUR | {line['discount_percentage']}% | {line['tax_rate']}% | {line['total']} EUR")
        result.extend(("", f"Base imponible: {draft['subtotal']} EUR", f"IVA: {draft['tax_total']} EUR", f"TOTAL: {draft['total']} EUR", "", "La emisión fiscal, la numeración y la conformidad SIF/VERI*FACTU están bloqueadas."))
        return result


def _pdf_text(value: str) -> bytes:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("cp1252", "replace")


def _simple_pdf(lines: list[str]) -> bytes:
    """PDF mínimo con fuente estándar; suficiente para un documento local de prueba."""
    pages = [lines[index:index + 48] for index in range(0, len(lines), 48)] or [[]]
    objects: list[bytes] = [b"<< /Type /Catalog /Pages 2 0 R >>", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    page_ids: list[int] = []
    for page_lines in pages:
        page_id = len(objects) + 1; content_id = page_id + 1; page_ids.append(page_id)
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>".encode())
        stream = b"BT /F1 10 Tf 45 800 Td 14 TL " + b" ".join(b"(" + _pdf_text(line) + b") Tj T*" for line in page_lines) + b" ET"
        objects.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
    objects[1] = b"<< /Type /Pages /Kids [" + b" ".join(f"{item} 0 R".encode() for item in page_ids) + b"] /Count " + str(len(page_ids)).encode() + b" >>"
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets = [0]
    for index, item in enumerate(objects, start=1):
        offsets.append(len(output)); output.extend(f"{index} 0 obj\n".encode()); output.extend(item); output.extend(b"\nendobj\n")
    startxref = len(output); output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    output.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    output.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{startxref}\n%%EOF\n".encode())
    return bytes(output)
