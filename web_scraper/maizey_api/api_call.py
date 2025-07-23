import os
import requests
import json

# lingering questions:
#   can we make multiple calls per conversation pk?
#   if so, what is the limit? is there a time limit? an call limit?
#   if no limit, do we need to close the conversation?

class MaizeyCallError(Exception):
    pass

class MaizeyImproperJson(Exception):
    pass

def create_conversation(project_pk, api_key):
    base_url = os.environ.get("MAIZEY_API_BASE_URL")
    create_conversation_url = f"{base_url}{project_pk}/conversation/"
    headers = {
        'accept': 'application/json',
        'Authorization': f"Bearer {api_key}",
        'Content-Type': 'application/json',
    }

    response = requests.post(create_conversation_url, headers=headers)
    if response.status_code != 201:
        raise MaizeyCallError(f"Error {response.status_code}: {response.text}")

    return response.json()["pk"]

def call_api(project_pk, conversation_pk, api_key, prompt):
    base_url = os.environ.get("MAIZEY_API_BASE_URL")
    prompt_url = f"{base_url}{project_pk}/conversation/{conversation_pk}/messages/"

    headers = {
        'accept': 'application/json',
        'Authorization': f"Bearer {api_key}",
        'Content-Type': 'application/json',
    }

    data = {
        "query": prompt,
    }

    response = requests.post(prompt_url, headers=headers, json=data)
    if response.status_code != 201:
        raise MaizeyCallError(f"Error {response.status_code}: {response.text}")

    return response.json()["response"]
