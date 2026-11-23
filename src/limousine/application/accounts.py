"""Office sign-in use case."""

from typing import Protocol


class AccountRepository(Protocol):
    def sign_in(
        self, username: str, password: str, seconds: int, previous_token: str
    ) -> str | None: ...


class AccountService:
    def __init__(self, repository: AccountRepository):
        self.repository = repository

    def sign_in(self, username, password, seconds, previous_token):
        return self.repository.sign_in(username.strip(), password, seconds, previous_token)
