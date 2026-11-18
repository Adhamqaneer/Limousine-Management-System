"""Build private, temporary ZIP downloads from authorized attachment snapshots."""

import re
import unicodedata
from pathlib import PurePosixPath
from tempfile import SpooledTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

CHUNK_BYTES = 64 * 1024
SPOOL_BYTES = 8 * 1024 * 1024


def _entry_name(original_name, attachment_id, used):
    name = unicodedata.normalize("NFC", original_name).replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(
        "_" if char in '<>:"|?*' else char
        for char in name
        if not unicodedata.category(char).startswith("C")
    ).strip(" .")
    if not name:
        name = f"attachment-{attachment_id}"
    if re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", name.split(".")[0]):
        name = "_" + name
    suffix = PurePosixPath(name).suffix
    stem = name[: -len(suffix)] if suffix else name
    candidate, number = name, 2
    while candidate.casefold() in used:
        candidate = f"{stem} ({number}){suffix}"
        number += 1
    used.add(candidate.casefold())
    return candidate


def build_attachment_archive(attachments, store):
    """Finish before responding so a missing file never produces a partial ZIP."""
    output = SpooledTemporaryFile(max_size=SPOOL_BYTES, mode="w+b")
    try:
        used = set()
        with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=1) as archive:
            for item in attachments:
                name = _entry_name(item.original_name, item.id, used)
                with store.open(item.storage_key) as source, archive.open(name, "w") as destination:
                    copied = 0
                    while chunk := source.read(CHUNK_BYTES):
                        copied += len(chunk)
                        if copied > item.size:
                            raise OSError("Attachment size differs from its metadata.")
                        destination.write(chunk)
                    if copied != item.size:
                        raise OSError("Attachment size differs from its metadata.")
        output.seek(0)
        return output
    except BaseException:
        output.close()
        raise
