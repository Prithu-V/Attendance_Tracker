-- Fake test data: 12 students, 8 past sessions, 1 session open right now.
INSERT INTO student (name, roll_no, email) VALUES
 ('Aarav Sharma',  'CS001', 'aarav@example.edu'),
 ('Diya Patel',    'CS002', 'diya@example.edu'),
 ('Kabir Singh',   'CS003', 'kabir@example.edu'),
 ('Ananya Iyer',   'CS004', 'ananya@example.edu'),
 ('Rohan Mehta',   'CS005', 'rohan@example.edu'),
 ('Ishita Rao',    'CS006', 'ishita@example.edu'),
 ('Vihaan Gupta',  'CS007', 'vihaan@example.edu'),
 ('Meera Nair',    'CS008', 'meera@example.edu'),
 ('Arjun Reddy',   'CS009', 'arjun@example.edu'),
 ('Saanvi Joshi',  'CS010', 'saanvi@example.edu'),
 ('Kiran Das',     'CS011', 'kiran@example.edu'),
 ('Tara Menon',    'CS012', 'tara@example.edu');

INSERT INTO sessions (session_name, start_time, end_time, token)
SELECT 'Lecture ' || n,
       date_trunc('hour', now()) - make_interval(days => (9 - n) * 3),
       date_trunc('hour', now()) - make_interval(days => (9 - n) * 3) + interval '1 hour',
       'seedtoken' || n
FROM generate_series(1, 8) AS n;

-- Currently open session (use token=seedopen to test the student page)
INSERT INTO sessions (session_name, start_time, end_time, token)
VALUES ('Lecture 9 (open)', now() - interval '10 minutes', now() + interval '2 hours', 'seedopen');

-- Deterministic attendance: student i attends past session n unless (i*n) % k says otherwise.
-- CS011 and CS012 are deliberately low (<75%).
INSERT INTO attendance (student_id, session_id, submitted_at)
SELECT st.id, se.id, se.start_time + interval '5 minutes'
FROM student st
JOIN sessions se ON se.token LIKE 'seedtoken%'
WHERE CASE
        WHEN st.roll_no IN ('CS011','CS012') THEN (st.id + se.id) % 3 = 0
        ELSE (st.id * se.id) % 11 <> 0
      END;
