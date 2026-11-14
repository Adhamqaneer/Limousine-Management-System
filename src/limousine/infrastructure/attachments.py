"""Bounded local attachment storage; business metadata remains in Oracle."""

import io
import re
import unicodedata
import uuid
import warnings
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from PIL import Image, UnidentifiedImageError

from limousine.domain.vehicles import DomainError

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
IMAGE_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}
IMAGE_MIMES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp",
}
FILE_MIMES = {
    ".pdf": "application/pdf", ".txt": "text/plain; charset=utf-8",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class AttachmentTooLarge(DomainError):
    pass


@dataclass(frozen=True)
class StoredUpload:
    storage_key: str
    original_name: str
    kind: str
    size: int


def safe_original_name(name):
    name = unicodedata.normalize("NFC", str(name or "")).replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(character for character in name if not unicodedata.category(character).startswith("C"))
    name = name.strip(" .")
    if not name or len(name) > 180:
        raise DomainError("Choose a file with a name of 1 to 180 characters.")
    return name


def _validate_image(extension, content):
    expected_format = IMAGE_FORMATS[extension]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content), formats=[expected_format]) as image:
                if image.format != expected_format:
                    raise DomainError("The image format does not match its file extension.")
                width, height = image.size
                if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
                    raise DomainError("Photos must contain no more than 25 million pixels.")
                image.verify()
            # verify() checks structure but does not decode all pixel data.
            # Reopening and loading also rejects truncated compressed content.
            with Image.open(io.BytesIO(content), formats=[expected_format]) as image:
                image.load()
    except DomainError:
        raise
    except (
        UnidentifiedImageError, OSError, ValueError, SyntaxError, OverflowError,
        Image.DecompressionBombError, Image.DecompressionBombWarning,
    ) as error:
        raise DomainError("Choose a valid, complete JPG, PNG or WebP photo.") from error


def _validate_content(extension, content):
    if not content:
        raise DomainError("Empty files cannot be uploaded.")
    valid = False
    if extension in IMAGE_FORMATS:
        _validate_image(extension, content)
        return
    elif extension == ".pdf":
        valid = content.startswith(b"%PDF-")
    elif extension == ".txt":
        try:
            text = content.decode("utf-8-sig")
            valid = all(character in "\r\n\t" or unicodedata.category(character) != "Cc" for character in text)
        except UnicodeDecodeError:
            valid = False
    elif extension in (".docx", ".xlsx"):
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                infos = archive.infolist()
                names = {item.filename for item in infos}
                expected = "word/document.xml" if extension == ".docx" else "xl/workbook.xml"
                valid = (
                    len(infos) <= 5000
                    and sum(item.file_size for item in infos) <= 100 * 1024 * 1024
                    and {"[Content_Types].xml", "_rels/.rels", expected}.issubset(names)
                )
        except (zipfile.BadZipFile, OSError, ValueError):
            valid = False
    if not valid:
        raise DomainError("The file content does not match its supported file type.")


class LocalAttachmentStore:
    def __init__(self):
        self.storage = FileSystemStorage(location=settings.MEDIA_ROOT)

    def save(self, upload):
        if upload.size is not None and upload.size > MAX_ATTACHMENT_BYTES:
            raise AttachmentTooLarge("The file must be 10 MB or smaller.")
        name = safe_original_name(upload.name)
        extension = PurePosixPath(name).suffix.lower()
        if extension not in IMAGE_MIMES and extension not in FILE_MIMES:
            raise DomainError("Supported files: JPG, PNG, WebP, PDF, TXT, DOCX and XLSX.")
        content = upload.read(MAX_ATTACHMENT_BYTES + 1)
        if len(content) > MAX_ATTACHMENT_BYTES:
            raise AttachmentTooLarge("The file must be 10 MB or smaller.")
        _validate_content(extension, content)
        key = f"vehicles/{uuid.uuid4().hex}{extension}"
        saved_key = self.storage.save(key, ContentFile(content))
        return StoredUpload(saved_key, name, "image" if extension in IMAGE_MIMES else "file", len(content))

    @staticmethod
    def _check_key(key):
        # Keys are generated internally, but validate persisted values before filesystem use.
        if not isinstance(key, str) or not re.fullmatch(r"vehicles/[0-9a-f]{32}\.(?:jpe?g|png|webp|pdf|txt|docx|xlsx)", key):
            raise FileNotFoundError("Attachment not found.")

    def open(self, key):
        self._check_key(key)
        return self.storage.open(key, "rb")

    def delete(self, key):
        self._check_key(key)
        self.storage.delete(key)

    @staticmethod
    def content_type(key):
        return IMAGE_MIMES.get(PurePosixPath(key).suffix.lower(), "application/octet-stream")
