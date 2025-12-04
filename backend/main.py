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
        port=3306,
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

# ======================
#    MYSQL ENDPOINTS
# ======================
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



@app.get('/event/')
async def get_all_events():
    try:
        conn = get_mysql_conn()

        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
'''
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
                """
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
            WHERE s.id = %s
                """, (student_id,))
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
            detail=f"Student with ID {student_id} not found"
        )

    return results


@app.get('/leader/{leaderId}')
async def get_leader(leaderId: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                    SELECT 
                        CONCAT(l.first_name, ' ', l.last_name) AS leader_name,
                        sg.name AS small_group_name,
                        l.date_joined AS datejoined,
                        l.email AS email,
                        l.phone_number AS phone_number,
                        l.salary AS salary,
                        r.title AS title,
                        r.description AS description,
                        s.start_time AS ShiftStartTime,
                        s.end_time AS ShiftEndTime,
                        l.note AS note
                    FROM Leader l
                    LEFT JOIN LeaderRole lr ON lr.leader_id = l.id
                    LEFT JOIN Role r ON lr.role_id = r.id
                    LEFT JOIN LeaderShift ls ON ls.leader_id = l.id
                    LEFT JOIN Shift s ON s.id = ls.shift_id
                    LEFT JOIN SmallGroup sg ON sg.leader_id = l.id
                    WHERE l.id = %s
                ''', (leaderId,))
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
            detail=f"Leader with ID {leaderId} not found"
        )

    return results

@app.get('/event/{eventId}')
async def get_events(eventId: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                    SELECT 
                        e.start_time AS StartTime,
                        e.end_time AS EndTime,
                        sa.student_id AS studentId,
                        v.address as VenueAdress,
                        e.description AS description
                    FROM Event e
                    JOIN Venue v ON e.venue_id = v.id
                    JOIN StudentAttendance sa ON sa.event_id = e.id
                    WHERE e.id = %s;
                ''', (eventId,))
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
            detail=f"No events with {eventId} found"
        )

    return results

@app.get('/camp/{campId}')
async def get_camp(campId: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                    SELECT 
                        c.id as CampNumber,
                        e.start_time AS StartTime,
                        e.end_time AS EndTime,
                        e.description as description
                    FROM Camp c
                    JOIN Event e ON e.id = c.id
                    WHERE c.id = %s;
                ''', (campId,))
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
async def get_venue(venueId: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                    SELECT 
                        v.address as VenueAdress,
                        v.description AS description,
                        e.description AS description
                    FROM Venue v
                    JOIN Event e ON e.venue_id = v.id
                    WHERE v.id = %s;
                ''', (venueId,))
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
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                    SELECT 
                        c.id AS campId,
                        i.amount AS AmountPaid,
                        e.description AS description,
                        v.address AS VenueAdress,
                        v.description AS description
                    FROM CampRegistration cp
                    JOIN Camp c ON cp.camp_id = c.id 
                    JOIN Event e ON c.id = e.id
                    JOIN Venue v ON e.venue_id = v.id 
                    JOIN Invoice i ON cp.invoice_id = i.id
                    WHERE c.id = %s;
                ''', (campId,))
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
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
    '''
    SELECT  
        sg.name AS small_group_name,
        sg.meeting_time AS meeting_time,
        CONCAT(s.first_name, ' ', s.last_name) AS student_name
    FROM Student s
        JOIN SmallGroup sg ON sg.id = s.small_group_id
        JOIN Leader l ON l.id = sg.leader_id
    WHERE l.id = %s;
    ''', (leaderId,))
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
            detail="That small group isn't found"
        )

    return results


@app.get('/event/registration/{eventId}')
async def event_student_attendance(eventId: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
    '''
    SELECT *
    FROM Event e
        JOIN StudentAttendance sa ON e.id = sa.event_id
        JOIN Student s ON s.id = sa.student_id
    WHERE e.id = %s
    ''', (eventId,))
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
async def camp_registration_students(student_id: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(

                '''
                    SELECT
                         CONCAT(s.first_name, ' ', s.last_name) AS student_name,
                         c.id AS campId,
                         cp.timestamp AS registered_time,
                         i.amount AS amount_paid,
                         CONCAT(p.first_name, ' ', p.last_name) AS parent_name,
                         e.description AS description,
                         v.address AS venue_adress
                    FROM CampRegistration cp
                    JOIN Invoice i ON cp.invoice_id = i.id
                    JOIN Student s ON s.id = i.student_id
                    JOIN Parent p ON s.parent_id = p.id
                    JOIN Camp c ON cp.camp_id = c.id 
                    JOIN Event e ON c.id = e.id
                    JOIN Venue v ON e.venue_id = v.id
                    WHERE s.id = %s;
                ''', (student_id,))
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

