"""Real PostgreSQL/FastAPI workflow verification; clean only own fixtures."""
import io
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import replace
from uuid import uuid4
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT))

def main():
    import psycopg
    from fastapi.testclient import TestClient
    from PIL import Image
    from limousine.config.runtime import load_settings
    from limousine.infrastructure.accounts import token_hash
    from limousine.infrastructure.database import Database
    from limousine.infrastructure.migrations import media_manifest
    from limousine.presentation.web.app import create_app
    settings=load_settings()
    assert settings.db_host in ("127.0.0.1","localhost","::1") and settings.db_name=="limousine_local"
    database=Database(settings)
    tables=("limo_vehicle","limo_attachment","limo_vehicle_cover")
    with database.connect() as connection:
        baseline={name:connection.execute("SELECT * FROM "+name+" ORDER BY id").fetchall() for name in tables}
        accounts=connection.execute("SELECT * FROM hspace_user ORDER BY slot").fetchall()
        columns={row["column_name"] for row in connection.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='hspace_user'")}
    assert len(accounts)==4 and sum(row["role"]=="ADMIN" for row in accounts)==1
    assert next(row for row in accounts if row["role"]=="ADMIN")["username"]=="Adham qaneer"
    assert not columns & {"first_name","last_name","email","is_staff","is_superuser"}
    existing_files=media_manifest(settings.media_root)
    credentials=[line.split(": ",1) for line in (ROOT/".local/accounts.txt").read_text(encoding="utf-8").splitlines()[1:] if ": " in line]
    assert len(credentials)==4
    session_hashes=[]; vehicle_ids=[]
    with TemporaryDirectory(prefix="hspace-fastapi-check-") as media:
        app=create_app(replace(settings,media_root=Path(media),allowed_hosts=("testserver",)))
        anonymous=TestClient(app)
        assert anonymous.get("/api/vehicles/").status_code==401
        assert anonymous.post("/login/",data={"username":"x","password":"x"}).status_code==403
        clients={}
        try:
            for username,password in credentials:
                client=TestClient(app)
                assert client.get("/login/").status_code==200
                response=client.post("/login/",data={"username":username,"password":password,
                    "csrfmiddlewaretoken":client.cookies["csrftoken"]},follow_redirects=False)
                assert response.status_code==303, "An existing account could not sign in."
                clients[username]=client
                session_hashes.append(token_hash(client.cookies["hspace_session"]))
                assert client.get("/api/vehicles/").status_code==200
            admin=clients["Adham qaneer"]
            members=[client for name,client in clients.items() if name!="Adham qaneer"]
            def headers(client=admin): return {"X-CSRFToken":client.cookies["csrftoken"]}
            assert admin.get("/users/").status_code==200
            rows=admin.get("/api/users/").json()["users"]
            assert all("password" not in key for row in rows for key in row)
            assert members[0].get("/api/users/").status_code==403
            admin_id=next(row["id"] for row in rows if row["role"]=="ADMIN")
            assert admin.patch("/api/users/"+admin_id+"/",json={"is_active":False},headers=headers()).status_code==403
            member=next(row for row in rows if row["role"]=="MEMBER")
            victim=clients[member["username"]]
            endpoint="/api/users/"+member["id"]+"/"
            assert admin.patch(endpoint,json={"is_active":False},headers=headers()).status_code==200
            assert victim.get("/api/vehicles/").status_code==401
            assert admin.patch(endpoint,json={"is_active":True},headers=headers()).status_code==200
            deleted=admin.patch(endpoint,json={"is_deleted":True},headers=headers()).json()["user"]
            assert deleted["is_deleted"] and not deleted["is_active"] and deleted["deleted_at"]
            restored=admin.patch(endpoint,json={"is_deleted":False,"is_active":True},headers=headers()).json()["user"]
            assert restored["deleted_at"] is None and restored["is_active"]
            response=admin.post("/api/vehicles/",json={"plate_number":"000-FASTAPI-TEST","vehicle_type":"Test sedan"},headers=headers())
            assert response.status_code==201
            item=response.json()["vehicle"]; vehicle_ids.append(item["id"]); url="/api/vehicles/"+str(item["id"])+"/"
            assert admin.patch(url,json={"driver_name":"Test driver","chassis_number":"0000123","manufacture_year":"2020"},headers=headers()).status_code==200
            assert members[-1].get(url).json()["vehicle"]["chassis_number"]=="0000123"
            buffer=io.BytesIO(); Image.new("RGB",(2,2),"white").save(buffer,"PNG"); image=buffer.getvalue()
            documents=[("image.png",image),("text.txt",b"local preview"),("test.pdf",b"%PDF-1.7\n%%EOF")]
            office=[
                ("test.docx",{"word/document.xml":'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Local preview</w:t></w:r></w:p></w:body></w:document>'}),
                ("test.xlsx",{"xl/workbook.xml":'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Test" r:id="r1"/></sheets></workbook>',
                              "xl/_rels/workbook.xml.rels":'<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/></Relationships>',
                              "xl/worksheets/sheet1.xml":'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c r="A1" t="inlineStr"><is><t>Local preview</t></is></c></row></sheetData></worksheet>'})]
            for filename,parts in office:
                stream=io.BytesIO()
                with zipfile.ZipFile(stream,"w") as archive:
                    for name,content in {"[Content_Types].xml":"<Types/>","_rels/.rels":"<Relationships/>",**parts}.items():
                        archive.writestr(name,content)
                documents.append((filename,stream.getvalue()))
            for filename,data in documents:
                upload=admin.post(url+"attachments/",files={"file":(filename,data)},headers=headers())
                assert upload.status_code==201
                file=upload.json()["attachment"]
                assert admin.get(file["download_url"]).content==data
                view=admin.get(file["preview_url"])
                assert view.status_code==200
                if filename.endswith((".docx",".xlsx")): assert b"Local preview" in view.content
                else: assert view.content==data and "inline" in view.headers["content-disposition"]
                assert anonymous.get(file["preview_url"]).status_code==401
            assert admin.get(url).json()["vehicle"]["cover_url"] is None
            for color in ("blue","red"):
                stream=io.BytesIO(); Image.new("RGB",(2,2),color).save(stream,"PNG"); cover=stream.getvalue()
                response=admin.post(url+"cover/",files={"file":("cover.png",cover)},headers=headers())
                assert response.status_code==201 and response.json()["vehicle"]["attachment_count"]==5
                assert admin.get(url+"cover/").content==cover
                assert anonymous.get(url+"cover/").status_code==401
            # Database constraint enforces the four-account cap, even outside the API.
            try:
                with database.connect() as connection:
                    connection.execute("INSERT INTO hspace_user(id,slot,username,password_hash,role) VALUES(%s,5,'invalid-fifth','invalid','MEMBER')",(uuid4(),))
            except psycopg.IntegrityError: pass
            else: raise AssertionError("Database accepted a fifth account.")
            with database.connect() as connection:
                connection.execute("UPDATE hspace_session SET expires_at=CURRENT_TIMESTAMP-INTERVAL '1 second' WHERE token_hash=%s",(session_hashes[-1],))
            assert clients[credentials[-1][0]].get("/api/vehicles/").status_code==401
            assert admin.post("/logout/",data={"csrfmiddlewaretoken":admin.cookies["csrftoken"]},follow_redirects=False).status_code==303
            assert admin.get("/api/vehicles/").status_code==401
        finally:
            with database.connect() as connection:
                connection.execute("DELETE FROM limo_vehicle_cover WHERE vehicle_id=ANY(%s)",(vehicle_ids,))
                connection.execute("DELETE FROM limo_attachment WHERE vehicle_id=ANY(%s)",(vehicle_ids,))
                connection.execute("DELETE FROM limo_vehicle WHERE id=ANY(%s)",(vehicle_ids,))
                connection.execute("DELETE FROM hspace_session WHERE token_hash=ANY(%s)",(session_hashes,))
                for account in accounts:
                    connection.execute("UPDATE hspace_user SET is_active=%s,is_deleted=%s,deleted_at=%s WHERE id=%s",
                        (account["is_active"],account["is_deleted"],account["deleted_at"],account["id"]))
        with database.connect() as connection:
            for name in tables: assert connection.execute("SELECT * FROM "+name+" ORDER BY id").fetchall()==baseline[name]
            after=connection.execute("SELECT id,password_hash FROM hspace_user ORDER BY slot").fetchall()
            assert [row["password_hash"] for row in after]==[row["password_hash"] for row in accounts]
        assert media_manifest(settings.media_root)==existing_files
    print("PASS: four existing passwords, UUID/roles, owner-only access, disable/delete/restore and session revocation.")
    print("PASS: expiry, CSRF, vehicle create/edit, independent cover, all file previews and private downloads.")
    print("Existing vehicle rows, attachment metadata, file bytes and passwords were preserved; only test fixtures removed.")

if __name__=="__main__":
    try: main()
    except Exception as error:
        print(f"Local verification failed ({type(error).__name__}); confidential details suppressed.")
        raise SystemExit(1)
