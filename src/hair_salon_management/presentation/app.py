from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QMainWindow, QMessageBox, QPushButton, QStackedWidget, QVBoxLayout,
                               QWidget, QTextEdit, QComboBox, QTabWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QFrame, QGridLayout, QFileDialog)

from hair_salon_management.application.auth import AuthService, RegisterCommand, UpdateProfileCommand
from hair_salon_management.application.invoicing import (CreateDraftCommand, InvoiceLineCommand,
                                                         InvoicingService, UpdateDraftCommand)
from hair_salon_management.application.management import (CustomerCommand, LegalEntityCommand,
                                                           ManagementService, SalonCommand)
from hair_salon_management.domain.errors import DomainError
from hair_salon_management.infrastructure.backups import BackupService
from hair_salon_management.infrastructure.exports import ExportService
from hair_salon_management.infrastructure.pdf_export import PdfExportService


def field(label: str, secret: bool = False) -> tuple[str, QLineEdit]:
    input_field = QLineEdit()
    input_field.setAccessibleName(label)
    if secret:
        input_field.setEchoMode(QLineEdit.EchoMode.Password)
    return label, input_field


class AccessPage(QWidget):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(38, 26, 38, 26)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        self.layout.addWidget(heading)
        self.form = QFormLayout()
        self.layout.addLayout(self.form)
        self.notice = QLabel()
        self.notice.setWordWrap(True)
        self.layout.addWidget(self.notice)
        self.layout.addStretch()

    def error(self, exception: Exception) -> None:
        self.notice.setText(str(exception))
        self.notice.setStyleSheet("color: #a8162d;")

    def success(self, message: str) -> None:
        self.notice.setText(message)
        self.notice.setStyleSheet("color: #075ca8;")


