from dataclasses import replace
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient
from limousine.config.runtime import Settings
from limousine.domain.accounts import User, Role, AccessDenied, validate_slot, normalize_username, authorize_account_change
from limousine.infrastructure.passwords import hash_password, verify_password
from limousine.presentation.web.app import create_app

STAMP=datetime.now(timezone.utc)
ADMIN=User(uuid4(),1,"Adham qaneer",Role.ADMIN,True,False,None,STAMP)
MEMBER=User(uuid4(),2,"Member",Role.MEMBER,True,False,None,STAMP)

class AccountTests(TestCase):
    def test_names_uuid_roles_and_four_slots(self):
        self.assertEqual(normalize_username(" Adham qaneer "),"Adham qaneer")
        for value in (0,5,True,"1"):
            with self.assertRaises(ValueError): validate_slot(value)
        for value in ("","name\nother","<name>"):
            with self.assertRaises(ValueError): normalize_username(value)
        self.assertEqual(Role.ADMIN.value,"ADMIN")
        self.assertTrue(ADMIN.can_login)
        self.assertFalse(replace(MEMBER,is_deleted=True).can_login)

    def test_only_admin_can_manage_members_and_admin_is_protected(self):
        with self.assertRaises(AccessDenied): authorize_account_change(MEMBER,MEMBER,{"is_active":False})
        with self.assertRaises(AccessDenied): authorize_account_change(ADMIN,ADMIN,{"is_active":False})
        self.assertEqual(authorize_account_change(ADMIN,MEMBER,{"is_deleted":True}),(False,True))
        with self.assertRaises(ValueError): authorize_account_change(ADMIN,MEMBER,{"is_active":"false"})

    def test_password_hashes_are_compatible_and_never_plaintext(self):
        encoded=hash_password("Different8")
        self.assertNotIn("Different8",encoded)
        self.assertTrue(verify_password("Different8",encoded))
        self.assertFalse(verify_password("wrong",encoded))
        self.assertFalse(verify_password("wrong","invalid"))

    def test_all_business_and_file_routes_require_sign_in(self):
        client=TestClient(create_app(Settings()))
        for path in ("/api/vehicles/","/api/vehicles/1/","/api/vehicles/1/cover/",
                     "/api/vehicles/1/attachments/1/preview/","/api/vehicles/1/attachments/1/download/","/api/users/"):
            self.assertEqual(client.get(path).status_code,401)
        self.assertEqual(client.get("/",follow_redirects=False).headers["location"],"/login/")

    def test_signed_csrf_blocks_missing_forged_and_cross_session_tokens(self):
        app=create_app(Settings())
        app.state.accounts=MagicMock()
        app.state.accounts.session_user.return_value=MEMBER
        client=TestClient(app)
        self.assertEqual(client.post("/login/",data={"password":"private"}).status_code,403)
        client.get("/login/")
        token=client.cookies["csrftoken"]
        self.assertEqual(client.post("/logout/",data={"csrfmiddlewaretoken":"forged"}).status_code,403)
        client.cookies.set("hspace_session","another-session")
        self.assertEqual(client.post("/logout/",data={"csrfmiddlewaretoken":token}).status_code,403)

    def test_member_is_forbidden_from_owner_routes(self):
        app=create_app(Settings()); app.state.accounts=MagicMock()
        app.state.accounts.session_user.return_value=MEMBER
        client=TestClient(app,cookies={"hspace_session":"opaque-session"})
        self.assertEqual(client.get("/api/users/").status_code,403)
        self.assertEqual(client.get("/users/").status_code,403)
