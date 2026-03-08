import pytest
from app.infrastructure.repositories.user_repository import UserRepository
from app.domain.entities.user import User
from app.interface.dependencies import hash_password


def _make_user(**kwargs):
    defaults = dict(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("pass123"),
    )
    defaults.update(kwargs)
    return User(**defaults)


class TestUserRepository:
    def test_create_and_get_by_id(self, session):
        repo = UserRepository(session)
        user = repo.create(_make_user())
        found = repo.get_by_id(user.id)
        assert found is not None
        assert found.username == "testuser"

    def test_get_by_username(self, session):
        repo = UserRepository(session)
        repo.create(_make_user())
        found = repo.get_by_username("testuser")
        assert found is not None

    def test_get_by_username_not_found(self, session):
        repo = UserRepository(session)
        assert repo.get_by_username("nobody") is None

    def test_get_by_email(self, session):
        repo = UserRepository(session)
        repo.create(_make_user())
        found = repo.get_by_email("test@example.com")
        assert found is not None

    def test_exists_any_false_when_empty(self, session):
        repo = UserRepository(session)
        assert repo.exists_any() is False

    def test_exists_any_true_after_create(self, session):
        repo = UserRepository(session)
        repo.create(_make_user())
        assert repo.exists_any() is True

    def test_create_admin_with_superuser(self, session):
        repo = UserRepository(session)
        user = repo.create(_make_user(is_superuser=True))
        assert user.is_superuser is True
