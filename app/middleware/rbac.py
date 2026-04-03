from fastapi import Depends

from app.errors import ForbiddenError
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.user import Role


class RequireRole:
    """
    FastAPI dependency that enforces role-based access control.

    Checks that the authenticated user has one of the allowed roles.
    Returns the user if authorized, raises ForbiddenError otherwise.

    Usage:
        # Single role
        @router.get('/admin-only')
        async def admin_route(user: User = Depends(RequireRole(Role.ADMIN))):
            ...

        # Multiple roles
        @router.get('/analysts-and-admins')
        async def analyst_route(user: User = Depends(RequireRole(Role.ANALYST, Role.ADMIN))):
            ...

    Permissions:
        1. Viewer
            - View own records
            - View dashboard (own)
        2. Analyst
            - View own records
            - View dashboard (own)
            - Access insights
        3. Admin
            - View all records
            - Create, Update, Delete Records
            - View dashboard (own and global)
            - Access insights
            - Manage users
    """

    def __init__(self, *allowed_roles: Role):
        if not allowed_roles:
            raise ValueError("At least one role must be specified")
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """Check if the current user's role in the allowed list."""
        user_role = current_user.role

        # Check if user's role matches any of the allowed roles
        allowed_values = [role.value for role in self.allowed_roles]
        if user_role not in allowed_values:
            raise ForbiddenError(
                f"Role '{user_role}' does not have permission for this action. "
                f"Required role(s): {', '.join(allowed_values)}"
            )

        return current_user
