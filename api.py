import requests

API_BASE = "http://localhost:8000"
TASKS_URL = f"{API_BASE}/api/periodic_tasks/"
AUTH_URL = f"{API_BASE}/api-token-auth/"

# Authentication
def get_token(username, password):
    res = requests.post(AUTH_URL, data={"username": username, "password": password})
    if res.status_code == 200:
        return res.json()["token"]
    return None

# Getting the celery schedule
def get_schedules(token):
    headers = {"Authorization": f"Token {token}"}
    res = requests.get(TASKS_URL, headers=headers)
    return res.json()

# Creating schedule
def create_schedule(data, token):
    headers = {"Authorization": f"Token {token}"}
    res = requests.post(TASKS_URL, json=data, headers=headers)
    return res.json() 

def update_schedule(task_id, data, token):
    headers = {"Authorization": f"Token {token}"}
    res = requests.put(f"{TASKS_URL}{task_id}/", json=data, headers=headers)
    return res.json()

def delete_schedule(task_id, token):
    headers = {"Authorization": f"Token {token}"}
    return requests.delete(f"{TASKS_URL}{task_id}/", headers=headers)
