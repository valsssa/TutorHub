"""Tests for data integrity validation utilities."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from core.integrity_checks import DataIntegrityChecker


class TestCheckRoleProfileConsistency:
    """Tests for check_role_profile_consistency method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    def test_consistent_data(self, mock_db):
        """Test when data is consistent."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = DataIntegrityChecker.check_role_profile_consistency(mock_db)

        assert result["is_consistent"] is True
        assert result["total_issues"] == 0
        assert result["tutors_without_profiles"] == []
        assert result["profiles_without_tutor_role"] == []

    def test_tutors_without_profiles(self, mock_db):
        """Test detecting tutors without profiles."""
        mock_query_tutors = MagicMock()
        mock_query_tutors.filter.return_value.all.return_value = [(1,), (2,), (3,)]

        mock_query_profiles = MagicMock()
        mock_query_profiles.join.return_value.filter.return_value.all.return_value = []

        mock_db.query.side_effect = [mock_query_tutors, mock_query_profiles]

        result = DataIntegrityChecker.check_role_profile_consistency(mock_db)

        assert result["is_consistent"] is False
        assert result["tutors_without_profiles"] == [1, 2, 3]
        assert result["total_issues"] == 3

    def test_profiles_without_tutor_role(self, mock_db):
        """Test detecting profiles without tutor role."""
        mock_query_tutors = MagicMock()
        mock_query_tutors.filter.return_value.all.return_value = []

        mock_query_profiles = MagicMock()
        mock_query_profiles.join.return_value.filter.return_value.all.return_value = [
            (10,),
            (20,),
        ]

        mock_db.query.side_effect = [mock_query_tutors, mock_query_profiles]

        result = DataIntegrityChecker.check_role_profile_consistency(mock_db)

        assert result["is_consistent"] is False
        assert result["profiles_without_tutor_role"] == [10, 20]
        assert result["total_issues"] == 2

    def test_both_types_of_issues(self, mock_db):
        """Test detecting both types of inconsistencies."""
        mock_query_tutors = MagicMock()
        mock_query_tutors.filter.return_value.all.return_value = [(1,)]

        mock_query_profiles = MagicMock()
        mock_query_profiles.join.return_value.filter.return_value.all.return_value = [
            (10,)
        ]

        mock_db.query.side_effect = [mock_query_tutors, mock_query_profiles]

        result = DataIntegrityChecker.check_role_profile_consistency(mock_db)

        assert result["is_consistent"] is False
        assert result["tutors_without_profiles"] == [1]
        assert result["profiles_without_tutor_role"] == [10]
        assert result["total_issues"] == 2

    def test_logs_warning_on_inconsistency(self, mock_db):
        """Test warning is logged when inconsistencies found."""
        mock_query_tutors = MagicMock()
        mock_query_tutors.filter.return_value.all.return_value = [(1,)]

        mock_query_profiles = MagicMock()
        mock_query_profiles.join.return_value.filter.return_value.all.return_value = []

        mock_db.query.side_effect = [mock_query_tutors, mock_query_profiles]

        with patch("core.integrity_checks.logger") as mock_logger:
            DataIntegrityChecker.check_role_profile_consistency(mock_db)
            mock_logger.warning.assert_called_once()


class TestAutoRepairConsistency:
    """Tests for auto_repair_consistency method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    def test_no_repairs_needed(self, mock_db):
        """Test when no repairs are needed."""
        with patch.object(
            DataIntegrityChecker,
            "check_role_profile_consistency",
            return_value={
                "tutors_without_profiles": [],
                "profiles_without_tutor_role": [],
                "is_consistent": True,
                "total_issues": 0,
            },
        ):
            result = DataIntegrityChecker.auto_repair_consistency(mock_db)

            assert result["profiles_created"] == 0
            assert result["profiles_archived"] == 0
            assert result["total_fixed"] == 0
            mock_db.commit.assert_not_called()

    def test_creates_missing_profiles(self, mock_db):
        """Test creating missing tutor profiles."""
        with patch.object(
            DataIntegrityChecker,
            "check_role_profile_consistency",
            return_value={
                "tutors_without_profiles": [1, 2],
                "profiles_without_tutor_role": [],
                "is_consistent": False,
                "total_issues": 2,
            },
        ):
            result = DataIntegrityChecker.auto_repair_consistency(mock_db)

            assert result["profiles_created"] == 2
            assert mock_db.add.call_count == 2
            mock_db.commit.assert_called_once()

    def test_archives_orphaned_profiles(self, mock_db):
        """Test archiving orphaned profiles."""
        mock_update = MagicMock()
        mock_update.update.return_value = 1
        mock_db.query.return_value.filter.return_value = mock_update

        with patch.object(
            DataIntegrityChecker,
            "check_role_profile_consistency",
            return_value={
                "tutors_without_profiles": [],
                "profiles_without_tutor_role": [10, 20],
                "is_consistent": False,
                "total_issues": 2,
            },
        ):
            result = DataIntegrityChecker.auto_repair_consistency(mock_db)

            assert result["profiles_archived"] == 2
            mock_db.commit.assert_called_once()

    def test_handles_both_repairs(self, mock_db):
        """Test handling both types of repairs."""
        mock_update = MagicMock()
        mock_update.update.return_value = 1
        mock_db.query.return_value.filter.return_value = mock_update

        with patch.object(
            DataIntegrityChecker,
            "check_role_profile_consistency",
            return_value={
                "tutors_without_profiles": [1],
                "profiles_without_tutor_role": [10],
                "is_consistent": False,
                "total_issues": 2,
            },
        ):
            result = DataIntegrityChecker.auto_repair_consistency(mock_db)

            assert result["profiles_created"] == 1
            assert result["profiles_archived"] == 1
            assert result["total_fixed"] == 2

    def test_handles_profile_creation_error(self, mock_db):
        """Test handling profile creation error."""
        mock_db.add.side_effect = Exception("Database error")

        with patch.object(
            DataIntegrityChecker,
            "check_role_profile_consistency",
            return_value={
                "tutors_without_profiles": [1],
                "profiles_without_tutor_role": [],
                "is_consistent": False,
                "total_issues": 1,
            },
        ):
            with patch("core.integrity_checks.logger") as mock_logger:
                result = DataIntegrityChecker.auto_repair_consistency(mock_db)

                assert result["profiles_created"] == 0
                mock_logger.error.assert_called()

    def test_handles_archive_error(self, mock_db):
        """Test handling profile archive error."""
        mock_db.query.return_value.filter.return_value.update.side_effect = Exception(
            "Database error"
        )

        with patch.object(
            DataIntegrityChecker,
            "check_role_profile_consistency",
            return_value={
                "tutors_without_profiles": [],
                "profiles_without_tutor_role": [10],
                "is_consistent": False,
                "total_issues": 1,
            },
        ):
            with patch("core.integrity_checks.logger") as mock_logger:
                result = DataIntegrityChecker.auto_repair_consistency(mock_db)

                assert result["profiles_archived"] == 0
                mock_logger.error.assert_called()

    def test_includes_original_issues_in_details(self, mock_db):
        """Test that original issues are included in result details."""
        issues = {
            "tutors_without_profiles": [],
            "profiles_without_tutor_role": [],
            "is_consistent": True,
            "total_issues": 0,
        }

        with patch.object(
            DataIntegrityChecker,
            "check_role_profile_consistency",
            return_value=issues,
        ):
            result = DataIntegrityChecker.auto_repair_consistency(mock_db)

            assert result["details"] == issues


