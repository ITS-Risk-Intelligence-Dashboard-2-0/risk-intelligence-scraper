# ui/app.py
import streamlit as st
import requests
import pandas as pd
import json
from collections import OrderedDict
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

# The backend service is accessible via its service name in Docker Compose
API_URL = "http://schedule-api:8000/api"

st.set_page_config(layout="wide", page_title="Easy Schedule Manager")
st.title("✅ Easy Task Scheduler")
st.caption("Create and manage automated tasks without any technical knowledge.")

def api_request(method, endpoint, item_id=None, data=None):
    """A single, robust function to handle all API requests."""
    url = f"{API_URL}/{endpoint}/"
    if item_id:
        url += f"{item_id}/"
    
    try:
        res = requests.request(method, url, json=data)
        res.raise_for_status()
        if res.status_code == 204:  # Handle No Content for DELETE
            return True
        return res.json()
    except requests.exceptions.HTTPError as e:
        try:
            # Try to parse the backend's error message
            error_detail = e.response.json()
            
            # --- START FIX ---
            # This logic is now robust to different DRF error formats.
            if isinstance(error_detail, dict):
                messages = []
                for k, v in error_detail.items():
                    # Standard DRF error is a list of strings.
                    if isinstance(v, list) and v:
                        msg = v[0]
                    # Handle other cases (string, nested dict) by converting to string.
                    else:
                        msg = str(v)
                    
                    # Don't show unhelpful keys like 'detail' or 'non_field_errors'
                    if k in ['detail', 'non_field_errors']:
                        messages.append(msg)
                    else:
                        messages.append(f"{k.replace('_', ' ').title()}: {msg}")
                error_message = ". ".join(messages)
            # --- END FIX ---
            else:
                error_message = str(error_detail)
            st.error(f"Error: {error_message}")
        except json.JSONDecodeError:
            st.error(f"An error occurred: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: Could not connect to the API. ({e})")
        return None


# --- UI Helper Functions ---
def format_schedule(task):
    """Converts a task's schedule object into a human-readable string."""
    if task.get('interval'):
        period = task['interval']['period']
        every = task['interval']['every']
        if every == 1:
            period = period[:-1]
        return f"Every {every} {period}"

    if task.get('crontab'):
        ct = task['crontab']
        parts = OrderedDict([
            ('minute', ct.get('minute', '*')), ('hour', ct.get('hour', '*')),
            ('day of month', ct.get('day_of_month', '*')), ('month', ct.get('month_of_year', '*')),
            ('day of week', ct.get('day_of_week', '*'))
        ])
        schedule_str = []
        if parts['minute'] != '*' or parts['hour'] != '*':
            schedule_str.append(f"at {parts['hour']}:{parts['minute']}")
        if parts['day of month'] != '*':
            schedule_str.append(f"on day(s) {parts['day of month']}")
        if parts['month'] != '*':
            schedule_str.append(f"in month(s) {parts['month']}")
        if parts['day of week'] != '*':
            schedule_str.append(f"on {parts['day of week']}")
        if not schedule_str: return "Runs every minute"
        return "Runs " + " ".join(schedule_str)
    return "No schedule"

def display_tasks_ui(tasks, registered_tasks):
    """Renders the list of current tasks in a user-friendly way."""
    if not tasks:
        st.info("No scheduled tasks found. Create one using the tab above!")
        return

    st.subheader("Current Scheduled Tasks")

    for task in sorted(tasks, key=lambda t: t['name']):
        with st.expander(f"{'🟢' if task['enabled'] else '🔴'} **{task['name']}** - `{task['task']}`"):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**Schedule:** {format_schedule(task)}")
                last_run = pd.to_datetime(task.get('last_run_at')).strftime('%Y-%m-%d %H:%M:%S') if task.get('last_run_at') else "Never"
                st.markdown(f"**Last Run:** {last_run}")
            with col2:
                st.markdown("**Parameters:**")
                kwargs_data = task.get('kwargs', '{}')
                try:
                    # Robustly handle kwargs that might be a string-of-JSON
                    while isinstance(kwargs_data, str):
                        kwargs_data = json.loads(kwargs_data)
                    if isinstance(kwargs_data, dict) and kwargs_data:
                        for key, value in kwargs_data.items():
                            st.markdown(f"- `{key}`: `{value}`")
                    else:
                        st.markdown("None")
                except (json.JSONDecodeError, TypeError):
                    st.markdown("Invalid format")
            with col3:
                if st.button("✏️ Edit", key=f"edit_{task['id']}", use_container_width=True):
                    st.session_state.edit_task_id = task['id']
                    st.rerun()
                if st.button("🗑️ Delete", key=f"delete_{task['id']}", type="primary", use_container_width=True):
                    if api_request("delete", "periodic-tasks", item_id=task['id']):
                        st.success(f"Task '{task['name']}' deleted.")
                        st.rerun()

