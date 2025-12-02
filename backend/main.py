'''
@author Will Eaton, Nice Hirwa

builds entrypoint for graphql using FastAPI
'''
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
import pymysql
import redis
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
# from strawberry.fastapi import GraphQLRouter
from app_graphql.schema import schema

app = FastAPI()
load_dotenv()

def get_mysql_conn():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        port=3307,
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
        cursorclass=pymysql.cursors.DictCursor
    )

def get_redis_conn():
    return redis.Redis(
        host= os.getenv('REDIS_ENDPOINT'),
        port=11044,
        decode_responses=True,
        username= os.getenv('REDIS_USERNAME'),
        password= os.getenv('REDIS_PASSWORD')
    )

def get_mongo_conn():
    client = MongoClient(
        f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@cs-125.3xkvzsq.mongodb.net/?appName=CS-125",
        server_api=ServerApi('1')
    )
    return client

# We'll figure out how to plug in Graphql later :)
# graphql_app = GraphQLRouter(schema)
# app.include_router(graphql_app, prefix="/graphql")

@app.get('/')
async def root():
    return {'message': 'Service is running'}

@app.get('/student')
async def get_all_students():
    try:
        conn = get_mysql_conn()

        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(

'''
    SELECT 
        CONCAT(p.first_name, ' ', p.last_name) AS parent_name,
        CONCAT(s.first_name, ' ', s.last_name) AS student_name,
        sg.name AS small_group_name,
        CONCAT(l.first_name, ' ', l.last_name) AS small_group_leader_name,
        s.email AS email,
        s.phone_number AS phone_number,
        s.note AS note
    FROM Student s
    JOIN Parent p ON s.parent_id = p.id
    JOIN SmallGroup sg ON sg.id = s.small_group_id
    JOIN Leader l ON sg.leader_id = l.id;
''')
            results = cursor.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No students found"
        )

    return results

# We use payload because when the fast api sends in a request, it sends it in as a whole dictionary
@app.put('/student')
async def update_student(student_id: int, payload: dict):
    email = payload.get('email')
    phone_number = payload.get('phone_number')
    note = payload.get('note')
    student_name = payload.get('student_name')
    parent_name = payload.get('parent_name')
    small_group_name = payload.get('small_group_name')
    small_group_leader_name = payload.get('small_group_leader_name')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(''' UPDATE Student
                SET email = %s, phone_number = %s, note = %s, student_name = %s, parent_name = %s, small_group_name = %s, small_group_leader_name = %s
                WHERE id = %s;''', (email, phone_number, note, student_id, student_name, parent_name, small_group_name, small_group_leader_name))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, 'Student not found')
    except Exception as e:
        raise HTTPException(500, f'Database query failed: {str(e)}')
    finally:
        conn.close()
    return {'message': 'Student updated successfully'}

