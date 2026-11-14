"""Oracle-only Django configuration, with optional Autonomous mTLS wallets."""

import os

from django.core.exceptions import ImproperlyConfigured


def oracle_database():
    values = {name: os.environ.get(name, "") for name in (
        "ORACLE_DSN", "ORACLE_USER", "ORACLE_PASSWORD"
    )}
    values["ORACLE_DSN"] = values["ORACLE_DSN"].strip()
    values["ORACLE_USER"] = values["ORACLE_USER"].strip()
    configured = all(values.values())
    if any(values.values()) and not configured:
        missing = ", ".join(name for name, value in values.items() if not value)
        raise ImproperlyConfigured(f"Incomplete Oracle configuration. Missing: {missing}")

    options = {"tcp_connect_timeout": 5, "retry_count": 0}
    for variable, option in (
        ("ORACLE_CONFIG_DIR", "config_dir"),
        ("ORACLE_WALLET_LOCATION", "wallet_location"),
        ("ORACLE_WALLET_PASSWORD", "wallet_password"),
    ):
        if value := os.environ.get(variable, ""):
            options[option] = value

    return {
        "ENGINE": "django.db.backends.oracle",
        "NAME": values["ORACLE_DSN"],
        "USER": values["ORACLE_USER"],
        "PASSWORD": values["ORACLE_PASSWORD"],
        # A full DSN/Easy Connect string belongs in NAME; leave HOST and PORT empty.
        "HOST": "",
        "PORT": "",
        "OPTIONS": options,
        "CONN_MAX_AGE": 0,
    }, configured
