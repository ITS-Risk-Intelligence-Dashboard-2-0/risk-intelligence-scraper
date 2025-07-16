# model.py - Simplified for a key-value table
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, Text, Boolean
from sqlalchemy.dialects.postgresql import JSON # Still good for storing the 'value' as JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base # Deprecated in SQLAlchemy 2.0+

# Using the recommended import for declarative_base for SQLAlchemy 2.0+
# If you are using an older version of SQLAlchemy, keep the original import.
Base = declarative_base() # Base of all sqlalchemy models

# No ConfigEnvironment enum needed if environments are not explicitly managed

# Simplified AppConfig for a key-value store
class AppConfig(Base):
    __tablename__ = "app_configs" # You can rename this to match your existing table if desired
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False) # The unique key for the config
    value = Column(JSON, nullable=False) # Stores the actual JSON content. JSONB is efficient for PostgreSQL.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    __table_args__ = (
        # Only 'key' needs to be unique for a simple key-value store
        UniqueConstraint('key', name='_key_uc'),
    )

    def __repr__(self):
        return f"<AppConfig(key='{self.key}')>"

# AdminUser model remains the same
class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(Integer, primary_key=True, index = True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False) # storing password
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False) # For fine-grained permission
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AdminUser(username='{self.username}')>"
