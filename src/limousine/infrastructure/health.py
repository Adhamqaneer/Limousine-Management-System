"""Oracle readiness probe; technical status is kept outside business layers."""

from django.conf import settings
from django.db import Error, connections


def database_status():
    if not settings.ORACLE_CONFIGURED:
        return "not_configured"
    connection = connections["default"]
    status = "unavailable"
    try:
        with connection.cursor() as cursor:
            connection.connection.call_timeout = 2000
            cursor.execute("SELECT 1 FROM DUAL")
            if cursor.fetchone() == (1,):
                status = "ok"
    except Error:
        # Exception messages may contain hosts, DSNs, or other confidential data.
        pass
    finally:
        try:
            connection.close()
        except Error:
            status = "unavailable"
    return status
