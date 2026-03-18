import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.main import app
from app.infrastructure.database import get_session
import app.infrastructure.database as db_module
from app.infrastructure.repositories.user_repository import UserRepository
from app.domain.entities.user import User
from app.interface.dependencies import hash_password

# Import all entities so SQLModel registers their metadata
from app.domain.entities import (  # noqa: F401
    user, client, procedure, appointment, payment,
    anamnesis, material, stock_movement, expense,
    time_slot, blocked_date,
)


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client_app")
def client_app_fixture(engine, session):
    def override_get_session():
        yield session

    # Redirect the module-level engine so lifespan uses the test DB (not the file-based SQLite)
    original_engine = db_module.engine
    db_module.engine = engine

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
    db_module.engine = original_engine


@pytest.fixture(name="admin_user")
def admin_user_fixture(session):
    repo = UserRepository(session)
    user = User(
        username="admin",
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        is_superuser=True,
    )
    return repo.create(user)


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(client_app, admin_user):
    resp = client_app.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}
