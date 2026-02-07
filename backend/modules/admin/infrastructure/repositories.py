"""
SQLAlchemy and Redis repository implementations for admin module.

Provides concrete implementations of the repository protocols defined
in the domain layer.
"""

from __future__ import annotations

import contextlib
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from core.datetime_utils import utc_now
from typing import Any

from sqlalchemy.orm import Session

from core.feature_flags import FeatureFlag, FeatureFlags, FeatureState
from models.admin import AuditLog
from modules.admin.domain.entities import AdminActionLog, FeatureFlagEntity
from modules.admin.domain.exceptions import (
    FeatureFlagAlreadyExistsError,
    FeatureFlagNotFoundError,
)
from modules.admin.domain.value_objects import (
    AdminActionType,
    AdminUserId,
    FeatureFlagId,
    FeatureFlagState,
    TargetType,
)

logger = logging.getLogger(__name__)


def _core_state_to_domain(state: FeatureState) -> FeatureFlagState:
    """Convert core FeatureState to domain FeatureFlagState."""
    mapping = {
        FeatureState.DISABLED: FeatureFlagState.DISABLED,
        FeatureState.ENABLED: FeatureFlagState.ENABLED,
        FeatureState.PERCENTAGE: FeatureFlagState.PERCENTAGE,
        FeatureState.ALLOWLIST: FeatureFlagState.ALLOWLIST,
        FeatureState.DENYLIST: FeatureFlagState.DENYLIST,
    }
    return mapping[state]


def _domain_state_to_core(state: FeatureFlagState) -> FeatureState:
    """Convert domain FeatureFlagState to core FeatureState."""
    mapping = {
        FeatureFlagState.DISABLED: FeatureState.DISABLED,
        FeatureFlagState.ENABLED: FeatureState.ENABLED,
        FeatureFlagState.PERCENTAGE: FeatureState.PERCENTAGE,
        FeatureFlagState.ALLOWLIST: FeatureState.ALLOWLIST,
        FeatureFlagState.DENYLIST: FeatureState.DENYLIST,
    }
    return mapping[state]


def _core_flag_to_entity(flag: FeatureFlag, flag_id: int | None = None) -> FeatureFlagEntity:
    """
    Convert core FeatureFlag to domain FeatureFlagEntity.

    Args:
        flag: Core feature flag object
        flag_id: Optional ID to assign (Redis doesn't use IDs natively)

    Returns:
        FeatureFlagEntity domain object
    """
    return FeatureFlagEntity(
        id=FeatureFlagId(flag_id) if flag_id else None,
        name=flag.name,
        is_enabled=flag.state != FeatureState.DISABLED,
        state=_core_state_to_domain(flag.state),
        description=flag.description,
        percentage=flag.percentage,
        allowlist=flag.allowlist.copy(),
        denylist=flag.denylist.copy(),
        metadata=flag.metadata.copy() if flag.metadata else {},
        created_at=flag.created_at,
        updated_at=flag.updated_at,
    )


def _entity_to_core_flag(entity: FeatureFlagEntity) -> FeatureFlag:
    """
    Convert domain FeatureFlagEntity to core FeatureFlag.

    Args:
        entity: Domain feature flag entity

    Returns:
        Core FeatureFlag object
    """
    return FeatureFlag(
        name=entity.name,
        state=_domain_state_to_core(entity.state),
        percentage=entity.percentage,
        allowlist=entity.allowlist.copy(),
        denylist=entity.denylist.copy(),
        description=entity.description,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        metadata=entity.metadata.copy() if entity.metadata else {},
    )


