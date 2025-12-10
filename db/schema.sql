
DROP DATABASE IF EXISTS YouthGroup;
CREATE DATABASE IF NOT EXISTS YouthGroup;
USE YouthGroup;


CREATE TABLE Role (
    id SMALLINT UNSIGNED PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description VARCHAR(100)
);

CREATE TABLE Shift (
    id SMALLINT UNSIGNED PRIMARY KEY,
    start_time DATETIME,
    end_time DATETIME
);

CREATE TABLE Leader (
    id SMALLINT UNSIGNED PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(50),
    phone_number VARCHAR(10) NOT NULL,
    note VARCHAR(255),
    date_joined DATE,
    salary SMALLINT UNSIGNED,
    role_id SMALLINT UNSIGNED NOT NULL,
    FOREIGN KEY (role_id) REFERENCES Role(id)
);

CREATE TABLE SmallGroup (
    id SMALLINT UNSIGNED PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    leader_id SMALLINT UNSIGNED,
    meeting_time TIMESTAMP,
    FOREIGN KEY (leader_id) REFERENCES Leader(id) ON DELETE SET NULL
);

CREATE TABLE Parent (
    id SMALLINT UNSIGNED PRIMARY KEY ,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(50),
    phone_number VARCHAR(10) NOT NULL,
    note VARCHAR(255)
);

CREATE TABLE Student (
    id SMALLINT UNSIGNED PRIMARY KEY ,
    parent_id SMALLINT UNSIGNED,
    small_group_id SMALLINT UNSIGNED,
    note VARCHAR(255),
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(50) UNIQUE,
    phone_number VARCHAR(10) NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES Parent(id) ON DELETE SET NULL,
    FOREIGN KEY (small_group_id) REFERENCES SmallGroup(id)
);

CREATE TABLE Venue (
    id SMALLINT UNSIGNED PRIMARY KEY,
    address VARCHAR(100),
    description VARCHAR(150)
);

CREATE TABLE Event (
    id SMALLINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    venue_id SMALLINT UNSIGNED,
    start_time DATETIME,
    end_time DATETIME,
    description VARCHAR(256),
    FOREIGN KEY (venue_id) REFERENCES Venue(id)
);

CREATE TABLE Camp (
    id SMALLINT UNSIGNED PRIMARY KEY,
    FOREIGN KEY (id) REFERENCES Event(id)
);

CREATE TABLE Invoice (
    id SMALLINT UNSIGNED PRIMARY KEY ,
    parent_id SMALLINT UNSIGNED NOT NULL,
    timestamp TIMESTAMP,
    amount SMALLINT UNSIGNED,
    student_id SMALLINT UNSIGNED NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Student(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES Parent(id) ON DELETE CASCADE
);

CREATE TABLE CampRegistration (
    id SMALLINT UNSIGNED PRIMARY KEY ,
    camp_id SMALLINT UNSIGNED,
    student_id SMALLINT UNSIGNED NOT NULL,
    timestamp TIMESTAMP,
    invoice_id SMALLINT UNSIGNED NOT NULL UNIQUE,
    FOREIGN KEY (camp_id) REFERENCES Camp(id),
    FOREIGN KEY (invoice_id) REFERENCES Invoice(id) ON DELETE CASCADE ,
    FOREIGN KEY  (student_id) REFERENCES Student(id) ON DELETE CASCADE
);

CREATE TABLE StudentAttendance (
    student_id SMALLINT UNSIGNED,
    event_id SMALLINT UNSIGNED,
    timestamp TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Student(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES Event(id),
    PRIMARY KEY (student_id, event_id)
);

CREATE TABLE LeaderRole (
    leader_id SMALLINT UNSIGNED,
    role_id SMALLINT UNSIGNED,
    FOREIGN KEY (leader_id) REFERENCES Leader(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) references Role(id),
    PRIMARY KEY (leader_id, role_id)
);

CREATE TABLE LeaderShift (
    leader_id SMALLINT UNSIGNED,
    shift_id SMALLINT UNSIGNED,
    FOREIGN KEY (leader_id) REFERENCES Leader(id) ON DELETE CASCADE,
    FOREIGN KEY (shift_id) REFERENCES Shift(id),
    PRIMARY KEY (leader_id, shift_id)
);