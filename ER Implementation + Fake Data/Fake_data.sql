# FAKE DATA

USE YouthGroup;
ALTER TABLE Event AUTO_INCREMENT = 1; # Prevents event from entering weird autoincrement

-- Parents (10)
INSERT INTO Parent (id, first_name, last_name, email, phone_number, note) VALUES
(1, 'Karen', 'Mitchell', 'karen.mitchell@example.com', '5551000001', 'Allergies: peanuts'),
(2, 'James', 'Rodriguez', 'james.rodriguez@example.com', '5551000002', ''),
(3, 'Sofia', 'Nguyen', 'sofia.nguyen@example.com', '5551000003', 'Emergency contact: aunt Elaine'),
(4, 'Ethan', 'Brown', 'ethan.brown@example.com', '5551000004', ''),
(5, 'Maria', 'Garcia', 'maria.garcia@example.com', '5551000005', ''),
(6, 'Oliver', 'Johnson', 'oliver.johnson@example.com', '5551000006', ''),
(7, 'Ava', 'Davis', 'ava.davis@example.com', '5551000007', ''),
(8, 'Liam', 'Martinez', 'liam.martinez@example.com', '5551000008', ''),
(9, 'Emma', 'Wilson', 'emma.wilson@example.com', '5551000009', ''),
(10, 'Noah', 'Anderson', 'noah.anderson@example.com', '5551000010', '');

-- Roles (4)
INSERT INTO Role (id, title, description) VALUES
(1, 'Lead Pastor', 'Senior leader'),
(2, 'Small Group Leader', 'Leads a small group'),
(3, 'Volunteer', 'Event volunteer'),
(4, 'Camp Coordinator', 'Coordinates camps');

-- Leaders (5)
-- Note: schema did not declare roleId column explicitly, so we only insert declared columns.
INSERT INTO Leader (id, first_name, last_name, email, phone_number, note, date_joined, salary, role_id) VALUES
(1, 'Will', 'Eaton', 'will.eaton@example.com', '5552000001', 'Head of youth ministry', '2019-08-01', 45000, 3),
(2, 'Nice', 'Hirwa', 'nice.hirwa@example.com', '5552000002', 'Student ministry coordinator', '2021-01-15', 30000, 4),
(3, 'Grace', 'Kim', 'grace.kim@example.com', '5552000003', '', '2020-06-10', 0, 1),
(4, 'Ben', 'Lopez', 'ben.lopez@example.com', '5552000004', 'Background checked', '2022-03-20', 0, 2),
(5, 'Hannah', 'Park', 'hannah.park@example.com', '5552000005', '', '2023-09-01', 0, 3);

-- Venues (3)
INSERT INTO Venue (id, address, description) VALUES
(1, '100 Church St', 'Main Sanctuary'),
(2, '200 Fellowship Rd', 'Fellowship Hall'),
(3, '150 Youth Ln', 'Youth Room / Basement');

-- Events (8)
INSERT INTO Event (venue_id, start_time, end_time, description) VALUES
( 1, '2025-06-01 18:00:00', '2025-06-01 20:00:00', 'Weekly Youth Gathering'),
(2, '2025-06-08 18:00:00', '2025-06-08 20:00:00', 'Service Night'),
( 3, '2025-06-15 09:00:00', '2025-06-15 16:00:00', 'Day Retreat'),
(1, '2025-07-01 09:00:00', '2025-07-01 17:00:00', 'Summer Kickoff'),
( 2, '2025-07-15 18:00:00', '2025-07-15 21:00:00', 'Volunteer Training'),
( 3, '2025-08-01 08:00:00', '2025-08-07 17:00:00', 'Camp: Wilderness Adventure (week)'),
( 3, '2025-08-10 08:00:00', '2025-08-12 17:00:00', 'Camp: Lakeside Weekend'),
( 3, '2025-12-20 18:00:00', '2025-12-20 21:00:00', 'Christmas Youth Party');

-- Camps (3) — camp.id MUST equal an event.id (camp is a subtype of event)
INSERT INTO Camp (id) VALUES
(6),
(7),
(8);

