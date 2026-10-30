# Hair Salon Management

Hair Salon Management is a local desktop application for managing one or more hair salons. It is built with Python and PySide6 and keeps its data in a local SQLite database.

The current release focuses on secure local access, customer and salon management, invoice **draft composition**, local operation, and a clear path for future extensions. The user interface is in Spanish (Spain).

> **Important:** this is not invoicing software for real-world use. It does not issue fiscal invoices and does not claim compliance with SIF, VERI*FACTU, or NO VERI*FACTU.

## Features

- Local operator registration, login, logout, progressive login throttling, and one-use offline recovery codes.
- Password storage using salted `scrypt`; no passwords or recovery codes are stored in plain text.
- Account-scoped customer management: create, update, search, archive, and export to CSV.
- Fiscal-entity and salon management, including shared legal entities, opening hours, and a persistent active salon.
- Multi-line service drafts calculated with `Decimal`, configurable VAT and discounts, and no floating-point money calculations.
- Editable or discardable drafts and non-fiscal PDF composition previews.
- Local SQLite backups and schema-checked restoration.
- Account preferences for date format and the default CSV export folder.
- Metallic white, blue, and red desktop interface.

## Scope and limitations

PDF exports are visibly labelled as test composition documents. They have no fiscal number, QR code, hash, record chaining, signature, AEAT submission, or legal value as an issued invoice.

Fiscal issuance, invoice numbering, payment collection for issued invoices, SIF records, and tax compliance are deliberately outside this distribution's scope. Any developer adapting the project for real invoicing is responsible for defining, implementing, testing, and validating the applicable legal requirements. See the [composition-document scope](docs/invoicing-compliance.md) and [ADR 0002](docs/decisions/0002-alcance-documentos-de-prueba.md).

## Requirements

- Python 3.11 or newer
- PySide6 6.6 or newer

## Install and run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m hair_salon_management
```

The application stores its SQLite database in the user data directory (`~/.local/share/hair-salon-management` on Unix-like systems). To use a different location, define `HAIR_SALON_MANAGER_DATA_DIR` before starting the application.

## Tests

Run the complete test suite with:

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
```

`QT_QPA_PLATFORM=offscreen` enables the interface smoke tests on headless environments. The test suite covers authentication, backups, exports, draft calculations, preferences, data integrity, and basic UI construction.

## Architecture

The project follows a pragmatic dependency flow:

```text
Presentation (PySide6) → Application services → Domain
                                     ↑
                         Infrastructure (SQLite, security, exports)
```

Widgets do not access SQLite directly. Business rules and account scoping live in application services, while persistence, backups, CSV exports, and PDF composition are infrastructure concerns.

Further details are available in the [architecture guide](docs/architecture.md) and [data model](docs/data-model.md).

## Windows packaging

Windows packaging is prepared with PyInstaller:

```powershell
.\scripts\build-windows.ps1
```

The GitHub Actions workflow in `.github/workflows/windows.yml` runs tests and produces a Windows artifact when the repository is pushed to GitHub. Packaging has not been validated on a clean Windows machine and no executable is signed or published yet. See the [Windows packaging guide](docs/packaging-windows.es.md).

## Licensing and contributions

The repository does not yet declare a project license. Do not publish or redistribute a binary until the owner has chosen a license and added `LICENSE` and `NOTICE` files. PySide6/Qt and all future dependencies must be reviewed for their applicable licensing obligations.

Contributions should preserve the local-first design, avoid adding secrets or real customer data, include automated tests, and keep functional documentation accurate. The detailed functional specification is currently maintained in Spanish in [README.es.md](README.es.md).

## Documentation

- [Spanish README](README.es.md)
- [User guide](docs/user-guide.es.md)
- [Implementation plan](docs/implementation-plan.md)
- [Invoicing and composition scope](docs/invoicing-compliance.md)
- [Windows packaging guide](docs/packaging-windows.es.md)
