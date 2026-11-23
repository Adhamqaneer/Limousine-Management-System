"""ASGI entry point for the local website."""

from .factory import create_app as create_app

app = create_app()
