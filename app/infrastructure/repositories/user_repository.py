import uuid
from typing import Optional
from sqlmodel import select
from app.infrastructure.repositories.base import BaseRepository
from app.domain.entities.user import User


class UserRepository(BaseRepository[User]):
    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.session.get(User, user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        return self.session.exec(
            select(User).where(User.username == username)
        ).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.exec(
            select(User).where(User.email == email)
        ).first()

    def create(self, user: User) -> User:
        return self._save(user)

    def update(self, user: User) -> User:
        return self._touch(user)

    def exists_any(self) -> bool:
        """Returns True if at least one user exists (used in lifespan admin seed)."""
        result = self.session.exec(select(User).limit(1)).first()
        return result is not None