@app.delete('/student/{student_id}')
async def delete_student(student_id: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('DELETE FROM Student WHERE id = %s;', (student_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, "Student not found")
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")
    finally:
        conn.close()

    return {"message": "Student deleted successfully"}


@app.get('/parent')
async def get_all_parents():
    try:
        conn = get_mysql_conn()

        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                SELECT 
                    p.id AS parent_id,
                    CONCAT(p.first_name, ' ', p.last_name) AS parent_name,
                    p.email AS email,
                    p.phone_number AS phone_number,
                    p.note AS note,
                    CONCAT(s.first_name, ' ', s.last_name) AS student_name
                FROM Parent p
                JOIN Student s ON s.parent_id = p.id
                ORDER BY p.id;
                '''
            )
            rows = cursor.fetchall()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No parents found")

    # ---- Grouping logic ----
    parents = {}

    for row in rows:
        pid = row["parent_id"]

        if pid not in parents:
            parents[pid] = {
                "parent_id": pid,
                "parent_name": row["parent_name"],
                "email": row["email"],
                "phone_number": row["phone_number"],
                "note": row["note"],
                "students": []
            }

        parents[pid]["students"].append(row["student_name"])

    return list(parents.values())

@app.put('/parent/{parent_id}')
async def update_parent(parent_id: int, payload: dict):
    email = payload.get('email')
    phone_number = payload.get('phone_number')
    note = payload.get('note')
    student_name = payload.get('student_name')
    parent_name = payload.get('parent_name')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(''' UPDATE Parent
                SET email = %s, phone_number = %s, note = %s, student_name = %s, parent_name = %s
                WHERE id = %s;''', (email, phone_number, note, parent_id,student_name, parent_name))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, 'parent not found')
    except Exception as e:
        raise HTTPException(500, f'Database query failed: {str(e)}')
    finally:
        conn.close()
    return {'message': 'parent updated successfully'}

@app.delete('/parent/{parent_id}')
async def delete_parent(parent_id: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('DELETE FROM Parent WHERE id = %s;', (parent_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, "Parent not found")
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")
    finally:
        conn.close()

    return {"message": "Parent deleted successfully"}


import pymysql.cursors

@app.get('/leader')
async def get_all_leaders():
    try:
        conn = get_mysql_conn()

        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('''
                SELECT 
                    l.id AS leader_id,
                    CONCAT(l.first_name, ' ', l.last_name) AS leader_name,
                    sg.name AS small_group_name,
                    l.date_joined AS datejoined,
                    l.email AS email,
                    l.phone_number AS phone_number,
                    l.salary AS salary,
                    l.note AS note,
                    s.start_time AS shift_start,
                    s.end_time AS shift_end
                FROM Leader l
                LEFT JOIN SmallGroup sg ON sg.leader_id = l.id
                LEFT JOIN LeaderShift ls ON ls.leader_id = l.id
                LEFT JOIN Shift s ON ls.shift_id = s.id;
            ''')
            rows = cursor.fetchall()

    except Exception as e:
        raise HTTPException(500, f"Database query failed: {str(e)}")

    finally:
        conn.close()

    if not rows:
        raise HTTPException(404, "No leaders found")

    leaders = {}

    for row in rows:
        lid = row["leader_id"]

        if lid not in leaders:
            leaders[lid] = {
                "leader_id": lid,
                "leader_name": row["leader_name"],
                "small_group_name": row["small_group_name"],
                "datejoined": row["datejoined"],
                "email": row["email"],
                "phone_number": row["phone_number"],
                "salary": row["salary"],
                "note": row["note"],
                "shifts": []
            }

        if row["shift_start"] and row["shift_end"]:
            leaders[lid]["shifts"].append({
                "start_time": row["shift_start"],
                "end_time": row["shift_end"]
            })

    return list(leaders.values())

@app.put('/leader/{leader_id}')
async def update_leader(leader_id: int, payload: dict):
    email = payload.get('email')
    phone_number = payload.get('phone_number')
    note = payload.get('note')
    small_group_name = payload.get('small_group_name')
    datejoined = payload.get('datejoined')
    salary = payload.get('salary')
    start_time = payload.get('start_time')
    end_time = payload.get('end_time')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(''' UPDATE Leader
                SET email = %s, phone_number = %s, note = %s, small_group_name = %s, date_joined = %s, salary=%s, start_time=%s, end_time=%s
                WHERE id = %s;''', (email, phone_number, note, small_group_name, datejoined, salary, start_time, end_time, leader_id))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, 'Leader not found')
    except Exception as e:
        raise HTTPException(500, f'Database query failed: {str(e)}')
    finally:
        conn.close()
    return {'message': 'Leader updated successfully'}

@app.delete('/Leader/{leader_id}')
async def delete_leader(leader_id: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('DELETE FROM Leader WHERE id = %s;', (leader_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, "Leader not found")
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")
    finally:
        conn.close()

    return {"message": "Leader deleted successfully"}



@app.get('/event/')
async def get_all_events():
    try:
        conn = get_mysql_conn()

        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
'''
   -- Adding venues 
    SELECT 
        e.start_time AS StartTime,
        e.end_time AS EndTime,
        e.description AS description
    FROM Event e
    JOIN Venue v ON e.venue_id = v.id
    JOIN StudentAttendance sa ON sa.event_id = e.id;
''')
            results = cursor.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No events found"
        )

    return results


@app.put('/event/{event_id}')
async def update_event(event_id: int, payload: dict):
    description = payload.get('description')
    start_time = payload.get('start_time')
    end_time = payload.get('end_time')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(''' UPDATE Leader
                SET description = %s, start_time=%s, end_time=%s
                WHERE id = %s;''', (description, start_time, end_time, event_id))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, 'Event not found')
    except Exception as e:
        raise HTTPException(500, f'Database query failed: {str(e)}')
    finally:
        conn.close()
    return {'message': 'Event updated successfully'}

@app.delete('/Event/{Event_id}')
async def delete_event(event_id: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('DELETE FROM Event WHERE id = %s;', (event_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, "Event not found")
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")
    finally:
        conn.close()

    return {"message": "Event deleted successfully"}

@app.get('/camp/')
async def get_camps():
    conn = get_mysql_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                    SELECT 
                        c.id as CampNumber
                    FROM Camp c
                    JOIN event e ON e.id = c.id;
                ''')
            results = cursor.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No camps found"
        )

    return results

