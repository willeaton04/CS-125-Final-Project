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
from strawberry.fastapi import GraphQLRouter
from app_graphql.schema import schema, get_mysql_conn, get_redis_conn

app = FastAPI()
load_dotenv()

# importing conn's from schema.py

_mongo_client = None

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

def get_mongo_conn():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(
            f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@cs-125.3xkvzsq.mongodb.net/?appName=CS-125",
            server_api=ServerApi('1')
        )
    return _mongo_client

def mongo_event_custom_values():
    client = get_mongo_conn()
    db = client['YouthGroup']
    return db['event_custom_values']

# Helps in sorting out and finding it instantly
def setup_mongodb_indexes():
    """Setup MongoDB indexes for better performance. Run once during initialization."""
    try:
        mongo_event_custom_values().create_index('event_id', unique=True)
        mongo_camp_custom_values().create_index('camp_id', unique=True)
        print("MongoDB indexes created successfully")
    except Exception as e:
        print(f"MongoDB index creation warning: {e}")


# This decorator tells FastAPI: "Run this function ONE
# TIME when the application starts up, before handling any requests."
@app.on_event("startup")
async def startup_event():
    setup_mongodb_indexes()

# ======================
#     REDIS ENDPOINTS
# ======================


@app.post('/redis/event/registration/{event_id}')
async def load_student_event_reg(event_id: int):
    try:
        redis_conn = get_redis_conn()
        mysql_conn = get_mysql_conn()

        if redis_conn.exists(f"event:{event_id}:students") == 1:
            return {
                "event_id": event_id,
                'message': 'Data already exists'
            }

        with mysql_conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
                SELECT e.id AS event_id,
                       e.venue_id,
                       e.start_time,
                       e.end_time,
                       e.description,
                       sa.student_id,
                       sa.timestamp,
                       s.note,
                       s.first_name,
                       s.last_name,
                       s.email,
                       s.phone_number,
                       s.parent_id,
                       s.small_group_id
                FROM Event e
                         JOIN StudentAttendance sa ON e.id = sa.event_id
                         JOIN Student s ON s.id = sa.student_id
                WHERE e.id = %s
                ''',
                (event_id,)
            )
            results = cursor.fetchall()

        # ---------------------------------------------------------
        # REDIS: FORMAT + STORE
        # ---------------------------------------------------------

        # Clear previous data for this event (optional but common)
        # redis_conn.delete(f"event:{event_id}:students")

        for row in results:
            student_id = row["student_id"]

            key = f"event:{event_id}:student:{student_id}"

            redis_data = {
                "event_id": row["event_id"],
                "venue_id": row["venue_id"],
                "start_time": str(row["start_time"]),
                "end_time": str(row["end_time"]),
                "description": row["description"],

                "student_id": student_id,
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "email": row["email"],
                "phone_number": row["phone_number"],
                "parent_id": row["parent_id"],
                "small_group_id": row["small_group_id"],

                "timestamp": str(row["timestamp"]),
                "note": row["note"] if row["note"] else "",
            }

            # Save hash into Redis
            redis_conn.hset(key, mapping=redis_data)
            redis_conn.expire(key, 86400)

            # Optional: Keep a list/set of all student keys
            redis_conn.sadd(f"event:{event_id}:students", key)
            redis_conn.expire(f"event:{event_id}:students", 86400)

        return {"message": "Event registration data loaded into Redis", "count": len(results), "success": True}


    except Exception as e:
        return HTTPException(
            status_code=500,
            detail=f"Failed to load data into redis {str(e)}"
        )
    finally:
        redis_conn.close()
        mysql_conn.close()


@app.get("/redis/event/registration/{event_id}")
async def get_student_event_reg(event_id: int):
    try:
        redis_conn = get_redis_conn()

        # Get all student keys for the event
        student_keys = redis_conn.smembers(f"event:{event_id}:students")

        if not student_keys:
            return {
                "event_id": event_id,
                "registrations": [],  # for frontend to decipher
                "message": "No event registration data found in Redis"
            }

        registrations = []

        for key in student_keys:
            # Redis returns bytes → decode to string
            key = key.decode() if isinstance(key, bytes) else key

            raw_data = redis_conn.hgetall(key)

            # Also convert bytes to strings for each field
            formatted_data = {
                k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
                for k, v in raw_data.items()
            }

            # Convert numeric strings to ints where appropriate
            for numeric_field in ["event_id", "venue_id", "student_id", "parent_id", "small_group_id"]:
                if numeric_field in formatted_data and formatted_data[numeric_field].isdigit():
                    formatted_data[numeric_field] = int(formatted_data[numeric_field])

            registrations.append(formatted_data)

        return {
            "event_id": event_id,
            "count": len(registrations),
            "registrations": registrations,
            "sucsess": True
        }


    except Exception as e:
        print("Redis fetch error:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/redis/event/registration/{event_id}")
async def update_student_event_reg(event_id: int):
    '''
        This method refreshes redis event registration
        :param event_id:
        :return: sql data
    '''
    try:
        redis_conn = get_redis_conn()
        mysql_conn = get_mysql_conn()

        # --------------------------------------
        # 1. Fetch the latest MySQL data
        # --------------------------------------
        with mysql_conn.cursor() as cursor:
            cursor.execute("USE YouthGroup;")
            cursor.execute(
                """
                SELECT
                    e.id AS event_id,
                    e.venue_id AS venue_id,
                    e.start_time AS start_time,
                    e.end_time AS end_time,
                    e.description AS end_time,
                    sa.student_id AS student_id,
                    sa.timestamp AS timestamp,
                    s.note AS note,
                    s.first_name AS first_name,
                    s.last_name AS last_name,
                    s.email AS email,
                    s.phone_number AS phone_number,
                    s.parent_id AS parent_id,
                    s.small_group_id AS small_group_id
                FROM Event e
                JOIN StudentAttendance sa ON e.id = sa.event_id
                JOIN Student s ON s.id = sa.student_id
                WHERE e.id = %s;
                """,
                (event_id,)
            )
            results = cursor.fetchall()

        # --------------------------------------
        # 2. DELETE OLD REDIS DATA FOR THIS EVENT
        # --------------------------------------
        old_keys = redis_conn.smembers(f"event:{event_id}:students")

        # Delete student hashes
        if old_keys:
            redis_conn.delete(*old_keys)

        # Delete the student set
        redis_conn.delete(f"event:{event_id}:students")

        # --------------------------------------
        # 3. REBUILD REDIS KEYS WITH NEW DATA
        # --------------------------------------
        for row in results:
            student_id = row["student_id"]
            key = f"event:{event_id}:student:{student_id}"

            redis_data = {
                "event_id": row["event_id"],
                "venue_id": row["venue_id"],
                "start_time": str(row["start_time"]),
                "end_time": str(row["end_time"]),
                "description": row["description"],
                "student_id": student_id,
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "email": row["email"],
                "phone_number": row["phone_number"],
                "parent_id": row["parent_id"],
                "small_group_id": row["small_group_id"],
                "timestamp": str(row["timestamp"]),
                "note": row["note"] or "",
            }

            # Insert updated hash
            redis_conn.hset(key, mapping=redis_data)
            redis_conn.expire(key, 86400)  # TTL 24 hours

            # Add to event student set
            redis_conn.sadd(f"event:{event_id}:students", key)
            redis_conn.expire(f"event:{event_id}:students", 86400)
        return {
            "message": "Event registration Redis cache updated",
            "event_id": event_id,
            "count": len(results),
            "success": True
        }


    except Exception as e:
        print("Error updating Redis:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/redis/event/registration/{event_id}")
async def delete_student_event_reg(event_id: int):
    try:
        redis_conn = get_redis_conn()

        # --------------------------------------
        # 1. Find all student hash keys
        # --------------------------------------
        student_keys = redis_conn.smembers(f"event:{event_id}:students")

        deleted_count = 0

        # --------------------------------------
        # 2. Delete each student hash
        # --------------------------------------
        if student_keys:
            # Redis returns bytes → convert
            decoded_keys = [
                k.decode() if isinstance(k, bytes) else k
                for k in student_keys
            ]

            # Delete all hashes at once
            redis_conn.delete(*decoded_keys)
            deleted_count += len(decoded_keys)

        # --------------------------------------
        # 3. Delete the student set itself
        # --------------------------------------
        redis_conn.delete(f"event:{event_id}:students")

        return {
            "message": f"Redis event {event_id} data deleted",
            "event_id": event_id,
            "deleted_records": deleted_count,
            "success": True
        }


    except Exception as e:
        print("Error deleting Redis keys:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ======================
#    MYSQL ENDPOINTS
# ======================
@app.get('/')
async def root():
    return {'message': 'Service is running'}


@app.get('/student/')
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
@app.put('/student/{student_id}')
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
               WHERE id = %s;''', (email, phone_number, note, student_id, student_name, parent_name, small_group_name,
                                   small_group_leader_name))
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


@app.get('/parent/')
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


@app.get('/leader/')
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

@app.delete('/leader/{leader_id}')
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
            cursor.execute('''
   SELECT
       e.id AS event_id,
       e.start_time AS StartTime,
       e.end_time AS EndTime,
       e.description AS description
   FROM Event e
   JOIN Venue v ON e.venue_id = v.id
   GROUP BY e.id;
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

    # Add custom fields from MongoDB to each event
    for event in results:
        try:
            custom_doc = mongo_event_custom_values().find_one({'event_id': event['event_id']})
            event['custom_fields'] = custom_doc.get('custom_fields', {}) if custom_doc else {}
        except Exception as e:
            print(f"MongoDB fetch warning for event {event['event_id']}: {e}")
            event['custom_fields'] = {}

    return results


@app.put("/event/{event_id}")
async def update_event(event_id: int, payload: dict):
    description = payload.get("description")
    start_time = payload.get("start_time")
    end_time = payload.get("end_time")

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(''' UPDATE Leader
               SET description = %s, start_time=%s, end_time=%s
               WHERE id = %s;''', (description, start_time, end_time, event_id))
            cursor.execute("USE YouthGroup;")
            cursor.execute(
                """
                UPDATE Event
                SET description = %s, start_time = %s, end_time = %s
                WHERE id = %s;
                """,
                (description, start_time, end_time, event_id)
            )
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(404, "Event not found")

        return {"message": "Event updated successfully"}

    except Exception as e:
        raise HTTPException(500, f"Database query failed: {str(e)}")

    finally:
        conn.close()


@app.delete('/event/')
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


@app.get('/mongo/event/{eventId}')
async def get_event(eventId: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('''
               SELECT
                   e.id AS event_id,
                   e.start_time AS StartTime,
                   e.end_time AS EndTime,
                   sa.student_id AS studentId,
                   v.address as VenueAddress,
                   e.description AS description
               FROM Event e
               JOIN Venue v ON e.venue_id = v.id
               LEFT JOIN StudentAttendance sa ON sa.event_id = e.id
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

    # Adding custom fields from MongoDB
    try:
        custom_doc = mongo_event_custom_values().find_one({'event_id': eventId})
        custom_fields = custom_doc.get('custom_fields', {}) if custom_doc else {}
    except Exception as e:
        print(f"MongoDB fetch warning: {e}")
        custom_fields = {}

    return {
        'event_data': results,
        'custom_fields': custom_fields
    }


@app.post('/mongo/event/')
async def create_event(payload: dict):
    venue_id = payload.get('venue_id')
    start_time = payload.get('start_time')
    end_time = payload.get('end_time')
    description = payload.get('description')
    custom_fields = payload.get('custom_fields', {})

    if not all([venue_id, start_time, end_time]):
        raise HTTPException(400, 'Missing required event fields')

    event_id = None
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute("""
               INSERT INTO Event (venue_id, start_time, end_time, description)
               VALUES (%s, %s, %s, %s);
           """, (venue_id, start_time, end_time, description))
            conn.commit()
            event_id = cursor.lastrowid
    except Exception as e:
        raise HTTPException(500, f"MySQL insert failed: {e}")
    finally:
        conn.close()

    # Only saving to MongoDB if there are custom fields
    if custom_fields and event_id:
        try:
            mongo_event_custom_values().insert_one({
                'event_id': event_id,
                'custom_fields': custom_fields,
            })
        except Exception as e:
            print(f"MongoDB insert warning: {e}")
            # Don't fail the entire request if MongoDB fails

    return {
        'message': 'Event created',
        'event_id': event_id,
        'custom_fields': custom_fields
    }


@app.put('/mongo/event/{event_id}')
async def update_event(event_id: int, payload: dict):
    description = payload.get('description')
    start_time = payload.get('start_time')
    end_time = payload.get('end_time')
    custom_fields = payload.get('custom_fields')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('''
               UPDATE Event
               SET description = %s, start_time = %s, end_time = %s
               WHERE id = %s;
           ''', (description, start_time, end_time, event_id))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, 'Event not found')
    except Exception as e:
        raise HTTPException(500, f'Database query failed: {str(e)}')
    finally:
        conn.close()

    # Update custom fields in MongoDB if provided
    if custom_fields is not None:
        try:
            mongo_event_custom_values().update_one(
                {'event_id': event_id},
                {'$set': {'custom_fields': custom_fields}},
                upsert=True
            )
        except Exception as e:
            print(f"MongoDB update warning: {e}")

    return {'message': 'Event updated successfully'}