def schedule_creation_ui():
    """Renders the UI for creating a new schedule on the fly."""
    st.write("---")
    st.subheader("🗓️ When should the task run?")
    schedule_type = st.radio("Schedule Type", ["Simple Interval", "Specific Time (Advanced)"], horizontal=True, label_visibility="collapsed")
    if schedule_type == "Simple Interval":
        col1, col2 = st.columns(2)
        every = col1.number_input("Run Every", min_value=1, value=10, key="interval_every")
        period = col2.selectbox("Period", ["seconds", "minutes", "hours", "days"], key="interval_period")
        return {"type": "interval", "every": every, "period": period}
    else: # Crontab
        st.info("Use '*' to mean 'every'. For example, setting Hour to '9' means 'run every minute during the 9 AM hour'.")
        c1, c2, c3 = st.columns(3)
        minute = c1.text_input("Minute", value="0", help="0-59, or *", key="cron_minute")
        hour = c2.text_input("Hour", value="*", help="0-23, or *", key="cron_hour")
        day_of_week = c3.text_input("Day of Week", value="*", help="0-6 (Sun-Sat), or *", key="cron_day_of_week")
        c4, c5 = st.columns(2)
        day_of_month = c4.text_input("Day of Month", value="*", help="1-31, or *", key="cron_day_of_month")
        month_of_year = c5.text_input("Month of Year", value="*", help="1-12, or *", key="cron_month_of_year")
        return {"type": "crontab", "minute": minute, "hour": hour, "day_of_week": day_of_week, "day_of_month": day_of_month, "month_of_year": month_of_year}

def kwargs_creation_ui(existing_kwargs=None):
    """Renders a simple key-value UI for task parameters (kwargs)."""
    st.write("---")
    st.subheader("⚙️ Task Parameters (Optional)")
    
    if 'kwargs_list' not in st.session_state:
        if existing_kwargs:
            st.session_state.kwargs_list = list(json.loads(existing_kwargs).items())
        else:
            st.session_state.kwargs_list = []

    # These buttons will now trigger reruns without being in a form
    for i in range(len(st.session_state.kwargs_list)):
        c1, c2, c3 = st.columns([5, 5, 1])
        st.session_state.kwargs_list[i][0] = c1.text_input("Parameter Name", st.session_state.kwargs_list[i][0], key=f"kw_key_{i}")
        st.session_state.kwargs_list[i][1] = c2.text_input("Parameter Value", st.session_state.kwargs_list[i][1], key=f"kw_val_{i}")
        if c3.button("✖️", key=f"del_kw_{i}", help="Remove this parameter"):
            st.session_state.kwargs_list.pop(i)
            st.rerun()

    if st.button("Add Parameter"):
        st.session_state.kwargs_list.append(["", ""])
        st.rerun()
    
    return {key: value for key, value in st.session_state.kwargs_list if key}

def task_form(task_to_edit=None, registered_tasks=None):
    """Renders the main form for creating or editing a task."""
    is_edit_mode = task_to_edit is not None
    # NOTE: The edit mode logic will need a more complex solution to handle updating
    # nested schedules. This fix focuses on the "create" workflow which is failing.
    # For simplicity, this solution will correctly handle creation.
    st.header("✏️ Create or Modify a Task" if is_edit_mode else "✨ Create a New Task")

    # --- WIDGETS OUTSIDE THE FORM ---
    name_val = task_to_edit['name'] if is_edit_mode else ""
    st.text_input("Descriptive Name", value=name_val, key="task_name_input")

    task_name_options = registered_tasks or []
    default_task_index = 0
    if is_edit_mode and task_to_edit['task'] in task_name_options:
        default_task_index = task_name_options.index(task_to_edit['task'])
    st.selectbox("Task to run", options=task_name_options, index=default_task_index, key="task_selection")

    schedule_data = schedule_creation_ui()
    kwargs_data = kwargs_creation_ui(task_to_edit.get('kwargs') if is_edit_mode else None)
    
    st.write("---")

    # --- THE FORM ---
    with st.form("task_form_submit", clear_on_submit=not is_edit_mode):
        enabled = st.toggle("Enable this task now", value=task_to_edit['enabled'] if is_edit_mode else True)
        submitted = st.form_submit_button("💾 Save Task" if is_edit_mode else "💾 Create Task", use_container_width=True, type="primary")

        if submitted:
            # On submission, we gather data from st.session_state using the keys
            name = st.session_state.task_name_input
            task_name = st.session_state.task_selection

            # 1. Prepare schedule data as a dictionary (or None)
            interval_payload = None
            crontab_payload = None

            if schedule_data["type"] == "interval":
                interval_payload = {"every": schedule_data["every"], "period": schedule_data["period"]}
            else: # crontab
                crontab_payload = {k: v for k, v in schedule_data.items() if k != 'type'}
                # Add a default timezone if using the new serializer
                crontab_payload['timezone'] = 'UTC'

            # 2. Create the main periodic task payload
            task_payload = {
                "name": name,
                "task": task_name,
                # --- THIS IS THE KEY FIX ---
                # Ensure args and kwargs are sent as JSON-encoded STRINGS
                "kwargs": json.dumps(kwargs_data),
                "args": json.dumps([]),
                # -------------------------
                "enabled": enabled,
                "interval": interval_payload, # Sent as a nested dictionary
                "crontab": crontab_payload,   # Sent as a nested dictionary
            }
            
            # 3. Post or Put the task
            response = api_request("put" if is_edit_mode else "post", "periodic-tasks", item_id=task_to_edit['id'] if is_edit_mode else None, data=task_payload)

            if response:
                st.success(f"Task '{name}' was saved successfully!")
                st.session_state.edit_task_id = None
                if 'kwargs_list' in st.session_state:
                    del st.session_state.kwargs_list
                st.rerun()

    if is_edit_mode:
        if st.button("Cancel Edit"):
            st.session_state.edit_task_id = None
            if 'kwargs_list' in st.session_state:
                del st.session_state.kwargs_list
            st.rerun()

