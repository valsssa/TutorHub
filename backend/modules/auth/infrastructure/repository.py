"""Auth repository for database operations."""

from sqlalchemy.orm import Session

from models import User
from modules.auth.domain.entities import UserEntity


class UserRepository:
    """Repository for User database operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def _to_entity(self, user: User) -> UserEntity:
        """Convert database model to domain entity."""
        return UserEntity(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            first_name=getattr(user, "first_name", None),
            last_name=getattr(user, "last_name", None),
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            timezone=getattr(user, "timezone", "UTC"),
            currency=getattr(user, "currency", "USD"),
            created_at=user.created_at,
            updated_at=user.updated_at,
            password_changed_at=getattr(user, "password_changed_at", None),
            registration_ip=str(user.registration_ip) if getattr(user, "registration_ip", None) else None,
            trial_restricted=getattr(user, "trial_restricted", False),
        )

    def find_by_email(self, email: str | None) -> UserEntity | None:
        """Find user by email (case-insensitive), excluding soft-deleted users."""
        if not email:
            return None

        from sqlalchemy import func

        user = self.db.query(User).filter(
            func.lower(User.email) == email.lower(),
            User.deleted_at.is_(None),
        ).first()
        return self._to_entity(user) if user else None

    def find_by_id(self, user_id: int) -> UserEntity | None:
        """Find user by ID, excluding soft-deleted users."""
        user = self.db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None),
        ).first()
        return self._to_entity(user) if user else None

    def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email, excluding soft-deleted users."""
        from sqlalchemy import func

        return self.db.query(User).filter(
            func.lower(User.email) == email.lower(),
            User.deleted_at.is_(None),
        ).first() is not None

    def create(
        self,
        entity: UserEntity,
        registration_ip: str | None = None,
        trial_restricted: bool = False,
    ) -> UserEntity:
        """Create new user with optional fraud detection fields."""
        user = User(
            email=entity.email.lower(),
            hashed_password=entity.hashed_password,
            first_name=entity.first_name,
            last_name=entity.last_name,
            role=entity.role,
            is_active=entity.is_active,
            is_verified=entity.is_verified,
            timezone=entity.timezone,
            currency=entity.currency,
            registration_ip=registration_ip,
            trial_restricted=trial_restricted,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self._to_entity(user)

    def update(self, entity: UserEntity) -> UserEntity:
        """Update existing user."""
        user = self.db.query(User).filter(User.id == entity.id).first()
        if not user:
            raise ValueError(f"User with id {entity.id} not found")

        user.email = entity.email.lower()
        user.hashed_password = entity.hashed_password
        user.first_name = entity.first_name
        user.last_name = entity.last_name
        user.role = entity.role
        user.is_active = entity.is_active
        user.is_verified = entity.is_verified
        user.timezone = entity.timezone
        user.currency = entity.currency

        self.db.commit()
        self.db.refresh(user)
        return self._to_entity(user)

    def delete(self, user_id: int) -> bool:
        """Delete user by ID."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True

    def find_all(self, skip: int = 0, limit: int = 100, active_only: bool = False) -> list[UserEntity]:
        """Find all users with pagination, excluding soft-deleted users."""
        query = self.db.query(User).filter(User.deleted_at.is_(None))

        if active_only:
            query = query.filter(User.is_active.is_(True))

        users = query.offset(skip).limit(limit).all()
        return [self._to_entity(user) for user in users]

    def count(self, active_only: bool = False) -> int:
        """Count total users, excluding soft-deleted users."""
        query = self.db.query(User).filter(User.deleted_at.is_(None))

        if active_only:
            query = query.filter(User.is_active.is_(True))

        return query.count()

    def find_by_role(self, role: str, skip: int = 0, limit: int = 100) -> list[UserEntity]:
        """Find users by role with pagination, excluding soft-deleted users."""
        users = self.db.query(User).filter(
            User.role == role,
            User.deleted_at.is_(None),
        ).offset(skip).limit(limit).all()
        return [self._to_entity(user) for user in users]
