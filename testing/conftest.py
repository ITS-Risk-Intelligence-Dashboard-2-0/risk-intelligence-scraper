# testing/conftest.py

import pytest
import asyncio
from typing import AsyncGenerator
# Import ASGICLient for testing FastAPI applications directly
from httpx import AsyncClient, ASGICLient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import pytest_asyncio

# Import your FastAPI app and database Base from main.py and model.py
from main import app, get_db # We'll override get_db for testing
from model import Base

# --- Test Database Engine Fixture ---
@pytest_asyncio.fixture(scope="session")
async def db_engine_test():
    """
    Provides an in-memory SQLite database engine for testing.
    This database is created once per test session and is destroyed afterwards.
    """
    # Use an in-memory SQLite database for fast, isolated tests
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    print("\n--- Creating in-memory SQLite database for tests ---")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) # Create tables based on models
    yield engine
    print("--- Disposing of in-memory SQLite database ---")
    await engine.dispose()

# --- Test Database Session Fixture ---
@pytest_asyncio.fixture(scope="function")
async def db_session_test(db_engine_test): # Removed AsyncGenerator type hint for simplicity, it's an Engine
    """
    Provides an asynchronous database session for each test function.
    Each test runs within its own transaction, which is rolled back upon completion,
    ensuring test isolation.
    """
    async_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine_test,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    # Use a try-finally block to ensure transaction rollback
    async with async_session() as session:
        # Begin a transaction. This transaction will be rolled back in the finally block.
        # This allows tests to call session.commit() multiple times within their scope,
        # and each commit will effectively just "save" to the current transaction,
        # which is then discarded at the end of the test.
        transaction = await session.begin()
        try:
            yield session
        finally:
            # Ensure the transaction is rolled back, cleaning up after the test
            await transaction.rollback()
            # Also close the session to release resources
            await session.close()


# --- Test FastAPI Client Fixture ---
@pytest_asyncio.fixture(scope="function")
async def client(db_session_test: AsyncSession):
    """
    Provides an asynchronous test client for the FastAPI application.
    It overrides the 'get_db' dependency to use the test database session.
    """
    # Override the get_db dependency to use the test session
    app.dependency_overrides[get_db] = lambda: db_session_test

    # Use ASGICLient for testing FastAPI applications directly
    async with ASGICLient(app=app, base_url="http://test") as ac:
        yield ac

    # Clean up dependency overrides after the test
    app.dependency_overrides.clear()

# --- Asyncio Event Loop Fixture (optional, for explicit control) ---
# If you continue to see warnings about event loop, uncomment this.
# @pytest.fixture(scope="session")
# def event_loop():
#     """Create an instance of the default event loop for each test session."""
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()


