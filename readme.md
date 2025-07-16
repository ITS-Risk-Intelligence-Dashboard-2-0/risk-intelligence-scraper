
# Curation UI Setup Guide

## Database Setup

### PostgreSQL on Linux

1. Check if PostgreSQL service is running:
   ```bash
   sudo systemctl status postgresql
   ```
   If it is not active, start it:
   ```bash
   sudo systemctl start postgresql
   ```
2. Create the database `userdb`:
   ```bash
   sudo -u postgres psql -c "CREATE DATABASE userdb;"
   ```

### PostgreSQL on Mac

1. Start the PostgreSQL service:
   ```bash
   brew services start postgresql
   ```
2. Open the PostgreSQL CLI:
   ```bash
   psql postgres
   ```
3. Create the database inside the CLI:
   ```sql
   CREATE DATABASE userdb;
   ```

> You may substitute `userdb` with your preferred database name.

---

## Running the Curation UI

### Backend

1. Change to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install fastapi uvicorn sqlalchemy psycopg2-binary
   ```
4. Start the backend server (using port 4000):
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 4000
   ```

### Frontend

1. Change to the frontend directory:
   ```bash
   cd frontend
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install requests pandas streamlit
   ```
4. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

---

## Additional Resources

- [CRUD FastAPI app with SQLAlchemy - Mattermost Tutorial](https://mattermost.com/blog/building-a-crud-fastapi-app-with-sqlalchemy/)
