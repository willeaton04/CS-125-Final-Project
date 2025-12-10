import strawberry
from typing import List, Optional, Dict, Any
import pymysql
import redis
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

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
        host=os.getenv('REDIS_ENDPOINT'),
        port=11044,
        decode_responses=True,
        username=os.getenv('REDIS_USERNAME'),
        password=os.getenv('REDIS_PASSWORD')
    )

def get_mongo_conn():
    client = MongoClient(
        f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@cs-125.3xkvzsq.mongodb.net/?appName=CS-125",
        server_api=ServerApi('1')
    )
    return client

@strawberry.type
class Student:
    parent_name: str
    student_name: str
    small_group_name: str
    small_group_leader_name: str
    email: str
    phone_number: str
    note: str

@strawberry.type
class Parent:
    parent_id: int
    parent_name: str
    email: str
    phone_number: str
    note: str
    students: List[str]

@strawberry.type
class Shift:
    start_time: str
    end_time: str

@strawberry.type
class Leader:
    leader_id: int
    leader_name: str
    small_group_name: Optional[str]
    datejoined: str
    email: str
    phone_number: str
    salary: float
    note: str
    shifts: List[Shift]

@strawberry.type
class Event:
    StartTime: str
    EndTime: str
    description: str

@strawberry.type
class EventDetail:
    StartTime: str
    EndTime: str
    studentId: int
    VenueAdress: str
    description: str

@strawberry.type
class Camp:
    CampNumber: int

@strawberry.type
class CampDetail:
    CampNumber: int
    StartTime: str
    EndTime: str
    description: str

@strawberry.type
class Venue:
    VenueAdress: str
    description: str

@strawberry.type
class VenueDetail:
    VenueAdress: str
    description: str

@strawberry.type
class CampRegistration:
    campId: int
    AmountPaid: float
    description: str
    VenueAdress: str

@strawberry.type
class SmallGroupInfo:
    small_group_name: str
    meeting_time: str
    student_name: str

@strawberry.type
class EventAttendance:
    event_id: int
    venue_id: int
    start_time: str
    end_time: str
    description: str
    student_id: int
    first_name: str
    last_name: str
    email: str
    phone_number: str
    parent_id: int
    small_group_id: int
    timestamp: str
    note: str

@strawberry.type
class CampRegistrationDetail:
    student_name: str
    campId: int
    registered_time: str
    amount_paid: float
    parent_name: str
    description: str
    venue_address: str

import strawberry
from typing import List, Optional

@strawberry.type
class RedisEventRegistration:
    event_id: int
    venue_id: int
    start_time: str
    end_time: str
    description: str
    student_id: int
    first_name: str
    last_name: str
    email: str
    phone_number: str
    parent_id: int
    small_group_id: int
    timestamp: str
    note: str

@strawberry.type
class RedisEventRegistrationResponse:
    event_id: int
    count: int
    registrations: List[RedisEventRegistration] = strawberry.field(default_factory=list)  # ✅ Correct
    message: Optional[str] = None
    success: bool

@strawberry.input
class StudentUpdateInput:
    email: Optional[str] = None
    phone_number: Optional[str] = None
    note: Optional[str] = None
    student_name: Optional[str] = None
    parent_name: Optional[str] = None
    small_group_name: Optional[str] = None
    small_group_leader_name: Optional[str] = None

@strawberry.input
class ParentUpdateInput:
    email: Optional[str] = None
    phone_number: Optional[str] = None
    note: Optional[str] = None
    student_name: Optional[str] = None
    parent_name: Optional[str] = None

@strawberry.input
class LeaderUpdateInput:
    email: Optional[str] = None
    phone_number: Optional[str] = None
    note: Optional[str] = None
    small_group_name: Optional[str] = None
    datejoined: Optional[str] = None
    salary: Optional[float] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

@strawberry.input
class EventUpdateInput:
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

@strawberry.input
class EventCreateInput:
    venue_id: int
    start_time: str
    end_time: str
    description: Optional[str] = None
    custom_fields: Optional[strawberry.scalars.JSON] = None

@strawberry.input
class CampCreateInput:
    date: str
    venue_id: int
    start_time: str
    end_time: str
    description: Optional[str] = None
    custom_fields: Optional[strawberry.scalars.JSON] = None

