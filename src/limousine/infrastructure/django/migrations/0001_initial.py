"""Initial vehicle records; apply only after configuring the Oracle connection."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="VehicleRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plate_number", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "limo_vehicle", "ordering": ("id",)},
        ),
        migrations.CreateModel(
            name="AttachmentRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("storage_key", models.CharField(max_length=500)),
                ("original_name", models.CharField(max_length=255)),
                ("kind", models.CharField(choices=[("image", "Image"), ("file", "File")], max_length=5)),
                ("size", models.PositiveBigIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("vehicle", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="foundation.vehiclerecord")),
            ],
            options={"db_table": "limo_attachment", "ordering": ("id",)},
        ),
    ]
