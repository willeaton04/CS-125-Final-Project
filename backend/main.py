'''
@author Will Eaton, Nice Hirwa

builds entrypoint for graphql using FastAPI
'''

from fastapi import FastAPI
import pymysql
import redis
from pymongo import MongoClient
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
def root():
    return {'message': 'Service is running'}