@strawberry.type
class Query:
    @strawberry.field
    def students(self) -> List[Student]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
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
                return [Student(**result) for result in results]
        finally:
            conn.close()

    @strawberry.field
    def student(self, student_id: int) -> Optional[Student]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
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
                ''', (student_id,))
                result = cursor.fetchone()
                return Student(**result) if result else None
        finally:
            conn.close()

    @strawberry.field
    def parents(self) -> List[Parent]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
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
                ''')
                rows = cursor.fetchall()
                
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
                
                return [Parent(**parent) for parent in parents.values()]
        finally:
            conn.close()

    @strawberry.field
    def leaders(self) -> List[Leader]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
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
                
                leaders = {}
                for row in rows:
                    lid = row["leader_id"]
                    if lid not in leaders:
                        leaders[lid] = {
                            "leader_id": lid,
                            "leader_name": row["leader_name"],
                            "small_group_name": row["small_group_name"],
                            "datejoined": str(row["datejoined"]),
                            "email": row["email"],
                            "phone_number": row["phone_number"],
                            "salary": row["salary"],
                            "note": row["note"],
                            "shifts": []
                        }
                    
                    if row["shift_start"] and row["shift_end"]:
                        leaders[lid]["shifts"].append(Shift(
                            start_time=str(row["shift_start"]),
                            end_time=str(row["shift_end"])
                        ))
                
                return [Leader(**leader) for leader in leaders.values()]
        finally:
            conn.close()

    @strawberry.field
    def leader(self, leader_id: int) -> Optional[Leader]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
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
                LEFT JOIN Shift s ON ls.shift_id = s.id
                WHERE l.id = %s;
                ''', (leader_id,))
                rows = cursor.fetchall()
                
                if not rows:
                    return None
                
                leader_data = {
                    "leader_id": rows[0]["leader_id"],
                    "leader_name": rows[0]["leader_name"],
                    "small_group_name": rows[0]["small_group_name"],
                    "datejoined": str(rows[0]["datejoined"]),
                    "email": rows[0]["email"],
                    "phone_number": rows[0]["phone_number"],
                    "salary": rows[0]["salary"],
                    "note": rows[0]["note"],
                    "shifts": []
                }
                
                for row in rows:
                    if row["shift_start"] and row["shift_end"]:
                        leader_data["shifts"].append(Shift(
                            start_time=str(row["shift_start"]),
                            end_time=str(row["shift_end"])
                        ))
                
                return Leader(**leader_data)
        finally:
            conn.close()

    @strawberry.field
    def events(self) -> List[Event]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
                SELECT 
                    e.start_time AS StartTime,
                    e.end_time AS EndTime,
                    e.description AS description
                FROM Event e
                JOIN Venue v ON e.venue_id = v.id
                JOIN StudentAttendance sa ON sa.event_id = e.id;
                ''')
                results = cursor.fetchall()
                return [Event(StartTime=str(r["StartTime"]), EndTime=str(r["EndTime"]), description=r["description"]) for r in results]
        finally:
            conn.close()

    @strawberry.field
    def event(self, event_id: int) -> List[EventDetail]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
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
                ''', (event_id,))
                results = cursor.fetchall()
                return [EventDetail(
                    StartTime=str(r["StartTime"]),
                    EndTime=str(r["EndTime"]),
                    studentId=r["studentId"],
                    VenueAdress=r["VenueAdress"],
                    description=r["description"]
                ) for r in results]
        finally:
            conn.close()

    @strawberry.field
    def camps(self) -> List[Camp]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
                SELECT 
                    c.id as CampNumber
                FROM Camp c
                JOIN event e ON e.id = c.id;
                ''')
                results = cursor.fetchall()
                return [Camp(**result) for result in results]
        finally:
            conn.close()

    @strawberry.field
    def camp(self, camp_id: int) -> List[CampDetail]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
                SELECT 
                    c.id as CampNumber,
                    e.start_time AS StartTime,
                    e.end_time AS EndTime,
                    e.description as description
                FROM Camp c
                JOIN Event e ON e.id = c.id
                WHERE c.id = %s;
                ''', (camp_id,))
                results = cursor.fetchall()
                return [CampDetail(
                    CampNumber=r["CampNumber"],
                    StartTime=str(r["StartTime"]),
                    EndTime=str(r["EndTime"]),
                    description=r["description"]
                ) for r in results]
        finally:
            conn.close()

    @strawberry.field
    def venues(self) -> List[Venue]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
                SELECT 
                    v.address as VenueAdress,
                    v.description AS description
                FROM Venue v;
                ''')
                results = cursor.fetchall()
                return [Venue(**result) for result in results]
        finally:
            conn.close()

    @strawberry.field
    def venue(self, venue_id: int) -> List[VenueDetail]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
                SELECT 
                    v.address as VenueAdress,
                    v.description AS description
                FROM Venue v
                JOIN Event e ON e.venue_id = v.id
                WHERE v.id = %s;
                ''', (venue_id,))
                results = cursor.fetchall()
                return [VenueDetail(**result) for result in results]
        finally:
            conn.close()

    @strawberry.field
    def camp_registration(self, camp_id: int) -> List[CampRegistration]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
                SELECT 
                    c.id AS campId,
                    i.amount AS AmountPaid,
                    e.description AS description,
                    v.address AS VenueAdress
                FROM CampRegistration cp
                JOIN Camp c ON cp.camp_id = c.id 
                JOIN Event e ON c.id = e.id
                JOIN Venue v ON e.venue_id = v.id 
                JOIN Invoice i ON cp.invoice_id = i.id
                WHERE c.id = %s;
                ''', (camp_id,))
                results = cursor.fetchall()
                return [CampRegistration(**result) for result in results]
        finally:
            conn.close()

    @strawberry.field
    def leader_small_group(self, leader_id: int) -> List[SmallGroupInfo]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
                SELECT  
                    sg.name AS small_group_name,
                    sg.meeting_time AS meeting_time,
                    CONCAT(s.first_name, ' ', s.last_name) AS student_name
                FROM Student s
                    JOIN SmallGroup sg ON sg.id = s.small_group_id
                    JOIN Leader l ON l.id = sg.leader_id
                WHERE l.id = %s;
                ''', (leader_id,))
                results = cursor.fetchall()
                return [SmallGroupInfo(
                    small_group_name=r["small_group_name"],
                    meeting_time=str(r["meeting_time"]),
                    student_name=r["student_name"]
                ) for r in results]
        finally:
            conn.close()

    @strawberry.field
    def event_attendance(self, event_id: int) -> List[EventAttendance]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
                SELECT 
                    e.id AS event_id,
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
                ''', (event_id,))
                results = cursor.fetchall()
                return [EventAttendance(
                    event_id=r["event_id"],
                    venue_id=r["venue_id"],
                    start_time=str(r["start_time"]),
                    end_time=str(r["end_time"]),
                    description=r["description"],
                    student_id=r["student_id"],
                    first_name=r["first_name"],
                    last_name=r["last_name"],
                    email=r["email"],
                    phone_number=r["phone_number"],
                    parent_id=r["parent_id"],
                    small_group_id=r["small_group_id"],
                    timestamp=str(r["timestamp"]),
                    note=r["note"] or ""
                ) for r in results]
        finally:
            conn.close()

    @strawberry.field
    def camp_registration_student(self, student_id: int) -> List[CampRegistrationDetail]:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
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
                return [CampRegistrationDetail(
                    student_name=r["student_name"],
                    campId=r["campId"],
                    registered_time=str(r["registered_time"]),
                    amount_paid=r["amount_paid"],
                    parent_name=r["parent_name"],
                    description=r["description"],
                    venue_address=r["venue_address"]
                ) for r in results]
        finally:
            conn.close()

    @strawberry.field
    def redis_event_registration(self, event_id: int) -> RedisEventRegistrationResponse:
        redis_conn = get_redis_conn()
        try:
            student_keys = redis_conn.smembers(f"event:{event_id}:students")
            
            if not student_keys:
                return RedisEventRegistrationResponse(
                    event_id=event_id,
                    count=0,
                    registrations=[],
                    message="No event registration data found in Redis",
                    success=False
                )

            registrations = []
            for key in student_keys:
                key = key.decode() if isinstance(key, bytes) else key
                raw_data = redis_conn.hgetall(key)
                
                formatted_data = {
                    k.decode() if isinstance(k, bytes) else k:
                    v.decode() if isinstance(v, bytes) else v
                    for k, v in raw_data.items()
                }
                
                for numeric_field in ["event_id", "venue_id", "student_id", "parent_id", "small_group_id"]:
                    if numeric_field in formatted_data and formatted_data[numeric_field].isdigit():
                        formatted_data[numeric_field] = int(formatted_data[numeric_field])

                registration = RedisEventRegistration(
                    event_id=int(formatted_data.get("event_id", 0)),
                    venue_id=int(formatted_data.get("venue_id", 0)),
                    start_time=formatted_data.get("start_time", ""),
                    end_time=formatted_data.get("end_time", ""),
                    description=formatted_data.get("description", ""),
                    student_id=int(formatted_data.get("student_id", 0)),
                    first_name=formatted_data.get("first_name", ""),
                    last_name=formatted_data.get("last_name", ""),
                    email=formatted_data.get("email", ""),
                    phone_number=formatted_data.get("phone_number", ""),
                    parent_id=int(formatted_data.get("parent_id", 0)),
                    small_group_id=int(formatted_data.get("small_group_id", 0)),
                    timestamp=formatted_data.get("timestamp", ""),
                    note=formatted_data.get("note", "")
                )
                registrations.append(registration)  # ✅ This is a RedisEventRegistration object

            return RedisEventRegistrationResponse(
                event_id=event_id,
                count=len(registrations),
                registrations=registrations,
                success=True
            )
        finally:
            redis_conn.close()

