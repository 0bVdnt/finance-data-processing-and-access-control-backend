from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=ApiResponse[TokenResponse],
    status_code=201,
    summary="Register a new user",
    description=(
        "Create a new user account. New users are assigned the 'viewer' role by default."
        "Return a JWT token so the user is logged in immediately."
    ),
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    result = await service.register(data)
    return ApiResponse(success=True, data=result)


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    summary="Login with email and password",
    description=(
        "Authenticate with email and password."
        "Returns a JWT token to use in subsequent requests."
    ),
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    result = await service.login(data)
    return ApiResponse(success=True, data=result)


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return ApiResponse(
        success=True,
        data=UserResponse.model_validate(current_user),
    )
