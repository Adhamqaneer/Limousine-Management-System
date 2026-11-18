from dataclasses import replace
from unittest import TestCase
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from limousine.application.recycling import RecyclingService
from limousine.config.runtime import Settings
from limousine.domain.accounts import AccessDenied
from limousine.domain.vehicles import DomainError
from limousine.presentation.web.app import create_app
from limousine.presentation.web.security import administrator, current_user
from tests.test_accounts import ADMIN, MEMBER


class RecyclingRulesTests(TestCase):
    def test_all_members_can_delete_but_only_admin_can_restore_or_read_history(self):
        repo = MagicMock()
        service = RecyclingService(repo)
        for user in (ADMIN, MEMBER):
            service.delete_vehicle(7, user)
        self.assertEqual(repo.delete_vehicle.call_count, 2)
        for action in (
            lambda: service.restore_item("vehicle", 7, MEMBER),
            lambda: service.list_deleted(MEMBER),
            lambda: service.list_activity(MEMBER),
            lambda: service.delete_vehicle(7, replace(MEMBER, is_active=False)),
        ):
            with self.assertRaises(AccessDenied):
                action()
        repo.restore_item.assert_not_called()
        service.restore_item("vehicle", 7, ADMIN)
        repo.restore_item.assert_called_once_with("vehicle", 7, ADMIN)
        with self.assertRaises(DomainError):
            service.restore_item("invalid", 7, ADMIN)


class RecyclingHttpTests(TestCase):
    def setUp(self):
        self.app = create_app(Settings())
        self.client = TestClient(self.app)
        self.service = MagicMock()
        self.app.state.recycling = self.service
        self.service.list_deleted.return_value = []
        self.service.list_activity.return_value = []
        self.client.get("/login/")
        self.headers = {"X-CSRFToken": self.client.cookies["csrftoken"]}

    def test_anonymous_and_member_cannot_access_recovery_or_activity(self):
        self.assertEqual(self.client.get("/recycle-bin/", follow_redirects=False).status_code, 303)
        for path in ("/api/recycle-bin/", "/api/activity/"):
            self.assertEqual(self.client.get(path).status_code, 401)
        self.app.dependency_overrides[current_user] = lambda: MEMBER
        # administrator uses the real account/session lookup, not the overridden dependency.
        self.app.state.accounts.session_user = MagicMock(return_value=MEMBER)
        self.client.cookies.set("hspace_session", "member-session")
        for path in ("/recycle-bin/", "/api/recycle-bin/", "/api/activity/"):
            self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(
            self.client.post(
                "/api/recycle-bin/vehicle/1/restore/", headers=self.headers
            ).status_code,
            403,
        )
        self.service.restore_item.assert_not_called()

    def test_member_delete_requires_csrf_and_carries_actor(self):
        self.app.dependency_overrides[current_user] = lambda: MEMBER
        self.assertEqual(self.client.delete("/api/vehicles/7/").status_code, 403)
        self.assertEqual(
            self.client.delete("/api/vehicles/7/", headers=self.headers).status_code, 204
        )
        self.service.delete_vehicle.assert_called_once_with(7, MEMBER)

    def test_admin_restore_and_page_are_private_and_readable(self):
        self.app.dependency_overrides[administrator] = lambda: ADMIN
        response = self.client.get("/recycle-bin/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response.headers["cache-control"])
        self.assertIn('id="deleted-list"', response.text)
        self.assertEqual(self.client.post("/api/recycle-bin/vehicle/7/restore/").status_code, 403)
        self.assertEqual(
            self.client.post(
                "/api/recycle-bin/vehicle/7/restore/", headers=self.headers
            ).status_code,
            204,
        )
        self.service.restore_item.assert_called_once_with("vehicle", 7, ADMIN)
        self.assertEqual(self.client.get("/api/activity/?before=0").status_code, 400)
