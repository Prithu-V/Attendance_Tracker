"""Student page: the QR code target."""
import streamlit as st

import db

st.set_page_config(page_title="Mark Attendance", page_icon="✅", layout="centered")

MESSAGES = {
    db.NO_TOKEN:      ("error",   "No session token in the link. Scan the QR code shown by your teacher."),
    db.INVALID_TOKEN: ("error",   "Invalid QR code. Ask your teacher to show it again."),
    db.NOT_STARTED:   ("warning", "This session hasn't started yet."),
    db.CLOSED:        ("warning", "This session is closed."),
    db.UNKNOWN_ROLL:  ("error",   "Unknown roll number. Check it and try again."),
}

st.title("Mark attendance")
token = st.query_params.get("token")

if not token:
    st.error(MESSAGES[db.NO_TOKEN][1])
    st.stop()

with st.form("attendance"):
    roll_no = st.text_input("Roll number", max_chars=20)
    submitted = st.form_submit_button("Submit")

if submitted:
    if not roll_no.strip():
        st.warning("Enter your roll number.")
    else:
        code, name = db.mark_attendance(token, roll_no)
        if code == db.OK:
            st.success(f"Marked present. Thanks, {name}!")
        elif code == db.ALREADY:
            st.info(f"{name}, you're already marked present for this session.")
        else:
            level, msg = MESSAGES[code]
            getattr(st, level)(msg)