@strawberry.type
class Mutation:
    @strawberry.field
    def update_student(self, student_id: int, input: StudentUpdateInput) -> str:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
                UPDATE Student
                    SET email = %s, 
                        phone_number = %s, 
                        note = %s
                WHERE id = %s;
                ''', (input.email, input.phone_number, input.note, student_id))
                conn.commit()
                if cursor.rowcount == 0:
                    return "Student not found"
                return "Student updated successfully"
        finally:
            conn.close()

    @strawberry.field
    def delete_student(self, student_id: int) -> str:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('DELETE FROM Student WHERE id = %s;', (student_id,))
                conn.commit()
                if cursor.rowcount == 0:
                    return "Student not found"
                return "Student deleted successfully"
        finally:
            conn.close()

    @strawberry.field
    def update_parent(self, parent_id: int, input: ParentUpdateInput) -> str:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
                UPDATE Parent
                    SET email = %s, phone_number = %s, note = %s
                WHERE id = %s;
                ''', (input.email, input.phone_number, input.note, parent_id))
                conn.commit()
                if cursor.rowcount == 0:
                    return "Parent not found"
                return "Parent updated successfully"
        finally:
            conn.close()

    @strawberry.field
    def delete_parent(self, parent_id: int) -> str:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('DELETE FROM Parent WHERE id = %s;', (parent_id,))
                conn.commit()
                if cursor.rowcount == 0:
                    return "Parent not found"
                return "Parent deleted successfully"
        finally:
            conn.close()

    @strawberry.field
    def update_leader(self, leader_id: int, input: LeaderUpdateInput) -> str:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
                UPDATE Leader
                    SET email = %s, phone_number = %s, note = %s, date_joined = %s, salary = %s
                WHERE id = %s;
                ''', (input.email, input.phone_number, input.note, input.datejoined, input.salary, leader_id))
                conn.commit()
                if cursor.rowcount == 0:
                    return "Leader not found"
                return "Leader updated successfully"
        finally:
            conn.close()

    @strawberry.field
    def delete_leader(self, leader_id: int) -> str:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('DELETE FROM Leader WHERE id = %s;', (leader_id,))
                conn.commit()
                if cursor.rowcount == 0:
                    return "Leader not found"
                return "Leader deleted successfully"
        finally:
            conn.close()

    @strawberry.field
    def update_event(self, event_id: int, input: EventUpdateInput) -> str:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("USE YouthGroup;")
                cursor.execute('''
                UPDATE Event
                SET description = %s, start_time = %s, end_time = %s
                WHERE id = %s;
                ''', (input.description, input.start_time, input.end_time, event_id))
                conn.commit()
                if cursor.rowcount == 0:
                    return "Event not found"
                return "Event updated successfully"
        finally:
            conn.close()

    @strawberry.field
    def delete_event(self, event_id: int) -> str:
        conn = get_mysql_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("USE YouthGroup;")
                cursor.execute("DELETE FROM StudentAttendance WHERE event_id = %s;", (event_id,))
                cursor.execute("DELETE FROM Event WHERE id = %s;", (event_id,))
                conn.commit()
                if cursor.rowcount == 0:
                    return "Event not found"
                return "Event deleted successfully"
        finally:
            conn.close()

    @strawberry.field
    def load_redis_event_registration(self, event_id: int) -> str:
        redis_conn = get_redis_conn()
        mysql_conn = get_mysql_conn()
        try:
            if redis_conn.exists(f"event:{event_id}:students") == 1:
                return f"Data for event {event_id} already exists in Redis"

            with mysql_conn.cursor() as cursor:
                cursor.execute('USE YouthGroup;')
                cursor.execute('''
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
                ''', (event_id,))
                results = cursor.fetchall()

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

                redis_conn.hset(key, mapping=redis_data)
                redis_conn.expire(key, 86400)
                redis_conn.sadd(f"event:{event_id}:students", key)
                redis_conn.expire(f"event:{event_id}:students", 86400)

            return f"Event registration data loaded into Redis for event {event_id}. Count: {len(results)}"
        finally:
            redis_conn.close()
            mysql_conn.close()

    @strawberry.field
    def update_redis_event_registration(self, event_id: int) -> str:
        redis_conn = get_redis_conn()
        mysql_conn = get_mysql_conn()
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("USE YouthGroup;")
                cursor.execute('''
                SELECT 
                    e.id AS event_id,
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
                WHERE e.id = %s;
                ''', (event_id,))
                results = cursor.fetchall()

            old_keys = redis_conn.smembers(f"event:{event_id}:students")
            if old_keys:
                redis_conn.delete(*old_keys)
            redis_conn.delete(f"event:{event_id}:students")

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

                redis_conn.hset(key, mapping=redis_data)
                redis_conn.expire(key, 86400)
                redis_conn.sadd(f"event:{event_id}:students", key)
                redis_conn.expire(f"event:{event_id}:students", 86400)

            return f"Redis cache updated for event {event_id}. Count: {len(results)}"
        finally:
            redis_conn.close()
            mysql_conn.close()

    @strawberry.field
    def delete_redis_event_registration(self, event_id: int) -> str:
        redis_conn = get_redis_conn()
        try:
            student_keys = redis_conn.smembers(f"event:{event_id}:students")
            deleted_count = 0

            if student_keys:
                decoded_keys = [k.decode() if isinstance(k, bytes) else k for k in student_keys]
                redis_conn.delete(*decoded_keys)
                deleted_count = len(decoded_keys)

            redis_conn.delete(f"event:{event_id}:students")
            return f"Redis event {event_id} data deleted. Deleted records: {deleted_count}"
        finally:
            redis_conn.close()

    @strawberry.field
    def create_mongo_event(self, input: EventCreateInput) -> str:
        mysql_conn = get_mysql_conn()
        mongo_client = get_mongo_conn()
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute('''
                INSERT INTO Event (venue_id, start_time, end_time, description)
                VALUES (%s, %s, %s, %s);
                ''', (input.venue_id, input.start_time, input.end_time, input.description))
                mysql_conn.commit()
                event_id = cursor.lastrowid

            db = mongo_client['YouthGroup']
            collection = db['event_custom_values']
            collection.insert_one({
                'event_id': event_id,
                'custom_fields': input.custom_fields or {},
            })

            return f"Event created with ID: {event_id}"
        finally:
            mysql_conn.close()
            mongo_client.close()

    @strawberry.field
    def create_mongo_camp(self, input: CampCreateInput) -> str:
        mysql_conn = get_mysql_conn()
        mongo_client = get_mongo_conn()
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute('''
                INSERT INTO Event (venue_id, start_time, end_time, description)
                VALUES (%s, %s, %s, %s);
                ''', (input.venue_id, input.start_time, input.end_time, input.description))
                mysql_conn.commit()
                event_id = cursor.lastrowid
                
                cursor.execute('''
                INSERT INTO CAMP (camp_id, event_id)
                VALUES (NULL, %s);
                ''', (event_id,))
                mysql_conn.commit()
                camp_id = cursor.lastrowid

            db = mongo_client['YouthGroup']
            collection = db['camp_custom_values']
            collection.insert_one({
                'camp_id': camp_id,
                'event_id': event_id,
                'custom_fields': input.custom_fields or {},
            })

            return f"Camp created with camp_id: {camp_id}, event_id: {event_id}"
        finally:
            mysql_conn.close()
            mongo_client.close()

schema = strawberry.Schema(query=Query, mutation=Mutation)