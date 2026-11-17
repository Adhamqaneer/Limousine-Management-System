from unittest import TestCase
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from limousine.config.runtime import Settings
from limousine.presentation.web.app import create_app
from limousine.presentation.web.security import current_user
from tests.test_accounts import ADMIN, MEMBER


class VehicleReportTests(TestCase):
    def setUp(self):
        self.app = create_app(Settings())
        self.client = TestClient(self.app)

    def test_report_requires_authentication_and_is_not_cacheable(self):
        response = self.client.get('/reports/vehicles/', follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers['location'], '/login/')
        self.assertIn('no-store', response.headers['cache-control'])

    def test_both_roles_can_open_report_without_mutating_or_loading_records(self):
        service = MagicMock()
        self.app.state.vehicles = service
        for user in (ADMIN, MEMBER):
            self.app.dependency_overrides[current_user] = lambda: user
            response = self.client.get('/reports/vehicles/')
            self.assertEqual(response.status_code, 200)
            self.assertIn('id="report-choices"', response.text)
            self.assertIn('id="print-report" disabled', response.text)
            self.assertIn('lang="en" dir="ltr"', response.text)
            self.assertIn('aria-current="page"', response.text)
            self.assertIn('no-store', response.headers['cache-control'])
        self.assertEqual(service.mock_calls, [])

    def test_report_assets_are_available_and_native_print_stays_read_only(self):
        self.app.dependency_overrides[current_user] = lambda: MEMBER
        for asset in ('vehicle-report.css', 'vehicle-report.js', 'report-data.js'):
            self.assertEqual(self.client.get('/static/web/' + asset).status_code, 200)
        self.assertEqual(self.client.post('/reports/vehicles/').status_code, 405)

    def test_letterhead_is_in_repeating_table_head_and_watermark_is_decorative(self):
        self.app.dependency_overrides[current_user] = lambda: MEMBER
        html = self.client.get('/reports/vehicles/').text
        heading = html.split('<thead>', 1)[1].split('</thead>', 1)[0]
        self.assertIn('class="office-letterhead"', heading)
        self.assertIn('HORIZONTAL SPACE', heading)
        self.assertIn('lang="ar" dir="rtl"', heading)
        self.assertIn('class="letterhead-ribbon"', heading)
        self.assertIn('class="report-watermark" aria-hidden="true"', html)
