"""Make an unconfigured Oracle connection a clear error before migrations."""

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.commands.migrate import Command as Migrate


class Command(Migrate):
    def handle(self, *args, **options):
        if not settings.ORACLE_CONFIGURED:
            raise CommandError("Configure ORACLE_DSN, ORACLE_USER, and ORACLE_PASSWORD before migrating.")
        return super().handle(*args, **options)
