"""Shared office-file use cases; HTTP and storage stay in adapters."""

from typing import Protocol

from limousine.domain.attachments import AttachmentNameConflict, renamed_attachment_name
from limousine.domain.office import OfficeAttachment
from limousine.domain.recycling import require_actor
from limousine.domain.vehicles import DomainError, NotFound


class OfficeRepository(Protocol):
    def list_files(self) -> list[OfficeAttachment]: ...
    def get(self, item_id) -> OfficeAttachment: ...
    def add(self, storage_key, original_name, kind, size, actor) -> OfficeAttachment: ...
    def rename(self, item_id, name, expected_name, actor) -> OfficeAttachment: ...
    def delete(self, item_id, actor): ...


class OfficeService:
    def __init__(self, repository: OfficeRepository):
        self.repository = repository

    def list_files(self):
        return self.repository.list_files()

    def get(self, item_id):
        return self.repository.get(item_id)

    def add(self, storage_key, original_name, kind, size, actor):
        require_actor(actor)
        valid_storage_key = (
            isinstance(storage_key, str)
            and storage_key.startswith("office/")
            and len(storage_key) <= 500
        )
        valid_name = (
            isinstance(original_name, str)
            and bool(original_name.strip())
            and len(original_name) <= 180
        )
        valid_size = isinstance(size, int) and not isinstance(size, bool) and 0 < size <= 10485760
        if not all((valid_storage_key, valid_name, valid_size, kind in ("image", "file"))):
            raise DomainError("Invalid office attachment metadata.")
        return self.repository.add(storage_key, original_name, kind, size, actor)

    def rename(self, item_id, name, expected_name, actor):
        require_actor(actor)
        item = self.get(item_id)
        if item.original_name != expected_name:
            raise AttachmentNameConflict("The attachment name changed. Refresh and try again.")
        return self.repository.rename(
            item_id, renamed_attachment_name(name, item.original_name), expected_name, actor
        )

    def delete(self, item_id, actor):
        require_actor(actor)
        self.repository.delete(item_id, actor)

    def download(self, kind):
        if kind not in ("image", "file"):
            raise DomainError("Choose photos or files.")
        items = tuple(item for item in self.list_files() if item.kind == kind)
        if not items:
            raise NotFound("No office attachments in this section.")
        return items
