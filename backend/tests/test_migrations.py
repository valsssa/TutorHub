"""Tests for database migration system."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session


class TestMigrationManager:
    """Test MigrationManager class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock(spec=Session)
        db.execute = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db

    @pytest.fixture
    def temp_migrations_dir(self):
        """Create a temporary directory for migration files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def migration_manager(self, mock_db, temp_migrations_dir):
        """Create MigrationManager with mock db and temp migrations dir."""
        from core.migrations import MigrationManager

        manager = MigrationManager(mock_db)
        manager.migrations_dir = temp_migrations_dir
        return manager

    def test_init_sets_attributes(self, mock_db):
        """Test MigrationManager __init__ sets attributes correctly."""
        from core.migrations import MigrationManager

        manager = MigrationManager(mock_db, migrations_dir="database/migrations")

        assert manager.db is mock_db
        assert str(manager.migrations_dir).endswith("database/migrations")

    def test_ensure_migrations_table_creates_table(self, migration_manager, mock_db):
        """Test ensure_migrations_table creates schema_migrations table."""
        migration_manager.ensure_migrations_table()

        # Verify execute was called with CREATE TABLE
        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS schema_migrations" in str(call_args)
        mock_db.commit.assert_called_once()

    def test_get_applied_migrations_returns_set(self, migration_manager, mock_db):
        """Test get_applied_migrations returns set of applied versions."""
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([("001",), ("002",), ("003",)]))
        mock_db.execute.return_value = mock_result

        applied = migration_manager.get_applied_migrations()

        assert applied == {"001", "002", "003"}

    def test_get_applied_migrations_empty(self, migration_manager, mock_db):
        """Test get_applied_migrations returns empty set when no migrations."""
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_db.execute.return_value = mock_result

        applied = migration_manager.get_applied_migrations()

        assert applied == set()

    def test_get_pending_migrations_no_dir(self, migration_manager):
        """Test get_pending_migrations returns empty when dir doesn't exist."""
        migration_manager.migrations_dir = Path("/nonexistent/path")

        pending = migration_manager.get_pending_migrations()

        assert pending == []

    def test_get_pending_migrations_no_new_migrations(
        self, migration_manager, mock_db, temp_migrations_dir
    ):
        """Test get_pending_migrations returns empty when all applied."""
        # Create migration files
        (temp_migrations_dir / "001_initial.sql").write_text("SELECT 1;")
        (temp_migrations_dir / "002_add_users.sql").write_text("SELECT 1;")

        # Mock all migrations as applied
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([("001",), ("002",)]))
        mock_db.execute.return_value = mock_result

        pending = migration_manager.get_pending_migrations()

        assert pending == []

    def test_get_pending_migrations_returns_pending(
        self, migration_manager, mock_db, temp_migrations_dir
    ):
        """Test get_pending_migrations returns unapplied migrations."""
        # Create migration files
        (temp_migrations_dir / "001_initial.sql").write_text("SELECT 1;")
        (temp_migrations_dir / "002_add_users.sql").write_text("SELECT 1;")
        (temp_migrations_dir / "003_add_bookings.sql").write_text("SELECT 1;")

        # Mock only first migration as applied
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([("001",)]))
        mock_db.execute.return_value = mock_result

        pending = migration_manager.get_pending_migrations()

        assert len(pending) == 2
        assert pending[0][0] == "002"
        assert pending[1][0] == "003"
        assert pending[0][1].name == "002_add_users.sql"
        assert pending[1][1].name == "003_add_bookings.sql"

    def test_get_pending_migrations_sorted_by_version(
        self, migration_manager, mock_db, temp_migrations_dir
    ):
        """Test get_pending_migrations returns sorted list."""
        # Create migration files out of order
        (temp_migrations_dir / "003_third.sql").write_text("SELECT 1;")
        (temp_migrations_dir / "001_first.sql").write_text("SELECT 1;")
        (temp_migrations_dir / "002_second.sql").write_text("SELECT 1;")

        # No migrations applied
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_db.execute.return_value = mock_result

        pending = migration_manager.get_pending_migrations()

        assert len(pending) == 3
        assert [p[0] for p in pending] == ["001", "002", "003"]

    def test_calculate_checksum(self, migration_manager, temp_migrations_dir):
        """Test calculate_checksum returns SHA-256 hash."""
        # Create test file with known content
        test_file = temp_migrations_dir / "test.sql"
        test_file.write_text("SELECT 1;")

        checksum = migration_manager.calculate_checksum(test_file)

        # SHA-256 produces 64-character hex string
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)

    def test_calculate_checksum_different_content(self, migration_manager, temp_migrations_dir):
        """Test calculate_checksum returns different hashes for different content."""
        file1 = temp_migrations_dir / "file1.sql"
        file2 = temp_migrations_dir / "file2.sql"
        file1.write_text("SELECT 1;")
        file2.write_text("SELECT 2;")

        checksum1 = migration_manager.calculate_checksum(file1)
        checksum2 = migration_manager.calculate_checksum(file2)

        assert checksum1 != checksum2

    def test_apply_migration_success(self, migration_manager, mock_db, temp_migrations_dir):
        """Test apply_migration successfully applies migration."""
        # Create migration file
        migration_file = temp_migrations_dir / "001_add_users.sql"
        migration_file.write_text("CREATE TABLE users (id INT);")

        migration_manager.apply_migration("001", migration_file)

        # Verify SQL was executed
        assert mock_db.execute.call_count >= 2  # Migration + record insertion
        mock_db.commit.assert_called()

    def test_apply_migration_records_in_schema_migrations(
        self, migration_manager, mock_db, temp_migrations_dir
    ):
        """Test apply_migration records migration in schema_migrations table."""
        migration_file = temp_migrations_dir / "001_add_users.sql"
        migration_file.write_text("SELECT 1;")

        migration_manager.apply_migration("001", migration_file)

        # Find the INSERT call
        insert_call_found = False
        for call in mock_db.execute.call_args_list:
            call_str = str(call)
            if "INSERT INTO schema_migrations" in call_str:
                insert_call_found = True
                break

        assert insert_call_found

    def test_apply_migration_rollback_on_failure(
        self, migration_manager, mock_db, temp_migrations_dir
    ):
        """Test apply_migration rolls back on failure."""
        migration_file = temp_migrations_dir / "001_bad.sql"
        migration_file.write_text("INVALID SQL;")

        # Make execute raise an exception
        mock_db.execute.side_effect = Exception("SQL Error")

        with pytest.raises(Exception) as exc_info:
            migration_manager.apply_migration("001", migration_file)

        assert "SQL Error" in str(exc_info.value)
        mock_db.rollback.assert_called_once()

    def test_run_migrations_creates_table_first(self, migration_manager, mock_db):
        """Test run_migrations ensures migrations table exists first."""
        # No migrations to run
        with patch.object(migration_manager, "get_pending_migrations", return_value=[]):
            with patch.object(migration_manager, "ensure_migrations_table") as mock_ensure:
                migration_manager.run_migrations()

        mock_ensure.assert_called_once()

    def test_run_migrations_no_pending(self, migration_manager, mock_db):
        """Test run_migrations returns 0 when no pending migrations."""
        with patch.object(migration_manager, "ensure_migrations_table"):
            with patch.object(migration_manager, "get_pending_migrations", return_value=[]):
                count = migration_manager.run_migrations()

        assert count == 0

    def test_run_migrations_applies_all_pending(
        self, migration_manager, mock_db, temp_migrations_dir
    ):
        """Test run_migrations applies all pending migrations."""
        # Create migration files
        file1 = temp_migrations_dir / "001_first.sql"
        file2 = temp_migrations_dir / "002_second.sql"
        file1.write_text("SELECT 1;")
        file2.write_text("SELECT 2;")

        pending = [("001", file1), ("002", file2)]

        with patch.object(migration_manager, "ensure_migrations_table"):
            with patch.object(migration_manager, "get_pending_migrations", return_value=pending):
                with patch.object(migration_manager, "apply_migration") as mock_apply:
                    count = migration_manager.run_migrations()

        assert count == 2
        assert mock_apply.call_count == 2
        mock_apply.assert_any_call("001", file1)
        mock_apply.assert_any_call("002", file2)

    def test_run_migrations_stops_on_failure(
        self, migration_manager, mock_db, temp_migrations_dir
    ):
        """Test run_migrations stops when a migration fails."""
        file1 = temp_migrations_dir / "001_first.sql"
        file2 = temp_migrations_dir / "002_second.sql"
        file1.write_text("SELECT 1;")
        file2.write_text("SELECT 2;")

        pending = [("001", file1), ("002", file2)]

        with patch.object(migration_manager, "ensure_migrations_table"):
            with patch.object(migration_manager, "get_pending_migrations", return_value=pending):
                with patch.object(
                    migration_manager,
                    "apply_migration",
                    side_effect=Exception("Migration failed"),
                ):
                    with pytest.raises(Exception):
                        migration_manager.run_migrations()

    def test_get_migration_status(self, migration_manager, mock_db, temp_migrations_dir):
        """Test get_migration_status returns correct status dict."""
        # Create migration files
        (temp_migrations_dir / "001_first.sql").write_text("SELECT 1;")
        (temp_migrations_dir / "002_second.sql").write_text("SELECT 2;")
        (temp_migrations_dir / "003_third.sql").write_text("SELECT 3;")

        # Mock first two as applied
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([("001",), ("002",)]))
        mock_db.execute.return_value = mock_result

        with patch.object(migration_manager, "ensure_migrations_table"):
            status = migration_manager.get_migration_status()

        assert status["applied_count"] == 2
        assert status["pending_count"] == 1
        assert "001" in status["applied_versions"]
        assert "002" in status["applied_versions"]
        assert "003" in status["pending_versions"]