-- Small groups (5) — reference existing leaders
INSERT INTO SmallGroup (id, name, leader_id, meeting_time) VALUES
(1, 'Alpha Group', 2, '2025-06-03 19:00:00'),
(2, 'Beta Group', 3, '2025-06-04 19:30:00'),
(3, 'Gamma Group', 4, '2025-06-05 18:30:00'),
(4, 'Delta Group', 5, '2025-06-06 19:00:00'),
(5, 'Epsilon Group', 1, '2025-06-07 19:00:00');

-- Students (20) — each student has a parentId and optionally smallGroupId
INSERT INTO Student (id, parent_id, small_group_id, note, first_name, last_name, email, phone_number) VALUES
(1, 1, 1, '', 'Aiden', 'Mitchell', 'aiden.mitchell@example.com', '5553000001'),
(2, 1, 1, '', 'Lily', 'Mitchell', 'lily.mitchell@example.com', '5553000002'),
(3, 2, 2, 'Needs asthma inhaler', 'Jacob', 'Rodriguez', 'jacob.rodriguez@example.com', '5553000003'),
(4, 2, 2, '', 'Samantha', 'Rodriguez', 'samantha.rodriguez@example.com', '5553000004'),
(5, 3, 3, '', 'Noah', 'Nguyen', 'noah.nguyen@example.com', '5553000005'),
(6, 3, 3, '', 'Chloe', 'Nguyen', 'chloe.nguyen@example.com', '5553000006'),
(7, 4, 4, '', 'Mason', 'Brown', 'mason.brown@example.com', '5553000007'),
(8, 4, 4, '', 'Zoe', 'Brown', 'zoe.brown@example.com', '5553000008'),
(9, 5, 5, '', 'Lucas', 'Garcia', 'lucas.garcia@example.com', '5553000009'),
(10, 5, 5, '', 'Maya', 'Garcia', 'maya.garcia@example.com', '5553000010'),
(11, 6, 1, '', 'Evelyn', 'Johnson', 'evelyn.johnson@example.com', '5553000011'),
(12, 6, 2, '', 'Logan', 'Johnson', 'logan.johnson@example.com', '5553000012'),
(13, 7, 3, '', 'Isabella', 'Davis', 'isabella.davis@example.com', '5553000013'),
(14, 7, 3, '', 'Ethan', 'Davis', 'ethan.davis@example.com', '5553000014'),
(15, 8, 4, '', 'Harper', 'Martinez', 'harper.martinez@example.com', '5553000015'),
(16, 8, 4, '', 'Owen', 'Martinez', 'owen.martinez@example.com', '5553000016'),
(17, 9, 5, '', 'Abigail', 'Wilson', 'abigail.wilson@example.com', '5553000017'),
(18, 9, 5, '', 'Henry', 'Wilson', 'henry.wilson@example.com', '5553000018'),
(19, 10, 1, '', 'Ella', 'Anderson', 'ella.anderson@example.com', '5553000019'),
(20, 10, 2, '', 'James', 'Anderson', 'james.anderson@example.com', '5553000020');

-- Invoices (20) — reference parent and optionally student
-- We create one invoice per camp registration; ids 1..20 to be used by campRegistration.invoiceId
INSERT INTO Invoice (id, parent_id, timestamp, amount, student_id) VALUES
(1, 1, '2025-05-01 09:00:00', 200, 1),
(2, 1, '2025-05-01 09:05:00', 200, 2),
(3, 2, '2025-05-02 10:00:00', 220, 3),
(4, 2, '2025-05-02 10:05:00', 220, 4),
(5, 3, '2025-05-03 11:00:00', 250, 5),
(6, 3, '2025-05-03 11:05:00', 250, 6),
(7, 4, '2025-05-04 12:00:00', 180, 7),
(8, 4, '2025-05-04 12:05:00', 180, 8),
(9, 5, '2025-05-05 13:00:00', 210, 9),
(10, 5, '2025-05-05 13:05:00', 210, 10),
(11, 6, '2025-05-06 14:00:00', 230, 11),
(12, 6, '2025-05-06 14:05:00', 230, 12),
(13, 7, '2025-05-07 15:00:00', 190, 13),
(14, 7, '2025-05-07 15:05:00', 190, 14),
(15, 8, '2025-05-08 16:00:00', 210, 15),
(16, 8, '2025-05-08 16:05:00', 210, 16),
(17, 9, '2025-05-09 17:00:00', 220, 17),
(18, 9, '2025-05-09 17:05:00', 220, 18),
(19, 10, '2025-05-10 18:00:00', 200, 19),
(20, 10, '2025-05-10 18:05:00', 200, 20);

