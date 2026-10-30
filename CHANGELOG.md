# Changelog

All notable changes are documented here.

## [0.1.0] - 2026-10-29

### Added

- Local SQLite schema and migration bootstrap.
- Secure local account registration, login throttling and one-use offline recovery codes.
- PySide6 access flow and authentication tests.
- Architecture, data-model, usage and invoicing-scope documentation.
- Migration and application services for legal entities, salons, opening intervals and customers.
- Basic protected customer registration and listing screen.
- Customer update/archive controls and protected forms for issuers, salons and opening hours.
- Persistent active-salon preference and dashboard indicators backed by stored data.
- Draft invoices with `Decimal` calculations, discount and configurable VAT, without fiscal issuance.
- Desktop shell with persistent sidebar, visual theme and customer list/form tabs with search table.
- Dashboard metric cards, profile summary and explicit settings scope in the protected shell.
- Editable operator profile and password change protected by the current password.
- Controlled editing/archiving of issuers and salons, plus multiline draft-invoice entry UI.
- Consistent local SQLite backups and integrity-checked restoration with explicit confirmation.
- Account-scoped CSV export of customers and draft invoices without authentication secrets.
- Assisted opening-hours consultation and replacement by salon and weekday.
- Editable and discardable draft invoices, restricted to drafts and clearly blocked from fiscal issuance.
- PDF export for drafts, visibly marked as a non-fiscal test document.
- White, blue and red metallic visual palette, plus an explicit open-source scope limited to draft composition documents.
- Per-account date and export-folder preferences, and schema-validated backup restoration.
- Windows packaging script and distribution/licensing checklist.
- Headless smoke tests for the composition-only interface and metallic palette contract.
- GitHub Actions workflow to test and package the Windows artifact.
