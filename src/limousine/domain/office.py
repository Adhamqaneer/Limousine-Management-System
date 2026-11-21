"""Office documents belong to the office, independently of any vehicle."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OfficeAttachment:
    id: int
    storage_key: str
    original_name: str
    kind: str
    size: int
    created_at: datetime
    category_id: int | None = None
