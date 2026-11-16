import io
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from PIL import Image
import psycopg
from limousine.config.runtime import Settings
from limousine.domain.vehicles import Vehicle, VehicleCover, Attachment, NotFound
from limousine.presentation.web.app import create_app
from limousine.presentation.web.security import current_user, administrator
from tests.test_accounts import ADMIN

STAMP=datetime.now(timezone.utc)
def photo():
    stream=io.BytesIO(); Image.new("RGB",(2,2),"white").save(stream,"PNG"); return stream.getvalue()

class VehicleHttpTests(TestCase):
    def setUp(self):
        self.directory=TemporaryDirectory(); self.addCleanup(self.directory.cleanup)
        self.app=create_app(Settings(media_root=Path(self.directory.name)))
        self.app.dependency_overrides[current_user]=lambda:ADMIN
        self.app.dependency_overrides[administrator]=lambda:ADMIN
        self.service=MagicMock(); self.app.state.vehicles=self.service
        self.car=Vehicle(1,"001",STAMP,vehicle_type="Sedan")
        self.service.get_vehicle.return_value=self.car
        self.service.create_vehicle.return_value=self.car
        self.service.update_vehicle.return_value=self.car
        self.client=TestClient(self.app)
        self.client.get("/login/")
        self.headers={"X-CSRFToken":self.client.cookies["csrftoken"]}

    def test_fixed_fields_create_patch_and_private_serialization(self):
        response=self.client.post("/api/vehicles/",json={"plate_number":"001","vehicle_type":"Sedan"},headers=self.headers)
        self.assertEqual(response.status_code,201)
        self.client.patch("/api/vehicles/1/",json={"driver_name":"Driver"},headers=self.headers)
        self.service.create_vehicle.assert_called_once_with(plate_number="001",vehicle_type="Sedan")
        self.service.update_vehicle.assert_called_once_with(1,driver_name="Driver")
        self.assertNotIn("storage_key",response.text)

    def test_invalid_body_csrf_and_database_errors(self):
        self.assertEqual(self.client.post("/api/vehicles/",json={"plate_number":"001"}).status_code,403)
        for body in ("[]","{broken",'{"plate_number":"001","extra":"no"}'):
            self.assertEqual(self.client.post("/api/vehicles/",content=body,headers={**self.headers,"Content-Type":"application/json"}).status_code,400)
        self.service.list_vehicles.side_effect=psycopg.OperationalError("private-secret")
        response=self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code,503); self.assertNotIn("private-secret",response.text)

    def test_gallery_is_independent_of_cover(self):
        item=Attachment(1,1,"private.png","photo.png","image",20,STAMP)
        self.service.list_vehicles.return_value=[Vehicle(1,"001",STAMP,(item,),cover=None)]
        self.assertIsNone(self.client.get("/api/vehicles/").json()["vehicles"][0]["cover_url"])
        self.service.list_vehicles.return_value=[Vehicle(1,"001",STAMP,cover=VehicleCover(1,"key","cover.png",20))]
        self.assertEqual(self.client.get("/api/vehicles/").json()["vehicles"][0]["cover_url"],"/api/vehicles/1/cover/")

    def test_upload_cleanup_on_failed_metadata_and_invalid_files(self):
        self.service.add_attachment.side_effect=psycopg.OperationalError("redacted")
        response=self.client.post("/api/vehicles/1/attachments/",files={"file":("car.png",photo(),"image/png")},headers=self.headers)
        self.assertEqual(response.status_code,503)
        self.assertEqual(list(Path(self.directory.name).rglob("*.png")),[])
        response=self.client.post("/api/vehicles/1/cover/",files={"file":("file.txt",b"hello","text/plain")},headers=self.headers)
        self.assertEqual(response.status_code,400)

    def test_preview_download_and_ownership(self):
        from tests.uploads import SimpleUploadedFile
        for filename,content,mime in (("car.png",photo(),"image/png"),("text.txt",b"<script>hello</script>","text/plain; charset=utf-8"),("test.pdf",b"%PDF-1.7\n%%EOF","application/pdf")):
            stored=self.app.state.store.save(SimpleUploadedFile(filename,content))
            self.service.get_attachment.return_value=Attachment(1,1,stored.storage_key,filename,stored.kind,len(content),STAMP)
            response=self.client.get("/api/vehicles/1/attachments/1/preview/")
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.content,content)
            self.assertEqual(response.headers["content-type"],mime)
            self.assertIn("inline",response.headers["content-disposition"])
            download=self.client.get("/api/vehicles/1/attachments/1/download/")
            self.assertIn("attachment",download.headers["content-disposition"])
        self.service.get_attachment.side_effect=NotFound()
        self.assertEqual(self.client.get("/api/vehicles/2/attachments/1/preview/").status_code,404)

    def test_jinja_pages_and_csrf_cookie_are_stable_between_tabs(self):
        response=self.client.get("/")
        self.assertIn("H SPACE | Vehicles",response.text)
        self.assertIn('href="/users/"',response.text)
        self.assertEqual(self.client.cookies["csrftoken"],self.headers["X-CSRFToken"])
        self.assertEqual(self.client.get("/users/").status_code,200)
