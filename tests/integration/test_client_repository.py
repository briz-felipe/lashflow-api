import uuid
from app.infrastructure.repositories.client_repository import ClientRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.domain.entities.client import Client
from app.domain.entities.user import User
from app.interface.dependencies import hash_password


def _make_professional(session) -> User:
    repo = UserRepository(session)
    return repo.create(User(
        username="prof",
        email="prof@test.com",
        password_hash=hash_password("pass"),
        is_superuser=True,
    ))


def _make_client(professional_id: uuid.UUID, **kwargs) -> Client:
    defaults = dict(professional_id=professional_id, name="Ana Silva", phone="11999990000")
    defaults.update(kwargs)
    return Client(**defaults)


class TestClientRepository:
    def test_create_and_get_by_id(self, session):
        prof = _make_professional(session)
        repo = ClientRepository(session)
        client = repo.create(_make_client(prof.id))
        found = repo.get_by_id(prof.id, client.id)
        assert found is not None
        assert found.name == "Ana Silva"

    def test_get_by_phone(self, session):
        prof = _make_professional(session)
        repo = ClientRepository(session)
        repo.create(_make_client(prof.id, phone="11999990001"))
        found = repo.get_by_phone(prof.id, "11999990001")
        assert found is not None

    def test_get_by_phone_not_found(self, session):
        prof = _make_professional(session)
        repo = ClientRepository(session)
        assert repo.get_by_phone(prof.id, "99999999999") is None

    def test_soft_delete_hides_client(self, session):
        prof = _make_professional(session)
        repo = ClientRepository(session)
        client = repo.create(_make_client(prof.id))
        repo.soft_delete(client)
        found = repo.get_by_id(prof.id, client.id)
        assert found is None

    def test_list_pagination(self, session):
        prof = _make_professional(session)
        repo = ClientRepository(session)
        for i in range(5):
            repo.create(_make_client(prof.id, name=f"Client {i}", phone=f"1199999000{i}"))

        clients, total = repo.list(prof.id, page=1, per_page=3)
        assert total == 5
        assert len(clients) == 3

    def test_list_search_by_name(self, session):
        prof = _make_professional(session)
        repo = ClientRepository(session)
        repo.create(_make_client(prof.id, name="Maria Silva", phone="11111111111"))
        repo.create(_make_client(prof.id, name="João Santos", phone="22222222222"))

        clients, total = repo.list(prof.id, search="Maria")
        assert total == 1
        assert clients[0].name == "Maria Silva"

    def test_professional_isolation(self, session):
        prof1 = _make_professional(session)
        prof2 = UserRepository(session).create(User(
            username="prof2",
            email="prof2@test.com",
            password_hash=hash_password("pass"),
        ))
        repo = ClientRepository(session)
        repo.create(_make_client(prof1.id))

        clients, total = repo.list(prof2.id)
        assert total == 0
