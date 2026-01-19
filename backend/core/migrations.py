"""
Database Migration System - Auto-Applied on Startup

DDD+KISS Principle: Simple, file-based migrations that run automatically.
No complex migration frameworks - just SQL files applied in order.
"""
import os
from pathlib import Path
from typing import List, Tuple
import hashlib
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Simple migration manager that applies SQL files in order.
    
    Business Rules:
    - Migrations run automatically on application startup
    - Each migration runs exactly once (tracked in schema_migrations table)
    - Migrations are idempotent (safe to re-run)
    - Failed migrations halt startup (fail-fast principle)
    """
    
    def __init__(self, db: Session, migrations_dir: str = "database/migrations"):
        self.db = db
        # Resolve path relative to project root
        # In Docker: /app/backend/core/migrations.py -> /app/
        # In dev: backend/core/migrations.py -> project_root/
        base_path = Path(__file__).resolve().parent.parent.parent  # core/ -> backend/ -> /app/
        self.migrations_dir = base_path / migrations_dir
        
    def ensure_migrations_table(self) -> None:
        """Create schema_migrations table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(50) PRIMARY KEY,
            applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
            description TEXT,
            checksum VARCHAR(64)
        );
        """
        self.db.execute(text(create_table_sql))
        self.db.commit()
        logger.info("Ensured schema_migrations table exists")
    
    def get_applied_migrations(self) -> set:
        """Get set of already applied migration versions."""
        result = self.db.execute(
            text("SELECT version FROM schema_migrations ORDER BY version")
        )
        return {row[0] for row in result}
    
    def get_pending_migrations(self) -> List[Tuple[str, Path]]:
        """
        Get list of pending migrations to apply.
        
        Returns:
            List of (version, filepath) tuples sorted by version
        """
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return []
        
        applied = self.get_applied_migrations()
        pending = []
        
        # Find all .sql files
        for filepath in sorted(self.migrations_dir.glob("*.sql")):
            # Extract version from filename (e.g., "001_add_columns.sql" -> "001")
            version = filepath.stem.split("_")[0]
            
            if version not in applied:
                pending.append((version, filepath))
                
        return pending
    
    def calculate_checksum(self, filepath: Path) -> str:
        """Calculate MD5 checksum of migration file."""
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def apply_migration(self, version: str, filepath: Path) -> None:
        """
        Apply a single migration file.
        
        Args:
            version: Migration version identifier
            filepath: Path to SQL migration file
            
        Raises:
            Exception: If migration fails (will halt startup)
        """
        logger.info(f"Applying migration {version}: {filepath.name}")
        
        try:
            # Read migration SQL
            with open(filepath, "r", encoding="utf-8") as f:
                sql_content = f.read()
            
            # Execute migration
            self.db.execute(text(sql_content))
            
            # Record successful migration
            checksum = self.calculate_checksum(filepath)
            description = filepath.stem.replace("_", " ").title()
            
            insert_sql = text("""
                INSERT INTO schema_migrations (version, description, checksum)
                VALUES (:version, :description, :checksum)
                ON CONFLICT (version) DO NOTHING
            """)
            
            self.db.execute(
                insert_sql,
                {
                    "version": version,
                    "description": description,
                    "checksum": checksum
                }
            )
            
            self.db.commit()
            logger.info(f"✓ Successfully applied migration {version}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"✗ Failed to apply migration {version}: {e}")
            raise
    
    def run_migrations(self) -> int:
        """
        Run all pending migrations.
        
        Returns:
            Number of migrations applied
            
        Raises:
            Exception: If any migration fails
        """
        self.ensure_migrations_table()
        
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return 0
        
        logger.info(f"Found {len(pending)} pending migration(s)")
        
        for version, filepath in pending:
            self.apply_migration(version, filepath)
        
        logger.info(f"✓ Applied {len(pending)} migration(s) successfully")
        return len(pending)
    
    def get_migration_status(self) -> dict:
        """
        Get current migration status.
        
        Returns:
            Dict with applied and pending migration counts
        """
        self.ensure_migrations_table()
        
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        return {
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied_versions": sorted(list(applied)),
            "pending_versions": [v for v, _ in pending]
        }


def run_startup_migrations(db: Session) -> None:
    """
    Run migrations on application startup.
    
    This is called automatically when the backend starts.
    Follows KISS principle: simple, straightforward, no magic.
    """
    try:
        manager = MigrationManager(db)
        count = manager.run_migrations()
        
        if count > 0:
            logger.info(f"Database schema updated with {count} migration(s)")
        else:
            logger.info("Database schema is up to date")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise RuntimeError(
            "Database migration failed. Application cannot start. "
            f"Error: {e}"
        ) from e

