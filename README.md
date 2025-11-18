## CS-125-Final-Project

## Prerequsite 

Who’s using this?
- Leaders: Administration (distinguish roles) 

What do they want to do?
- Take attendance 
- Finances (who has paid for ...)
- Registration

What should they be able to do? 
- Take attendance 
- Finances (who has paid for ...)
- Registration: names, emails, phone numbers, parents 
- Description of youth members
- Keep track of students, leaders and volunteers

Assumptions: - We only record one parent per each student, event refers to every event that happens at the Church while camp means every event that happens outdoor 
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


