import streamlit as st
import requests

# TODO: add an option to delete articles (option to delete by default)

st.title("User Creator")

username = st.text_input("Username")
email = st.text_input("Email")

if st.button("Create User"):
    response = requests.post(
        "http://server:4000/users/create/", json={"username": username, "email": email}
    )
    st.write(response.json())


st.title("List of users")

# Fetch users from FastAPI GET /
response = requests.get("http://server:4000/users/")
print("Status code:", response.status_code)
print("Response text:", response.text) 
if response.status_code == 200:
    users = response.json()
    if users:
        # Display as a table with Streamlit
        st.table(users)
    else:
        st.write("No users found.")
else:
    st.write("Failed to fetch users from backend.")