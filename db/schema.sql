# FAKE DATA

CREATE DATABASE IF NOT EXISTS YouthGroup;
USE YouthGroup;


CREATE TABLE camp (
    id INTEGER PRIMARY KEY,
    FOREIGN KEY id REFERENCES event(id)

);

CREATE TABLE campRegistration (
    id INTEGER PRIMARY KEY,
    campId INTEGER,
    studentId INT NOT NULL,
    timestamp TIMESTAMP,
    invoiceId INT NOT NULL UNIQUE,
    FOREIGN KEY campId REFERENCES camp(id),
    FOREIGN KEY invoiceid REFERENCES invoice(id),
    FOREIGN KEY  studentid REFERENCES student(id)
);

CREATE TABLE invoice (
    id INTEGER PRIMARY KEY,
    parentId INTEGER,
    timestamp TIMESTAMP,
    amount INTEGER,
    studentId INT,
    FOREIGN KEY studentid REFERENCES student(id),
    FOREIGN KEY parentid REFERENCES parent(id)
);

CREATE TABLE student (
    id INTEGER PRIMARY KEY,
    parentId INTEGER NOT NULL,
    smallGroupId INTEGER,
    Note VARCHAR(255),
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    email VARCHAR(50) UNIQUE,
    phoneNumber VARCHAR(10) NOT NULL,
    FOREIGN KEY parentid REFERENCES parent(id),
    FOREIGN KEY smallGroupId REFERENCES smallGroup(id)

);

CREATE TABLE parent (
    id INTEGER PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    email VARCHAR(50),
    phoneNumber VARCHAR(10) NOT NULL,
    Note VARCHAR(255)
);

CREATE TABLE studentAttendance (
    studentId INTEGER,
    eventId INTEGER,
    Timestamp TIMESTAMP,
    FOREIGN KEY studentId references student(id),
    FOREIGN KEY eventId references event(id),
    PRIMARY KEY (studentId, eventId)

);

CREATE TABLE smallGroup (
    id INTEGER PRIMARY KEY,
    Name VARCHAR(100) NOT NULL UNIQUE,
    LeaderId Integer NOT NULL,
    meetingTime TIMESTAMP,
    FOREIGN KEY LeaderId REFERENCES Leader(id)
);

CREATE TABLE Leader (
    id INTEGER PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    email VARCHAR(50),
    phoneNumber VARCHAR(10) NOT NULL,
    Note VARCHAR(255),
    dateJoined DATE,
    Salary INTEGER,
    foreign key roleId REFERENCES Role(id)


);

CREATE TABLE LeaderRole (
    LeaderId INTEGER,
    RoleId INTEGER,
    FOREIGN KEY LeaderId references Leader(id),
    FOREIGN KEY RoleId references Role(id),
    PRIMARY KEY (LeaderId, RoleId)

);

CREATE TABLE Role (
    id INTEGER PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    Description VARCHAR(100)
);

CREATE TABLE LeaderShift (
    leaderId INTEGER,
    shiftId INTEGER,
    FOREIGN KEY leaderId REFERENCES Leader(id),
    FOREIGN KEY shiftId REFERENCES shift(id),
    PRIMARY KEY (leaderId, shiftId)
);

CREATE TABLE shift (
    id INTEGER PRIMARY KEY,
    startTime DATETIME,
    endTime DATETIME

);

CREATE TABLE venue (
    id INTEGER PRIMARY KEY,
    address VARCHAR(100),
    description VARCHAR(150)
);

CREATE TABLE event (
    id INTEGER PRIMARY KEY,
    venueId INTEGER,
    startTime DATETIME,
    endTime DATETIME,
    Description VARCHAR(256),
    FOREIGN KEY venueId REFERENCES venue(id)
);

