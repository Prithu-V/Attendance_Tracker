-- Attendance Tracker v1 schema. Safe to re-run: drops and recreates everything.
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS student;

CREATE TABLE student (
    id       SERIAL PRIMARY KEY,
    name     TEXT NOT NULL,
    roll_no  TEXT NOT NULL UNIQUE,          -- stored upper-case, app normalizes input
    email    TEXT UNIQUE
);

CREATE TABLE sessions (
    id            SERIAL PRIMARY KEY,
    session_name  TEXT NOT NULL,
    start_time    TIMESTAMPTZ NOT NULL,
    end_time      TIMESTAMPTZ NOT NULL,
    token         TEXT NOT NULL UNIQUE,
    CHECK (end_time > start_time)
);

CREATE TABLE attendance (
    id            SERIAL PRIMARY KEY,
    student_id    INT NOT NULL REFERENCES student(id)  ON DELETE CASCADE,
    session_id    INT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    submitted_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (student_id, session_id)
);

CREATE INDEX idx_attendance_session ON attendance(session_id);
CREATE INDEX idx_sessions_start     ON sessions(start_time);
