"""Recovery contracts and authorization, independent of HTTP/PostgreSQL."""
from typing import Protocol
from limousine.domain.recycling import require_actor, validate_kind
from limousine.domain.vehicles import DomainError

class RecyclingRepository(Protocol):
    def delete_vehicle(self, vehicle_id, actor): ...
    def list_deleted(self): ...
    def restore_item(self, kind, item_id, actor): ...
    def list_activity(self, before=None): ...

class RecyclingService:
    def __init__(self, repository: RecyclingRepository):
        self.repository = repository

    def delete_vehicle(self, vehicle_id, actor):
        require_actor(actor)
        return self.repository.delete_vehicle(vehicle_id, actor)

    def list_deleted(self, actor):
        require_actor(actor, restoring=True)
        return self.repository.list_deleted()

    def restore_item(self, kind, item_id, actor):
        require_actor(actor, restoring=True)
        validate_kind(kind)
        return self.repository.restore_item(kind, item_id, actor)

    def list_activity(self, actor, before=None):
        require_actor(actor, restoring=True)
        if before is not None and (isinstance(before, bool) or not isinstance(before, int) or not 0 < before <= 9223372036854775807):
            raise DomainError('Invalid activity cursor.')
        return self.repository.list_activity(before)