class MainWindow(QMainWindow):
    def __init__(self, auth: AuthService) -> None:
        super().__init__()
        self.auth = auth
        self.management = ManagementService(auth.database)
        self.invoicing = InvoicingService(auth.database)
        self.backups = BackupService(auth.database)
        self.exports = ExportService(auth.database)
        self.pdf_exports = PdfExportService(auth.database)
        self.account_id: int | None = None
        self.setWindowTitle("Hair Salon Management")
        self.resize(480, 500)
        self.setMinimumSize(440, 420)
        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)
        self.login_page = self._login_page()
        self.register_page = self._register_page()
        self.recovery_page = self._recovery_page()
        self.customers_page = self._customers_page()
        self.configuration_page = self._configuration_page()
        self.drafts_page = self._drafts_page()
        self.profile_page = self._profile_page()
        self.settings_page = self._settings_page()
        self.dashboard_page = self._dashboard_page()
        self.shell = self._shell_page()
        for page in (self.login_page, self.register_page, self.recovery_page, self.shell):
            self.pages.addWidget(page)
        self.pages.setCurrentWidget(self.login_page)

    def _button(self, text: str, callback: Callable[[], None]) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(callback)
        return button

    @staticmethod
    def _logo_label(height: int) -> QLabel:
        label = QLabel(); label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = Path(__file__).resolve().parents[3] / "images" / "HairSalonManager.png"
        pixmap = QPixmap(str(logo_path))
        if pixmap.isNull():
            label.setText("Hair Salon Management")
        else:
            label.setPixmap(pixmap.scaledToHeight(height, Qt.TransformationMode.SmoothTransformation))
        return label

    def _shell_page(self) -> QWidget:
        page = QWidget(); layout = QHBoxLayout(page); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(228); sidebar_layout = QVBoxLayout(sidebar); sidebar_layout.setContentsMargins(20, 28, 20, 22)
        sidebar_logo = self._logo_label(76); sidebar_logo.setObjectName("sidebarLogo"); sidebar_layout.addWidget(sidebar_logo)
        brand = QLabel("HAIR SALON\nMANAGEMENT"); brand.setObjectName("brand"); sidebar_layout.addWidget(brand)
        self.shell_user = QLabel("Sesión no iniciada"); self.shell_user.setObjectName("sidebarUser"); sidebar_layout.addWidget(self.shell_user)
        self.shell_salon = QLabel("Sin establecimiento activo"); self.shell_salon.setObjectName("activeSalon"); self.shell_salon.setWordWrap(True); sidebar_layout.addWidget(self.shell_salon)
        sidebar_layout.addSpacing(18)
        self.content = QStackedWidget()
        for label, target in (("Inicio", self.dashboard_page), ("Clientes", self.customers_page), ("Peluquerías", self.configuration_page), ("Facturas", self.drafts_page), ("Perfil", self.profile_page), ("Ajustes", self.settings_page)):
            button = self._button(label, lambda destination=target: self._navigate(destination))
            button.setObjectName("navButton"); sidebar_layout.addWidget(button)
        sidebar_layout.addStretch(); logout = self._button("Cerrar sesión", self._logout); logout.setObjectName("logoutButton"); sidebar_layout.addWidget(logout)
        for view in (self.dashboard_page, self.customers_page, self.configuration_page, self.drafts_page, self.profile_page, self.settings_page): self.content.addWidget(view)
        layout.addWidget(sidebar); layout.addWidget(self.content, 1)
        return page

    def _navigate(self, destination: QWidget) -> None:
        if destination is self.customers_page: self._refresh_customers()
        elif destination is self.configuration_page: self._refresh_configuration()
        elif destination is self.drafts_page: self._refresh_drafts()
        elif destination is self.profile_page: self._refresh_profile()
        elif destination is self.settings_page: self._refresh_settings()
        elif destination is self.dashboard_page: self._refresh_dashboard()
        self.content.setCurrentWidget(destination)

    def _show_access(self, destination: QWidget, width: int, height: int) -> None:
        self.pages.setCurrentWidget(destination)
        self.resize(width, height)

    def _login_page(self) -> AccessPage:
        page = AccessPage("Iniciar sesión")
        page.layout.insertWidget(0, self._logo_label(118))
        page.email = field("Email")[1]; page.password = field("Contraseña", True)[1]
        page.form.addRow("Email", page.email); page.form.addRow("Contraseña", page.password)
        page.layout.addWidget(self._button("Entrar", lambda: self._login(page)))
        row = QHBoxLayout()
        register = self._button("Crear cuenta", lambda: self._show_access(self.register_page, 540, 790))
        recovery = self._button("Recuperar contraseña", lambda: self._show_access(self.recovery_page, 480, 560))
        row.addWidget(register); row.addWidget(recovery); page.layout.addLayout(row)
        return page

    def _register_page(self) -> AccessPage:
        page = AccessPage("Crear cuenta de gestión")
        for attribute, label, secret in (("email", "Email", False), ("first_name", "Nombre", False),
            ("last_name", "Apellidos", False), ("tax_identifier", "CIF/NIF", False),
            ("address", "Dirección", False), ("postal_code", "Código postal", False),
            ("country", "País", False), ("phone", "Teléfono (opcional)", False),
            ("password", "Contraseña", True), ("confirmation", "Confirmar contraseña", True)):
            value = field(label, secret)[1]; setattr(page, attribute, value); page.form.addRow(label, value)
        page.layout.addWidget(self._button("Guardar cuenta", lambda: self._register(page)))
        page.layout.addWidget(self._button("Volver", lambda: self._show_access(self.login_page, 480, 500)))
        return page

    def _recovery_page(self) -> AccessPage:
        page = AccessPage("Recuperar contraseña")
        page.layout.insertWidget(1, QLabel("Introduce el código de recuperación guardado al crear la cuenta."))
        for attribute, label, secret in (("email", "Email", False), ("code", "Código de recuperación", True),
            ("password", "Nueva contraseña", True), ("confirmation", "Confirmar contraseña", True)):
            value = field(label, secret)[1]; setattr(page, attribute, value); page.form.addRow(label, value)
        page.layout.addWidget(self._button("Restablecer", lambda: self._recover(page)))
        page.layout.addWidget(self._button("Volver", lambda: self._show_access(self.login_page, 480, 500)))
        return page

    def _dashboard_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(42, 36, 42, 36); layout.setSpacing(18)
        heading = QLabel("Inicio"); heading.setObjectName("pageTitle"); layout.addWidget(heading)
        self.dashboard_active = QLabel("Establecimiento activo: sin seleccionar"); self.dashboard_active.setObjectName("dashboardContext"); layout.addWidget(self.dashboard_active)
        cards = QGridLayout(); cards.setSpacing(14); self.dashboard_cards: dict[str, QLabel] = {}
        for index, (key, label) in enumerate((("customers", "Clientes"), ("salons", "Peluquerías"), ("drafts", "Borradores"), ("pending_invoices", "Pendientes"))):
            card, value = self._metric_card(label); self.dashboard_cards[key] = value; cards.addWidget(card, 0, index)
        layout.addLayout(cards)
        quick_card = QFrame(); quick_card.setObjectName("contentCard"); quick_layout = QVBoxLayout(quick_card); quick_title = QLabel("Acciones rápidas"); quick_title.setObjectName("cardTitle"); quick_layout.addWidget(quick_title)
        shortcuts = QHBoxLayout(); shortcuts.addWidget(self._button("Nuevo cliente", self._open_customers)); shortcuts.addWidget(self._button("Nuevo borrador", self._open_drafts)); shortcuts.addWidget(self._button("Nueva peluquería", self._open_configuration)); shortcuts.addStretch(); quick_layout.addLayout(shortcuts); layout.addWidget(quick_card)
        warning = QLabel("Facturación real bloqueada: esta versión no es un sistema conforme al reglamento SIF/VERI*FACTU."); warning.setObjectName("legalWarning"); warning.setWordWrap(True); layout.addWidget(warning)
        layout.addStretch()
        return page

    def _metric_card(self, label: str) -> tuple[QFrame, QLabel]:
        card = QFrame(); card.setObjectName("metricCard"); card_layout = QVBoxLayout(card)
        value = QLabel("0"); value.setObjectName("metricValue"); card_layout.addWidget(value)
        caption = QLabel(label); caption.setObjectName("metricLabel"); card_layout.addWidget(caption)
        return card, value

    def _profile_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(42, 36, 42, 36)
        title = QLabel("Perfil"); title.setObjectName("pageTitle"); layout.addWidget(title)
        tabs = QTabWidget(); layout.addWidget(tabs)
        summary_tab = QWidget(); summary_layout = QVBoxLayout(summary_tab); card = QFrame(); card.setObjectName("contentCard"); form = QFormLayout(card)
        self.profile_name = QLabel("—"); self.profile_email = QLabel("—"); self.profile_tax_id = QLabel("—"); self.profile_phone = QLabel("—")
        form.addRow("Responsable", self.profile_name); form.addRow("Email", self.profile_email); form.addRow("CIF/NIF registrado", self.profile_tax_id); form.addRow("Teléfono", self.profile_phone); summary_layout.addWidget(card); summary_layout.addStretch(); tabs.addTab(summary_tab, "Resumen")
        edit_tab = QWidget(); edit_layout = QVBoxLayout(edit_tab); edit_card = QFrame(); edit_card.setObjectName("contentCard"); edit_form = QFormLayout(edit_card)
        self.profile_first_name = field("Nombre")[1]; self.profile_last_name = field("Apellidos")[1]; self.profile_email_input = field("Email")[1]; self.profile_phone_input = field("Teléfono")[1]
        edit_form.addRow("Nombre", self.profile_first_name); edit_form.addRow("Apellidos", self.profile_last_name); edit_form.addRow("Email", self.profile_email_input); edit_form.addRow("Teléfono", self.profile_phone_input); edit_form.addRow(self._button("Guardar cambios", self._save_profile)); edit_layout.addWidget(edit_card); edit_layout.addStretch(); tabs.addTab(edit_tab, "Datos personales")
        security_tab = QWidget(); security_layout = QVBoxLayout(security_tab); security_card = QFrame(); security_card.setObjectName("contentCard"); security_form = QFormLayout(security_card)
        self.current_password = field("Contraseña actual", True)[1]; self.new_password = field("Nueva contraseña", True)[1]; self.confirm_password = field("Confirmar contraseña", True)[1]
        security_form.addRow("Contraseña actual", self.current_password); security_form.addRow("Nueva contraseña", self.new_password); security_form.addRow("Confirmar contraseña", self.confirm_password); security_form.addRow(self._button("Cambiar contraseña", self._change_password)); security_layout.addWidget(security_card); security_layout.addStretch(); tabs.addTab(security_tab, "Seguridad")
        self.profile_notice = QLabel(); self.profile_notice.setWordWrap(True); layout.addWidget(self.profile_notice)
        return page
        return page

    def _settings_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(42, 36, 42, 36)
        title = QLabel("Ajustes"); title.setObjectName("pageTitle"); layout.addWidget(title)
        card = QFrame(); card.setObjectName("contentCard"); card_layout = QVBoxLayout(card)
        card_title = QLabel("Preferencias de operación"); card_title.setObjectName("cardTitle"); card_layout.addWidget(card_title)
        detail = QLabel("La paleta metalizada blanco, azul y rojo es la identidad fija de esta versión. Las preferencias se guardan por cuenta. Las copias de seguridad locales usan la API consistente de SQLite.")
        detail.setWordWrap(True); card_layout.addWidget(detail)
        preferences = QFormLayout(); self.preference_language = QComboBox(); self.preference_language.addItem("Español (España)", "es-ES")
        self.preference_date_format = QComboBox(); self.preference_date_format.addItem("31/12/2026", "DD/MM/YYYY"); self.preference_date_format.addItem("2026-12-31", "YYYY-MM-DD")
        self.preference_export_directory = field("Carpeta de exportación")[1]; self.preference_export_directory.setPlaceholderText("Se pedirá una ubicación al exportar")
        preferences.addRow("Idioma", self.preference_language); preferences.addRow("Formato de fecha", self.preference_date_format); preferences.addRow("Carpeta de exportación", self.preference_export_directory); preferences.addRow(self._button("Guardar preferencias", self._save_preferences)); card_layout.addLayout(preferences)
        backup_actions = QHBoxLayout(); backup_actions.addWidget(self._button("Crear copia de seguridad", self._create_backup)); backup_actions.addWidget(self._button("Restaurar copia", self._restore_backup)); card_layout.addLayout(backup_actions)
        export_actions = QHBoxLayout(); export_actions.addWidget(self._button("Exportar clientes CSV", self._export_customers)); export_actions.addWidget(self._button("Exportar borradores CSV", self._export_drafts)); card_layout.addLayout(export_actions)
        self.settings_notice = QLabel(); self.settings_notice.setWordWrap(True); card_layout.addWidget(self.settings_notice); layout.addWidget(card); layout.addStretch()
        return page

    def _customers_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(38, 30, 38, 30)
        title = QLabel("Clientes"); title.setObjectName("pageTitle"); layout.addWidget(title)
        subtitle = QLabel("Consulta, busca y mantiene las fichas de clientes."); subtitle.setObjectName("pageSubtitle"); layout.addWidget(subtitle)
        tabs = QTabWidget(); tabs.setObjectName("sectionTabs"); layout.addWidget(tabs)
        list_tab = QWidget(); list_layout = QVBoxLayout(list_tab)
        search_row = QHBoxLayout(); self.customer_search = field("Buscar clientes")[1]; self.customer_search.setPlaceholderText("Buscar por nombre, teléfono o email…")
        self.customer_search.returnPressed.connect(self._refresh_customers); search_row.addWidget(self.customer_search, 1); search_row.addWidget(self._button("Buscar", self._refresh_customers)); list_layout.addLayout(search_row)
        self.customer_table = QTableWidget(0, 5); self.customer_table.setHorizontalHeaderLabels(("ID", "Nombre", "Teléfono", "Email", "Estado")); self.customer_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.customer_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.customer_table.setAlternatingRowColors(True); list_layout.addWidget(self.customer_table)
        tabs.addTab(list_tab, "Listado")
        form_tab = QWidget(); form_layout = QVBoxLayout(form_tab); form = QFormLayout(); form_layout.addLayout(form)
        for attribute, label in (("customer_id", "ID (editar o archivar)"), ("first_name", "Nombre"), ("last_name", "Apellidos"),
            ("phone", "Teléfono"), ("email", "Email (opcional)"), ("address", "Dirección (opcional)"), ("notes", "Notas (opcional)")):
            value = field(label)[1]; setattr(page, attribute, value); form.addRow(label, value)
        actions = QHBoxLayout(); actions.addWidget(self._button("Guardar cliente", lambda: self._save_customer(page))); actions.addWidget(self._button("Archivar cliente", lambda: self._archive_customer(page))); form_layout.addLayout(actions)
        page.notice = QLabel(); page.notice.setWordWrap(True); form_layout.addWidget(page.notice); form_layout.addStretch(); tabs.addTab(form_tab, "Nueva ficha / edición")
        return page

    def _configuration_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(42, 30, 42, 30)
        layout.addWidget(QLabel("Peluquerías y emisores fiscales"))
        tabs = QTabWidget(); layout.addWidget(tabs)
        entity_tab = QWidget(); entity_form = QFormLayout(entity_tab); self.entity_inputs: dict[str, QLineEdit] = {}; self.entity_id = field("ID de emisor")[1]; entity_form.addRow("ID (editar o archivar)", self.entity_id)
        for name, label in (("tax_identifier", "CIF/NIF"), ("legal_name", "Razón social"), ("address", "Dirección"),
            ("postal_code", "Código postal"), ("locality", "Localidad"), ("province", "Provincia"),
            ("country", "País"), ("email", "Email (opcional)"), ("phone", "Teléfono (opcional)")):
            control = field(label)[1]; self.entity_inputs[name] = control; entity_form.addRow(label, control)
        entity_actions = QHBoxLayout(); entity_actions.addWidget(self._button("Guardar emisor", self._save_entity)); entity_actions.addWidget(self._button("Archivar emisor", self._archive_entity)); entity_form.addRow(entity_actions); tabs.addTab(entity_tab, "Emisores")
        salon_tab = QWidget(); salon_form = QFormLayout(salon_tab); self.salon_id = field("ID de peluquería")[1]; salon_form.addRow("ID (editar o archivar)", self.salon_id); self.salon_entity = QComboBox(); salon_form.addRow("Emisor fiscal", self.salon_entity); self.salon_inputs: dict[str, QLineEdit] = {}
        for name, label in (("name", "Nombre comercial"), ("address", "Dirección"), ("postal_code", "Código postal"),
            ("locality", "Localidad"), ("province", "Provincia"), ("country", "País"),
            ("email", "Email (opcional)"), ("phone", "Teléfono (opcional)")):
            control = field(label)[1]; self.salon_inputs[name] = control; salon_form.addRow(label, control)
        salon_actions = QHBoxLayout(); salon_actions.addWidget(self._button("Guardar peluquería", self._save_salon)); salon_actions.addWidget(self._button("Archivar peluquería", self._archive_salon)); salon_form.addRow(salon_actions); tabs.addTab(salon_tab, "Peluquerías")
        hours_tab = QWidget(); hours_form = QFormLayout(hours_tab); self.hours_salon = QComboBox(); self.hours_day = QComboBox()
        self.hours_day.addItems(("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")); self.hours_intervals = field("Tramos")[1]
        self.hours_intervals.setPlaceholderText("09:00-14:00, 16:00-20:00; vacío = cerrado")
        hours_form.addRow("Peluquería", self.hours_salon); hours_form.addRow("Día", self.hours_day); hours_form.addRow("Tramos", self.hours_intervals)
        hours_form.addRow(self._button("Guardar horario", self._save_hours)); self.hours_preview = QLabel("Selecciona una peluquería para consultar su horario."); self.hours_preview.setWordWrap(True); hours_form.addRow("Horario actual", self.hours_preview); self.hours_salon.currentIndexChanged.connect(self._refresh_hours); self.hours_day.currentIndexChanged.connect(self._refresh_hours); tabs.addTab(hours_tab, "Horarios")
        self.configuration_notice = QLabel(); self.configuration_notice.setWordWrap(True); layout.addWidget(self.configuration_notice)
        self.configuration_results = QTextEdit(); self.configuration_results.setReadOnly(True); layout.addWidget(self.configuration_results)
        self.active_salon = QComboBox(); layout.addWidget(QLabel("Establecimiento activo")); layout.addWidget(self.active_salon)
        layout.addWidget(self._button("Establecer como activa", self._set_active_salon))
        layout.addWidget(self._button("Volver a Inicio", lambda: self._navigate(self.dashboard_page)))
        return page

    def _drafts_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(38, 30, 38, 30)
        title = QLabel("Facturas"); title.setObjectName("pageTitle"); layout.addWidget(title)
        warning = QLabel("Solo documentos de composición: el PDF es de prueba y la emisión fiscal está bloqueada."); warning.setObjectName("legalWarning"); layout.addWidget(warning)
        self.draft_tabs = QTabWidget(); layout.addWidget(self.draft_tabs)
        list_tab = QWidget(); list_layout = QVBoxLayout(list_tab); self.draft_table = QTableWidget(0, 4); self.draft_table.setHorizontalHeaderLabels(("ID", "Cliente", "Peluquería", "Total")); self.draft_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.draft_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.draft_table.setAlternatingRowColors(True); list_layout.addWidget(self.draft_table)
        list_actions = QHBoxLayout(); list_actions.addWidget(self._button("Editar seleccionado", self._load_draft)); list_actions.addWidget(self._button("Exportar PDF de prueba", self._export_draft_pdf)); list_actions.addWidget(self._button("Descartar seleccionado", self._discard_draft)); list_actions.addStretch(); list_layout.addLayout(list_actions); self.draft_tabs.addTab(list_tab, "Borradores")
        create_tab = QWidget(); create_layout = QVBoxLayout(create_tab); customer_form = QFormLayout(); self.draft_customer_id = field("ID de cliente")[1]; customer_form.addRow("ID de cliente", self.draft_customer_id); create_layout.addLayout(customer_form)
        line_card = QFrame(); line_card.setObjectName("contentCard"); line_form = QFormLayout(line_card); line_title = QLabel("Añadir línea de servicio"); line_title.setObjectName("cardTitle"); line_form.addRow(line_title)
        self.line_description = field("Servicio")[1]; self.line_description.setText("Servicio de peluquería"); self.line_quantity = field("Cantidad")[1]; self.line_quantity.setText("1"); self.line_price = field("Precio sin IVA")[1]; self.line_discount = field("Descuento (%)")[1]; self.line_discount.setText("0"); self.line_tax = field("IVA (%)")[1]; self.line_tax.setText("21")
        for label, control in (("Servicio", self.line_description), ("Cantidad", self.line_quantity), ("Precio sin IVA", self.line_price), ("Descuento (%)", self.line_discount), ("IVA (%)", self.line_tax)): line_form.addRow(label, control)
        line_form.addRow(self._button("Añadir línea", self._add_draft_line)); create_layout.addWidget(line_card)
        self.draft_line_table = QTableWidget(0, 5); self.draft_line_table.setHorizontalHeaderLabels(("Servicio", "Cantidad", "Precio", "Desc.", "IVA")); self.draft_line_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.draft_line_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); create_layout.addWidget(self.draft_line_table)
        actions = QHBoxLayout(); actions.addWidget(self._button("Quitar línea seleccionada", self._remove_draft_line)); actions.addStretch(); self.save_draft_button = self._button("Crear borrador", self._save_draft); actions.addWidget(self.save_draft_button); create_layout.addLayout(actions); self.draft_notice = QLabel(); self.draft_notice.setWordWrap(True); create_layout.addWidget(self.draft_notice); self.draft_tabs.addTab(create_tab, "Nuevo borrador")
        self.draft_lines: list[InvoiceLineCommand] = []
        self.editing_draft_id: int | None = None
        return page

    def _open_customers(self) -> None:
        self._navigate(self.customers_page)

    def _open_configuration(self) -> None:
        self._navigate(self.configuration_page)

    def _open_drafts(self) -> None:
        self._navigate(self.drafts_page)

    def _refresh_drafts(self) -> None:
        if self.account_id is None: return
        rows = self.invoicing.list_drafts(self.account_id)
        self.draft_table.setRowCount(len(rows))
        for index, item in enumerate(rows):
            for column, value in enumerate((str(item["id"]), str(item["customer_name"]), str(item["salon_name"]), f"{item['total']} EUR")):
                self.draft_table.setItem(index, column, QTableWidgetItem(value))

    def _draft_message(self, message: str, error: bool = False) -> None:
        self.draft_notice.setText(message); self.draft_notice.setStyleSheet("color: #a8162d;" if error else "color: #075ca8;")

    def _add_draft_line(self) -> None:
        try:
            command = InvoiceLineCommand(self.line_description.text(), self.line_quantity.text(), self.line_price.text(), self.line_discount.text(), self.line_tax.text())
            self.invoicing.calculate_line(command)
            self.draft_lines.append(command); row = self.draft_line_table.rowCount(); self.draft_line_table.insertRow(row)
            for column, value in enumerate((command.description, command.quantity, command.unit_price, command.discount_percentage, command.tax_rate)): self.draft_line_table.setItem(row, column, QTableWidgetItem(value))
            self.line_price.clear(); self.line_description.setText("Servicio de peluquería"); self._draft_message("Línea añadida.")
        except DomainError as error:
            self._draft_message(str(error), True)

    def _remove_draft_line(self) -> None:
        row = self.draft_line_table.currentRow()
        if row < 0: self._draft_message("Selecciona una línea para eliminar.", True); return
        del self.draft_lines[row]; self.draft_line_table.removeRow(row); self._draft_message("Línea eliminada.")

    def _selected_draft_id(self) -> int:
        row = self.draft_table.currentRow()
        if row < 0 or not (item := self.draft_table.item(row, 0)):
            raise DomainError("Selecciona un borrador.")
        return int(item.text())

    def _load_draft(self) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            draft = self.invoicing.get_draft(self.account_id, self._selected_draft_id())
            self.editing_draft_id = int(draft["id"]); self.draft_customer_id.setText(str(draft["customer_id"]))
            self.draft_lines = [InvoiceLineCommand(**line) for line in draft["lines"]]
            self.draft_line_table.setRowCount(0)
            for command in self.draft_lines:
                row = self.draft_line_table.rowCount(); self.draft_line_table.insertRow(row)
                for column, value in enumerate((command.description, command.quantity, command.unit_price, command.discount_percentage, command.tax_rate)): self.draft_line_table.setItem(row, column, QTableWidgetItem(value))
            self.save_draft_button.setText("Guardar cambios"); self.draft_tabs.setCurrentIndex(1)
            self._draft_message("Editando borrador. Se conserva como borrador de prueba.")
        except (DomainError, ValueError) as error:
            self._draft_message(str(error), True)

    def _discard_draft(self) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            draft_id = self._selected_draft_id()
            answer = QMessageBox.question(self, "Descartar borrador", "Se eliminarán este borrador y sus líneas. No se ha emitido ninguna factura. ¿Deseas continuar?")
            if answer != QMessageBox.StandardButton.Yes: return
            self.invoicing.discard_draft(self.account_id, draft_id)
            if self.editing_draft_id == draft_id: self._reset_draft_form()
            self._refresh_drafts(); self._refresh_dashboard(); self._draft_message("Borrador descartado.")
        except DomainError as error:
            self._draft_message(str(error), True)

    def _export_draft_pdf(self) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            draft_id = self._selected_draft_id()
            selected, _ = QFileDialog.getSaveFileName(self, "Guardar PDF de prueba", f"borrador-{draft_id}.pdf", "PDF (*.pdf)")
            if not selected: return
            path = self.pdf_exports.export_draft(self.account_id, draft_id, Path(selected))
            self._draft_message(f"PDF de prueba guardado en: {path}. No es una factura fiscal.")
        except DomainError as error:
            self._draft_message(str(error), True)

    def _reset_draft_form(self) -> None:
        self.editing_draft_id = None; self.draft_customer_id.clear(); self.draft_lines.clear(); self.draft_line_table.setRowCount(0)
        self.save_draft_button.setText("Crear borrador")

    def _save_draft(self) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            active = self.management.active_salon(self.account_id)
            if not active: raise DomainError("Selecciona un establecimiento activo antes de crear un borrador.")
            command = CreateDraftCommand(int(active["id"]), int(self.draft_customer_id.text()), self.draft_lines)
            if self.editing_draft_id is None:
                self.invoicing.create_draft(self.account_id, command); message = "Borrador creado. No se ha emitido ninguna factura."
            else:
                self.invoicing.update_draft(self.account_id, self.editing_draft_id, UpdateDraftCommand(command.salon_id, command.customer_id, command.lines)); message = "Borrador actualizado. No se ha emitido ninguna factura."
            self._reset_draft_form(); self._draft_message(message); self._refresh_drafts(); self._refresh_dashboard()
        except DomainError as error:
            self._draft_message(str(error), True)
        except ValueError:
            self._draft_message("El ID de cliente debe ser numérico.", True)

    def _refresh_customers(self) -> None:
        if self.account_id is None: return
        rows = self.management.list_customers(self.account_id, self.customer_search.text())
        self.customer_table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            values = (str(row["id"]), f"{row['first_name']} {row['last_name']}", str(row["phone"]), str(row["email"] or "—"), "Activo" if row["active"] else "Archivado")
            for column, value in enumerate(values): self.customer_table.setItem(index, column, QTableWidgetItem(value))

    def _customer_message(self, message: str, error: bool = False) -> None:
        self.customers_page.notice.setText(message)
        self.customers_page.notice.setStyleSheet("color: #a8162d;" if error else "color: #075ca8;")

    def _save_customer(self, page: AccessPage) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            command = CustomerCommand(**{name: getattr(page, name).text() for name in CustomerCommand.__dataclass_fields__})
            if page.customer_id.text().strip(): self.management.update_customer(self.account_id, int(page.customer_id.text()), command)
            else: self.management.create_customer(self.account_id, command)
            for name in (*CustomerCommand.__dataclass_fields__, "customer_id"): getattr(page, name).clear()
            self._customer_message("Cliente guardado correctamente."); self._refresh_customers()
        except DomainError as error:
            self._customer_message(str(error), True)
        except ValueError:
            self._customer_message("El ID de cliente debe ser numérico.", True)

    def _archive_customer(self, page: AccessPage) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            self.management.archive_customer(self.account_id, int(page.customer_id.text()))
            page.customer_id.clear(); self._customer_message("Cliente archivado."); self._refresh_customers()
        except DomainError as error:
            self._customer_message(str(error), True)
        except ValueError:
            self._customer_message("Indica un ID de cliente numérico.", True)

    def _refresh_configuration(self) -> None:
        if self.account_id is None: return
        entities = self.management.list_legal_entities(self.account_id)
        salons = self.management.list_salons(self.account_id)
        self.salon_entity.clear()
        for entity in entities: self.salon_entity.addItem(f"{entity['legal_name']} · {entity['tax_identifier']}", entity["id"])
        self.hours_salon.clear()
        self.active_salon.clear()
        for salon in salons: self.hours_salon.addItem(f"{salon['name']} · {salon['legal_name']}", salon["id"])
        for salon in salons: self.active_salon.addItem(f"{salon['name']} · {salon['legal_name']}", salon["id"])
        selected = self.management.active_salon(self.account_id)
        if selected:
            index = self.active_salon.findData(selected["id"])
            self.active_salon.setCurrentIndex(index)
        entity_lines = [f"Emisor #{item['id']}: {item['legal_name']} · {item['tax_identifier']}" for item in entities]
        salon_lines = [f"Peluquería #{item['id']}: {item['name']} · {item['legal_name']}" for item in salons]
        self.configuration_results.setPlainText("\n".join(entity_lines + salon_lines) or "No hay emisores ni peluquerías registrados.")
        self._refresh_hours()

    def _refresh_hours(self) -> None:
        if self.account_id is None: return
        salon_id = self.hours_salon.currentData()
        if salon_id is None:
            self.hours_preview.setText("Selecciona una peluquería para consultar su horario."); return
        try:
            intervals = self.management.opening_intervals(self.account_id, int(salon_id), self.hours_day.currentIndex())
            if intervals:
                value = ", ".join(f"{start}–{end}" for start, end in intervals)
                self.hours_preview.setText(value); self.hours_intervals.setText(", ".join(f"{start}-{end}" for start, end in intervals))
            else:
                self.hours_preview.setText("Cerrado"); self.hours_intervals.clear()
        except DomainError as error:
            self.hours_preview.setText(str(error))

    def _refresh_dashboard(self) -> None:
        if self.account_id is None: return
        active = self.management.active_salon(self.account_id)
        metrics = self.management.dashboard_metrics(self.account_id)
        salon_name = str(active["name"]) if active else "sin seleccionar"
        profile = self.auth.profile_summary(self.account_id)
        self.shell_user.setText(f"{profile['first_name']} {profile['last_name']}")
        self.dashboard_active.setText("Establecimiento activo: " + salon_name)
        self.shell_salon.setText("Establecimiento activo\n" + salon_name)
        for key, value in self.dashboard_cards.items(): value.setText(str(metrics[key]))

    def _refresh_profile(self) -> None:
        if self.account_id is None: return
        profile = self.auth.profile_summary(self.account_id)
        self.profile_name.setText(f"{profile['first_name']} {profile['last_name']}")
        self.profile_email.setText(profile["email"])
        self.profile_tax_id.setText(profile["tax_identifier"])
        self.profile_phone.setText(profile["phone"] or "No indicado")
        self.profile_first_name.setText(profile["first_name"])
        self.profile_last_name.setText(profile["last_name"])
        self.profile_email_input.setText(profile["email"])
        self.profile_phone_input.setText(profile["phone"])

    def _profile_message(self, message: str, error: bool = False) -> None:
        self.profile_notice.setText(message)
        self.profile_notice.setStyleSheet("color: #a8162d;" if error else "color: #075ca8;")

    def _settings_message(self, message: str, error: bool = False) -> None:
        self.settings_notice.setText(message)
        self.settings_notice.setStyleSheet("color: #a8162d;" if error else "color: #075ca8;")

    def _refresh_settings(self) -> None:
        if self.account_id is None: return
        preferences = self.management.preferences(self.account_id)
        self.preference_language.setCurrentIndex(max(0, self.preference_language.findData(preferences["language"])))
        self.preference_date_format.setCurrentIndex(max(0, self.preference_date_format.findData(preferences["date_format"])))
        self.preference_export_directory.setText(str(preferences["export_directory"] or ""))

    def _save_preferences(self) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            self.management.update_preferences(self.account_id, str(self.preference_language.currentData()),
                                               str(self.preference_date_format.currentData()), self.preference_export_directory.text())
            self._settings_message("Preferencias guardadas para esta cuenta.")
        except DomainError as error:
            self._settings_message(str(error), True)

    def _create_backup(self) -> None:
        selected, _ = QFileDialog.getSaveFileName(self, "Guardar copia de seguridad", "hair-salon-backup.db", "Base de datos SQLite (*.db)")
        if not selected: return
        try:
            path = self.backups.create_backup(Path(selected))
            self._settings_message(f"Copia creada correctamente en: {path}")
        except DomainError as error:
            self._settings_message(str(error), True)

    def _restore_backup(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(self, "Seleccionar copia de seguridad", "", "Base de datos SQLite (*.db)")
        if not selected: return
        answer = QMessageBox.question(self, "Restaurar copia", "La restauración reemplazará los datos locales actuales y cerrará la sesión. ¿Deseas continuar?")
        if answer != QMessageBox.StandardButton.Yes: return
        try:
            self.backups.restore_backup(Path(selected))
            self._logout()
        except DomainError as error:
            self._settings_message(str(error), True)

    def _export_customers(self) -> None:
        self._export_csv("clientes.csv", self.exports.export_customers)

    def _export_drafts(self) -> None:
        self._export_csv("borradores.csv", self.exports.export_drafts)

    def _export_csv(self, suggested_name: str, export: Callable[[int, Path], Path]) -> None:
        if self.account_id is None:
            self._settings_message("La sesión ha terminado.", True); return
        directory = self.management.preferences(self.account_id)["export_directory"] or suggested_name
        selected, _ = QFileDialog.getSaveFileName(self, "Guardar exportación", str(Path(str(directory)) / suggested_name) if directory != suggested_name else suggested_name, "CSV (*.csv)")
        if not selected: return
        try:
            path = export(self.account_id, Path(selected))
            self._settings_message(f"Exportación creada correctamente en: {path}")
        except DomainError as error:
            self._settings_message(str(error), True)

    def _save_profile(self) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            self.auth.update_profile(self.account_id, UpdateProfileCommand(self.profile_first_name.text(), self.profile_last_name.text(), self.profile_email_input.text(), self.profile_phone_input.text()))
            self._refresh_profile(); self._refresh_dashboard(); self._profile_message("Datos personales actualizados.")
        except DomainError as error:
            self._profile_message(str(error), True)

    def _change_password(self) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            self.auth.change_password(self.account_id, self.current_password.text(), self.new_password.text(), self.confirm_password.text())
            self.current_password.clear(); self.new_password.clear(); self.confirm_password.clear(); self._profile_message("Contraseña actualizada correctamente.")
        except DomainError as error:
            self._profile_message(str(error), True)

    def _set_active_salon(self) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            salon_id = self.active_salon.currentData()
            if salon_id is None: raise DomainError("Crea primero una peluquería.")
            self.management.set_active_salon(self.account_id, int(salon_id))
            self._configuration_success("Establecimiento activo actualizado."); self._refresh_dashboard()
        except DomainError as error:
            self._configuration_error(error)

    def _configuration_error(self, error: DomainError) -> None:
        self.configuration_notice.setText(str(error)); self.configuration_notice.setStyleSheet("color: #a8162d;")

    def _configuration_success(self, message: str) -> None:
        self.configuration_notice.setText(message); self.configuration_notice.setStyleSheet("color: #075ca8;")

    def _save_entity(self) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            command = LegalEntityCommand(**{name: control.text() for name, control in self.entity_inputs.items()})
            if self.entity_id.text().strip(): self.management.update_legal_entity(self.account_id, int(self.entity_id.text()), command)
            else: self.management.create_legal_entity(self.account_id, command)
            for control in self.entity_inputs.values(): control.clear()
            self.entity_id.clear(); self._configuration_success("Emisor fiscal guardado."); self._refresh_configuration()
        except DomainError as error:
            self._configuration_error(error)
        except ValueError:
            self._configuration_error(DomainError("El ID de emisor debe ser numérico."))

    def _archive_entity(self) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            self.management.archive_legal_entity(self.account_id, int(self.entity_id.text()))
            self.entity_id.clear(); self._configuration_success("Emisor archivado."); self._refresh_configuration()
        except DomainError as error:
            self._configuration_error(error)
        except ValueError:
            self._configuration_error(DomainError("Indica un ID de emisor numérico."))

    def _save_salon(self) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            entity_id = self.salon_entity.currentData()
            if entity_id is None: raise DomainError("Crea primero un emisor fiscal.")
            command = SalonCommand(legal_entity_id=int(entity_id), **{name: control.text() for name, control in self.salon_inputs.items()})
            if self.salon_id.text().strip(): self.management.update_salon(self.account_id, int(self.salon_id.text()), command)
            else: self.management.create_salon(self.account_id, command)
            for control in self.salon_inputs.values(): control.clear()
            self.salon_id.clear(); self._configuration_success("Peluquería guardada."); self._refresh_configuration()
        except DomainError as error:
            self._configuration_error(error)
        except ValueError:
            self._configuration_error(DomainError("El ID de peluquería debe ser numérico."))

    def _archive_salon(self) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            self.management.archive_salon(self.account_id, int(self.salon_id.text()))
            self.salon_id.clear(); self._configuration_success("Peluquería archivada."); self._refresh_configuration(); self._refresh_dashboard()
        except DomainError as error:
            self._configuration_error(error)
        except ValueError:
            self._configuration_error(DomainError("Indica un ID de peluquería numérico."))

    def _save_hours(self) -> None:
        try:
            if self.account_id is None: raise DomainError("La sesión ha terminado.")
            salon_id = self.hours_salon.currentData()
            if salon_id is None: raise DomainError("Crea primero una peluquería.")
            values = [value.strip() for value in self.hours_intervals.text().split(",") if value.strip()]
            intervals = [tuple(value.split("-", 1)) for value in values]
            if any(len(interval) != 2 for interval in intervals): raise DomainError("Usa tramos con formato HH:MM-HH:MM.")
            self.management.set_opening_intervals(self.account_id, int(salon_id), self.hours_day.currentIndex(), intervals)
            self._configuration_success("Horario guardado."); self._refresh_hours()
        except DomainError as error:
            self._configuration_error(error)

    def _login(self, page: AccessPage) -> None:
        try:
            self.account_id = self.auth.authenticate(page.email.text(), page.password.text())
            page.password.clear(); self._refresh_dashboard(); self.pages.setCurrentWidget(self.shell); self.resize(1120, 720); self._navigate(self.dashboard_page)
        except DomainError as error:
            page.error(error)

    def _logout(self) -> None:
        self.account_id = None
        self._show_access(self.login_page, 480, 500)

    def _register(self, page: AccessPage) -> None:
        try:
            values = {name: getattr(page, name).text() for name in RegisterCommand.__dataclass_fields__
                      if name != "password_confirmation"}
            values["password_confirmation"] = page.confirmation.text()
            command = RegisterCommand(**values)
            code = self.auth.register(command)
            QMessageBox.information(self, "Guarda tu código", "Guárdalo fuera de la aplicación; solo se muestra una vez:\n\n" + code)
            self._show_access(self.login_page, 480, 500)
        except DomainError as error:
            page.error(error)

    def _recover(self, page: AccessPage) -> None:
        try:
            self.auth.reset_password(page.email.text(), page.code.text(), page.password.text(), page.confirmation.text())
            page.success("Contraseña actualizada. Ya puedes iniciar sesión.")
        except DomainError as error:
            page.error(error)


def run(auth: AuthService) -> int:
    application = QApplication.instance() or QApplication([])
    application.setStyle("Fusion")
    application.setStyleSheet("""
        QWidget { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:0.48 #eef5fb, stop:1 #ffffff); color: #102b52; font-family: "Inter", "Segoe UI", sans-serif; font-size: 14px; }
        QLabel#pageTitle { font-size: 30px; font-weight: 700; color: #075ca8; }
        QLabel#pageSubtitle { color: #315b84; margin-bottom: 14px; }
        QFrame#sidebar { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #032d62, stop:0.48 #126eb9, stop:1 #032d62); color: #ffffff; }
        QLabel#brand { background: transparent; color: #ffffff; font-size: 16px; font-weight: 800; letter-spacing: 1px; }
        QLabel#sidebarLogo { background: transparent; }
        QLabel#sidebarUser { background: transparent; color: #d9efff; margin-top: 12px; }
        QLabel#activeSalon { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #227fc8, stop:0.5 #064882, stop:1 #1c70b5); border: 1px solid #ffffff; border-radius: 10px; color: #ffffff; padding: 11px; margin-top: 16px; }
        QLabel#dashboardContext { color: #315b84; font-size: 15px; }
        QFrame#metricCard, QFrame#contentCard { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:0.5 #f0f8ff, stop:1 #ffffff); border: 1px solid #8abfe8; border-radius: 12px; }
        QLabel#metricValue { color: #075ca8; font-size: 28px; font-weight: 750; }
        QLabel#metricLabel { color: #315b84; font-size: 12px; font-weight: 600; }
        QLabel#cardTitle { color: #075ca8; font-size: 16px; font-weight: 700; }
        QLabel#legalWarning { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fff7f8, stop:0.5 #ffdce2, stop:1 #fff7f8); border: 1px solid #c91e3b; border-radius: 9px; color: #8d1027; padding: 12px; }
        QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a9be2, stop:0.48 #075ca8, stop:1 #043f78); border: 1px solid #ffffff; border-radius: 8px; color: white; font-weight: 650; padding: 10px 15px; }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #55b5f0, stop:0.48 #0a70c5, stop:1 #075ca8); }
        QPushButton#navButton, QPushButton#logoutButton { background: transparent; border: 1px solid transparent; color: #ffffff; text-align: left; padding: 11px 12px; }
        QPushButton#navButton:hover, QPushButton#logoutButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c91635, stop:0.5 #f0435d, stop:1 #c91635); border-color: #ffffff; }
        QLineEdit, QComboBox, QTextEdit, QTableWidget { background: #ffffff; border: 1px solid #78b6e4; border-radius: 8px; padding: 8px; selection-background-color: #c91635; selection-color: #ffffff; }
        QLineEdit:focus, QComboBox:focus { border: 2px solid #c91635; }
        QTabWidget::pane { border: 1px solid #78b6e4; background: #ffffff; border-radius: 10px; }
        QTabBar::tab { background: #dcefff; color: #075ca8; border: 1px solid #8abfe8; padding: 10px 18px; margin-right: 3px; }
        QTabBar::tab:selected { background: #ffffff; color: #c91635; font-weight: 700; }
        QHeaderView::section { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #eaf6ff, stop:0.5 #b6dfff, stop:1 #eaf6ff); color: #075ca8; border: 0; padding: 9px; font-weight: 700; }
    """)
    window = MainWindow(auth); window.show()
    return application.exec()
