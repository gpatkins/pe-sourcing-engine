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
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PASSWORD_CHANGED = "password_changed"
    ENV_VAR_UPDATE = "env_var_update"
    SYSTEM_CLEANUP = "system_cleanup"
    APP_RESTART = "app_restart"