class TestRunStartupMigrations:
    """Test run_startup_migrations function."""

    def test_run_startup_migrations_success(self):
        """Test run_startup_migrations runs successfully."""
        from core.migrations import run_startup_migrations

        mock_db = MagicMock(spec=Session)

        with patch("core.migrations.MigrationManager") as MockManager:
            mock_manager = MagicMock()
            mock_manager.run_migrations.return_value = 2
            MockManager.return_value = mock_manager

            run_startup_migrations(mock_db)

        MockManager.assert_called_once_with(mock_db)
        mock_manager.run_migrations.assert_called_once()

    def test_run_startup_migrations_no_pending(self):
        """Test run_startup_migrations logs when no migrations pending."""
        from core.migrations import run_startup_migrations

        mock_db = MagicMock(spec=Session)

        with patch("core.migrations.MigrationManager") as MockManager:
            mock_manager = MagicMock()
            mock_manager.run_migrations.return_value = 0
            MockManager.return_value = mock_manager

            # Should complete without error
            run_startup_migrations(mock_db)

    def test_run_startup_migrations_failure_raises_runtime_error(self):
        """Test run_startup_migrations raises RuntimeError on failure."""
        from core.migrations import run_startup_migrations

        mock_db = MagicMock(spec=Session)

        with patch("core.migrations.MigrationManager") as MockManager:
            mock_manager = MagicMock()
            mock_manager.run_migrations.side_effect = Exception("Database error")
            MockManager.return_value = mock_manager

            with pytest.raises(RuntimeError) as exc_info:
                run_startup_migrations(mock_db)

        assert "Database migration failed" in str(exc_info.value)
        assert "Application cannot start" in str(exc_info.value)


