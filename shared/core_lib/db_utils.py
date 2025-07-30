# from sqlalchemy import text
# from sqlalchemy.orm import sessionmaker
# from shared.core_lib.models import engine, Article, Sources
import uuid

import psycopg2
import os

def seed_sources(conn, cursor):
    query = "INSERT INTO sources (netloc, path, depth, target) VALUES (%s, %s, %s, %s)"
    values = ("www.gallup.com", "/corporate/470660/reports-perspective-papers.aspx", 1, "website")

    cursor.execute(query, values)

    conn.commit()

def establish_connection():
    DB_USER = os.environ.get("POSTGRES_USER", "default_user")
    DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "default_password")
    DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
    DB_NAME = os.environ.get("POSTGRES_DB", "default_db")

    #DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    DATABASE_URL = os.environ.get("DATABASE_URL", "None")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        return (conn, conn.cursor())

    except:
        print("Connection to database failed!")
        return None
