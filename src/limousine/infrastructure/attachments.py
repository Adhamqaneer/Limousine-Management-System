"""Bounded local attachment storage; business metadata remains in PostgreSQL."""

import io
import re
import unicodedata
import uuid
import warnings
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from PIL import Image, UnidentifiedImageError

from limousine.domain.vehicles import DomainError
from limousine.infrastructure.media_paths import STORAGE_KEY_PATTERN, section_for

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
IMAGE_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}
IMAGE_MIMES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
FILE_MIMES = {
    ".pdf": "application/pdf",
    ".txt": "text/plain; charset=utf-8",
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
    name = "".join(
        character for character in name if not unicodedata.category(character).startswith("C")
    )
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
        UnidentifiedImageError,
        OSError,
        ValueError,
        SyntaxError,
        OverflowError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
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
            valid = all(
                character in "\r\n\t" or unicodedata.category(character) != "Cc"
                for character in text
            )
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
    def __init__(self, root=None):
        from limousine.config.runtime import ROOT

        self.root = Path(root) if root is not None else ROOT / "media"

    def save(self, upload, *, namespace="vehicles", directory=None, card_photo=False):
        if namespace not in ("vehicles", "office"):
            raise DomainError("Invalid attachment namespace.")
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
        kind = "image" if extension in IMAGE_MIMES else "file"
        if directory is not None:
            section = "covers" if card_photo else section_for(kind)
            directory = directory.rstrip("/") + "/" + section
        elif namespace == "office":
            directory = "office/" + section_for(kind)
        else:
            directory = namespace
        key = f"{directory}/{uuid.uuid4().hex}{extension}"
        target = self.path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("xb") as output:
                output.write(content)
        except OSError:
            target.unlink(missing_ok=True)
            raise
        return StoredUpload(key, name, kind, len(content))

    def save_office_file(self, upload):
        return self.save(upload, namespace="office")

    def save_card_photo(self, upload, *, directory=None):
        if PurePosixPath(safe_original_name(upload.name)).suffix.lower() not in IMAGE_MIMES:
            raise DomainError("Choose a JPG, PNG or WebP card photo.")
        return self.save(upload, directory=directory, card_photo=True)

    @staticmethod
    def _check_key(key):
        # Keys are generated internally, but validate persisted values before filesystem use.
        if not isinstance(key, str) or not re.fullmatch(STORAGE_KEY_PATTERN, key):
            raise FileNotFoundError("Attachment not found.")
        if any(unicodedata.category(char).startswith("C") or char in '<>:"\\|?*' for char in key):
            raise FileNotFoundError("Attachment not found.")

    def open(self, key):
        self._check_key(key)
        return self.path(key).open("rb")

    def path(self, key):
        self._check_key(key)
        target = (self.root / key).resolve()
        if not target.is_relative_to(self.root.resolve()):
            raise FileNotFoundError("Attachment not found.")
        return target

    def delete(self, key):
        self._check_key(key)
        target = self.path(key)
        target.unlink(missing_ok=True)
        # Remove empty retired directories only; never recursively delete data.
        parent = target.parent
        while len(parent.relative_to(self.root.resolve()).parts) > 1:
            for name in ("photos", "files", "covers"):
                try:
                    (parent / name).rmdir()
                except OSError:
                    pass
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent

    @staticmethod
    def content_type(key):
        extension = PurePosixPath(key).suffix.lower()
        return IMAGE_MIMES.get(extension) or FILE_MIMES.get(extension, "application/octet-stream")