-- Camp Registrations (20) — each references campId (6,7,8), studentId, invoiceId
INSERT INTO CampRegistration (id, camp_id, student_id, timestamp, invoice_id) VALUES
(1, 6, 1, '2025-05-01 09:10:00', 1),
(2, 6, 2, '2025-05-01 09:12:00', 2),
(3, 6, 3, '2025-05-02 10:10:00', 3),
(4, 6, 4, '2025-05-02 10:12:00', 4),
(5, 7, 5, '2025-05-03 11:10:00', 5),
(6, 7, 6, '2025-05-03 11:12:00', 6),
(7, 7, 7, '2025-05-04 12:10:00', 7),
(8, 7, 8, '2025-05-04 12:12:00', 8),
(9, 8, 9, '2025-05-05 13:10:00', 9),
(10, 8, 10, '2025-05-05 13:12:00', 10),
(11, 6, 11, '2025-05-06 14:10:00', 11),
(12, 6, 12, '2025-05-06 14:12:00', 12),
(13, 7, 13, '2025-05-07 15:10:00', 13),
(14, 7, 14, '2025-05-07 15:12:00', 14),
(15, 8, 15, '2025-05-08 16:10:00', 15),
(16, 8, 16, '2025-05-08 16:12:00', 16),
(17, 6, 17, '2025-05-09 17:10:00', 17),
(18, 6, 18, '2025-05-09 17:12:00', 18),
(19, 7, 19, '2025-05-10 18:10:00', 19),
(20, 7, 20, '2025-05-10 18:12:00', 20);

-- Shifts (4)
INSERT INTO Shift (id, start_time, end_time) VALUES
(1, '2025-06-01 17:00:00', '2025-06-01 21:00:00'),
(2, '2025-06-08 17:00:00', '2025-06-08 21:00:00'),
(3, '2025-07-01 08:00:00', '2025-07-01 18:00:00'),
(4, '2025-08-01 07:00:00', '2025-08-07 19:00:00');

-- LeaderShift assignments
INSERT INTO LeaderShift (leader_id, shift_id) VALUES
(1, 3),
(2, 1),
(2, 4),
(3, 2),
(4, 1),
(5, 2);

-- LeaderRole (many-to-many)
INSERT INTO LeaderRole (leader_id, role_id) VALUES
(1, 1),
(1, 4),
(2, 4),
(2, 2),
(3, 2),
(4, 3),
(5, 3);

-- Student Attendance (some students attend various events)
INSERT INTO StudentAttendance (student_id, event_id, timestamp) VALUES
(1, 1, '2025-06-01 18:00:00'),
(2, 1, '2025-06-01 18:00:00'),
(3, 2, '2025-06-08 18:00:00'),
(4, 2, '2025-06-08 18:00:00'),
(5, 3, '2025-06-15 09:00:00'),
(6, 3, '2025-06-15 09:00:00'),
(7, 4, '2025-07-01 09:00:00'),
(8, 4, '2025-07-01 09:00:00'),
(9, 5, '2025-07-15 18:00:00'),
(10, 5, '2025-07-15 18:00:00'),
(11, 6, '2025-08-01 08:00:00'),
(12, 6, '2025-08-01 08:00:00'),
(13, 7, '2025-08-10 08:00:00'),
(14, 7, '2025-08-10 08:00:00'),
(15, 8, '2025-12-20 18:00:00'),
(16, 8, '2025-12-20 18:00:00'),
(17, 1, '2025-06-01 18:00:00'),
(18, 2, '2025-06-08 18:00:00'),
(19, 4, '2025-07-01 09:00:00'),
(20, 5, '2025-07-15 18:00:00');