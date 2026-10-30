import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from hair_salon_management.application.auth import AuthService
from hair_salon_management.infrastructure.database import Database
from hair_salon_management.presentation.app import MainWindow, run


class PresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def test_main_window_builds_composition_only_interface(self) -> None:
        with TemporaryDirectory() as directory:
            database = Database(Path(directory) / "app.db")
            database.migrate()
            window = MainWindow(AuthService(database))
            warnings = [label.text() for label in window.drafts_page.findChildren(QLabel)]
            self.assertTrue(any("documentos de composición" in text for text in warnings))
            self.assertEqual(window.preference_language.currentData(), "es-ES")
            window.close()

    def test_metallic_palette_is_declared(self) -> None:
        # run() opens the event loop, so only the stylesheet contract is checked through its source module.
        from inspect import getsource
        source = getsource(run)
        self.assertIn("qlineargradient", source)
        self.assertIn("#c91635", source)
        self.assertIn("#075ca8", source)