@app.get('/venue/')
async def get_venues():
    conn = get_mysql_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                    SELECT 
                        v.address as VenueAdress,
                        v.description AS description
                    FROM Venue v;
                ''')
            results = cursor.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No venues found"
        )

    return results


@app.get('/student/{student_id}/')
async def get_student(student_id: int):
    conn = get_mysql_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                f"""
            SELECT 
                CONCAT(p.first_name, ' ', p.last_name) AS parent_name,
                CONCAT(s.first_name, ' ', s.last_name) AS student_name,
                sg.name AS small_group_name,
                CONCAT(l.first_name, ' ', l.last_name) AS small_group_leader_name,
                s.email AS email,
                s.phone_number AS phone_number,
                s.note AS note
            FROM Student s
            JOIN Parent p ON s.parent_id = p.id
            JOIN SmallGroup sg ON sg.id = s.small_group_id
            JOIN Leader l ON sg.leader_id = l.id
            WHERE s.id = {student_id}
                """)
            results = cursor.fetchone()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="Student with ID {studentId} not found"
        )

    return results


@app.get('/leader/{leaderId}')
async def get_leader(leaderId: int):
    conn = get_mysql_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                    SELECT 
                        CONCAT(l.first_name, ' ', l.last_name) AS leader_name,
                        sg.name AS small_group_name,
                        l.datejoined AS datejoined,
                        CONCAT(l.first_name, ' ', l.last_name) AS small_group_leader_name,
                        l.email AS email,
                        l.phone_number AS phone_number,
                        l.salary AS salary,
                        r.title AS title,
                        r.desc AS description,
                        s.startTime AS ShiftStartTime,
                        s.endTime AS ShiftEndTime,
                        l.note AS note
                    FROM Leader l
                    JOIN LeaderRole lr ON lr.leader_id = l.id
                    JOIN role l ON lr.roleId = r.id
                    JOIN leaderShift ls ON ls.leader_id = l.id
                    JOIN Shift s ON s.id = ls.shift_id
                    JOIN SmallGroup sg ON sg.leader_id = l.id
                    JOIN LeaderShift ls ON ls.leader_id = l.id;
                ''')
            results = cursor.fetchone()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="Leader with ID {leaderId} not found"
        )

    return results

@app.get('/event/{eventId}')
async def get_events(eventId: int):
    conn = get_mysql_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                    SELECT 
                        e.startTime AS StartTime,
                        e.endTime AS EndTime,
                        sa.studentId AS studentId,
                        v.adress as VenueAdress,
                        e.description AS description
                    FROM Event e
                    JOIN venue v ON e.venue_id = v.id
                    JOIN StudentAttendance sa ON sa.event_id = e.id;
                ''')
            results = cursor.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No events with {eventId} found"
        )

    return results

@app.get('/camp/{campId}')
async def get_events(campId: int):
    conn = get_mysql_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                    SELECT 
                        c.id as CampNumber,
                        e.startTime AS StartTime,
                        e.endTime AS EndTime,
                        e.desc as description
                    FROM Camp c
                    JOIN event e ON e.id = c.id;
                ''')
            results = cursor.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No camps found"
        )

    return results

@app.get('/venue/{venueId}')
async def get_events(venueId: int):
    conn = get_mysql_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                    SELECT 
                        v.adress as VenueAdress,
                        v.description AS description,
                        e.desc AS description
                    FROM Venue v
                    JOIN event e ON e.venue_id = v.id;
                ''')
            results = cursor.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No venues found"
        )

    return results


@app.get('/camp/registration/{campId}')
async def student_camp_registration(campId: int):
    conn = get_mysql_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                    SELECT 
                        c.id AS campId,
                        i.amount AS AmountPaid,
                        e.description AS description,
                        v.adress AS VenueAdress,
                        v.desc AS description
                    FROM CampRegistration cp
                    JOIN camp c ON cp.camp_id = c.id 
                    JOIN event e ON c.id = e.id
                    JOIN venue v ON e.venue_id = v.id 
                    JOIN Invoice i ON cp.invoice_id = i.id;
                ''')
            results = cursor.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No Camp Registration found"
        )

    return results

@app.get('/leader/smallgroup/{leaderId}')
async def leader_small_group(leaderId: int):
    conn = get_mysql_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
    '''
    SELECT  
    CONCAT(l.first_name, ' ', l.last_name) AS leader_name, 
    sg.name AS small_group_name,
    sg.meetingTime AS MeetingTime,
    CONCAT(s.first_name, ' ', s.last_name) AS student_name
    FROM Student s
        JOIN SmallGroup sg ON sg.ID = s.smallGroupId
        JOIN Leader l ON l.leaderId = sg.leaderId
    WHERE l.leaderId = ${leaderId}
   ''')
            results = cursor.fetchone()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="That small group isn't found"
        )

    return results


