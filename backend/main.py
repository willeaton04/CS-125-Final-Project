'''
@author Will Eaton, Nice Hirwa

builds entrypoint for graphql using FastAPI
'''
from fastapi import FastAPI, HTTPException
import pymysql
import redis
from pymongo import MongoClient
import os
# from strawberry.fastapi import GraphQLRouter
from app_graphql.schema import schema

app = FastAPI()

def get_mysql_conn():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
        # This takes in my youth group already, so no reason of calling it each
        # time!?
        cursorclass=pymysql.cursors.DictCursor
    )

def get_redis_conn():
    return redis.Redis(host=os.getenv('REDIS_HOST'), port=6379, decode_responses=True)

def get_mongo_conn():
    client = MongoClient(
        f"mongodb://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_HOST')}:27017"
    )
    return client['testdb']

# We'll figure out how to plug in Graphql later :)
# graphql_app = GraphQLRouter(schema)
# app.include_router(graphql_app, prefix="/graphql")

@app.get('/')
async def root():
    return {'message': 'Service is running'}

@app.get('/student')
async def get_all_students():
    conn = get_mysql_conn()
    try:
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
    conn = get_mysql_conn()
    try:
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
    conn = get_mysql_conn()
    try:
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
    conn = get_mysql_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
'''
    SELECT 
        e.startTime AS StartTime,
        e.endTime AS EndTime,
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
                        v.adress as VenueAdress,
                        v.description AS description
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


@app.get('/student/{studentId}/')
async def get_student(studentId: int):
    conn = get_mysql_conn()
    try:
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
        s.note AS note,
        p.email AS parent_email,
        P.phone_number AS parent_phone,
        p.note AS parent_note
        FROM Student s
        JOIN Parent p ON s.parent_id = p.id
        JOIN SmallGroup sg ON sg.id = s.small_group_id
        JOIN studentAttendance sa ON sa.student_id = s.id;
        -- Should I add camp registration or not? ;
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
                    Join role l ON lr.roleId = r.id
                    Join leaderShift ls ON ls.leader_id = l.id;
                    Join Shift s ON s.id = ls.shift_id
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
                         CONCAT(s.first_name, ' ', s.last_name) AS student_name,
                        c.id AS campId,
                        cp.timestamp AS RegisteredTime,
                        i.amount AS AmountPaid,
                         CONCAT(p.first_name, ' ', p.last_name) AS parent_name
                         e.description AS description,
                    FROM CampRegistration c
                    JOIN camp c ON cp.camp_id = c.id 
                    JOIN event ON c.id = e.id
                    JOIN Invoice i ON cp.invoice_id = i.id
                    JOIN student s ON s.id = cp.student_id
                    JOIN parent p ON s.parent_id = p.id;
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
    CONCAT(s.first_name, ' ', s.last_name) AS student_name,
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









