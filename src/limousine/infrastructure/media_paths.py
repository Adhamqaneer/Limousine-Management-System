"""Private directory names and storage-key formats shared by disk and schema."""

import re
import unicodedata
from datetime import timedelta

FILE_PATTERN = r"[0-9a-f]{32}[.](jpg|jpeg|png|webp|pdf|txt|docx|xlsx)"
VEHICLE_DIRECTORY = r"vehicles/vehicle-[1-9][0-9]*"
DRIVER_DIRECTORY = r"drivers/[^/\\]+--period-[1-9][0-9]*"
VEHICLE_FILE_PATTERN = rf"^((vehicles/)|({VEHICLE_DIRECTORY}/(photos|files)/)|({DRIVER_DIRECTORY}/(photos|files)/)){FILE_PATTERN}$"
COVER_FILE_PATTERN = rf"^((vehicles/)|({VEHICLE_DIRECTORY}/covers/)){FILE_PATTERN}$"
OFFICE_FILE_PATTERN = rf"^(office/|office/(photos|files)/){FILE_PATTERN}$"
STORAGE_KEY_PATTERN = rf"^((vehicles|office)/|office/(photos|files)/|{VEHICLE_DIRECTORY}/(photos|files|covers)/|{DRIVER_DIRECTORY}/(photos|files)/){FILE_PATTERN}$"


def section_for(kind):
    return "photos" if kind == "image" else "files"


def vehicle_directory(vehicle_id):
    return f"vehicles/vehicle-{vehicle_id}"


def driver_directory(assignment):
    name = unicodedata.normalize("NFC", assignment["driver_name"])
    name = re.sub(r'[<>:"/\\|?*]', "-", name)
    name = "".join(char for char in name if not unicodedata.category(char).startswith("C"))
    name = name.strip(" .")[:60].rstrip(" .") or "Driver"
    start = assignment["started_on"]
    end = assignment["ended_on"]
    start_label = start.isoformat() if start else "بداية غير معروفة"
    if end is None:
        end_label = "الآن"
    else:
        # ended_on is exclusive; the folder shows the inclusive last working day.
        last_day = end - timedelta(days=1) if start is None or end > start else end
        end_label = last_day.isoformat()
    return f"drivers/{name} -- من {start_label} إلى {end_label} --period-{assignment['id']}"
