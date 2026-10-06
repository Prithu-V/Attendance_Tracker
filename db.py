"""All SQL lives here. Pages call these functions and never build SQL themselves.

Every query is parameterized (%s placeholders). Time comparisons use the
database's now(), never the client's clock.
"""
import os
import secrets
from contextlib import contextmanager
from datetime import datetime

import pandas as pd
import psycopg2
import psycopg2.extras

# Result codes returned by mark_attendance (the validation chain).
OK = "ok"
NO_TOKEN = "no_token"
INVALID_TOKEN = "invalid_token"
NOT_STARTED = "not_started"
CLOSED = "closed"
UNKNOWN_ROLL = "unknown_roll"
ALREADY = "already_marked"


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    import streamlit as st  # imported lazily so tests can run without Streamlit config
    return st.secrets["database_url"]


@contextmanager
def get_conn():
    conn = psycopg2.connect(_database_url())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _df(sql: str, params=None) -> pd.DataFrame:
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return pd.DataFrame(cur.fetchall())


# ---------------------------------------------------------------- validation chain
def mark_attendance(token: str | None, roll_no: str) -> tuple[str, str | None]:
    """Run the validation chain; stop at the first failure.

    Returns (result_code, student_name_or_None).
    """
    if not token:                                                    # 1
        return NO_TOKEN, None

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(                                                 # 2 + 3
            """SELECT id,
                      now() <  start_time AS not_started,
                      now() >= end_time   AS closed
               FROM sessions WHERE token = %s""",
            (token,),
        )
        row = cur.fetchone()
        if row is None:
            return INVALID_TOKEN, None
        session_id, not_started, closed = row
        if not_started:
            return NOT_STARTED, None
        if closed:
            return CLOSED, None

        cur.execute(                                                 # 4
            "SELECT id, name FROM student WHERE roll_no = %s",
            (roll_no.strip().upper(),),
        )
        student = cur.fetchone()
        if student is None:
            return UNKNOWN_ROLL, None
        student_id, name = student

        cur.execute(                                                 # 5 (no query-then-insert)
            """INSERT INTO attendance (student_id, session_id)
               VALUES (%s, %s)
               ON CONFLICT (student_id, session_id) DO NOTHING""",
            (student_id, session_id),
        )
        if cur.rowcount == 0:
            return ALREADY, name
        return OK, name


# ---------------------------------------------------------------- teacher
def create_session(name: str, start: datetime, end: datetime) -> dict:
    """start/end must be timezone-aware. Raises psycopg2.errors.CheckViolation if end <= start."""
    token = secrets.token_urlsafe(8)
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """INSERT INTO sessions (session_name, start_time, end_time, token)
               VALUES (%s, %s, %s, %s)
               RETURNING id, session_name, start_time, end_time, token""",
            (name, start, end, token),
        )
        return cur.fetchone()


def present_count(session_id: int) -> int:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM attendance WHERE session_id = %s", (session_id,))
        return cur.fetchone()[0]


def list_sessions() -> pd.DataFrame:
    return _df(
        """SELECT id, session_name, start_time, end_time, token
           FROM sessions ORDER BY start_time DESC"""
    )


# ---------------------------------------------------------------- dashboard
# "Counted" sessions = those that have ended. Open or future sessions would unfairly count as absences.
_COUNTED = "end_time <= now()"


def attendance_per_student() -> pd.DataFrame:
    """Attendance % per student, ranked with a window function."""
    return _df(
        f"""WITH counted AS (SELECT id FROM sessions WHERE {_COUNTED}),
                 total   AS (SELECT count(*) AS n FROM counted)
            SELECT s.roll_no, s.name,
                   count(a.id)                                          AS attended,
                   t.n                                                  AS total_sessions,
                   round(100.0 * count(a.id) / NULLIF(t.n, 0), 1)       AS pct,
                   rank() OVER (ORDER BY count(a.id) DESC)              AS rank
            FROM student s
            CROSS JOIN total t
            LEFT JOIN attendance a
                   ON a.student_id = s.id AND a.session_id IN (SELECT id FROM counted)
            GROUP BY s.id, s.roll_no, s.name, t.n
            ORDER BY rank, s.roll_no"""
    )


def attendance_per_session() -> pd.DataFrame:
    return _df(
        f"""SELECT se.id, se.session_name, se.start_time,
                   count(a.id) AS present,
                   (SELECT count(*) FROM student) AS roster,
                   round(100.0 * count(a.id) / NULLIF((SELECT count(*) FROM student), 0), 1) AS pct
            FROM sessions se
            LEFT JOIN attendance a ON a.session_id = se.id
            WHERE se.{_COUNTED}
            GROUP BY se.id
            ORDER BY se.start_time"""
    )


def below_threshold(threshold: float = 75.0) -> pd.DataFrame:
    df = attendance_per_student()
    return df[df["pct"].astype(float) < threshold] if not df.empty else df


def running_attendance(roll_no: str) -> pd.DataFrame:
    """Running attendance % for one student after each session (window functions)."""
    return _df(
        f"""SELECT se.start_time, se.session_name,
                   (a.id IS NOT NULL) AS present,
                   round(100.0 * sum((a.id IS NOT NULL)::int)
                         OVER (ORDER BY se.start_time)
                         / row_number() OVER (ORDER BY se.start_time), 1) AS running_pct
            FROM sessions se
            JOIN student st ON st.roll_no = %s
            LEFT JOIN attendance a ON a.session_id = se.id AND a.student_id = st.id
            WHERE se.{_COUNTED}
            ORDER BY se.start_time""",
        (roll_no.strip().upper(),),
    )
