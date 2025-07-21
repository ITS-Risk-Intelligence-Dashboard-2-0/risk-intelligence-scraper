import streamlit as st
from api import get_token, get_schedules, create_schedule, update_schedule, delete_schedule
import json

st.set_page_config(page_title="Configuration Admin", layout="wide")

st.title("Scraper Task Scheduler")

with st.sidebar:
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Log in"):
        token = get_token(username, password)
        if token:
            st.session_state["token"] = token
            st.success("Logged in")
        else:
            st.error("Invalid credentials")

# --- TOKEN CHECK ---
if "token" not in st.session_state:
    st.warning("Please log in to view or modify scheduled tasks.")
    st.stop()

token = st.session_state["token"]

# --- FETCH EXISTING TASKS ---
st.subheader("Existing Scheduled Tasks")
schedules = get_schedules(token)
if not schedules:
    st.info("No scheduled tasks found.")
else:
    for task in schedules:
        with st.expander(f"{task['name']}"):
            st.json(task)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"Delete '{task['name']}'", key=f"delete_{task['id']}"):
                    delete_schedule(task["id"], token)
                    st.success(f"Deleted {task['name']}")
                    st.experimental_rerun()

            with col2:
                if st.button(f"Update '{task['name']}'", key=f"edit_{task['id']}"):
                    with st.form(f"edit_form_{task['id']}"):
                        name = st.text_input("Task Name", value=task["name"])
                        task_name = st.text_input("Django Task Path", value=task["task"])
                        args = st.text_input("Args (JSON)", value=task["args"])
                        cron_minute = st.text_input("Minute", value=task["crontab"]["minute"])
                        cron_hour = st.text_input("Hour", value=task["crontab"]["hour"])

                        submitted = st.form_submit_button("Submit Changes")
                        if submitted:
                            update_schedule(task["id"], {
                                "name": name,
                                "task": task_name,
                                "args": args,
                                "crontab": {
                                    "minute": cron_minute,
                                    "hour": cron_hour,
                                    # Add other fields if needed
                                }
                            }, token)
                            st.success("Updated successfully")
                            st.experimental_rerun()

# --- CREATE NEW TASK ---
st.subheader("Create New Scheduled Task")

with st.form("create_task_form"):
    name = st.text_input("Task Name")
    task_name = st.text_input("Django Task Path (e.g. scrapers.tasks.run_scraper)")
    args = st.text_input("Args (JSON format)", value="[]")
    cron_minute = st.text_input("Minute (e.g. '0')", value="0")
    cron_hour = st.text_input("Hour (e.g. '*/6')", value="*/6")

    submitted = st.form_submit_button("Create Task")
    if submitted:
        try:
            json.loads(args)  # validate JSON
            response = create_schedule({
                "name": name,
                "task": task_name,
                "args": args,
                "crontab": {
                    "minute": cron_minute,
                    "hour": cron_hour,
                }
            }, token)
            if "id" in response:
                st.success(f"Created task '{name}'")
                st.experimental_rerun()
            else:
                st.error(f"Error creating task: {response}")
        except json.JSONDecodeError:
            st.error("Args must be valid JSON (e.g. ['arg1'])")

