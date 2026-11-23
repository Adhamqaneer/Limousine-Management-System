"""Shared classification and alias/merge use cases available to every active account."""

from typing import Protocol

from limousine.domain.categories import category_key, category_name
from limousine.domain.recycling import require_actor
from limousine.domain.vehicles import DomainError


def record_id(value):
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 < value <= 9223372036854775807
    ):
        raise DomainError("Choose a valid record.")
    return value


class CategoryRepository(Protocol):
    def list_categories(self, query=""): ...
    def create(self, name, key, actor, allow_similar=False): ...
    def add_alias(self, category_id, name, key, actor): ...
    def merge(self, source_id, target_id, actor): ...
    def classify(
        self, vehicle_id, attachment_id, category_id, actor, assignment_id=None
    ): ...
    def get(self, category_id): ...


class CategoryService:
    def __init__(self, repository: CategoryRepository):
        self.repository = repository

    def list_categories(self, query=""):
        if not isinstance(query, str) or len(query) > 100:
            raise DomainError("Category search is too long.")
        return self.repository.list_categories(query.strip())

    def get(self, category_id):
        return self.repository.get(record_id(category_id))

    def create(self, name, actor, allow_similar=False):
        require_actor(actor)
        if type(allow_similar) is not bool:
            raise DomainError("Confirm whether this is a distinct type.")
        name = category_name(name)
        return self.repository.create(name, category_key(name), actor, allow_similar)

    def add_alias(self, category_id, name, actor):
        require_actor(actor)
        name = category_name(name)
        return self.repository.add_alias(record_id(category_id), name, category_key(name), actor)

    def merge(self, source_id, target_id, actor):
        require_actor(actor)
        return self.repository.merge(record_id(source_id), record_id(target_id), actor)

    def classify(
        self, vehicle_id, attachment_id, category_id, actor, assignment_id=None
    ):
        require_actor(actor)
        return self.repository.classify(
            vehicle_id,
            record_id(attachment_id),
            record_id(category_id),
            actor,
            assignment_id,
        )
