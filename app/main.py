from fastapi_mcp import FastApiMCP
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session, text

import app.infrastructure.database as _db
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command
import os
from app.infrastructure.settings import settings
from app.infrastructure.repositories.user_repository import UserRepository
from app.domain.entities.user import User
from app.domain.exceptions import (
    InvalidStatusTransition,
    SlotUnavailable,
    InsufficientStock,
    DuplicatePhone,
    AllergyDetailRequired,
)
from app.interface.dependencies import hash_password
from app.interface.routers import auth as auth_router
from app.interface.routers import clients as clients_router
from app.interface.routers import procedures as procedures_router
from app.interface.routers import appointments as appointments_router
from app.interface.routers import payments as payments_router
from app.interface.routers import anamneses as anamneses_router
from app.interface.routers import stock as stock_router
from app.interface.routers import expenses as expenses_router
from app.interface.routers import settings_router
from app.interface.routers import dashboard as dashboard_router
from app.interface.routers import public as public_router
from app.interface.routers import integrations_router


def _run_migrations() -> None:
    """Run any pending Alembic migrations on startup."""
    try:
        ini_path = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
        cfg = AlembicConfig(os.path.abspath(ini_path))
        alembic_command.upgrade(cfg, "head")
    except Exception as e:
        # Don't crash the server if migrations fail — log and continue
        import logging
        logging.getLogger(__name__).error("Alembic migration failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run DB migrations (creates tables + applies pending ALTER TABLE, etc.)
    _run_migrations()

    # Seed admin user if no users exist
    with Session(_db.engine) as session:
        repo = UserRepository(session)
        if not repo.exists_any():
            admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL if settings.ADMIN_EMAIL else None,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                is_superuser=True,
            )
            repo.create(admin)

    yield


app = FastAPI(
    title="LashFlow API",
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

# --- CORS ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception Handlers ---

@app.exception_handler(InvalidStatusTransition)
async def handle_invalid_transition(request: Request, exc: InvalidStatusTransition):
    return JSONResponse(
        status_code=422,
        content={"error": "INVALID_TRANSITION", "message": str(exc), "status_code": 422},
    )


@app.exception_handler(SlotUnavailable)
async def handle_slot_unavailable(request: Request, exc: SlotUnavailable):
    return JSONResponse(
        status_code=409,
        content={"error": "SLOT_UNAVAILABLE", "message": str(exc), "status_code": 409},
    )


@app.exception_handler(InsufficientStock)
async def handle_insufficient_stock(request: Request, exc: InsufficientStock):
    return JSONResponse(
        status_code=422,
        content={"error": "INSUFFICIENT_STOCK", "message": str(exc), "status_code": 422},
    )


@app.exception_handler(DuplicatePhone)
async def handle_duplicate_phone(request: Request, exc: DuplicatePhone):
    return JSONResponse(
        status_code=409,
        content={"error": "DUPLICATE_PHONE", "message": str(exc), "status_code": 409},
    )


@app.exception_handler(AllergyDetailRequired)
async def handle_allergy_detail(request: Request, exc: AllergyDetailRequired):
    return JSONResponse(
        status_code=422,
        content={"error": "ALLERGY_DETAIL_REQUIRED", "message": str(exc), "status_code": 422},
    )
    
# -- Health Check Endpoint ---
@app.get("/health")
def health_check():
    """Simple health check endpoint to verify the API is running."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}





# --- Routers ---

PREFIX = "/api/v1"

app.include_router(auth_router.router, prefix=PREFIX)
app.include_router(clients_router.router, prefix=PREFIX)
app.include_router(procedures_router.router, prefix=PREFIX)
app.include_router(appointments_router.router, prefix=PREFIX)
app.include_router(payments_router.router, prefix=PREFIX)
app.include_router(anamneses_router.router, prefix=PREFIX)
app.include_router(stock_router.router, prefix=PREFIX)
app.include_router(expenses_router.router, prefix=PREFIX)
app.include_router(settings_router.router, prefix=PREFIX)
app.include_router(dashboard_router.router, prefix=PREFIX)
app.include_router(public_router.router, prefix=PREFIX)
app.include_router(integrations_router.router, prefix=PREFIX)

# --- MCP Server (deve ser montado após todos os routers) ---
mcp = FastApiMCP(app)
mcp.mount()
