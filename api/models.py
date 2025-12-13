"""
SQLAlchemy Database Models for PE Sourcing Engine v5.1
Defines User, ApiCredential, and UserActivity models for authentication system.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class User(Base):
    """
    User model for authentication and authorization.
    Supports two roles: 'admin' (full access) and 'user' (limited access).
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), nullable=False, default='user', index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")
    api_credential_updates = relationship("ApiCredential", back_populates="updated_by_user")
    
    # Add constraint for role validation
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'user')", name='check_user_role'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    @property
    def is_admin(self):
        """Check if user has admin privileges."""
        return self.role == 'admin'


class ApiCredential(Base):
    """
    Centralized API credential storage.
    Only admins can view and update these credentials.
    """
    __tablename__ = 'api_credentials'
    
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(100), unique=True, nullable=False, index=True)
    api_key = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationship
    updated_by_user = relationship("User", back_populates="api_credential_updates")
    
    def __repr__(self):
        return f"<ApiCredential(service='{self.service_name}', active={self.is_active})>"
    
    @property
    def masked_key(self):
        """Return masked API key for display (shows only last 4 characters)."""
        if not self.api_key or len(self.api_key) < 8:
            return "****"
        return f"{'*' * (len(self.api_key) - 4)}{self.api_key[-4:]}"


class UserActivity(Base):
    """
    Activity log for tracking user actions.
    Used for audit trails and usage analytics.
    """
    __tablename__ = 'user_activity'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    activity_type = Column(String(100), nullable=False, index=True)
    details = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship
    user = relationship("User", back_populates="activities")
    
    def __repr__(self):
        return f"<UserActivity(user_id={self.user_id}, type='{self.activity_type}', at={self.created_at})>"


# Activity type constants for consistency
class ActivityType:
    """Constants for user activity types."""
    LOGIN = "login"
    LOGOUT = "logout"
    DISCOVERY_RUN = "discovery_run"
    ENRICHMENT_RUN = "enrichment_run"
    EXPORT_DATA = "export_data"
    API_KEY_UPDATE = "api_key_update"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PASSWORD_CHANGED = "password_changed"
