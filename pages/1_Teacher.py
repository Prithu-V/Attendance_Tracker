"""Teacher page: password-protected. Create a session and show its QR code."""
import hmac
import io
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import psycopg2.errors
import qrcode
import streamlit as st

import db

st.set_page_config(page_title="Teacher", page_icon="🎓")
st.title("Teacher")

# ---- auth
if not st.session_state.get("teacher_ok"):
    pw = st.text_input("Password", type="password")
    if st.button("Log in"):
        if hmac.compare_digest(pw.encode(), st.secrets["teacher_password"].encode()):
            st.session_state.teacher_ok = True
            st.rerun()
        else:
            st.error("Wrong password.")
    st.stop()

tz = ZoneInfo(st.secrets.get("timezone", "UTC"))
base_url = st.secrets.get("app_url", "http://localhost:8501").rstrip("/")

# ---- create session
now_local = datetime.now(tz)
with st.form("new_session"):
    name = st.text_input("Session name", placeholder="DBMS Lecture 5")
    c1, c2 = st.columns(2)
    start_d = c1.date_input("Start date", now_local.date())
    start_t = c1.time_input("Start time", now_local.time().replace(second=0, microsecond=0))
    end_d = c2.date_input("End date", now_local.date())
    end_t = c2.time_input("End time", (now_local + timedelta(hours=1)).time().replace(second=0, microsecond=0))
    create = st.form_submit_button("Create session")

if create:
    start = datetime.combine(start_d, start_t, tzinfo=tz)
    end = datetime.combine(end_d, end_t, tzinfo=tz)
    if not name.strip():
        st.error("Give the session a name.")
    else:
        try:
            st.session_state.active = dict(db.create_session(name.strip(), start, end))
        except psycopg2.errors.CheckViolation:
            st.error("End time must be after start time.")

# ---- show QR
active = st.session_state.get("active")
if active:
    url = f"{base_url}/?token={active['token']}"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    st.subheader(active["session_name"])
    st.image(buf.getvalue(), width=320)
    st.code(url, language=None)

    @st.fragment(run_every=5)
    def live_count():
        st.metric("Marked present", db.present_count(active["id"]))

    live_count()
