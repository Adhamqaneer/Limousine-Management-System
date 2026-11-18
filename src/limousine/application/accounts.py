"""Account authentication and administration use cases."""

from typing import Protocol
from uuid import UUID

from limousine.domain.accounts import User, authorize_account_change


class AccountRepository(Protocol):
    def authenticate(self, username: str, password: str) -> User | None: ...
    def list_users(self) -> list[User]: ...
    def get_user(self, user_id: UUID) -> User: ...
    def update_status(self, user_id: UUID, active: bool, deleted: bool) -> User: ...


class AccountService:
    def __init__(self, repository: AccountRepository):
        self.repository = repository

    def authenticate(self, username, password):
        if not isinstance(username, str) or not isinstance(password, str):
            return None
        return self.repository.authenticate(username.strip(), password)

    def change_status(self, actor, user_id, changes):
        target = self.repository.get_user(user_id)
        active, deleted = authorize_account_change(actor, target, changes)
        return self.repository.update_status(user_id, active, deleted)
