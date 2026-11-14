"""Oracle-backed records. Business validation belongs in the application layer."""

from django.db import models


class VehicleRecord(models.Model):
    plate_number = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "limo_vehicle"
        ordering = ("id",)


class AttachmentRecord(models.Model):
    vehicle = models.ForeignKey(VehicleRecord, on_delete=models.CASCADE, related_name="attachments")
    storage_key = models.CharField(max_length=500)
    original_name = models.CharField(max_length=255)
    kind = models.CharField(max_length=5, choices=[("image", "Image"), ("file", "File")])
    size = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "limo_attachment"
        ordering = ("id",)
