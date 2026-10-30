from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def migrate(self) -> None:
        migrations = {1: self._migration_1, 2: self._migration_2, 3: self._migration_3, 4: self._migration_4, 5: self._migration_5}
        with self.session() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)")
            applied = {row["version"] for row in connection.execute("SELECT version FROM schema_migrations")}
            for version, migration in migrations.items():
                if version not in applied:
                    migration(connection)
                    connection.execute("INSERT INTO schema_migrations(version) VALUES (?)", (version,))

    @staticmethod
    def _migration_1(connection: sqlite3.Connection) -> None:
        connection.executescript("""
                    CREATE TABLE operator_accounts (
                      id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                      password_hash TEXT NOT NULL, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
                      tax_identifier TEXT NOT NULL, address TEXT NOT NULL, postal_code TEXT NOT NULL,
                      country TEXT NOT NULL, phone TEXT, active INTEGER NOT NULL DEFAULT 1,
                      failed_attempts INTEGER NOT NULL DEFAULT 0, locked_until TEXT,
                      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE recovery_credentials (
                      id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL REFERENCES operator_accounts(id),
                      code_hash TEXT NOT NULL, used_at TEXT, revoked_at TEXT,
                      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE audit_events (
                      id INTEGER PRIMARY KEY, account_id INTEGER REFERENCES operator_accounts(id),
                      event_type TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX idx_audit_account_created ON audit_events(account_id, created_at);
        """)

    @staticmethod
    def _migration_2(connection: sqlite3.Connection) -> None:
        connection.executescript("""
            CREATE TABLE legal_entities (
              id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL REFERENCES operator_accounts(id),
              tax_identifier TEXT NOT NULL, legal_name TEXT NOT NULL, address TEXT NOT NULL,
              postal_code TEXT NOT NULL, locality TEXT NOT NULL, province TEXT NOT NULL,
              country TEXT NOT NULL, email TEXT, phone TEXT, active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(account_id, tax_identifier)
            );
            CREATE TABLE salons (
              id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL REFERENCES operator_accounts(id),
              legal_entity_id INTEGER NOT NULL REFERENCES legal_entities(id), name TEXT NOT NULL,
              address TEXT NOT NULL, postal_code TEXT NOT NULL, locality TEXT NOT NULL,
              province TEXT NOT NULL, country TEXT NOT NULL, email TEXT, phone TEXT,
              active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE opening_intervals (
              id INTEGER PRIMARY KEY, salon_id INTEGER NOT NULL REFERENCES salons(id) ON DELETE CASCADE,
              weekday INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 6), starts_at TEXT NOT NULL,
              ends_at TEXT NOT NULL, CHECK(starts_at < ends_at), UNIQUE(salon_id, weekday, starts_at, ends_at)
            );
            CREATE TABLE customers (
              id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL REFERENCES operator_accounts(id),
              first_name TEXT NOT NULL, last_name TEXT NOT NULL, address TEXT, email TEXT,
              phone TEXT NOT NULL, notes TEXT, active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX idx_customers_account_name ON customers(account_id, last_name, first_name);
            CREATE INDEX idx_customers_account_phone ON customers(account_id, phone);
            CREATE INDEX idx_salons_account ON salons(account_id);
        """)

    @staticmethod
    def _migration_3(connection: sqlite3.Connection) -> None:
        connection.executescript("""
            CREATE TABLE account_preferences (
              account_id INTEGER PRIMARY KEY REFERENCES operator_accounts(id),
              active_salon_id INTEGER REFERENCES salons(id),
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

    @staticmethod
    def _migration_4(connection: sqlite3.Connection) -> None:
        connection.executescript("""
            CREATE TABLE invoices (
              id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL REFERENCES operator_accounts(id),
              salon_id INTEGER NOT NULL REFERENCES salons(id), legal_entity_id INTEGER NOT NULL REFERENCES legal_entities(id),
              customer_id INTEGER NOT NULL REFERENCES customers(id), fiscal_status TEXT NOT NULL DEFAULT 'DRAFT'
                CHECK(fiscal_status IN ('DRAFT')),
              payment_status TEXT NOT NULL DEFAULT 'PENDING' CHECK(payment_status IN ('PENDING')),
              subtotal TEXT NOT NULL, tax_total TEXT NOT NULL, total TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE invoice_lines (
              id INTEGER PRIMARY KEY, invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
              position INTEGER NOT NULL, description TEXT NOT NULL, quantity TEXT NOT NULL, unit_price TEXT NOT NULL,
              discount_percentage TEXT NOT NULL, tax_rate TEXT NOT NULL, taxable_base TEXT NOT NULL,
              tax_amount TEXT NOT NULL, total TEXT NOT NULL, UNIQUE(invoice_id, position)
            );
            CREATE INDEX idx_invoices_account_status ON invoices(account_id, fiscal_status, created_at);
            CREATE INDEX idx_invoices_customer ON invoices(customer_id, created_at);
        """)

    @staticmethod
    def _migration_5(connection: sqlite3.Connection) -> None:
        connection.executescript("""
            ALTER TABLE account_preferences ADD COLUMN language TEXT NOT NULL DEFAULT 'es-ES'
              CHECK(language IN ('es-ES'));
            ALTER TABLE account_preferences ADD COLUMN date_format TEXT NOT NULL DEFAULT 'DD/MM/YYYY'
              CHECK(date_format IN ('DD/MM/YYYY', 'YYYY-MM-DD'));
            ALTER TABLE account_preferences ADD COLUMN export_directory TEXT;
        """)
