
import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import os

# --- Page & API Configuration ---
st.set_page_config(layout="wide", page_title="Risk Intelligence Scraper")
API_URL = os.environ.get("API_URL", "http://localhost:8000/api")

# --- Styling ---
st.markdown("""
<style>
    .main .block-container { padding: 2rem 5rem; }
    h1, h2, h3 { color: #2E3B55; font-weight: bold; }
    .stButton>button { border-radius: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# --- API Request Handler ---
def api_request(method, endpoint, item_id=None, data=None):
    headers = {}
    if "auth_token" in st.session_state:
        headers["Authorization"] = f"Token {st.session_state.auth_token}"
    
    url = f"{API_URL}/{endpoint}/"
    if item_id:
        url += f"{item_id}/"
    
    try:
        res = requests.request(method, url, headers=headers, json=data)
        res.raise_for_status()
        if res.status_code == 204: return True
        return res.json()
    except requests.exceptions.HTTPError as e:
        error_message = f"Error: {e.response.status_code}"
        try:
            error_detail = e.response.json()
            if isinstance(error_detail, dict):
                messages = [f"{k.replace('_', ' ').title()}: {v[0] if isinstance(v, list) else v}" for k, v in error_detail.items()]
                error_message += " - " + ". ".join(messages)
            else:
                error_message += f" - {error_detail}"
        except json.JSONDecodeError:
            error_message += f" - {e.response.text}"
        st.error(error_message)
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: Could not connect to the API at {API_URL}. ({e})")
        return None

# --- UI Components ---
def schedule_management_ui(registered_tasks):
    st.title("🗓️ Scraping Schedule Manager")
    st.markdown("Schedule the automated web scraping workflow. The system will periodically scan for new information based on the schedule you set.")
    
    scraping_task_name = next((t for t in registered_tasks if 'start_scraping_workflow' in t), None)
    if not scraping_task_name:
        st.warning("The main scraping workflow task (`start_scraping_workflow`) is not available. Please contact support.")
        return

    # --- Scheduling Form ---
    st.header("Create a New Schedule")
    
    col1, col2 = st.columns([1, 2])
    
    # Define periods and their corresponding max values
    period_options = ("seconds", "minutes", "hours", "days", "months")
    max_values = {
        "seconds": 60,
        "minutes": 60,
        "hours": 24,
        "days": 31,  # A sensible upper limit
        "months": 12
    }

    # First, the user selects the period
    period = col2.selectbox("Period", period_options, index=3) # Default to 'days'
    
    # Then, the number input's range is dynamically set
    max_for_period = max_values.get(period)
    every = col1.number_input("Run Every", min_value=1, value=10, max_value=max_for_period)

    if st.button("💾 Schedule Now", use_container_width=True, type="primary"):
        period_singular = period[:-1]
        task_name = f"Automated Web Scraping (Every {every} {period_singular if every == 1 else period})"
        
        interval_payload = {
            "every": int(every),
            "period": period
        }
        task_payload = {
            "name": task_name,
            "task": scraping_task_name,
            "kwargs": json.dumps({}),
            "args": json.dumps([]),
            "enabled": True,
            "interval": interval_payload,
            "crontab": None
        }
        if api_request("post", "periodic-tasks", data=task_payload):
            st.success("Successfully scheduled task!")
            st.rerun()

    # --- Advanced Scheduling for Admins ---
    if st.session_state.user.get('is_staff'):
        with st.expander("⚙️ Advanced Scheduling (Admins Only)"):
            st.info("Use cron syntax for more complex schedules. For example, `0 9,17 * * *` runs the task at 9 AM and 5 PM every day.")
            with st.form("advanced_schedule_form"):
                name = st.text_input("Schedule Name", placeholder="e.g., 'Weekday Morning Scan'")
                minute = st.text_input("Minute", "0")
                hour = st.text_input("Hour", "9")
                day_of_week = st.text_input("Day of Week", "*")
                day_of_month = st.text_input("Day of Month", "*")
                month_of_year = st.text_input("Month of Year", "*")
                
                submitted = st.form_submit_button("💾 Save Advanced Schedule")
                if submitted and name:
                    crontab_payload = {
                        "minute": minute, "hour": hour, "day_of_week": day_of_week,
                        "day_of_month": day_of_month, "month_of_year": month_of_year,
                        "timezone": "UTC"
                    }
                    task_payload = {
                        "name": name, "task": scraping_task_name,
                        "kwargs": "{}", "args": "[]", "enabled": True,
                        "crontab": crontab_payload, "interval": None
                    }
                    if api_request("post", "periodic-tasks", data=task_payload):
                        st.success(f"Advanced schedule '{name}' saved!")
                        st.rerun()
                elif submitted:
                    st.warning("Please provide a name for the advanced schedule.")

    # --- Display Existing Tasks ---
    st.header("Current Scheduled Tasks")
    tasks = api_request("get", "periodic-tasks")
    if tasks:
        for task in sorted(tasks, key=lambda t: t['name']):
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.markdown(f"**{'🟢' if task['enabled'] else '🔴'} {task['name']}**")
            
            schedule_str = ""
            if task.get('interval'):
                schedule_str = f"Every {task['interval']['every']} {task['interval']['period']}"
            elif task.get('crontab'):
                ct = task['crontab']
                schedule_str = f"At {ct.get('hour', '*')}:{ct.get('minute', '*')} on day {ct.get('day_of_month', '*')} of month, on {ct.get('day_of_week', '*')} of week"
            col2.markdown(f"Schedule: `{schedule_str}`")
            
            if col3.button("🗑️ Delete", key=f"delete_{task['id']}", use_container_width=True):
                if api_request("delete", "periodic-tasks", item_id=task['id']):
                    st.success(f"Task '{task['name']}' deleted.")
                    st.rerun()
    else:
        st.info("No scheduled tasks found.")

def article_management_ui():
    st.title("📝 Article Manager")
    articles = api_request("get", "articles")
    if not articles:
        st.info("No articles found.")
        return
    for article in sorted(articles, key=lambda x: x['creation_date'], reverse=True):
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**URL:** [{article['url']}]({article['url']})")
                date = pd.to_datetime(article['creation_date']).strftime("%B %d, %Y at %I:%M %p")
                st.caption(f"Scraped on: {date}")
                status = "✅ Approved" if article['approved'] else "PENDING"
                drive_id = f"Drive ID: `{article.get('drive_id', 'N/A')}`"
                st.markdown(f"Status: **{status}** | {drive_id}")
            if col2.button("🗑️ Delete", key=f"delete_{article['id']}", use_container_width=True, type="primary"):
                if api_request("delete", "articles", item_id=article['id']):
                    st.success("Article deleted.")
                    st.rerun()

def admin_tools_ui():
    st.title("⚙️ Admin Tools")
    st.header("Database and Google Drive Seeding")
    st.warning("⚠️ **Warning:** This will delete existing test articles before seeding new ones.")
    if st.button("🌱 Seed Test Data", type="primary"):
        with st.spinner("Executing seeding script..."):
            response = api_request("post", "seed-data")
            if response and response.get("status") == "success":
                st.success("Seeding script executed successfully!")
                st.code(response.get("log", "No output log available."))
            else:
                st.error("An error occurred while running the seeding script.")

# --- Main Application & Login Flow ---
def main_app():
    st.sidebar.title(f"Welcome, {st.session_state.user.get('username', 'User')}!")
    
    tabs = ["🗓️ Scraping Schedule", "📝 Manage Articles"]
    if st.session_state.user.get('is_staff', False):
        tabs.append("⚙️ Admin Tools")
    
    selected_tab = st.sidebar.radio("Navigation", tabs, key="navigation")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    if selected_tab == "🗓️ Scraping Schedule":
        registered_tasks = api_request("get", "registered-tasks")
        if registered_tasks:
            schedule_management_ui(registered_tasks)
    elif selected_tab == "📝 Manage Articles":
        article_management_ui()
    elif selected_tab == "⚙️ Admin Tools":
        admin_tools_ui()

def login_ui():
    st.title("Risk Intelligence Scraper")
    st.subheader("Please log in to continue")
    with st.form("login_form"):
        username = st.text_input("Username").lower()
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
        
        if submitted:
            if not username or not password:
                st.warning("Please enter both username and password.")
                return
            
            try:
                login_payload = {"username": username, "password": password}
                response = requests.post(f"{API_URL}/login/", data=login_payload)
                response.raise_for_status()
                
                st.session_state.auth_token = response.json()['token']
                user_details = api_request("get", "user")
                
                if user_details:
                    st.session_state.user = user_details
                    st.rerun()
                else:
                    st.error("Login successful, but failed to retrieve user details.")
            
            except requests.exceptions.HTTPError as e:
                st.error("Invalid credentials. Please try again.")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the API. Please ensure the backend is running. Error: {e}")

# --- Entry Point ---
if "auth_token" not in st.session_state:
    login_ui()
else:
    main_app()