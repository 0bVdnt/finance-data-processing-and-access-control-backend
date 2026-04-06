import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import create_access_token
from app.core.security import hash_password, verify_password
from app.errors import ConflictError
from app.errors.exceptions import InactiveAccountError, UnauthorizedError
from app.repositories.user_repository import UserRepository
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse, UserResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Handles authentication"""

    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def register(self, data: RegisterRequest) -> TokenResponse:
        """
        Register a new user.

        Flow:
            1. Check if email is already taken
            2. Hash the password
            3. Create the user with default role (viewer)
            4. Generate JWT token
            5. Return token + user data
        """

        # Check for duplicate email
        if await self.user_repo.email_exists(data.email):
            raise ConflictError(f"Email '{data.email}' is already registered")

        # Hash password and create_user
        hashed = hash_password(data.password)
        user = await self.user_repo.create(
            email=data.email,
            password_hash=hashed,
            full_name=data.full_name,
            role="viewer",
        )

        logger.info(f"User registered: {user.email} (id={user.id})")

        # Generate token so user is logged in immediately after registration
        token = create_access_token(user_id=user.id, role=user.role)

        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    async def login(self, data: LoginRequest) -> TokenResponse:
        """
        Authenticate a user with email and password

        Flow:
            1. Find user by email
            2. Verify password
            3. Check if account is active
            4. Generate and return JWT token

        Returns the same error for 'user not found' and 'wrong password'
        to prevent email enumeration attacks
        """

        # Find user - use generic error to prevent email enumeration
        user = await self.user_repo.get_by_email(data.email)
        if user is None:
            raise UnauthorizedError("Invalid email or password")

        # Verify password
        if not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        # Check account status
        if not user.is_active:
            raise InactiveAccountError()

        logger.info(f"User logged in: {user.email} (id={user.id})")

        token = create_access_token(user_id=user.id, role=user.role)

        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )
