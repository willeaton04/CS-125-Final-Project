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

@app.get('/student/')
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
    conn.close()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No students found"
        )

    return results

@app.get('/leader/')
async def get_all_leaders():
    pass

@app.get('/event/')
async def get_events():
    pass

@app.get('/camp/')
async def get_camps():
    pass

@app.get('/venue/')
async def get_venues():
    pass


@app.get('/student/{studentId}/')
async def get_student(studentId: int):
    '''
    SELECT *
    FROM Student s
        JOIN Parent p ON p.ID = s.parentId
    WHERE ID = ${ID}
    '''
    pass

@app.get('/leader/{leaderId}')
async def get_leader(leaderId: int):
    pass

@app.get('/event/{eventId}')
async def get_events(eventId: int):
    pass

@app.get('/camp/{campId}')
async def get_events(campId: int):
    pass

@app.get('/venue/{venueId}')
async def get_events(venueId: int):
    pass


@app.get('/camp/registration/{campId}')
async def student_camp_registration(campId: int):
    pass

@app.get('/leader/smallgroup/{leaderId}')
async def leader_small_group(leaderId: int):
    '''
    SELECT sg.leaderId, s.first_name, s.last_name
    FROM Student s
        JOIN SmallGroup sg ON sg.ID = s.smallGroupId
        JOIN Leader l ON l.leaderId = sg.leaderId
    WHERE l.leaderId = ${leaderId}
    '''
    pass

@app.get('/event/registration/{eventId}')
async def event_student_attendance(eventId: int):
    '''
    SELECT *
    FROM Event e
        JOIN StudentAttendance sa ON e.ID = sa.eventId
        JOIN Student s ON s.ID = sa.studentId
    WHERE e.ID = ${eventId}
    '''
    pass








