# main.py - Simplified for a key-value table
import os
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from passlib.context import CryptContext
from contextlib import asynccontextmanager

# Import database models (AppConfig will be simplified)
from model import Base, AppConfig, AdminUser # ConfigEnvironment is no longer needed here

# Import SQLAdmin setup function and authentication helpers
from admin import setup_sqladmin, get_admin_user_by_username

# --- Configuration ---
# IMPORTANT: Replace with your actual database credentials
DATABASE_URL = os.environ.get('DATABASE_URL')
# Example: DATABASE_URL = "postgresql+asyncpg://postgres:mypassword@localhost:5432/my_config_db"

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# --- Dependency to Get a Database Session ---
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# FastAPI application init
app = FastAPI(
    title="Config Management System (Key-Value)",
    description="Admin panel and API for managing simple key-value application configurations.",
    version="0.1.0",
)

# --- Lifespan Event: Database Initialization and Default Admin User Creation ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Initializing database and checking for default admin user")

    async with engine.begin() as conn:
        # This will create the 'app_configs' table with 'key' and 'value' and 'admin_users'
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables ensured.")

    async with AsyncSessionLocal() as session:
        existing_admin = await get_admin_user_by_username(session, "admin")
        if not existing_admin:
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed_password = pwd_context.hash("supersecretpassword")

            new_admin = AdminUser(
                username="admin",
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True
            )
            session.add(new_admin)
            await session.commit()
            print("\n!!! IMPORTANT: Default admin user 'admin' created with password 'supersecretpassword'.")
            print("!!!         Change this immediately after first login in production!")
            print("!!!         Consider removing this automatic creation in production deployments.\n")
        else:
            print("Default admin user already exists.")

    yield

    print("Application shutdown: Closing database connections.")
    await engine.dispose()

# Assign the lifespan context manager to the FastAPI app
app.router.lifespan_context = lifespan

# Setup SQLAdmin
setup_sqladmin(app, engine)
print("SQLAdmin panel initialized at /admin")

# API Endpoints
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Config Management System (Key-Value)!"}

@app.get("/api/config/{config_key}", tags=["Config API"], summary="Retrieve application configuration by key")
async def get_config_by_key(
    config_key: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AppConfig).where(AppConfig.key == config_key)
    )
    config_item = result.scalar_one_or_none()

    if not config_item:
        raise HTTPException(
            status_code=404,
            detail=f"Config with key '{config_key}' not found."
        )

    return config_item.value # Return the JSON value directly
