# Hair Salon Management Wiki

## Overview

Hair Salon Management is a **local-first desktop application** for managing one or more hair salons. It is built with Python and PySide6, uses a local SQLite database, and currently provides a Spanish (Spain) interface.

The project focuses on secure local access, customer records, salon and fiscal-entity configuration, service-document drafts, exports, and recoverable local operation.

> **Important:** Hair Salon Management is not software for real-world invoicing. Its PDF exports are test composition documents only; it does not issue fiscal invoices and makes no claim of SIF, VERI*FACTU, or NO VERI*FACTU compliance.

## What you can do

- Register, sign in, sign out, and recover local access with one-use offline recovery codes.
- Keep credentials protected with salted `scrypt`; passwords and recovery codes are never stored in plain text.
- Create, update, search, archive, and export customer records, scoped to the current account.
- Configure fiscal entities, salons, opening hours, and a persistent active salon.
- Compose editable multi-line service drafts using `Decimal` calculations, configurable VAT, and discounts.
- Produce visibly non-fiscal PDF composition previews, or discard a draft.
- Create local SQLite backups, restore a schema-checked backup, and export CSV files.
- Set per-account date-format and default CSV-export-folder preferences.

## First steps

### Requirements

- Python 3.11 or later
- PySide6 6.6 or later

### Install and run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m hair_salon_management
```

By default, the application keeps its database in the operating system user-data directory (for example, `~/.local/share/hair-salon-management` on Unix-like systems). Set `HAIR_SALON_MANAGER_DATA_DIR` before launching it to use another local location.

## Everyday workflow

1. Create a local operator account and sign in.
2. Add the fiscal entity and the salon or salons it owns.
3. Select the active salon and configure its opening hours.
4. Add and maintain customer records.
5. Compose a service draft, adjusting VAT and discounts as needed.
6. Export a **test-only** PDF composition or keep the draft editable.
7. Create backups regularly and verify the restore procedure on non-production data.

## Data, privacy, and backups

The application is designed for local operation. Data is stored in SQLite and does not require a remote service. Keep database files, backup files, CSV exports, and PDF compositions in locations protected by your operating system account.

Do not post real customer data, passwords, recovery codes, database files, or backups in GitHub Issues or Discussions. When reporting an issue, use fictional examples and remove paths or details that could identify a person or a business.

## Document scope

PDF exports are deliberately marked as test composition documents. They do not contain a fiscal number, QR code, hash, record chain, signature, AEAT submission, or any legal value as an issued invoice.

Fiscal issuance, invoice numbering, payment collection for issued invoices, SIF records, and tax compliance are outside the current distribution. Any future adaptation for real invoicing must be independently designed, implemented, tested, and validated against the applicable legal requirements.

See the [composition-document scope](docs/invoicing-compliance.md) and [ADR 0002](docs/decisions/0002-alcance-documentos-de-prueba.md).

## Architecture

The project follows a pragmatic dependency flow:

```text
Presentation (PySide6) → Application services → Domain
                                     ↑
                         Infrastructure (SQLite, security, exports)
```

Widgets do not access SQLite directly. Application services hold business rules and account scoping; infrastructure handles persistence, security, backups, CSV exports, and PDF composition.

Read the [architecture guide](docs/architecture.md) and the [data model](docs/data-model.md) for more detail.

## Testing

Run the full suite with:

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
```

The off-screen Qt setting enables interface smoke tests in headless environments. The suite covers authentication, backups, exports, draft calculations, preferences, data integrity, and basic UI construction.

## Windows packaging

The project includes a PyInstaller-based Windows packaging workflow:

```powershell
.\scripts\build-windows.ps1
```

The GitHub Actions workflow at `.github/workflows/windows.yml` runs tests and creates a Windows artifact after a push. Packaging still needs validation on a clean Windows machine; the executable is neither signed nor published. Consult the [Windows packaging guide](docs/packaging-windows.es.md) before distributing any artifact.

## Contributing and discussing changes

Contributions should preserve the local-first approach, avoid secrets and real personal data, add suitable automated tests, and keep documentation accurate.

- Use [Issues](https://github.com/ManuelAf-ConnectApp/HairSalonManager/issues) for reproducible bugs and agreed, actionable work.
- Use [Discussions](https://github.com/ManuelAf-ConnectApp/HairSalonManager/discussions) for ideas, questions, product feedback, and non-sensitive examples.
- Read the [Spanish functional specification](README.es.md) for the maintained detailed specification.

## License status

The project does not yet declare a license. Do not publish or redistribute a binary until the owner selects a license and adds `LICENSE` and `NOTICE` files. Review the licensing obligations of Python, PySide6/Qt, and any future dependencies before distribution.

## Documentation map

- [README](README.md)
- [Spanish README](README.es.md)
- [User guide (Spanish)](docs/user-guide.es.md)
- [Implementation plan](docs/implementation-plan.md)
- [Composition-document scope](docs/invoicing-compliance.md)
- [Windows packaging guide (Spanish)](docs/packaging-windows.es.md)