@dataclass(slots=True)
class FeatureFlagRepositoryImpl:
    """
    Redis-backed repository for feature flags.

    Wraps the existing FeatureFlags singleton to provide a repository
    interface for the domain layer.

    Note: Redis doesn't use integer IDs natively. We use the flag name
    as the unique identifier and generate synthetic IDs based on hash
    for compatibility with the domain interface.
    """

    feature_flags: FeatureFlags

    def _name_to_id(self, name: str) -> int:
        """Generate a synthetic ID from flag name."""
        return hash(name) & 0x7FFFFFFF

    async def get_by_id(self, flag_id: FeatureFlagId) -> FeatureFlagEntity | None:
        """
        Get a feature flag by its ID.

        Note: Since Redis uses names as keys, this method searches all flags
        to find one with a matching synthetic ID.

        Args:
            flag_id: Feature flag's unique identifier

        Returns:
            FeatureFlagEntity if found, None otherwise
        """
        flags = await self.feature_flags.list_flags()
        for flag in flags:
            if self._name_to_id(flag.name) == flag_id:
                return _core_flag_to_entity(flag, flag_id)
        return None

    async def get_by_name(self, name: str) -> FeatureFlagEntity | None:
        """
        Get a feature flag by its name.

        Args:
            name: Feature flag's name (case-sensitive)

        Returns:
            FeatureFlagEntity if found, None otherwise
        """
        flag = await self.feature_flags.get_flag(name)
        if flag:
            return _core_flag_to_entity(flag, self._name_to_id(name))
        return None

    async def get_all(
        self,
        *,
        is_enabled: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[FeatureFlagEntity]:
        """
        Get all feature flags with optional filtering.

        Args:
            is_enabled: Filter by enabled status
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching feature flags
        """
        all_flags = await self.feature_flags.list_flags()
        entities = [
            _core_flag_to_entity(f, self._name_to_id(f.name))
            for f in all_flags
        ]

        if is_enabled is not None:
            entities = [
                e for e in entities
                if e.is_enabled == is_enabled
            ]

        offset = (page - 1) * page_size
        return entities[offset:offset + page_size]

    async def create(self, flag: FeatureFlagEntity) -> FeatureFlagEntity:
        """
        Create a new feature flag.

        Args:
            flag: Feature flag entity to create

        Returns:
            Created feature flag with populated ID and timestamps

        Raises:
            FeatureFlagAlreadyExistsError: If flag name already exists
        """
        existing = await self.feature_flags.get_flag(flag.name)
        if existing is not None:
            raise FeatureFlagAlreadyExistsError(flag.name)

        core_flag = _entity_to_core_flag(flag)
        await self.feature_flags.set_flag(core_flag)

        updated_flag = await self.feature_flags.get_flag(flag.name)
        if updated_flag:
            return _core_flag_to_entity(updated_flag, self._name_to_id(flag.name))

        raise RuntimeError(f"Failed to create feature flag: {flag.name}")

    async def update(self, flag: FeatureFlagEntity) -> FeatureFlagEntity:
        """
        Update an existing feature flag.

        Args:
            flag: Feature flag entity with updated fields

        Returns:
            Updated feature flag entity with new timestamp

        Raises:
            FeatureFlagNotFoundError: If flag doesn't exist
        """
        existing = await self.feature_flags.get_flag(flag.name)
        if existing is None:
            raise FeatureFlagNotFoundError(flag_name=flag.name)

        core_flag = _entity_to_core_flag(flag)
        core_flag.created_at = existing.created_at
        await self.feature_flags.set_flag(core_flag)

        updated_flag = await self.feature_flags.get_flag(flag.name)
        if updated_flag:
            return _core_flag_to_entity(
                updated_flag,
                self._name_to_id(flag.name),
            )

        raise RuntimeError(f"Failed to update feature flag: {flag.name}")

    async def toggle(self, name: str, enabled: bool) -> FeatureFlagEntity:
        """
        Toggle a feature flag's enabled state.

        Args:
            name: Feature flag name
            enabled: New enabled state

        Returns:
            Updated feature flag entity

        Raises:
            FeatureFlagNotFoundError: If flag doesn't exist
        """
        existing = await self.feature_flags.get_flag(name)
        if existing is None:
            raise FeatureFlagNotFoundError(flag_name=name)

        if enabled:
            updated = await self.feature_flags.enable(name)
        else:
            updated = await self.feature_flags.disable(name)

        return _core_flag_to_entity(updated, self._name_to_id(name))

    async def delete(self, name: str) -> bool:
        """
        Delete a feature flag.

        Args:
            name: Feature flag name to delete

        Returns:
            True if deleted, False if not found
        """
        return await self.feature_flags.delete_flag(name)

    async def exists(self, name: str) -> bool:
        """
        Check if a feature flag exists.

        Args:
            name: Feature flag name to check

        Returns:
            True if exists, False otherwise
        """
        flag = await self.feature_flags.get_flag(name)
        return flag is not None

    async def count(self, *, is_enabled: bool | None = None) -> int:
        """
        Count feature flags with optional filtering.

        Args:
            is_enabled: Filter by enabled status

        Returns:
            Count of matching feature flags
        """
        all_flags = await self.feature_flags.list_flags()

        if is_enabled is None:
            return len(all_flags)

        return sum(
            1 for f in all_flags
            if (f.state != FeatureState.DISABLED) == is_enabled
        )


def _audit_log_to_entity(model: AuditLog) -> AdminActionLog:
    """
    Convert AuditLog SQLAlchemy model to AdminActionLog domain entity.

    Maps the general-purpose AuditLog table to admin-specific domain model.

    Args:
        model: AuditLog SQLAlchemy model

    Returns:
        AdminActionLog domain entity
    """
    action_mapping = {
        "INSERT": AdminActionType.USER_CREATE,
        "UPDATE": AdminActionType.USER_UPDATE,
        "DELETE": AdminActionType.USER_DELETE,
        "SOFT_DELETE": AdminActionType.USER_DELETE,
        "RESTORE": AdminActionType.DATA_RESTORE,
    }

    action = action_mapping.get(model.action, AdminActionType.USER_UPDATE)

    new_data = model.new_data or {}
    if "action_type" in new_data:
        with contextlib.suppress(ValueError):
            action = AdminActionType(new_data["action_type"])

    target_type = TargetType.USER
    if "target_type" in new_data:
        with contextlib.suppress(ValueError):
            target_type = TargetType(new_data["target_type"])
    elif model.table_name:
        table_to_target = {
            "users": TargetType.USER,
            "tutor_profiles": TargetType.TUTOR_PROFILE,
            "feature_flags": TargetType.FEATURE_FLAG,
            "bookings": TargetType.BOOKING,
        }
        target_type = table_to_target.get(model.table_name, TargetType.SYSTEM)

    details = new_data.get("details", {}) if isinstance(new_data, dict) else {}

    return AdminActionLog(
        id=model.id,
        admin_id=AdminUserId(model.changed_by) if model.changed_by else AdminUserId(0),
        action=action,
        target_type=target_type,
        target_id=str(model.record_id) if model.record_id else None,
        details=details,
        previous_state=model.old_data,
        new_state=model.new_data,
        ip_address=str(model.ip_address) if model.ip_address else None,
        user_agent=model.user_agent,
        created_at=model.changed_at,
    )


def _entity_to_audit_log(entity: AdminActionLog) -> dict[str, Any]:
    """
    Convert AdminActionLog domain entity to AuditLog model data.

    Args:
        entity: AdminActionLog domain entity

    Returns:
        Dictionary of data for creating/updating AuditLog
    """
    table_name = "admin_actions"
    if entity.target_type == TargetType.USER:
        table_name = "users"
    elif entity.target_type == TargetType.TUTOR_PROFILE:
        table_name = "tutor_profiles"
    elif entity.target_type == TargetType.FEATURE_FLAG:
        table_name = "feature_flags"
    elif entity.target_type == TargetType.BOOKING:
        table_name = "bookings"

    action_mapping = {
        AdminActionType.USER_CREATE: "INSERT",
        AdminActionType.USER_UPDATE: "UPDATE",
        AdminActionType.USER_DELETE: "SOFT_DELETE",
        AdminActionType.USER_ACTIVATE: "UPDATE",
        AdminActionType.USER_DEACTIVATE: "UPDATE",
        AdminActionType.USER_ROLE_CHANGE: "UPDATE",
        AdminActionType.TUTOR_APPROVE: "UPDATE",
        AdminActionType.TUTOR_REJECT: "UPDATE",
        AdminActionType.FEATURE_FLAG_CREATE: "INSERT",
        AdminActionType.FEATURE_FLAG_UPDATE: "UPDATE",
        AdminActionType.FEATURE_FLAG_DELETE: "DELETE",
        AdminActionType.FEATURE_FLAG_TOGGLE: "UPDATE",
        AdminActionType.CACHE_INVALIDATE: "UPDATE",
        AdminActionType.DATA_PURGE: "DELETE",
        AdminActionType.DATA_RESTORE: "RESTORE",
    }
    action = action_mapping.get(entity.action, "UPDATE")

    new_data = {
        "action_type": entity.action.value,
        "target_type": entity.target_type.value,
        "details": entity.details,
    }
    if entity.new_state:
        new_data.update(entity.new_state)

    return {
        "table_name": table_name,
        "record_id": int(entity.target_id) if entity.target_id and entity.target_id.isdigit() else 0,
        "action": action,
        "old_data": entity.previous_state,
        "new_data": new_data,
        "changed_by": int(entity.admin_id) if entity.admin_id else None,
        "ip_address": entity.ip_address,
        "user_agent": entity.user_agent,
    }


@dataclass(slots=True)
class AdminActionLogRepositoryImpl:
    """
    SQLAlchemy-backed repository for admin action logs.

    Uses the existing AuditLog table to store admin actions with
    additional metadata in the JSON fields.
    """

    db: Session

    def create(self, log: AdminActionLog) -> AdminActionLog:
        """
        Create a new admin action log entry.

        Args:
            log: Admin action log entity to create

        Returns:
            Created log entry with populated ID and timestamp
        """
        data = _entity_to_audit_log(log)

        model = AuditLog(
            table_name=data["table_name"],
            record_id=data["record_id"],
            action=data["action"],
            old_data=data["old_data"],
            new_data=data["new_data"],
            changed_by=data["changed_by"],
            ip_address=data["ip_address"],
            user_agent=data["user_agent"],
        )

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        return _audit_log_to_entity(model)

    def get_by_admin(
        self,
        admin_id: AdminUserId,
        *,
        action_types: list[AdminActionType] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[AdminActionLog]:
        """
        Get action logs for a specific admin.

        Args:
            admin_id: Admin user's ID
            action_types: Filter by action types
            from_date: Filter by start date
            to_date: Filter by end date
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching admin action logs
        """
        query = self.db.query(AuditLog).filter(AuditLog.changed_by == int(admin_id))

        if from_date:
            query = query.filter(AuditLog.changed_at >= from_date)

        if to_date:
            query = query.filter(AuditLog.changed_at <= to_date)

        query = query.order_by(AuditLog.changed_at.desc())

        offset = (page - 1) * page_size
        models = query.offset(offset).limit(page_size).all()

        entities = [_audit_log_to_entity(m) for m in models]

        if action_types:
            action_values = set(action_types)
            entities = [e for e in entities if e.action in action_values]

        return entities

    def get_recent(
        self,
        *,
        action_types: list[AdminActionType] | None = None,
        target_type: TargetType | None = None,
        limit: int = 100,
    ) -> list[AdminActionLog]:
        """
        Get recent admin action logs.

        Args:
            action_types: Filter by action types
            target_type: Filter by target type
            limit: Maximum number of logs to return

        Returns:
            List of recent admin action logs (newest first)
        """
        query = self.db.query(AuditLog)

        if target_type:
            table_mapping = {
                TargetType.USER: "users",
                TargetType.TUTOR_PROFILE: "tutor_profiles",
                TargetType.FEATURE_FLAG: "feature_flags",
                TargetType.BOOKING: "bookings",
                TargetType.SYSTEM: "admin_actions",
            }
            table_name = table_mapping.get(target_type)
            if table_name:
                query = query.filter(AuditLog.table_name == table_name)

        query = query.order_by(AuditLog.changed_at.desc())

        fetch_limit = limit * 3 if action_types else limit
        models = query.limit(fetch_limit).all()

        entities = [_audit_log_to_entity(m) for m in models]

        if action_types:
            action_values = set(action_types)
            entities = [e for e in entities if e.action in action_values]

        return entities[:limit]

    def get_by_target(
        self,
        target_type: TargetType,
        target_id: str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> list[AdminActionLog]:
        """
        Get action logs for a specific target.

        Args:
            target_type: Type of the target entity
            target_id: ID of the target entity
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of admin action logs for the target
        """
        table_mapping = {
            TargetType.USER: "users",
            TargetType.TUTOR_PROFILE: "tutor_profiles",
            TargetType.FEATURE_FLAG: "feature_flags",
            TargetType.BOOKING: "bookings",
            TargetType.SYSTEM: "admin_actions",
        }

        table_name = table_mapping.get(target_type)
        record_id = int(target_id) if target_id.isdigit() else 0

        query = self.db.query(AuditLog).filter(
            AuditLog.table_name == table_name,
            AuditLog.record_id == record_id,
        )

        query = query.order_by(AuditLog.changed_at.desc())

        offset = (page - 1) * page_size
        models = query.offset(offset).limit(page_size).all()

        return [_audit_log_to_entity(m) for m in models]

    def count_by_admin(
        self,
        admin_id: AdminUserId,
        *,
        action_types: list[AdminActionType] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> int:
        """
        Count action logs for a specific admin.

        Args:
            admin_id: Admin user's ID
            action_types: Filter by action types
            from_date: Filter by start date
            to_date: Filter by end date

        Returns:
            Count of matching logs
        """
        query = self.db.query(AuditLog).filter(AuditLog.changed_by == int(admin_id))

        if from_date:
            query = query.filter(AuditLog.changed_at >= from_date)

        if to_date:
            query = query.filter(AuditLog.changed_at <= to_date)

        if action_types:
            action_mapping = {
                AdminActionType.USER_CREATE: "INSERT",
                AdminActionType.USER_DELETE: "DELETE",
                AdminActionType.DATA_RESTORE: "RESTORE",
            }
            sql_actions = {action_mapping.get(a, "UPDATE") for a in action_types}
            query = query.filter(AuditLog.action.in_(sql_actions))

        return query.count()

    def get_activity_summary(
        self,
        admin_id: AdminUserId,
        *,
        days: int = 30,
    ) -> dict[AdminActionType, int]:
        """
        Get activity summary for an admin over a time period.

        Args:
            admin_id: Admin user's ID
            days: Number of days to look back

        Returns:
            Dictionary mapping action types to counts
        """
        from_date = utc_now() - timedelta(days=days)

        query = self.db.query(AuditLog).filter(
            AuditLog.changed_by == int(admin_id),
            AuditLog.changed_at >= from_date,
        )

        models = query.all()
        entities = [_audit_log_to_entity(m) for m in models]

        summary: dict[AdminActionType, int] = defaultdict(int)
        for entity in entities:
            summary[entity.action] += 1

        return dict(summary)