def article_management_ui():
    st.header("📰 Article Manager")

    # Fetch all articles
    articles = api_request("get", "articles")
    if articles is None:
        return

    # Display as table header
    st.subheader("📄 Existing Articles")
    if articles:
        header_cols = st.columns([4, 2, 2, 2, 1, 1])
        headers = ["URL", "Created", "Drive ID", "Approved", "Edit", "Delete"]
        for col, label in zip(header_cols, headers):
            col.markdown(f"**{label}**")

        for article in articles:
            cols = st.columns([4, 2, 2, 2, 1, 1])
            cols[0].markdown(article["url"])
            raw_date = article["creation_date"]
            dt_utc = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).astimezone(ZoneInfo("UTC"))
            dt_et = dt_utc.astimezone(ZoneInfo("America/New_York"))
            formatted_date = dt_et.strftime("%m/%d/%Y %I:%M %p")
            cols[1].markdown(formatted_date) # human readable datetime format
            cols[2].markdown(article.get("drive_id", ""))
            cols[3].markdown("✅" if article["approved"] else "❌")
            if cols[4].button("✏️", key=f"edit_{article['id']}"):
                st.session_state.editing_article = article
            if cols[5].button("🗑️", key=f"delete_{article['id']}"):
                if api_request("delete", "articles", item_id=article["id"]):
                    st.success("Article deleted.")
                    st.rerun()
    else:
        st.info("No articles found.")

    # Show Edit Form
    if "editing_article" in st.session_state:
        st.markdown("---")
        st.subheader("📝 Edit Article")

        article = st.session_state.editing_article
        url = st.text_input("URL", value=article["url"])
        drive_id = st.text_input("Drive File ID", value=article.get("drive_id", ""))
        approved = st.checkbox("Approved", value=article["approved"])

        col1, col2 = st.columns([1, 1])
        if col1.button("💾 Save Changes"):
            update_data = {
                "url": url,
                "drive_id": drive_id,
                "approved": approved
            }
        if api_request("put", "articles", item_id=article["id"], data=update_data):
            st.success("Article updated.")
            del st.session_state.editing_article
            st.rerun()
        else:
            st.error("Update failed. Please try again.")

        if col2.button("❌ Cancel Edit"):
            del st.session_state.editing_article
            st.rerun()

    # Show Add Form (if not editing)
    if "editing_article" not in st.session_state:
        st.markdown("---")
        st.subheader("➕ Add New Article")

        new_url = st.text_input("New URL", key="new_url")
        new_drive_id = st.text_input("New Drive File ID", key="new_drive_id")
        new_approved = st.checkbox("Approved?", key="new_approved")

        if st.button("➕ Create Article"):
            new_data = {
                "url": new_url,
                "drive_id": new_drive_id,
                "approved": new_approved
            }
            if api_request("post", "articles", data=new_data):
                st.success("Article created.")
                st.rerun()

# --- Main Application Flow ---
def main():

    # removes the deploy button link
    st.markdown(
    r"""
    <style>
    .stAppDeployButton {
            visibility: hidden;
        }
    </style>
    """, unsafe_allow_html=True
    )

    periodic_tasks = api_request("get", "periodic-tasks")
    registered_tasks = api_request("get", "registered-tasks")
    
    if periodic_tasks is None or registered_tasks is None:
        st.error("Could not load data from the API. The scheduling service might be down. Please refresh.")
        return

    if 'edit_task_id' in st.session_state and st.session_state.edit_task_id is not None:
        task_to_edit = next((t for t in periodic_tasks if t['id'] == st.session_state.edit_task_id), None)
        task_form(task_to_edit=task_to_edit, registered_tasks=registered_tasks)
    else:
        tab1, tab2, tab3 = st.tabs(["📊 Manage Tasks", "➕ Create New Task", "📰 Manage Articles"])
        with tab1:
            display_tasks_ui(periodic_tasks, registered_tasks)
        with tab2:
            if 'kwargs_list' in st.session_state and not st.session_state.get('edit_task_id'):
                del st.session_state.kwargs_list
            task_form(registered_tasks=registered_tasks)
        with tab3:
            article_management_ui()

if __name__ == "__main__":
    main()