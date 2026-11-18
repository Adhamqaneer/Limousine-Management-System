"""Attachment display-name rules; stored file identity and extension stay fixed."""

import re
import unicodedata
from pathlib import PurePosixPath

from limousine.domain.vehicles import DomainError


class AttachmentNameError(DomainError):
    pass


class AttachmentNameConflict(DomainError):
    pass


def renamed_attachment_name(name, current_name):
    if not isinstance(name, str):
        raise AttachmentNameError("Enter a file name.")
    name = unicodedata.normalize("NFC", name.strip())
    extension = PurePosixPath(current_name).suffix
    if (
        not name
        or name in (".", "..")
        or name.endswith(".")
        or any(char in '<>:"/\\|?*' or unicodedata.category(char).startswith("C") for char in name)
        or re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", name.split(".")[0])
        or len(name + extension) > 180
    ):
        raise AttachmentNameError(
            "Use a name up to 180 characters including its fixed extension, without path or reserved characters."
        )
    return name + extension
