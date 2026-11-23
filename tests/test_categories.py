"""Classification rules and HTTP boundaries, without a database fallback."""

from unittest import TestCase
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from limousine.application.categories import CategoryService, record_id
from limousine.config.runtime import Settings
from limousine.domain.accounts import AccessDenied
from limousine.domain.categories import (
    CategoryInUse,
    category_key,
    category_name,
    require_free_category,
    similar_categories,
)
from limousine.domain.vehicles import DomainError
from limousine.presentation.web.app import create_app
from limousine.presentation.web.security import current_user
from tests.test_accounts import OPERATOR


class CategoryTests(TestCase):
    def test_one_named_category_slot_but_other_accepts_many(self):
        require_free_category(False, False)
        require_free_category(True, True)
        with self.assertRaises(CategoryInUse):
            require_free_category(False, True)

    def test_normalized_names_match_arabic_variants_and_english_case(self):
        self.assertEqual(category_key("كرت الإِتـجاه"), category_key("كرت الاتجاه"))
        self.assertEqual(category_key(" Vehicle-LICENSE "), category_key("vehicle license"))
        self.assertEqual(category_name("  رخصة   السيارة  "), "رخصة السيارة")
        for invalid in ("", "!!!", "a" * 101, "\u202ename", None):
            with self.subTest(invalid=invalid), self.assertRaises(DomainError):
                category_key(invalid)

    def test_similar_names_use_aliases_but_other_is_never_a_suggestion(self):
        categories = [
            dict(id=1, name="رخصة السيارة", aliases=["Vehicle license"], is_other=False),
            dict(id=2, name="Other", aliases=[], is_other=True),
        ]
        self.assertEqual(similar_categories(categories, "Vehicle licens")[0]["id"], 1)
        self.assertEqual(similar_categories(categories, "Other"), [])

    def test_signed_in_operator_can_manage_types(self):
        repository = MagicMock()
        service = CategoryService(repository)
        service.create("Insurance", OPERATOR)
        repository.create.assert_called_once_with("Insurance", "insurance", OPERATOR, False)
        service.merge(1, 2, OPERATOR)
        repository.merge.assert_called_once_with(1, 2, OPERATOR)
        with self.assertRaises(AccessDenied):
            service.create("Insurance", None)
        with self.assertRaises(DomainError):
            service.create("Insurance", OPERATOR, "true")
        for invalid in (True, -1, 0, "1", 2**63):
            with self.assertRaises(DomainError):
                record_id(invalid)

    def test_category_routes_require_authentication_and_mutations_require_csrf(self):
        app = create_app(Settings())
        app.state.categories = MagicMock()
        client = TestClient(app)
        self.assertEqual(client.get("/api/attachment-categories/").status_code, 401)
        self.assertEqual(
            client.get("/attachments/download/", follow_redirects=False).status_code, 303
        )
        app.dependency_overrides[current_user] = lambda: OPERATOR
        self.assertEqual(client.get("/attachment-categories/").status_code, 404)
        self.assertEqual(client.get("/attachments/download/").status_code, 200)
        client.get("/login/")
        headers = {"X-CSRFToken": client.cookies["csrftoken"]}
        result = dict(id=5, name="Insurance", code=None, is_other=False)
        app.state.categories.create.return_value = result
        for url, payload in (
            ("/api/attachment-categories/", {"name": "Insurance"}),
            ("/api/attachment-categories/5/aliases/", {"name": "Policy"}),
            ("/api/attachment-categories/5/merge/", {"target_id": 6}),
        ):
            self.assertEqual(client.post(url, json=payload).status_code, 403)
        response = client.post(
            "/api/attachment-categories/", json={"name": "Insurance"}, headers=headers
        )
        self.assertEqual(response.status_code, 200)
        app.state.categories.create.assert_called_once_with("Insurance", OPERATOR, False)
        self.assertEqual(
            client.post(
                "/api/attachment-categories/",
                json={"name": "Insurance", "admin": True},
                headers=headers,
            ).status_code,
            400,
        )
        self.assertEqual(
            client.patch(
                "/api/vehicles/1/attachments/1/category/", json={"category_id": 5}
            ).status_code,
            403,
        )
        self.assertEqual(
            client.post(
                "/api/attachment-download/", json={"vehicle_ids": [1], "category_ids": [5]}
            ).status_code,
            403,
        )