@app.get('/event/registration/{eventId}')
async def event_student_attendance(eventId: int):

    conn = get_mysql_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
    '''
    SELECT *
    FROM Event e
        JOIN StudentAttendance sa ON e.ID = sa.eventId
        JOIN Student s ON s.ID = sa.studentId
    WHERE e.ID = ${eventId}
    ''')
            results = cursor.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="That event doesn't exist in our db"
        )

    return results

@app.get('/campregistration/student/{student_id}')
async def campregistration_students(student_id: int):

    conn = get_mysql_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(

                '''
                    SELECT
                         CONCAT(s.first_name, ' ', s.last_name) AS student_name,
                        c.id AS campId,
                        cp.timestamp AS RegisteredTime,
                        i.amount AS AmountPaid,
                         CONCAT(p.first_name, ' ', p.last_name) AS parent_name,
                         e.description AS description,
                         v.adress AS VenueAdress
                    FROM CampRegistration cp
                    JOIN Invoice i ON cp.invoice_id = i.id
                    JOIN student s ON s.id = i.student_id
                    JOIN parent p ON s.parent_id = p.id
                    JOIN camp c ON cp.camp_id = c.id 
                    JOIN event e ON c.id = e.id
                    JOIN venue v ON e.venue_id = v.id;
                ''')
            results = cursor.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
    finally:
        conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="That event doesn't exist in our db"
        )

    return results

def mongo_event_custom_values():
    client = get_mongo_conn()
    db = client['YouthGroup']
    return db['event_custom_values']


@app.post('/events')
async def create_event(payload: dict):
    event_id = payload.get('event_id')
    date = payload.get('date')
    venue_id = payload.get('venue_id')
    start_time = payload.get('start_time')
    end_time = payload.get('end_time')
    description = payload.get('description')
    custom_fields = payload.get('custom_fields', {})

    if not all([event_id, date, venue_id, start_time, end_time]):
        raise HTTPException(400, 'Missing required event fields')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute("""
                   INSERT INTO Event (event_type_id, venue_id, start_time, end_time, description)
                   VALUES (%s, %s, %s, %s, %s);
               """, (event_id, venue_id, start_time, end_time, description))

            conn.commit()
            event_id = cursor.lastrowid  # ← NOW event_id exists!
    except Exception as e:
        raise HTTPException(500, f"MySQL insert failed: {e}")
    finally:
        conn.close()

    try:
        mongo_event_custom_values().insert_one({
            'event_id':event_id,
            'custom_fields':custom_fields,

        })
    except Exception as e:
        raise HTTPException(500, f'MongoDB insert failed: {e}')

    return {
        'message': 'Event created',
        'event_id': event_id,
        'custom_fields': custom_fields
    }

def mongo_camp_custom_values():
    client = get_mongo_conn()
    db = client['YouthGroup']
    return db['camp_custom_values']


@app.post('/camps')
async def create_camp(payload: dict):
    date = payload.get('date')
    venue_id = payload.get('venue_id')
    start_time = payload.get('start_time')
    end_time = payload.get('end_time')
    description = payload.get('description')
    custom_fields = payload.get('custom_fields', {})

    if not all([ date, venue_id, start_time, end_time]):
        raise HTTPException(400, 'Missing required event fields')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute("""
                   INSERT INTO Event ( venue_id, start_time, end_time, description)
                   VALUES (%s, %s, %s, %s, %s);
               """, ( venue_id, start_time, end_time, description))

            conn.commit()
            event_id = cursor.lastrowid
            cursor.execute("""
                            INSERT INTO CAMP (camp_id, event_id)
                            VALUES (NULL, %s);
                        """, (event_id,))
            conn.commit()
            camp_id = cursor.lastrowid
    except Exception as e:
        raise HTTPException(500, f"MySQL insert failed: {e}")
    finally:
        conn.close()

    try:
        mongo_camp_custom_values().insert_one({
            'camp_id': camp_id,
            'event_id': event_id,
            'custom_fields': custom_fields,
        })
    except Exception as e:
        raise HTTPException(500, f'MongoDB insert failed: {e}')

    return {
        'message': 'Camp created',
        'event_id': event_id,
        'camp_id': camp_id,
        'custom_fields': custom_fields
    }