class TestMigrationFileExtraction:
    """Test migration file version extraction."""

    @pytest.fixture
    def manager_with_temp_dir(self):
        """Create manager with temporary migrations directory."""
        from core.migrations import MigrationManager

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.__iter__ = MagicMock(return_value=iter([]))

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MigrationManager(mock_db)
            manager.migrations_dir = Path(tmpdir)
            yield manager, Path(tmpdir)

    def test_version_extraction_simple(self, manager_with_temp_dir):
        """Test version extraction from simple filename."""
        manager, temp_dir = manager_with_temp_dir

        (temp_dir / "001_add_users.sql").write_text("SELECT 1;")

        pending = manager.get_pending_migrations()

        assert len(pending) == 1
        assert pending[0][0] == "001"

    def test_version_extraction_with_underscores(self, manager_with_temp_dir):
        """Test version extraction from filename with multiple underscores."""
        manager, temp_dir = manager_with_temp_dir

        (temp_dir / "025_add_booking_overlap_constraint.sql").write_text("SELECT 1;")

        pending = manager.get_pending_migrations()

        assert len(pending) == 1
        assert pending[0][0] == "025"

    def test_ignores_non_sql_files(self, manager_with_temp_dir):
        """Test that non-SQL files are ignored."""
        manager, temp_dir = manager_with_temp_dir

        (temp_dir / "001_migration.sql").write_text("SELECT 1;")
        (temp_dir / "README.md").write_text("Documentation")
        (temp_dir / "backup.bak").write_text("Backup")

        pending = manager.get_pending_migrations()

        assert len(pending) == 1
        assert pending[0][0] == "001"

    def test_handles_three_digit_versions(self, manager_with_temp_dir):
        """Test handling of three-digit version numbers."""
        manager, temp_dir = manager_with_temp_dir

        (temp_dir / "001_first.sql").write_text("SELECT 1;")
        (temp_dir / "010_tenth.sql").write_text("SELECT 1;")
        (temp_dir / "100_hundredth.sql").write_text("SELECT 1;")

        pending = manager.get_pending_migrations()

        versions = [p[0] for p in pending]
        assert versions == ["001", "010", "100"]


class TestMigrationDescription:
    """Test migration description generation."""

    def test_description_from_filename(self):
        """Test description is generated from filename."""
        from core.migrations import MigrationManager

        mock_db = MagicMock(spec=Session)
        mock_db.execute = MagicMock()
        mock_db.commit = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MigrationManager(mock_db)
            manager.migrations_dir = Path(tmpdir)

            migration_file = Path(tmpdir) / "001_add_user_avatars.sql"
            migration_file.write_text("SELECT 1;")

            manager.apply_migration("001", migration_file)

            # Find the INSERT call and check description
            for call in mock_db.execute.call_args_list:
                args = call[0]
                if len(args) > 1 and isinstance(args[1], dict) and "description" in args[1]:
                    # Description should be title-cased filename without version
                    desc = args[1]["description"]
                    assert "Add User Avatars" in desc or "add user avatars" in desc.lower()
                    break
