## CS-125-Final-Project

## Prerequsite 

Who’s using this?
- Leaders: Administration (distinguish roles) 

What do they want to do?
- Take attendance 
- Finances (who has paid for ...)
- Registration for several events 
- Leaders are able to access their shifts 
- The database should display event information 

What should they be able to do? 
- Take attendance 
- Finances (who has paid for ...)
- Registration: names, emails, phone numbers, parents 
- Description of youth members
- Keep track of students, leaders and volunteers

Assumptions: - We only record one parent per each student

What shouldn’t they do?


What’s your team’s name? 
Nice Will 

Create the repository ✅


## Goals 
1. Conceptual Design
2. Logical design 
3. BackEnd
4. FrontEnd 
5. Full stack

---

## Setup
To set docker services run this command:

> NOTE: ensure docker desktop is installed on your computer

```bash
chmod +x build-services.sh && ./build-services.sh
```

---
## Infra

- All docker containers are managed under docker compose.


```
            +-----------------------------+
            |        Docker Host          |
            |   (compose / single stack)  |
            +-----------------------------+
                        |
                        v
+--------------------------------------------------+
|            Docker Container Stack                |
| (All containers managed together via compose)    |
|                                                  |
|  +-----------+    +-----------+    +-----------+ |
|  |  redis    |    | mongodb   |    |  mysql    | |
|  | 6379      |    | 27017     |    | 3306      | |
|  +-----------+    +-----------+    +-----------+ |
|                                                  |
|                 +------------------+             |           
|                 |   python api     |             |           
|                 |  FastAPI +       |             |           
|                 |  Strawberry GQL  |             | /graphql  
|                 |  exposes:        | <------------------------->      
|                 |   /graphql       |             |
|                 +------------------+             |
|                                                  |
+--------------------------------------------------+
```

## Files Infrastructure  

Our file contains two directories: Backend and Db 

# Backend
This directory contains all the fields necessary for the backend knowledge. It holds the 
logic that makes fetching, writing, reading, modifying and all other functionalities possible. Here are the files in the backend:

- Main.py: Implements all the Mongo, Redis and Mysql's get, update and delete endpoints that makes fetching, updating and deleting information in the 
database possible. In total, it has 52 endpoints.

- Dockerfile: Implements the docker containers by setting the work directory, installing dependencies, and running the API server. 

- Requirements.txt: Serves as a standardized way to declare and manage the external packages and their 
versions that this whole project depends on.

- App_graphql: Contains schema.sql which is a GraphQl layer that sits on top og all the databases Mongo, Redis and MySql. The file defines the data types, displays how the data is supposed to be fetched, 
shows how to write/modify data through mutations in 'Post/Put/Delete' requests and clarifies what data the client needs to send. 

# Db 
This directory has the visual ER diagram implemented, and also contains the fake data that was generated with the help of CHATGPT. 

# Front End 
