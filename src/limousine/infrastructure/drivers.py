"""Transactional driver periods; flat current fields remain synchronized for reports."""
from psycopg.types.json import Jsonb
from limousine.domain.drivers import validate_boundary
from limousine.domain.vehicles import NotFound, DomainError

def snapshot(row):
    if not row:return None
    return {'driver_name':row['driver_name'],'driver_phone':row['driver_phone'],
            'started_on':row['started_on'].isoformat() if row['started_on'] else None}

def seed_driver(connection, vehicle, actor=None):
    if vehicle['driver_name'] or vehicle['driver_phone']:
        row=connection.execute('INSERT INTO hspace_driver_assignment(vehicle_id,driver_name,driver_phone,created_by,created_by_name) VALUES (%s,%s,%s,%s,%s) RETURNING *',
            (vehicle['id'],vehicle['driver_name'],vehicle['driver_phone'],actor.id if actor else None,actor.username if actor else None)).fetchone()
        if actor:record(connection,vehicle['id'],row['id'],'ASSIGN',actor,None,row)

def record(connection, vehicle_id, assignment_id, action, actor, before, after):
    connection.execute('INSERT INTO hspace_driver_change(vehicle_id,assignment_id,action,actor_id,actor_name,before_data,after_data) VALUES (%s,%s,%s,%s,%s,%s,%s)',
        (vehicle_id,assignment_id,action,actor.id,actor.username,Jsonb(snapshot(before)),Jsonb(snapshot(after))))

class PostgresDriverRepository:
    def __init__(self,database): self.database=database

    def change_driver(self,vehicle_id,details,started_on,actor,*,correcting=False):
        with self.database.connect() as conn:
            if not conn.execute('SELECT id FROM limo_vehicle WHERE id=%s AND NOT is_deleted FOR UPDATE',(vehicle_id,)).fetchone():raise NotFound('Vehicle not found.')
            current=conn.execute('SELECT * FROM hspace_driver_assignment WHERE vehicle_id=%s AND is_current FOR UPDATE',(vehicle_id,)).fetchone()
            previous=conn.execute('SELECT max(ended_on) AS ended_on FROM hspace_driver_assignment WHERE vehicle_id=%s AND NOT is_current',(vehicle_id,)).fetchone()['ended_on']
            validate_boundary(started_on,current['started_on'] if current else None,previous,correcting=correcting)
            if correcting:
                if not current:raise DomainError('There is no current driver to correct. Use Change driver.')
                row=conn.execute('UPDATE hspace_driver_assignment SET driver_name=%s,driver_phone=%s,started_on=%s,updated_by=%s,updated_by_name=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s RETURNING *',
                    (details['driver_name'],details['driver_phone'],started_on,actor.id,actor.username,current['id'])).fetchone()
            else:
                if current:conn.execute('UPDATE hspace_driver_assignment SET is_current=FALSE,ended_on=%s WHERE id=%s',(started_on,current['id']))
                row=conn.execute('INSERT INTO hspace_driver_assignment(vehicle_id,driver_name,driver_phone,started_on,created_by,created_by_name) VALUES (%s,%s,%s,%s,%s,%s) RETURNING *',
                    (vehicle_id,details['driver_name'],details['driver_phone'],started_on,actor.id,actor.username)).fetchone()
            conn.execute('UPDATE limo_vehicle SET driver_name=%s,driver_phone=%s WHERE id=%s',(details['driver_name'],details['driver_phone'],vehicle_id))
            record(conn,vehicle_id,row['id'],'CORRECT' if correcting else 'ASSIGN',actor,current,row)
            return row

    def history(self,vehicle_id=None,query='',on_date=None):
        with self.database.connect() as conn:
            if vehicle_id is not None and not conn.execute('SELECT 1 FROM limo_vehicle WHERE id=%s AND NOT is_deleted',(vehicle_id,)).fetchone():raise NotFound('Vehicle not found.')
            literal=query.replace('!','!!').replace('%','!%').replace('_','!_')
            return conn.execute("""SELECT a.*,v.plate_number,v.vehicle_type FROM hspace_driver_assignment a JOIN limo_vehicle v ON v.id=a.vehicle_id
                WHERE NOT v.is_deleted AND (%s::bigint IS NULL OR a.vehicle_id=%s)
                AND a.driver_name ILIKE %s ESCAPE '!'
                AND (%s::date IS NULL OR (a.started_on IS NOT NULL AND a.started_on<=%s AND (a.ended_on IS NULL OR %s<a.ended_on)))
                ORDER BY a.vehicle_id,a.id DESC""",(vehicle_id,vehicle_id,'%'+literal+'%',on_date,on_date,on_date)).fetchall()

    def corrections(self,vehicle_id):
        with self.database.connect() as conn:
            return conn.execute("""SELECT c.actor_name,c.before_data,c.after_data,c.created_at FROM hspace_driver_change c JOIN limo_vehicle v ON v.id=c.vehicle_id
                WHERE c.vehicle_id=%s AND NOT v.is_deleted AND c.action='CORRECT' ORDER BY c.id DESC""",(vehicle_id,)).fetchall()
