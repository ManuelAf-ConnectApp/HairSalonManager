from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from hair_salon_management.application.auth import AuthService, RegisterCommand
from hair_salon_management.application.invoicing import (CreateDraftCommand, InvoiceLineCommand,
                                                         InvoicingService, UpdateDraftCommand)
from hair_salon_management.application.management import CustomerCommand, LegalEntityCommand, ManagementService, SalonCommand
from hair_salon_management.domain.errors import DomainError
from hair_salon_management.infrastructure.database import Database
from hair_salon_management.infrastructure.pdf_export import PdfExportService


class InvoicingTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = self.enterContext(TemporaryDirectory()); database = Database(Path(directory) / "test.db"); database.migrate()
        auth = AuthService(database); auth.register(RegisterCommand("ana@ejemplo.es", "Clave-Segura-2026", "Clave-Segura-2026", "Ana", "García", "12345678Z", "Calle 1", "28001", "España"))
        self.account = auth.authenticate("ana@ejemplo.es", "Clave-Segura-2026"); management = ManagementService(database)
        entity = management.create_legal_entity(self.account, LegalEntityCommand("B12345678", "Ana SL", "Calle 1", "28001", "Madrid", "Madrid", "España"))
        self.salon = management.create_salon(self.account, SalonCommand(entity, "Centro", "Calle 1", "28001", "Madrid", "Madrid", "España"))
        self.customer = management.create_customer(self.account, CustomerCommand("Lucía", "López", "+34600111222")); self.invoicing = InvoicingService(database)

    def test_draft_calculates_decimal_amounts_and_persists_lines(self) -> None:
        invoice = self.invoicing.create_draft(self.account, CreateDraftCommand(self.salon, self.customer, [InvoiceLineCommand("Corte", "2", "10.00", "10", "21")]))
        draft = self.invoicing.list_drafts(self.account)[0]
        self.assertEqual(invoice, draft["id"])
        self.assertEqual(draft["total"], "21.78")

    def test_invalid_line_and_cross_account_customer_are_rejected(self) -> None:
        with self.assertRaises(DomainError): self.invoicing.create_draft(self.account, CreateDraftCommand(self.salon, self.customer, [InvoiceLineCommand("", "1", "10")]))
        with self.assertRaises(DomainError): self.invoicing.create_draft(self.account, CreateDraftCommand(self.salon, 999, [InvoiceLineCommand("Corte", "1", "10")]))

    def test_draft_can_be_updated_and_discarded_without_affecting_another_account(self) -> None:
        draft_id = self.invoicing.create_draft(self.account, CreateDraftCommand(self.salon, self.customer, [InvoiceLineCommand("Corte", "1", "10")]))
        self.invoicing.update_draft(self.account, draft_id, UpdateDraftCommand(self.salon, self.customer, [InvoiceLineCommand("Color", "2", "15", "0", "10")]))
        draft = self.invoicing.get_draft(self.account, draft_id)
        self.assertEqual(draft["lines"], [{"description": "Color", "quantity": "2", "unit_price": "15", "discount_percentage": "0", "tax_rate": "10"}])
        self.assertEqual(self.invoicing.list_drafts(self.account)[0]["total"], "33.00")
        self.invoicing.discard_draft(self.account, draft_id)
        self.assertEqual(self.invoicing.list_drafts(self.account), [])
        with self.assertRaises(DomainError): self.invoicing.discard_draft(self.account, draft_id)

    def test_draft_can_be_exported_as_clearly_marked_test_pdf(self) -> None:
        draft_id = self.invoicing.create_draft(self.account, CreateDraftCommand(self.salon, self.customer, [InvoiceLineCommand("Corte", "1", "10")]))
        with TemporaryDirectory() as directory:
            path = PdfExportService(self.invoicing.database).export_draft(self.account, draft_id, Path(directory) / "borrador")
            content = path.read_bytes()
        self.assertEqual(path.suffix, ".pdf")
        self.assertTrue(content.startswith(b"%PDF-1.4"))
        self.assertIn(b"BORRADOR DE PRUEBA", content)
        self.assertIn(b"NO ES UNA FACTURA", content)
