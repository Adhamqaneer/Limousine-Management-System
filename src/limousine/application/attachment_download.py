"""Select original vehicle attachments by type for a single ZIP download."""

from dataclasses import dataclass
from typing import Protocol

from limousine.application.categories import record_id
from limousine.domain.recycling import require_actor
from limousine.domain.vehicles import DomainError, NotFound


def selected_ids(values, limit):
    if not isinstance(values, list) or not values or len(values) > limit:
        raise DomainError("Choose a non-empty selection within the download limit.")
    return list(dict.fromkeys(record_id(value) for value in values))


class AttachmentDownloadRepository(Protocol):
    def selection(self, vehicle_ids, category_ids): ...
    def availability(self, vehicle_ids, category_ids): ...


@dataclass(frozen=True)
class VehicleArchiveSelection:
    files: tuple
    missing: tuple


class AttachmentDownloadService:
    def __init__(self, repository: AttachmentDownloadRepository):
        self.repository = repository

    def availability(self, vehicle_ids, category_ids, actor):
        require_actor(actor)
        vehicles, categories, counts = self.repository.availability(
            selected_ids(vehicle_ids, 500), selected_ids(category_ids, 50)
        )
        totals = {(row["vehicle_id"], row["category_id"]): row["count"] for row in counts}
        rows = [
            {
                "id": vehicle["id"],
                "plate_number": vehicle["plate_number"],
                "documents": [
                    {
                        "category_id": category["id"],
                        "count": totals.get((vehicle["id"], category["id"]), 0),
                    }
                    for category in categories
                ],
            }
            for vehicle in vehicles
        ]
        return {"vehicles": rows, "file_count": sum(totals.values())}

    def select(self, vehicle_ids, category_ids, actor):
        require_actor(actor)
        vehicles, categories, files = self.repository.selection(
            selected_ids(vehicle_ids, 500), selected_ids(category_ids, 50)
        )
        if not files:
            raise NotFound("No matching attachments to download.")
        if len(files) > 1000 or sum(item["size"] for item in files) > 1024**3:
            raise DomainError(
                "Download up to 1000 files and 1 GB at a time. Use vehicle filters for a smaller group."
            )
        present = {(item["vehicle_id"], item["category_id"]) for item in files}
        missing = tuple(
            {"plate_number": vehicle["plate_number"], "category_name": category["name"]}
            for vehicle in vehicles
            for category in categories
            if (vehicle["id"], category["id"]) not in present
        )
        return VehicleArchiveSelection(tuple(files), missing)
