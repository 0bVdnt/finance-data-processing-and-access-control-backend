import logging

from fastapi import FastAPI

from app.config import get_settings
from app.errors.handlers import register_error_handlers
from app.routers import auth, dashboard, health, records, users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Backend API for a finance dashboard system with "
            "role-based access control, financial record management, "
            "and summary analytics."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Register global error handlers
    register_error_handlers(app)

    # Register routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(records.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")

    logger.info(f"Application '{settings.APP_NAME}' initialized")
    return app


app = create_app()

