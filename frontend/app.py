
import streamlit as st
import requests
import pandas as pd
import json
from urllib.parse import urlparse, urlunparse
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import re

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
def scraper_control_ui():
    st.title("⚙️ Scraper Control & Configuration")
    
    # --- Source Management ---
    st.header("Manage Scraper Sources")
    
    # Fetch existing sources
    sources = api_request("get", "sources")
    if sources is None:
        st.error("Could not load sources from the API.")
        sources = []

    # Form to add a new source
    with st.expander("➕ Add New Source", expanded=False):
        with st.form("new_source_form", clear_on_submit=True):
            st.text_input("URL", key="new_source_url", placeholder="https://www.example.com/news")
            st.number_input("Depth", key="new_source_depth", value=1, step=1)
            st.selectbox("Target Content", ["Both", "PDFs Only", "Websites Only"], key="new_source_target")
            st.checkbox("Is Active", key="new_source_active", value=True)
            
            submitted = st.form_submit_button("Add Source")
            if submitted:
                target_map = {
                    "Both": "BOTH",
                    "PDFs Only": "PDF",
                    "Websites Only": "WEBSITE"
                }

                url_match = re.match(r'^https://[-a-zA-Z0-9.]+(/[a-zA-Z0-9\-=&?\./]*)?$', st.session_state.new_source_url.strip())
                parsed_url = urlparse(st.session_state.new_source_url)

                if url_match:
                    new_source = {
                        "netloc": parsed_url.netloc,
                        "path": parsed_url.path,
                        "depth": st.session_state.new_source_depth,
                        "target": target_map[st.session_state.new_source_target],
                        "is_active": st.session_state.new_source_active
                    }
                    response = api_request("post", "sources", data=new_source)
                    if response:
                        st.success(f"Source '{response.get('name')}' added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add source.")
                else:
                    st.error(url_match)
                    st.error(f"Invalid Url: {st.session_state.new_source_url} failed url validation check!")

    # Display existing sources in a table-like format
    st.subheader("Current Sources")
    for source in sources:
        source_url = urlunparse(("https", source["netloc"], source["path"], '', '', ''))

        col1, col2, col3, col4, col5 = st.columns([5, 3, 1, 1, 1])
        with col1:
            st.text_input("Url", value=source_url, key=f"name_{source['id']}", disabled=True)
        with col2:
            st.text_input("Target Content", value=source['target'], key=f"target_{source['id']}", disabled=True)
        with col3:
            st.text_input("Depth", value=source['depth'], key=f"url_{source['id']}", disabled=True)
        with col4:
            if st.button("✏️", key=f"edit_{source['id']}"):
                # This is a placeholder for a more complex edit modal/form
                st.info("Edit functionality would be built out here.")
        with col5:
            if st.button("🗑️", key=f"delete_{source['id']}"):
                api_request("delete", "sources", item_id=source['id'])
                st.rerun()
    
    # --- Scraper Control ---
    st.header("Manual Scraper Control")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Start Scraper", type="primary"):
            response = api_request("post", "scraper/control")
            if response and response.get("status") == "success":
                st.success(response.get("message"))
            else:
                error_message = response.get("message", "Failed to start scraper.") if response else "An unknown error occurred."
                st.error(error_message)
                
    with col2:
        if st.button("⏹️ Stop Scraper"):
            response = api_request("delete", "scraper/control")
            if response and response.get("status") == "success":
                st.info(response.get("message"))
            else:
                error_message = response.get("message", "Failed to stop scraper.") if response else "An unknown error occurred."
                st.error(error_message)

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
    st.subheader("Seed Test Data")
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
    
    is_admin = st.session_state.user.get('is_staff', False)
    
    if is_admin:
        app_pages = {
            "📰 Article Manager": article_management_ui,
            "🗓️ Scraping Schedule": schedule_management_ui,
            "⚙️ Scraper Control": scraper_control_ui,
            "🛠️ Admin Tools": admin_tools_ui
        }
    else:
        app_pages = {
            "📰 Article Manager": article_management_ui,
            "🗓️ Scraping Schedule": schedule_management_ui
        }
        
    selection = st.sidebar.radio("Go to", list(app_pages.keys()))
    
    # Fetch registered tasks once and pass to the relevant UI function
    if selection == "🗓️ Scraping Schedule":
        tasks = api_request("get", "task-choices")
        if tasks:
            app_pages[selection](tasks)
        else:
            st.error("Could not load task choices from the API.")
    else:
        app_pages[selection]()

    if st.sidebar.button("Logout"):
        logout()

def login_ui():
    st.title("Risk Intelligence Scraper Login")
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