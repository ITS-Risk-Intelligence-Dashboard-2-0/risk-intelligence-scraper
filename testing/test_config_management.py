# testing/test_config_management.py - Adapted for simple key-value table

import pytest
import json
import yaml # Still imported, but less critical for simple JSON values
import textwrap
from sqlalchemy import select
from httpx import AsyncClient
import asyncio
from datetime import datetime, timedelta

# Import your simplified models and admin views
from model import AppConfig, AdminUser, Base # ConfigEnvironment is no longer part of AppConfig
from admin import AppConfigAdmin, AdminUserAdmin
from admin import pwd_context
from starlette.requests import Request

# Mock Request object for on_model_change calls
class MockRequest:
    def __init__(self):
        self.session = {}
        self.state = {}

# ==============================================================================
# AppConfig ModelView Tests (Admin Panel Logic - Simplified)
# ==============================================================================

@pytest.mark.asyncio
async def test_app_config_creation_direct_json_input(db_session_test):
    """
    Tests creating an AppConfig with a direct Python dictionary input,
    ensuring it's stored as JSON.
    """
    db = db_session_test

    direct_json_input = {
        "setting_a": "value_1",
        "nested_param": {"sub_key": 123, "status": True}
    }

    new_config = AppConfig(
        key="test_config_key_creation",
        value=direct_json_input,
    )

    db.add(new_config)
    await db.commit()
    await db.refresh(new_config)

    stmt = select(AppConfig).where(AppConfig.key == "test_config_key_creation")
    result = await db.execute(stmt)
    retrieved_config = result.scalar_one_or_none()

    assert retrieved_config is not None
    assert retrieved_config.key == "test_config_key_creation"
    assert retrieved_config.value == direct_json_input
    assert retrieved_config.id is not None
    assert retrieved_config.created_at is not None
    assert retrieved_config.updated_at is not None


@pytest.mark.asyncio
async def test_app_config_update_value_and_timestamp(db_session_test):
    """
    Tests that updating an AppConfig's value updates its timestamp.
    """
    db = db_session_test

    initial_value_dict = {"param1": "old_value"}
    config = AppConfig(
        key="update_test_key",
        value=initial_value_dict,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    initial_updated_at = config.updated_at

    await asyncio.sleep(0.05) # Ensure a measurable time difference

    updated_value_dict = {"param1": "new_value", "new_setting": True}
    config.value = updated_value_dict

    await db.commit()
    await db.refresh(config)

    stmt = select(AppConfig).where(AppConfig.key == "update_test_key")
    result = await db.execute(stmt)
    retrieved_config = result.scalar_one_or_none()

    assert retrieved_config is not None
    assert retrieved_config.value == updated_value_dict
    assert retrieved_config.updated_at > initial_updated_at


@pytest.mark.asyncio
async def test_app_config_unique_key_constraint_violation(db_session_test):
    """
    Tests that creating an AppConfig with a duplicate key raises an IntegrityError.
    """
    db = db_session_test

    config1 = AppConfig(
        key="duplicate_key_test",
        value={"foo": "bar"}
    )
    db.add(config1)
    await db.commit()
    await db.refresh(config1)

    config2 = AppConfig(
        key="duplicate_key_test", # Same key, should cause conflict
        value={"baz": "qux"}
    )
    db.add(config2)

    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback() # Rollback the session after the failed commit


# ==============================================================================
# AdminUser ModelView Tests (Admin Panel Logic) - These remain largely unchanged
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_user_password_hashing_on_creation(db_session_test):
    """
    Tests that AdminUser passwords are hashed correctly on creation.
    """
    db = db_session_test
    admin_view = AdminUserAdmin()
    mock_request = MockRequest()

    user_data = {"username": "newtestadmin", "password": "securepassword456", "is_superuser": False}
    new_user = AdminUser(username=user_data["username"])

    await admin_view.on_model_change(mock_request, user_data, new_user, is_created=True)

    assert "password" not in user_data
    assert new_user.hashed_password is not None
    assert pwd_context.verify("securepassword456", new_user.hashed_password)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    retrieved_user = await db.execute(select(AdminUser).where(AdminUser.username == "newtestadmin"))
    retrieved_user = retrieved_user.scalar_one_or_none()
    assert retrieved_user is not None
    assert pwd_context.verify("securepassword456", retrieved_user.hashed_password)


@pytest.mark.asyncio
async def test_admin_user_password_hashing_on_update(db_session_test):
    """
    Tests that AdminUser passwords are re-hashed when updated.
    """
    db = db_session_test

    initial_password = "old_password_123"
    user = AdminUser(username="updateuser", hashed_password=pwd_context.hash(initial_password), is_active=True)

    db.add(user)
    await db.commit()
    await db.refresh(user)

    old_hashed_password = user.hashed_password

    admin_view = AdminUserAdmin()
    mock_request = MockRequest()
    update_data = {"password": "very_new_secure_password"}

    await admin_view.on_model_change(mock_request, update_data, user, is_created=False)

    assert user.hashed_password != old_hashed_password
    assert pwd_context.verify("very_new_secure_password", user.hashed_password)

    await db.commit()
    await db.refresh(user)

    retrieved_user = await db.execute(select(AdminUser).where(AdminUser.username == "updateuser"))
    retrieved_user = retrieved_user.scalar_one_or_none()
    assert retrieved_user is not None
    assert pwd_context.verify("very_new_secure_password", retrieved_user.hashed_password)


@pytest.mark.asyncio
async def test_admin_user_creation_requires_password(db_session_test):
    """
    Tests that creating a new AdminUser without a password raises a ValueError.
    """
    db = db_session_test
    admin_view = AdminUserAdmin()
    mock_request = MockRequest()

    user_data = {"username": "nopassworduser", "is_superuser": False}
    new_user = AdminUser(username=user_data["username"])

    with pytest.raises(ValueError, match="Password is required for new admin users."):
        await admin_view.on_model_change(mock_request, user_data, new_user, is_created=True)

    result = await db.execute(select(AdminUser).where(AdminUser.username == "nopassworduser"))
    retrieved_user = result.scalar_one_or_none()
    assert retrieved_user is None


# ==============================================================================
# FastAPI Endpoint Tests - Adjusted for simple key-value API
# ==============================================================================

@pytest.mark.asyncio
async def test_get_config_endpoint_returns_json_by_key(client: AsyncClient, db_session_test):
    """
    Tests that the /api/config/{config_key} endpoint retrieves JSON data correctly.
    """
    db = db_session_test
    c = client

    expected_data = {
        "api_setting": "value_from_db",
        "status": "active",
        "list_data": [1, {"nested": "value"}],
    }
    config = AppConfig(
        key="api_retrieve_test_key",
        value=expected_data,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    response = await c.get("/api/config/api_retrieve_test_key")

    assert response.status_code == 200
    assert response.json() == expected_data


@pytest.mark.asyncio
async def test_get_config_endpoint_not_found_by_key(client: AsyncClient):
    """
    Tests that the endpoint returns 404 for a non-existent config key.
    """
    c = client
    response = await c.get("/api/config/non_existent_key_xyz")
    assert response.status_code == 404
    assert response.json() == {"detail": "Config with key 'non_existent_key_xyz' not found."}