@app.delete('/mongo/event/{event_id}')
async def delete_event(event_id: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute("USE YouthGroup;")

            # First: Delete dependent attendance records
            cursor.execute(
                "DELETE FROM StudentAttendance WHERE event_id = %s;",
                (event_id,)
            )

            # Second: Delete the event itself
            cursor.execute(
                "DELETE FROM Event WHERE id = %s;",
                (event_id,)
            )

            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(404, "Event not found")

        return {"message": "Event deleted successfully"}

    except Exception as e:
        raise HTTPException(500, f"Delete failed: {str(e)}")

    finally:
        conn.close()

    # Delete associated MongoDB document
    try:
        mongo_event_custom_values().delete_one({'event_id': event_id})
    except Exception as e:
        print(f"MongoDB delete warning: {e}")

    return {"message": "Event deleted successfully"}


@app.get('/camp/')
async def get_camps():
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('''
               SELECT
                   c.id as camp_id,
                   e.start_time AS start_time,
                   e.end_time AS end_time,
                   e.description AS description
               FROM Camp c
               JOIN Event e ON e.id = c.id;
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

    # Add custom fields from MongoDB to each camp
    for camp in results:
        try:
            custom_doc = mongo_camp_custom_values().find_one({'camp_id': camp['camp_id']})
            camp['custom_fields'] = custom_doc.get('custom_fields', {}) if custom_doc else {}
        except Exception as e:
            print(f"MongoDB fetch warning for camp {camp['camp_id']}: {e}")
            camp['custom_fields'] = {}

    return results


@app.put('/camp/')
async def update_camp(camp_id: int, payload: dict):
    camp_id = payload.get('camp_id')
    start_time = payload.get('start_time')
    end_time = payload.get('end_time')
    description = payload.get('description')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(''' UPDATE Camp
               SET description = %s, start_time=%s, end_time=%s
               WHERE id = %s;''', (description, start_time, end_time, camp_id))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, 'Camp not found')
    except Exception as e:
        raise HTTPException(500, f'Database query failed: {str(e)}')
    finally:
        conn.close()
    return {'message': 'Camp updated successfully'}


@app.delete('/camp/')
async def delete_camp(camp_id: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('DELETE FROM Camp WHERE id = %s;', (camp_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, "Camp not found")
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")
    finally:
        conn.close()

    return {"message": "Camp deleted successfully"}


@app.get('/camp/{campId}')
async def get_camp(campId: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('''
               SELECT
                   c.id as camp_id,
                   e.start_time AS StartTime,
                   e.end_time AS EndTime,
                   e.description as description
               FROM Camp c
               JOIN Event e ON e.id = c.id
               WHERE c.id = %s;
           ''', (campId,))
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
            detail="Camp not found"
        )

    # Add custom fields from MongoDB
    try:
        custom_doc = mongo_camp_custom_values().find_one({'camp_id': campId})
        results['custom_fields'] = custom_doc.get('custom_fields', {}) if custom_doc else {}
    except Exception as e:
        print(f"MongoDB fetch warning: {e}")
        results['custom_fields'] = {}

    return results


@app.post('/camp')
async def create_camp(payload: dict):
    venue_id = payload.get('venue_id')
    start_time = payload.get('start_time')
    end_time = payload.get('end_time')
    description = payload.get('description')
    custom_fields = payload.get('custom_fields', {})

    if not all([venue_id, start_time, end_time]):
        raise HTTPException(400, 'Missing required camp fields')

    event_id = None
    camp_id = None

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute("""
               INSERT INTO Event (venue_id, start_time, end_time, description)
               VALUES (%s, %s, %s, %s);
           """, (venue_id, start_time, end_time, description))
            conn.commit()
            event_id = cursor.lastrowid

            cursor.execute("""
               INSERT INTO Camp (id)
               VALUES (%s);
           """, (event_id,))
            conn.commit()
            camp_id = cursor.lastrowid
    except Exception as e:
        raise HTTPException(500, f"MySQL insert failed: {e}")
    finally:
        conn.close()

    # Save custom fields to MongoDB if provided
    if custom_fields and camp_id:
        try:
            mongo_camp_custom_values().insert_one({
                'camp_id': camp_id,
                'event_id': event_id,
                'custom_fields': custom_fields,
            })
        except Exception as e:
            print(f"MongoDB insert warning: {e}")

    return {
        'message': 'Camp created',
        'event_id': event_id,
        'camp_id': camp_id,
        'custom_fields': custom_fields
    }


@app.put('/camp/{camp_id}')
async def update_camp(camp_id: int, payload: dict):
    start_time = payload.get('start_time')
    end_time = payload.get('end_time')
    description = payload.get('description')
    custom_fields = payload.get('custom_fields')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            # Update the Event table since Camp inherits from Event
            cursor.execute('''
               UPDATE Event e
               JOIN Camp c ON c.id = e.id
               SET e.start_time = %s, e.end_time = %s, e.description = %s
               WHERE c.id = %s;
           ''', (start_time, end_time, description, camp_id))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, 'Camp not found')
    except Exception as e:
        raise HTTPException(500, f'Database query failed: {str(e)}')
    finally:
        conn.close()

    # Update custom fields in MongoDB if provided
    if custom_fields is not None:
        try:
            mongo_camp_custom_values().update_one(
                {'camp_id': camp_id},
                {'$set': {'custom_fields': custom_fields}},
                upsert=True
            )
        except Exception as e:
            print(f"MongoDB update warning: {e}")

    return {'message': 'Camp updated successfully'}


@app.delete('/camp/{camp_id}')
async def delete_camp(camp_id: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('DELETE FROM Camp WHERE id = %s;', (camp_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, "Camp not found")
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")
    finally:
        conn.close()

    # Delete associated MongoDB document
    try:
        mongo_camp_custom_values().delete_one({'camp_id': camp_id})
    except Exception as e:
        print(f"MongoDB delete warning: {e}")

    return {"message": "Camp deleted successfully"}


@app.get('/venue')
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


@app.put('/venue')
async def update_venue(venue_id: int, payload: dict):
    address = payload.get('address')
    description = payload.get('description')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(''' UPDATE Venue
               SET address = %s, description = %s
               WHERE id = %s;''', (address, description))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, 'Venue not found')
    except Exception as e:
        raise HTTPException(500, f'Database query failed: {str(e)}')
    finally:
        conn.close()
    return {'message': 'Venue updated successfully'}


@app.delete('/Venue')
async def delete_venue(venue_id: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('DELETE FROM Venue WHERE id = %s;', (venue_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, "Venue not found")
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")
    finally:
        conn.close()

    return {"message": "Venue deleted successfully"}


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


@app.put('/student/{student_id}')
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
               WHERE id = %s;''', (email, phone_number, note, student_id, student_name, parent_name, small_group_name,
                                   small_group_leader_name))
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
                    WHERE l.id = %s;
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
            detail=f"Leader with ID {leaderId} not found"
        )

    return results


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
               WHERE id = %s;''', (
                email, phone_number, note, small_group_name, datejoined, salary, start_time, end_time, leader_id))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, 'Leader not found')
    except Exception as e:
        raise HTTPException(500, f'Database query failed: {str(e)}')
    finally:
        conn.close()
    return {'message': 'Leader updated successfully'}


@app.delete('/leader/{leader_id}')
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
                        v.description AS descriptionVenue,
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


# Does camp have its own id or it has the event_id


@app.put('/venue/{venue_id}')
async def update_venue(venue_id: int, payload: dict):
    address = payload.get('address')
    description = payload.get('description')
    descriptionVenue = payload.get('descriptionVenue')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(''' UPDATE Venue
               SET address = %s, description = %s, descriptionVenue = %s
               WHERE id = %s;''', (address, description, descriptionVenue, venue_id))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, 'Venue not found')
    except Exception as e:
        raise HTTPException(500, f'Database query failed: {str(e)}')
    finally:
        conn.close()
    return {'message': 'Venue updated successfully'}


@app.delete('/venue/{venue_id}')
async def delete_venue(venue_id: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('DELETE FROM Venue WHERE id = %s;', (venue_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, "Venue not found")
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")
    finally:
        conn.close()

    return {"message": "Venue deleted successfully"}


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
                     JOIN StudentAttendance sa ON e.id = sa.event_id
                     JOIN Student s ON s.id = sa.event_id
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


@app.put('/camp/registration/{campId}')
async def update_student_camp_registration(camp_id: int, payload: dict):
    camp_id = payload.get('campId')
    AmountPaid = payload.get('amountPaid')
    description = payload.get('description')
    VenueAddress = payload.get('venueAdress')
    descriptionVenue = payload.get('descriptionVenue')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(''' UPDATE camp
               SET VenueAddress = %s, description = %s, descriptionVenue = %s, AmountPaid = %s, camp_id = %s
               WHERE id = %s;''', (camp_id, description, AmountPaid, descriptionVenue, VenueAddress))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, 'Camp Registration not found')
    except Exception as e:
        raise HTTPException(500, f'Database query failed: {str(e)}')
    finally:
        conn.close()
    return {'message': 'Camp Registration updated successfully'}


@app.delete('/camp/registration/{campId}')
async def delete_student_camp_registration(camp_id: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('DELETE FROM camp WHERE id = %s;', (camp_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, "CampRegistration not found")
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")
    finally:
        conn.close()

    return {"message": "CampRegistration deleted successfully"}


@app.get('/leader/smallgroup/{leaderId}')
async def leader_small_group(leaderId: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(
                '''
    SELECT 
      CONCAT(l.first_name, ' ', l.last_name) AS leader_name,
    sg.name AS small_group_name,
    sg.meeting_time AS MeetingTime,
    CONCAT(s.first_name, ' ', s.last_name) AS student_name
    FROM Student s
        JOIN SmallGroup sg ON sg.id = s.small_group_id
        JOIN Leader l ON l.id = sg.leader_id
    WHERE l.id = %s
    GROUP BY s.id;
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
            detail="That small group isn't found"
        )

    return results