class TestGetConsistencyReport:
    """Tests for get_consistency_report method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.query.return_value.count.return_value = 100
        db.query.return_value.filter.return_value.count.return_value = 10
        return db

    def test_report_includes_all_stats(self, mock_db):
        """Test report includes all statistics."""
        with patch.object(
            DataIntegrityChecker,
            "check_role_profile_consistency",
            return_value={
                "tutors_without_profiles": [],
                "profiles_without_tutor_role": [],
                "is_consistent": True,
                "total_issues": 0,
            },
        ):
            result = DataIntegrityChecker.get_consistency_report(mock_db)

            assert "total_users" in result
            assert "tutor_users" in result
            assert "tutor_profiles" in result
            assert "active_profiles" in result
            assert "archived_profiles" in result
            assert "issues" in result
            assert "health_status" in result

    def test_healthy_status(self, mock_db):
        """Test healthy status when consistent."""
        with patch.object(
            DataIntegrityChecker,
            "check_role_profile_consistency",
            return_value={
                "tutors_without_profiles": [],
                "profiles_without_tutor_role": [],
                "is_consistent": True,
                "total_issues": 0,
            },
        ):
            result = DataIntegrityChecker.get_consistency_report(mock_db)

            assert result["health_status"] == "healthy"

    def test_warning_status(self, mock_db):
        """Test warning status for minor issues."""
        with patch.object(
            DataIntegrityChecker,
            "check_role_profile_consistency",
            return_value={
                "tutors_without_profiles": [1, 2],
                "profiles_without_tutor_role": [],
                "is_consistent": False,
                "total_issues": 2,
            },
        ):
            result = DataIntegrityChecker.get_consistency_report(mock_db)

            assert result["health_status"] == "warning"

    def test_critical_status(self, mock_db):
        """Test critical status for many issues."""
        with patch.object(
            DataIntegrityChecker,
            "check_role_profile_consistency",
            return_value={
                "tutors_without_profiles": [1, 2, 3, 4, 5, 6],
                "profiles_without_tutor_role": [],
                "is_consistent": False,
                "total_issues": 6,
            },
        ):
            result = DataIntegrityChecker.get_consistency_report(mock_db)

            assert result["health_status"] == "critical"

    def test_boundary_warning_threshold(self, mock_db):
        """Test boundary at warning threshold (5 issues)."""
        with patch.object(
            DataIntegrityChecker,
            "check_role_profile_consistency",
            return_value={
                "tutors_without_profiles": [1, 2, 3, 4, 5],
                "profiles_without_tutor_role": [],
                "is_consistent": False,
                "total_issues": 5,
            },
        ):
            result = DataIntegrityChecker.get_consistency_report(mock_db)

            assert result["health_status"] == "warning"


class TestCreatedProfileDefaults:
    """Tests for default values in created profiles."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    def test_profile_defaults(self, mock_db):
        """Test profile is created with correct defaults."""
        with patch.object(
            DataIntegrityChecker,
            "check_role_profile_consistency",
            return_value={
                "tutors_without_profiles": [1],
                "profiles_without_tutor_role": [],
                "is_consistent": False,
                "total_issues": 1,
            },
        ):
            DataIntegrityChecker.auto_repair_consistency(mock_db)

            call_args = mock_db.add.call_args[0][0]
            assert call_args.user_id == 1
            assert call_args.title == ""
            assert call_args.hourly_rate == Decimal("1.00")
            assert call_args.experience_years == 0
            assert call_args.languages == []
            assert call_args.profile_status == "incomplete"
            assert call_args.is_approved is False
