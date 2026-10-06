"""Dashboard: attendance analytics."""
import streamlit as st

import db

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("Attendance dashboard")

THRESHOLD = 75.0
per_student = db.attendance_per_student()
per_session = db.attendance_per_session()

if per_session.empty:
    st.info("No sessions yet.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Sessions held", len(per_session))
c2.metric("Students", len(per_student))
c3.metric("Average attendance", f"{per_student['pct'].astype(float).mean():.1f}%")

st.subheader("Attendance % per student")
st.dataframe(per_student, hide_index=True, width="stretch")

st.subheader(f"Below {THRESHOLD:.0f}%")
low = db.below_threshold(THRESHOLD)
if low.empty:
    st.success("Everyone is at or above the threshold.")
else:
    st.dataframe(low, hide_index=True, width="stretch")

st.subheader("Attendance per session")
st.dataframe(per_session, hide_index=True, width="stretch")

st.subheader("Trend over time")
st.line_chart(per_session.set_index("start_time")["pct"].astype(float))

st.subheader("Running attendance % for one student")
pick = st.selectbox("Student", per_student["roll_no"] + " – " + per_student["name"])
running = db.running_attendance(pick.split(" – ")[0])
if not running.empty:
    st.line_chart(running.set_index("start_time")["running_pct"].astype(float))
