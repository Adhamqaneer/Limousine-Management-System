"""Allow local foundation work before an Oracle account is available."""

from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import Command as Runserver


class Command(Runserver):
    def check_migrations(self):
        if not settings.ORACLE_CONFIGURED:
            self.stdout.write(self.style.WARNING(
                "Oracle is not configured. Database features remain unavailable; readiness returns 503."
            ))
            return
        super().check_migrations()
