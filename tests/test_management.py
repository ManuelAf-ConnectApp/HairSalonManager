from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from hair_salon_management.application.auth import AuthService, RegisterCommand
from hair_salon_management.application.management import CustomerCommand, LegalEntityCommand, ManagementService, SalonCommand
from hair_salon_management.domain.errors import DomainError
from hair_salon_management.infrastructure.database import Database


class ManagementTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = self.enterContext(TemporaryDirectory())
        database = Database(Path(directory) / "test.db"); database.migrate()
        auth = AuthService(database)
        self.account_id = auth.register(RegisterCommand("ana@ejemplo.es", "Clave-Segura-2026", "Clave-Segura-2026", "Ana", "García", "12345678Z", "Calle 1", "28001", "España"))
        self.account_id = auth.authenticate("ana@ejemplo.es", "Clave-Segura-2026")
        self.management = ManagementService(database)

    def entity(self) -> LegalEntityCommand:
        return LegalEntityCommand("B12345678", "Peluquerías Ana SL", "Calle 1", "28001", "Madrid", "Madrid", "España", "info@ana.es")

    def test_entity_can_be_shared_by_two_salons(self) -> None:
        entity_id = self.management.create_legal_entity(self.account_id, self.entity())
        command = SalonCommand(entity_id, "Centro", "Calle 1", "28001", "Madrid", "Madrid", "España")
        first = self.management.create_salon(self.account_id, command)
        second = self.management.create_salon(self.account_id, SalonCommand(entity_id, "Norte", "Calle 2", "28002", "Madrid", "Madrid", "España"))
        self.assertNotEqual(first, second)
        with self.assertRaises(DomainError): self.management.create_legal_entity(self.account_id, self.entity())

    def test_opening_intervals_reject_overlap_and_allow_closed_day(self) -> None:
        entity_id = self.management.create_legal_entity(self.account_id, self.entity())
        salon = self.management.create_salon(self.account_id, SalonCommand(entity_id, "Centro", "Calle 1", "28001", "Madrid", "Madrid", "España"))
        self.management.set_opening_intervals(self.account_id, salon, 0, [("09:00", "14:00"), ("16:00", "20:00")])
        self.assertEqual(self.management.opening_intervals(self.account_id, salon, 0), [("09:00", "14:00"), ("16:00", "20:00")])
        self.management.set_opening_intervals(self.account_id, salon, 6, [])
        with self.assertRaises(DomainError): self.management.set_opening_intervals(self.account_id, salon, 1, [("09:00", "14:00"), ("13:00", "20:00")])

    def test_active_salon_is_scoped_to_account(self) -> None:
        entity_id = self.management.create_legal_entity(self.account_id, self.entity())
        salon = self.management.create_salon(self.account_id, SalonCommand(entity_id, "Centro", "Calle 1", "28001", "Madrid", "Madrid", "España"))
        self.management.set_active_salon(self.account_id, salon)
        self.assertEqual(self.management.active_salon(self.account_id)["name"], "Centro")
        self.assertEqual(self.management.dashboard_metrics(self.account_id)["salons"], 1)
        with self.assertRaises(DomainError): self.management.set_active_salon(self.account_id, 999)

    def test_entity_and_salon_can_be_updated_and_archived_safely(self) -> None:
        entity_id = self.management.create_legal_entity(self.account_id, self.entity())
        salon = self.management.create_salon(self.account_id, SalonCommand(entity_id, "Centro", "Calle 1", "28001", "Madrid", "Madrid", "España"))
        self.management.update_salon(self.account_id, salon, SalonCommand(entity_id, "Centro Nuevo", "Calle 2", "28002", "Madrid", "Madrid", "España"))
        self.assertEqual(self.management.list_salons(self.account_id)[0]["name"], "Centro Nuevo")
        with self.assertRaises(DomainError): self.management.archive_legal_entity(self.account_id, entity_id)
        self.management.archive_salon(self.account_id, salon)
        self.management.archive_legal_entity(self.account_id, entity_id)

    def test_customer_search_and_archive(self) -> None:
        customer = self.management.create_customer(self.account_id, CustomerCommand("Lucía", "López", "+34600111222", email="lucia@ejemplo.es"))
        self.assertEqual(self.management.list_customers(self.account_id, "600")[0]["id"], customer)
        self.management.update_customer(self.account_id, customer, CustomerCommand("Lucía", "Martín", "+34600111222"))
        self.assertEqual(self.management.list_customers(self.account_id)[0]["last_name"], "Martín")
        self.management.archive_customer(self.account_id, customer)
        self.assertFalse(self.management.list_customers(self.account_id)[0]["active"])
        with self.assertRaises(DomainError): self.management.create_customer(self.account_id, CustomerCommand("Ana", "", "600"))

    def test_preferences_are_persisted_per_account(self) -> None:
        self.assertEqual(self.management.preferences(self.account_id)["date_format"], "DD/MM/YYYY")
        self.management.update_preferences(self.account_id, "es-ES", "YYYY-MM-DD", "/tmp/exportaciones")
        self.assertEqual(self.management.preferences(self.account_id), {"language": "es-ES", "date_format": "YYYY-MM-DD", "export_directory": "/tmp/exportaciones"})
        with self.assertRaises(DomainError): self.management.update_preferences(self.account_id, "en-US", "YYYY-MM-DD", "")
