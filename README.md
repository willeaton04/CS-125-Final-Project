# CS-125-Final-Project

# Prerequsite 

Who’s using this?
- Leaders: Administration (distinguish roles) 

What do they want to do?
- View students or members of the Youth group, leaders of small groups and parents 
- Create/Update registration for several events 
- Leaders are able to access their shifts in a nicely crafted calendar
- The database should display event information 

What should they be able to do? 
- Search / display information of students, leaders and parents 
- Registration: names, emails, phone numbers 
- Description of youth members
- Keep track of leaders, and volunteers

Assumptions: - We only record one parent per each student

# Team Name
Nice Will 


# Goals 
1. Conceptual Design
2. Logical design 
3. BackEnd
4. FrontEnd 
5. Full stack

---

# Setup
To set docker services run this command:

> NOTE: ensure docker desktop is installed on your computer

```bash
chmod +x build-services.sh && ./build-services.sh
```

This sets up the entire project locally :)

---
# Infra

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

# Detailed File Infrastructure  

Our file contains two directories: Backend and Db 

## Backend
This directory contains all the fields necessary for the backend knowledge. It holds the 
logic that makes fetching, writing, reading, modifying and all other functionalities possible. Here are the files in the backend:

- Main.py: Implements all the Mongo, Redis and Mysql's get, update and delete endpoints that makes fetching, updating and deleting information in the 
database possible. In total, it has 52 endpoints. Want to know which ones? Quickly rush to our main.py file 

- Dockerfile: Implements the docker containers by setting the work directory, installing dependencies, and running the API server. 

- Requirements.txt: Serves as a standardized way to declare and manage the external packages and their 
versions that this whole project depends on.

- App_graphql: Contains schema.sql which is a GraphQl layer that sits on top of all the databases Mongo, Redis and MySql. The file is divided into three main sections:
1. Strawberry types: It defines the data types within each entity which makes it easy for the users to know which type is which event. 
2. Queries: These functions are responsible for displaying the data like 'show me all students' or 'Find student #10'. It is done by hitting my sql 
, get all students and then returning them.
3. Mutations: Responsible for updating and deleting any data which makes our UI/UX so easy to do such a thing. After deleting, it does a good job of sending the notification that a particular
field was deleted or updated. 
 

# Db 
This directory has the visual ER diagram implemented, and also contains the fake data that was generated with the help of CHATGPT. 

# Front End 
The Front end folder holds an index.html that was vibe coded by Gemini, and of course we had to make some changes to make the front end look prettier and very aesthetic. 

# How do I run the front end?
Go into index.html and click on the google chrome or firefox icon you would want to view our front end in. Make sure your docker is running in the backend so it would be eays to pull, fetch and basically have fun with our front end. 


