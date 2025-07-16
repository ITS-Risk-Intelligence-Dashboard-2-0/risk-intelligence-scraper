# admin.py - Adjusted for a simple key-value table 
import json
import yaml
from sqladmin import Admin, ModelView
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.authentication import AuthCredentials, SimpleUser
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND

# Import your models (AppConfig will be simplified)
from Backend.model import AppConfig, AdminUser # ConfigEnvironment is no longer needed for AppConfig

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- AdminUser Authentication Helpers (remain the same) ---
async def get_admin_user_by_username(session: AsyncSession, username: str):
    """Retrieves an AdminUser by username."""
    result = await session.execute(select(AdminUser).where(AdminUser.username == username))
    return result.scalar_one_or_none()

def verify_admin_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

# --- Custom Authentication Backend for SQLAdmin (remains the same) ---
class SQLAdminAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/admin") and not request.url.path.startswith("/admin/static"):
            if request.session.get("is_authenticated"):
                request.scope["auth"] = AuthCredentials(["authenticated"])
                request.scope["user"] = SimpleUser(request.session.get("username"))
            else:
                if request.url.path != "/admin/login":
                    return RedirectResponse(url="/admin/login", status_code=HTTP_302_FOUND)
        response = await call_next(request)
        return response

# --- SQLAdmin Setup Function (remains the same) ---
def setup_sqladmin(app, engine):
    """
    Initializes SQLAdmin with the FastAPI app and SQLAlchemy engine.
    Registers ModelViews and adds authentication middleware.
    """
    admin = Admin(app, engine)
    admin.add_view(AppConfigAdmin)
    admin.add_view(AdminUserAdmin)
    app.add_middleware(SQLAdminAuthMiddleware)
    return admin

# --- ModelView Definitions ---

class AppConfigAdmin(ModelView, model=AppConfig):
    """
    Admin view for AppConfig model, simplified for key-value.
    """
    column_list = [AppConfig.id, AppConfig.key, AppConfig.value, AppConfig.created_at, AppConfig.updated_at]
    column_details_list = [AppConfig.id, AppConfig.key, AppConfig.value, AppConfig.created_at, AppConfig.updated_at]
    column_searchable_list = [AppConfig.key]
    column_sortable_list = [AppConfig.key, AppConfig.created_at, AppConfig.updated_at]
    form_columns = [AppConfig.key, AppConfig.value]

    # No custom on_model_change needed here, as 'value' is directly JSONB
    # and 'key' is a simple string.

class AdminUserAdmin(ModelView, model=AdminUser):
    """
    Admin view for AdminUser model.
    Handles password hashing on creation and update.
    """
    column_details_list = [AdminUser.id, AdminUser.username, AdminUser.is_superuser, AdminUser.is_active, AdminUser.created_at, AdminUser.updated_at]
    column_searchable_list = [AdminUser.username]
    column_sortable_list = [AdminUser.username, AdminUser.is_superuser, AdminUser.is_active, AdminUser.created_at]
    form_columns = [AdminUser.username, AdminUser.is_superuser, AdminUser.is_active, "password"]
    column_exclude_list = [AdminUser.hashed_password]

    async def on_model_change(self, request: Request, data, model, is_created):
        if "password" in data and data["password"]:
            model.hashed_password = pwd_context.hash(data["password"])
            del data["password"]
        elif is_created and not model.hashed_password:
            raise ValueError("Password is required for new admin users.")
        return await super().on_model_change(request, data, model, is_created)
