import io
import struct
import zlib
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from PIL import Image

from limousine.domain.vehicles import DomainError
from limousine.infrastructure.attachments import LocalAttachmentStore


def image_bytes(image_format, size=(2, 2)):
    with io.BytesIO() as buffer, Image.new("RGB", size, "white") as image:
        image.save(buffer, format=image_format)
        return buffer.getvalue()


def png_with_dimensions(width, height):
    """Change a tiny PNG's IHDR without allocating its advertised pixel data."""
    content = bytearray(image_bytes("PNG"))
    content[16:24] = struct.pack(">II", width, height)
    content[29:33] = struct.pack(">I", zlib.crc32(content[12:29]) & 0xFFFFFFFF)
    return bytes(content)


class ImageUploadValidationTests(SimpleTestCase):
    def setUp(self):
        self.media = TemporaryDirectory(prefix="limousine-image-tests-")
        self.addCleanup(self.media.cleanup)
        settings_override = override_settings(MEDIA_ROOT=self.media.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        self.store = LocalAttachmentStore()

    def assert_rejected_without_saved_bytes(self, name, content):
        with self.assertRaises(DomainError):
            self.store.save(SimpleUploadedFile(name, content))
        self.assertEqual(list(Path(self.media.name).rglob("*")), [])

    def test_supported_photos_are_decoded_and_original_bytes_are_preserved(self):
        for extension, image_format in (("jpg", "JPEG"), ("jpeg", "JPEG"), ("png", "PNG"), ("webp", "WEBP")):
            with self.subTest(extension=extension):
                content = image_bytes(image_format)
                stored = self.store.save(SimpleUploadedFile(f"car.{extension}", content))
                self.assertEqual(stored.kind, "image")
                self.assertEqual((Path(self.media.name) / stored.storage_key).read_bytes(), content)

    def test_signature_only_jpeg_and_webp_are_rejected(self):
        for name, content in (
            ("fake.jpg", b"\xff\xd8\xff\xff\xd9"),
            ("fake.webp", b"RIFF0000WEBPVP8 " + b"0000"),
        ):
            with self.subTest(name=name):
                self.assert_rejected_without_saved_bytes(name, content)

    def test_truncated_photos_are_rejected(self):
        for extension, image_format in (("jpg", "JPEG"), ("png", "PNG"), ("webp", "WEBP")):
            with self.subTest(extension=extension):
                self.assert_rejected_without_saved_bytes(f"car.{extension}", image_bytes(image_format)[:-12])

    def test_photo_contents_must_match_the_extension(self):
        self.assert_rejected_without_saved_bytes("car.jpg", image_bytes("PNG"))

    def test_pixel_limit_is_checked_without_changing_pillow_global_limits(self):
        original_limit = Image.MAX_IMAGE_PIXELS
        with patch("limousine.infrastructure.attachments.MAX_IMAGE_PIXELS", 3):
            self.assert_rejected_without_saved_bytes("car.png", image_bytes("PNG", size=(2, 2)))
        self.assertEqual(Image.MAX_IMAGE_PIXELS, original_limit)

    def test_decompression_warning_and_error_are_reported_as_invalid_photos(self):
        for dimensions in ((10_000, 10_000), (20_000, 20_000)):
            with self.subTest(dimensions=dimensions):
                self.assert_rejected_without_saved_bytes("oversized.png", png_with_dimensions(*dimensions))
