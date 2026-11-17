"""Upgrade the intended local schema with backup, then verify recovery in a rolled-back transaction."""
import io
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))

def main():
    from fastapi.testclient import TestClient
    from PIL import Image
    import psycopg
    from limousine.config.runtime import load_settings
    from limousine.infrastructure.database import Database
    from limousine.infrastructure.migrations import migrate, media_manifest
    from limousine.infrastructure.accounts import PostgresAccountRepository
    from limousine.infrastructure.vehicle_repository import PostgresVehicleRepository
    from limousine.infrastructure.attachments import LocalAttachmentStore
    from limousine.infrastructure.file_cleanup import FileCleanup
    from limousine.application.vehicles import VehicleService
    from limousine.application.recycling import RecyclingService
    from limousine.domain.accounts import AccessDenied
    from limousine.domain.vehicles import NotFound
    from limousine.presentation.web.app import create_app
    from limousine.presentation.web.security import current_user, administrator
    from tests.uploads import SimpleUploadedFile

    settings = load_settings()
    assert settings.db_name == 'limousine_local' and settings.db_host in ('127.0.0.1','localhost','::1')
    db = Database(settings)
    tables = ('limo_vehicle','limo_attachment','limo_vehicle_cover','hspace_user','hspace_session','hspace_file_cleanup')
    def snapshot():
        with db.connect() as conn:
            result = {}
            for table in tables:
                rows = conn.execute('SELECT * FROM '+table+' ORDER BY 1').fetchall()
                result[table] = [{key:value for key,value in row.items() if key not in ('created_by','is_deleted','deleted_by','deleted_at') or table=='hspace_user'} for row in rows]
                if table=='limo_vehicle_cover':
                    result[table] = [{key:value for key,value in row.items() if key!='created_at'} for row in result[table]]
            return result
    before, files = snapshot(), media_manifest(settings.media_root)
    backup = migrate(db)
    assert snapshot()==before and media_manifest(settings.media_root)==files
    assert migrate(db) is None
    users = PostgresAccountRepository(db).list_users()
    admin = next(user for user in users if user.role=='ADMIN')
    member = next(user for user in users if user.role=='MEMBER' and user.can_login)
    with TemporaryDirectory() as directory, db.connect() as conn:
        class TransactionDatabase:
            @contextmanager
            def connect(self):
                yield conn
        transactional = TransactionDatabase()
        repo = PostgresVehicleRepository(transactional)
        vehicles, recycling = VehicleService(repo), RecyclingService(repo)
        store = LocalAttachmentStore(Path(directory))
        cleanup = FileCleanup(transactional,store)
        car = vehicles.create_vehicle('00999-001','Camry',actor=member,owner_name='Test owner',manufacture_year='2022')
        sibling = vehicles.create_vehicle('00999-002','Accord',actor=admin)
        stored = store.save(SimpleUploadedFile('note.txt',b'retained content'))
        attachment = vehicles.add_attachment(car.id,storage_key=stored.storage_key,original_name=stored.original_name,kind=stored.kind,size=stored.size,actor=member)
        stored_two = store.save(SimpleUploadedFile('other.txt',b'separate file'))
        second = vehicles.add_attachment(car.id,storage_key=stored_two.storage_key,original_name=stored_two.original_name,kind=stored_two.kind,size=stored_two.size,actor=admin)
        image=io.BytesIO();Image.new('RGB',(2,2),'white').save(image,'PNG')
        photo=store.save_card_photo(SimpleUploadedFile('cover.png',image.getvalue()))
        vehicles.replace_cover(car.id,storage_key=photo.storage_key,original_name=photo.original_name,size=photo.size,actor=member)
        app=create_app(settings);app.state.vehicles=vehicles;app.state.recycling=recycling;app.state.store=store;app.state.cleanup=cleanup
        app.dependency_overrides[current_user]=lambda:member
        app.dependency_overrides[administrator]=lambda:admin
        client=TestClient(app);client.get('/login/');headers={'X-CSRFToken':client.cookies['csrftoken']}
        url=f'/api/vehicles/{car.id}/attachments/{attachment.id}'
        assert client.get(url+'/preview/').content==b'retained content'
        assert client.delete(url+'/',headers=headers).status_code==204
        assert client.get(url+'/preview/').status_code==404
        assert client.get(url+'/download/').status_code==404
        assert client.get('/api/vehicles/').json()['vehicles'][-2]['attachment_count']==1
        cleanup.discard(stored.storage_key)
        assert store.path(stored.storage_key).read_bytes()==b'retained content'
        try: recycling.restore_item('attachment',attachment.id,member)
        except AccessDenied: pass
        else: raise AssertionError('Member restored an item')
        assert client.delete(f'/api/vehicles/{car.id}/',headers=headers).status_code==204
        assert car.id not in [item['id'] for item in client.get('/api/vehicles/').json()['vehicles']]
        assert client.get(f'/api/vehicles/{car.id}/').status_code==404
        assert client.get(f'/api/vehicles/{car.id}/cover/').status_code==404
        assert client.get(f'/api/vehicles/{car.id}/attachments/{second.id}/preview/').status_code==404
        assert client.patch(f'/api/vehicles/{car.id}/',json={'owner_name':'Changed'},headers=headers).status_code==404
        assert client.post(f'/api/recycle-bin/attachment/{attachment.id}/restore/',headers=headers).status_code==404
        assert client.post(f'/api/recycle-bin/vehicle/{car.id}/restore/',headers=headers).status_code==204
        assert vehicles.get_vehicle(car.id).cover.storage_key==photo.storage_key
        assert [item.id for item in vehicles.get_vehicle(car.id).attachments]==[second.id]
        assert client.post(f'/api/recycle-bin/attachment/{attachment.id}/restore/',headers=headers).status_code==204
        assert client.get(url+'/preview/').content==b'retained content'
        replacement=store.save_card_photo(SimpleUploadedFile('new.png',image.getvalue()))
        vehicles.replace_cover(car.id,storage_key=replacement.storage_key,original_name=replacement.original_name,size=replacement.size,actor=admin)
        deleted_cover=next(item for item in recycling.list_deleted(admin) if item['kind']=='cover' and item['vehicle_id']==car.id)
        restore_cover=f"/api/recycle-bin/cover/{deleted_cover['id']}/restore/"
        assert client.post(restore_cover,headers=headers).status_code==400
        assert vehicles.get_cover(car.id).storage_key==replacement.storage_key
        vehicles.delete_cover(car.id,actor=member)
        assert client.post(restore_cover,headers=headers).status_code==204
        assert vehicles.get_cover(car.id).storage_key==photo.storage_key
        history=recycling.list_activity(admin)
        assert {'CREATE','DELETE','RESTORE'} <= {item['action'] for item in history}
        assert {member.username,admin.username} <= {item['actor_name'] for item in history}
        assert any(item['reason']=='replaced' for item in history)
        assert vehicles.get_vehicle(sibling.id).plate_number=='00999-002'
        assert store.path(photo.storage_key).is_file() and store.path(replacement.storage_key).is_file()
        for query,params in [('DELETE FROM limo_vehicle WHERE id=%s',(car.id,)),('DELETE FROM limo_attachment WHERE id=%s',(attachment.id,)),('UPDATE hspace_activity SET label=label WHERE vehicle_id=%s',(car.id,))]:
            try:
                with conn.transaction():conn.execute(query,params)
            except psycopg.errors.CheckViolation:pass
            else:raise AssertionError('Retained data could be physically changed')
        conn.rollback()
    assert snapshot()==before and media_manifest(settings.media_root)==files
    print('PASS: schema 4/idempotency, actor audit, soft deletion, hidden downloads/list/edits, parent/child recovery, member denial, cover conflict, retained bytes and rollback.')
    print('Existing rows, account data and original file hashes preserved. Private upgrade backup created.' if backup else 'Existing rows/files preserved; schema was already current.')

if __name__=='__main__':
    try:main()
    except Exception as error:
        print(f'Recovery verification failed ({type(error).__name__}); private details suppressed.')
        raise SystemExit(1)
