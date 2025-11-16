'''
@author Will Eaton

builds entrypoint for graphql using FastAPI
'''

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from app_graphql.schema import schema

app = FastAPI()

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
def root():
    return {"message": "GraphQL running at /graphql"}
