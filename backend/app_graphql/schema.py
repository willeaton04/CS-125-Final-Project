'''
@author Will Eaton
'''

import strawberry
import os
import pymysql
import redis
from pymongo import MongoClient

# DB helper methods

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


# GraphQL Schema
@strawberry.type
class Query:
    hello: str='Hello!'

    @strawberry.field
    def mysql_test(self) -> list[str]:
        conn = get_mysql_conn()
        with conn.cursor() as cur:
            cur.execute('SHOW DATABASES;')
            rows = cur.fetchall()

        return [row['Database'] for row in rows]

    @strawberry.field
    def redis_test(self) -> str | None:
        '''
        tests conn with redis
        '''
        r = get_redis_conn()
        r.set('demo', 'Redis is working!')
        return r.get('demo')

    @strawberry.field
    def mongo_test(self) -> list[str]:
        '''
        Tests conn with MongoDB
        '''
        db = get_mongo_conn()
        db.test_collection.insert_one({'name': 'Mongo works!'})
        return [d['name'] for d in db.test_collection.find()]


schema = strawberry.Schema(
    query=Query,
)