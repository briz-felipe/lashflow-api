from typing import Generic, TypeVar
from datetime import datetime, timezone
from sqlmodel import Session, SQLModel

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: Session) -> None:
        self.session = session

    def _save(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def _delete(self, obj: ModelT) -> None:
        self.session.delete(obj)
        self.session.commit()

    def _touch(self, obj: ModelT) -> ModelT:
        """Update updated_at timestamp and save."""
        if hasattr(obj, "updated_at"):
            obj.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]
        return self._save(obj)

    # NOTE: Cache hooks — to add a cache layer in the future, wrap individual
    # repository methods in concrete subclasses with a cache.get/cache.set
    # pattern. The BaseRepository interface does not change — callers stay the same.
    # Example future pattern per method:
    #   cache_key = f"{entity}:{professional_id}:{id}"
    #   cached = self.cache.get(cache_key)
    #   if cached: return cached
    #   result = <query>
    #   self.cache.set(cache_key, result, ttl=300)
    #   return result
