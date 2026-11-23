"""Active links must retain their shared icon/text layout classes."""

from html.parser import HTMLParser
from unittest import TestCase

from fastapi.testclient import TestClient

from limousine.config.runtime import Settings
from limousine.presentation.web.app import create_app
from limousine.presentation.web.security import current_user
from tests.test_accounts import OPERATOR


class NavigationParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if tag == "a" and attributes.get("href") in {
            "/",
            "/reports/vehicles/",
            "/drivers/",
            "/office/",
            "/recycle-bin/",
            "/users/",
        }:
            if "aria-label" not in attributes:
                self.links.append(attributes)


class NavigationTests(TestCase):
    def test_each_current_page_preserves_link_layout_and_active_state(self):
        app = create_app(Settings())
        app.dependency_overrides[current_user] = lambda: OPERATOR
        client = TestClient(app)
        pages = ("/", "/reports/vehicles/", "/drivers/", "/office/", "/recycle-bin/")
        for page in pages:
            with self.subTest(page=page):
                response = client.get(page)
                self.assertEqual(response.status_code, 200)
                parser = NavigationParser()
                parser.feed(response.text)
                # Ignore other in-page links to these URLs.
                links = [link for link in parser.links if "nav-link" in link.get("class", "")]
                self.assertEqual({link["href"] for link in links}, set(pages))
                for link in links:
                    classes = link["class"].split()
                    self.assertIn("nav-link", classes)
                    self.assertEqual("active" in classes, link["href"] == page)
                    self.assertEqual(link.get("aria-current") == "page", link["href"] == page)