@app.put('/leader/smallgroup/{leaderId}')
async def update_leader_small_group(leaderId: int, payload: dict):
    meeting_time = payload.get('meeting_time')
    student_name = payload.get('student_name')
    smallGroupName = payload.get('smallGroupName')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(''' UPDATE leader
               SET meeting_time = %s, student_name = %s, smallGroupName = %s, leader_id = %s
               WHERE id = %s;''', (meeting_time, student_name, smallGroupName, leaderId))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, 'Leader small group not found')
    except Exception as e:
        raise HTTPException(500, f'Database query failed: {str(e)}')
    finally:
        conn.close()
    return {'message': 'Leader small group updated successfully'}


@app.delete('/leader/smallgroup/{leaderId}')
async def delete_leader_small_group(leaderId: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('DELETE FROM leader WHERE id = %s;', (leaderId,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, "Leader small group not found")
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")
    finally:
        conn.close()

    return {"message": "Leader small group deleted successfully"}


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


@app.delete('/event/registration/{eventId}')
async def delete_event_student_attendance(eventId: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('DELETE FROM event WHERE id = %s;', (eventId,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, "CampRegistration not found")
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")
    finally:
        conn.close()

    return {"message": "CampRegistration deleted successfully"}


@app.get('/camp_registration/student/{student_id}')
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
                         v.address AS venue_address
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


@app.put('/camp_registration/student/{student_id}')
async def update_camp_registration_students(student_id: int, payload: dict):
    student_name = payload.get('student_name')
    campId = payload.get('campId')
    registered_time = payload.get('registered_time')
    amount_paid = payload.get('amount_paid')
    parent_name = payload.get('parent_name')
    description = payload.get('description')
    venue_address = payload.get('venue_address')

    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute(''' UPDATE camp, student
               SET student_name = %s, campId = %s, registered_time = %s, amount_paid = %s, parent_name = %s, description = %s, venue_address = %s
               WHERE id = %s;''', (
                student_name, campId, registered_time, amount_paid, parent_name, description, venue_address))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, 'Camp Registration students not found')
    except Exception as e:
        raise HTTPException(500, f'Database query failed: {str(e)}')
    finally:
        conn.close()
    return {'message': 'Camp Registration students updated successfully'}


@app.delete('/camp/registration/{campId}')
async def delete_camp_registration_students(student_id: int):
    try:
        conn = get_mysql_conn()
        with conn.cursor() as cursor:
            cursor.execute('USE YouthGroup;')
            cursor.execute('DELETE FROM camp WHERE id = %s;', (student_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(404, "CampRegistration students not found")
    except Exception as e:
        raise HTTPException(500, f"Delete failed: {e}")
    finally:
        conn.close()

    return {"message": "CampRegistration students deleted successfully"}
