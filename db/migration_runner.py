"""Database migration runner with version tracking and rollback support."""
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Protocol


class DatabaseConnection(Protocol):
    def execute(self, query: str, params: tuple = ()) -> Any: ...
    def fetchone(self) -> Optional[tuple]: ...
    def fetchall(self) -> list[tuple]: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


@dataclass
class Migration:
    version: str
    name: str
    up_sql: str
    down_sql: str
    checksum: str = ""
    applied_at: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.checksum:
            self.checksum = hashlib.sha256(self.up_sql.encode()).hexdigest()[:12]


@dataclass
class MigrationResult:
    version: str
    name: str
    status: str
    duration_ms: float
    error: Optional[str] = None


class MigrationRunner:
    """Manages database schema migrations with version control."""

    MIGRATION_TABLE = "_schema_migrations"
    VERSION_PATTERN = re.compile(r"^V(\d+)__(.+)\.(up|down)\.sql$")

    def __init__(self, migrations_dir: Path) -> None:
        self.migrations_dir = migrations_dir
        self._migrations: dict[str, Migration] = {}

    def discover(self) -> list[Migration]:
        up_files: dict[str, Path] = {}
        down_files: dict[str, Path] = {}
        if not self.migrations_dir.exists():
            return []
        for f in sorted(self.migrations_dir.iterdir()):
            match = self.VERSION_PATTERN.match(f.name)
            if match:
                version, name, direction = match.groups()
                if direction == "up":
                    up_files[version] = f
                else:
                    down_files[version] = f
        migrations = []
        for version in sorted(up_files.keys(), key=int):
            up_path = up_files[version]
            down_path = down_files.get(version)
            up_sql = up_path.read_text(encoding="utf-8")
            down_sql = down_path.read_text(encoding="utf-8") if down_path else ""
            name_match = self.VERSION_PATTERN.match(up_path.name)
            name = name_match.group(2) if name_match else f"migration_{version}"
            migration = Migration(
                version=version,
                name=name.replace("_", " "),
                up_sql=up_sql,
                down_sql=down_sql,
            )
            self._migrations[version] = migration
            migrations.append(migration)
        return migrations

    def _ensure_migration_table(self, conn: DatabaseConnection) -> None:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.MIGRATION_TABLE} (
                version VARCHAR(20) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                checksum VARCHAR(12) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                execution_ms FLOAT
            )
        """)
        conn.commit()

    def _applied_versions(self, conn: DatabaseConnection) -> set[str]:
        conn.execute(f"SELECT version FROM {self.MIGRATION_TABLE} ORDER BY version")
        rows = conn.fetchall()
        return {r[0] for r in rows}

    def pending(self, conn: DatabaseConnection) -> list[Migration]:
        self._ensure_migration_table(conn)
        applied = self._applied_versions(conn)
        all_migrations = self.discover()
        return [m for m in all_migrations if m.version not in applied]

    def migrate(self, conn: DatabaseConnection, target_version: Optional[str] = None) -> list[MigrationResult]:
        self._ensure_migration_table(conn)
        pending = self.pending(conn)
        results: list[MigrationResult] = []
        for migration in pending:
            if target_version and int(migration.version) > int(target_version):
                break
            start = time.monotonic()
            try:
                conn.execute(migration.up_sql)
                duration_ms = (time.monotonic() - start) * 1000
                conn.execute(
                    f"INSERT INTO {self.MIGRATION_TABLE} (version, name, checksum, execution_ms) VALUES (?, ?, ?, ?)",
                    (migration.version, migration.name, migration.checksum, duration_ms),
                )
                conn.commit()
                results.append(
                    MigrationResult(
                        version=migration.version,
                        name=migration.name,
                        status="applied",
                        duration_ms=duration_ms,
                    )
                )
            except Exception as e:
                conn.rollback()
                results.append(
                    MigrationResult(
                        version=migration.version,
                        name=migration.name,
                        status="failed",
                        duration_ms=(time.monotonic() - start) * 1000,
                        error=str(e),
                    )
                )
                break
        return results

    def rollback(self, conn: DatabaseConnection, steps: int = 1) -> list[MigrationResult]:
        self._ensure_migration_table(conn)
        applied = self._applied_versions(conn)
        results: list[MigrationResult] = []
        for version in sorted(applied, key=int, reverse=True)[:steps]:
            migration = self._migrations.get(version)
            if migration is None or not migration.down_sql:
                results.append(
                    MigrationResult(
                        version=version,
                        name="unknown",
                        status="skipped",
                        duration_ms=0,
                        error="No down migration found",
                    )
                )
                continue
            start = time.monotonic()
            try:
                conn.execute(migration.down_sql)
                conn.execute(
                    f"DELETE FROM {self.MIGRATION_TABLE} WHERE version = ?",
                    (version,),
                )
                conn.commit()
                results.append(
                    MigrationResult(
                        version=version,
                        name=migration.name,
                        status="rolled_back",
                        duration_ms=(time.monotonic() - start) * 1000,
                    )
                )
            except Exception as e:
                conn.rollback()
                results.append(
                    MigrationResult(
                        version=version,
                        name=migration.name,
                        status="rollback_failed",
                        duration_ms=(time.monotonic() - start) * 1000,
                        error=str(e),
                    )
                )
                break
        return results
