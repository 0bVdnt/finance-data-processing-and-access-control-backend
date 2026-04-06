import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    UpdateUserRoleRequest,
    UpdateUserStatusRequest,
    UserListParams,
)

logger = logging.getLogger(__name__)


class UserService:
    """Business logic for user management operations (admin only)."""

    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def list_users(self, params: UserListParams) -> tuple[list[User], int]:
        """
        List all users with optional filters.
        Only accessible by admins (enforced at router level).
        """
        role_value = params.role.value if params.role else None

        users, total = await self.user_repo.list_users(
            role=role_value,
            is_active=params.is_active,
            limit=params.per_page,
            offset=params.offset,
        )

        return users, 0 if total is None else total

    async def get_user(self, user_id: UUID) -> User:
        """Get a single user by ID."""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User", str(user_id))
        return user

    async def update_role(
        self,
        user_id: UUID,
        data: UpdateUserRoleRequest,
        admin_user: User,
    ) -> User | None:
        """
        Update a user's role.

        Business rules:
          - Only admins can change roles (enforced at router level)
          - Admins cannot change their own role (prevents lockout)
          - Target user must exist
        """
        # Prevent self-role change
        if user_id == admin_user.id:
            raise ForbiddenError(
                "You cannot change your own role. Ask another admin to do this."
            )

        # Verify target user exists
        target_user = await self.user_repo.get_by_id(user_id)
        if target_user is None:
            raise NotFoundError("User", str(user_id))

        # Check if role is actually changing
        if target_user.role == data.role.value:
            raise ConflictError(f"User already has the '{data.role.value}' role")

        # Update role
        updated_user = await self.user_repo.update_role(user_id, data.role.value)

        logger.info(
            f"User role updated: user={user_id} "
            f"from='{target_user.role}' to='{data.role.value}' "
            f"by={admin_user.id}"
        )

        return updated_user

    async def update_status(
        self,
        user_id: UUID,
        data: UpdateUserStatusRequest,
        admin_user: User,
    ) -> User:
        """
        Activate or deactivate a user account.

        Business rules:
          - Only admins can change status (enforced at router level)
          - Admins cannot deactivate themselves (prevents lockout)
          - Target user must exist
        """
        # Prevent self-deactivation
        if user_id == admin_user.id and not data.is_active:
            raise ForbiddenError(
                "You cannot deactivate your own account. Ask another admin to do this."
            )

        # Verify target user exists
        target_user = await self.user_repo.get_by_id(user_id)
        if target_user is None:
            raise NotFoundError("User", str(user_id))

        # Check if status is actually changing
        if target_user.is_active == data.is_active:
            status_word = "active" if data.is_active else "inactive"
            raise ConflictError(f"User is already {status_word}")

        # Update status
        updated_user = await self.user_repo.update_status(user_id, data.is_active)
        if updated_user is None:
            raise NotFoundError("User", str(user_id))

        action = "activated" if data.is_active else "deactivated"
        logger.info(f"User {action}: user={user_id} by={admin_user.id}")

        return updated_user
