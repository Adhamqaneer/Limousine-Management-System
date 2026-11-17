from datetime import date
from unittest import TestCase
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from limousine.config.runtime import Settings
from limousine.application.drivers import DriverService
from limousine.domain.drivers import DriverValidationError,driver_date,validate_boundary
from limousine.domain.vehicles import DomainError
from limousine.presentation.web.app import create_app
from limousine.presentation.web.security import current_user
from tests.test_accounts import MEMBER

class DriverRuleTests(TestCase):
    def test_invalid_input_has_stable_field_and_reason(self):
        service=DriverService(MagicMock(),today=lambda:date(2022,1,1))
        cases=[
            ('Driver1','123','2021-01-01','driver_name','nameRule'),
            ('Driver','+123','2021-01-01','driver_phone','phoneRule'),
            ('Driver','123',None,'started_on','startRequired'),
            ('Driver','123','2021-02-30','started_on','dateInvalid'),
            ('Driver','123','2022-01-02','started_on','futureStart'),
        ]
        for name,phone,start,field,reason in cases:
            with self.subTest(reason=reason),self.assertRaises(DriverValidationError) as result:
                service.assign(1,name,phone,start,MEMBER)
            self.assertEqual((result.exception.field,result.exception.reason),(field,reason))
        with self.assertRaises(DriverValidationError) as result:
            validate_boundary(date(2021,1,1),date(2022,1,1))
        self.assertEqual((result.exception.field,result.exception.reason),('started_on','overlapStart'))

    def test_dates_and_period_boundaries(self):
        self.assertIsNone(driver_date(None))
        self.assertEqual(driver_date('2022-01-01'),date(2022,1,1))
        for value in ('2022-02-30','20220101',123):
            with self.assertRaises(DomainError):driver_date(value)
        with self.assertRaises(DomainError):driver_date(None,required=True)
        with self.assertRaises(DomainError):validate_boundary(date(2021,1,1),date(2022,1,1))
        with self.assertRaises(DomainError):validate_boundary(date(2021,1,1),previous_end=date(2022,1,1),correcting=True)
        with self.assertRaises(DomainError):validate_boundary(None,date(2022,1,1),correcting=True)
        validate_boundary(date(2022,1,1),date(2022,1,1))

    def test_assignment_and_correction_are_distinct_and_validate_phone(self):
        repo=MagicMock();service=DriverService(repo)
        service.assign(1,' Driver ','00123','2022-01-01',MEMBER)
        repo.change_driver.assert_called_with(1,{'driver_name':'Driver','driver_phone':'00123'},date(2022,1,1),MEMBER)
        service.correct(1,'Driver','00124',None,MEMBER)
        repo.change_driver.assert_called_with(1,{'driver_name':'Driver','driver_phone':'00124'},None,MEMBER,correcting=True)
        for name,phone in (('', '123'),('Driver1','123'),('Driver','+123')):
            with self.assertRaises(DomainError):service.assign(1,name,phone,'2022-01-01',MEMBER)
        with self.assertRaises(DomainError):DriverService(repo,today=lambda:date(2022,1,1)).assign(1,'Driver','123','2022-01-02',MEMBER)

class DriverHttpTests(TestCase):
    def setUp(self):
        self.app=create_app(Settings());self.client=TestClient(self.app);self.service=MagicMock();self.app.state.drivers=self.service
        self.service.history.return_value=[];self.service.corrections.return_value=[]
        self.client.get('/login/');self.headers={'X-CSRFToken':self.client.cookies['csrftoken']}

    def test_all_driver_routes_require_authentication(self):
        for path in ('/api/drivers/','/api/vehicles/1/drivers/'):
            self.assertEqual(self.client.get(path).status_code,401)
        self.assertEqual(self.client.get('/drivers/',follow_redirects=False).status_code,303)
        self.assertEqual(self.client.post('/api/vehicles/1/drivers/',json={},headers=self.headers).status_code,401)

    def test_members_can_read_search_and_write_with_csrf(self):
        from tests.test_vehicle_http import STAMP
        from limousine.domain.vehicles import Vehicle
        self.app.dependency_overrides[current_user]=lambda:MEMBER
        self.app.state.vehicles=MagicMock();self.app.state.vehicles.get_vehicle.return_value=Vehicle(1,'001',STAMP,vehicle_type='Camry')
        self.assertEqual(self.client.get('/drivers/').status_code,200)
        response=self.client.get('/api/drivers/?q=Driver&on_date=2022-01-01')
        self.assertEqual(response.status_code,200);self.assertIn('no-store',response.headers['cache-control'])
        self.service.history.assert_called_with(None,'Driver','2022-01-01')
        body={'driver_name':'Driver','driver_phone':'00123','started_on':'2022-01-01'}
        self.assertEqual(self.client.post('/api/vehicles/1/drivers/',json=body).status_code,403)
        self.assertEqual(self.client.post('/api/vehicles/1/drivers/',json=body,headers=self.headers).status_code,200)
        self.service.assign.assert_called_once_with(1,'Driver','00123','2022-01-01',MEMBER)
        self.assertEqual(self.client.patch('/api/vehicles/1/drivers/current/',json=body,headers=self.headers).status_code,200)
        self.service.correct.assert_called_once_with(1,'Driver','00123','2022-01-01',MEMBER)
        self.assertEqual(self.client.post('/api/vehicles/1/drivers/',json={**body,'actor':'fake'},headers=self.headers).status_code,400)

    def test_direct_driver_edit_is_blocked_by_application(self):
        from limousine.application.vehicles import VehicleService
        repo=MagicMock()
        with self.assertRaises(DomainError):VehicleService(repo).update_vehicle(1,driver_phone='0079')
        repo.update_vehicle.assert_not_called()

    def test_validation_error_identifies_the_driver_field(self):
        from limousine.domain.drivers import DriverValidationError
        self.app.dependency_overrides[current_user]=lambda:MEMBER
        self.service.assign.side_effect=DriverValidationError('driver_phone','phoneRule','Use English digits.')
        response=self.client.post('/api/vehicles/1/drivers/',json={'driver_name':'Driver','driver_phone':'+123','started_on':'2022-01-01'},headers=self.headers)
        self.assertEqual(response.status_code,400)
        self.assertEqual(response.json()['error']['field'],'driver_phone')
        self.assertEqual(response.json()['error']['reason'],'phoneRule')
