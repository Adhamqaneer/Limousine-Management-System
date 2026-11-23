from unittest import TestCase
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from limousine.config.runtime import Settings
from limousine.domain.accounts import OPERATOR_USERNAME, User
from limousine.infrastructure.accounts import PostgresAccountRepository, token_hash
from limousine.infrastructure.passwords import hash_password, verify_password
from limousine.presentation.web.app import create_app

OPERATOR = User(uuid4(), OPERATOR_USERNAME)
TEST_PASSWORD = "Test-only password"


class AccountTests(TestCase):
    def test_only_the_office_username_can_create_a_session(self):
        database = MagicMock()
        connection = database.connect.return_value.__enter__.return_value
        encoded = hash_password(TEST_PASSWORD)
        connection.execute.return_value.fetchone.return_value = {
            "user_id": OPERATOR.id,
            "password_hash": encoded,
        }
        accounts = PostgresAccountRepository(database)
        self.assertIsNone(accounts.sign_in("Former user", TEST_PASSWORD, 60))
        self.assertIsNone(accounts.sign_in(OPERATOR_USERNAME, "incorrect", 60))
        token = accounts.sign_in(OPERATOR_USERNAME, TEST_PASSWORD, 60, "prior-session")
        self.assertTrue(token)
        connection.execute.assert_any_call(
            "INSERT INTO hspace_session (token_hash,user_id,expires_at) VALUES (%s,%s,%s)",
            (token_hash(token), OPERATOR.id, connection.execute.call_args_list[-2].args[1][2]),
        )

    def test_password_hashes_are_compatible_and_never_plaintext(self):
        encoded = hash_password(TEST_PASSWORD)
        self.assertNotIn(TEST_PASSWORD, encoded)
        self.assertTrue(verify_password(TEST_PASSWORD, encoded))
        self.assertFalse(verify_password("wrong", encoded))
        self.assertFalse(verify_password("wrong", "invalid"))

    def test_all_business_and_file_routes_require_sign_in(self):
        client = TestClient(create_app(Settings()))
        for path in (
            "/api/vehicles/",
            "/api/vehicles/1/",
            "/api/vehicles/1/cover/",
            "/api/vehicles/1/attachments/1/preview/",
            "/api/vehicles/1/attachments/1/download/",
        ):
            self.assertEqual(client.get(path).status_code, 401)
        self.assertEqual(client.get("/", follow_redirects=False).headers["location"], "/login/")

    def test_signed_csrf_blocks_missing_forged_and_cross_session_tokens(self):
        app = create_app(Settings())
        app.state.accounts = MagicMock()
        app.state.accounts.session_user.return_value = OPERATOR
        client = TestClient(app)
        self.assertEqual(client.post("/login/", data={"password": "private"}).status_code, 403)
        client.get("/login/")
        token = client.cookies["csrftoken"]
        self.assertEqual(
            client.post("/logout/", data={"csrfmiddlewaretoken": "forged"}).status_code, 403
        )
        client.cookies.set("hspace_session", "another-session")
        self.assertEqual(
            client.post("/logout/", data={"csrfmiddlewaretoken": token}).status_code, 403
        )

    def test_team_management_routes_are_removed(self):
        app = create_app(Settings())
        app.state.accounts = MagicMock()
        app.state.accounts.session_user.return_value = OPERATOR
        client = TestClient(app, cookies={"hspace_session": "opaque-session"})
        self.assertEqual(client.get("/api/users/").status_code, 404)
        self.assertEqual(client.get("/users/").status_code, 404)
        self.assertEqual(client.patch(f"/api/users/{OPERATOR.id}/").status_code, 404)
