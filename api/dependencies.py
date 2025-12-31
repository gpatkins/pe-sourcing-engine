"""
FastAPI Dependencies for PE Sourcing Engine v5.8
Provides authentication and authorization dependencies for route protection.
"""

from typing import Optional
from fastapi import Cookie, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from api.auth import verify_token, extract_user_from_token, COOKIE_NAME
from api.models import User
from etl.utils.db import get_db_connection
import psycopg


def get_db_session():
    """
    Dependency to get database session.
    Creates a new psycopg connection for each request.
    
    Yields:
        Database connection
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


async def get_current_user_optional(
    access_token: Optional[str] = Cookie(None, alias=COOKIE_NAME)
) -> Optional[dict]:
    """
    Optional authentication dependency.
    Returns user data if valid token exists, None otherwise.
    Does NOT raise exceptions - useful for pages that work with/without auth.
    
    Args:
        access_token: JWT token from cookie
        
    Returns:
        User data dict if authenticated, None otherwise
    """
    if not access_token:
        return None
    
    # Remove "Bearer " prefix if present
    if access_token.startswith("Bearer "):
        access_token = access_token[7:]
    
    user_data = extract_user_from_token(access_token)
    return user_data


async def get_current_user(
    access_token: Optional[str] = Cookie(None, alias=COOKIE_NAME)
) -> dict:
    """
    Required authentication dependency.
    Redirects to /login if no valid token exists.
    Use this for protected routes that require login.
    
    Args:
        access_token: JWT token from cookie
        
    Returns:
        User data dict (user_id, email, role)
        
    Raises:
        HTTPException: 303 redirect to /login if not authenticated
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    
    # Remove "Bearer " prefix if present
    if access_token.startswith("Bearer "):
        access_token = access_token[7:]
    
    user_data = extract_user_from_token(access_token)
    
    if user_data is None:
        # Token invalid or expired - redirect to login
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    
    return user_data


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db_session)
) -> dict:
    """
    Get current user and verify they are active in database.
    
    Args:
        current_user: User data from token
        db: Database connection
        
    Returns:
        User data dict
        
    Raises:
        HTTPException: 303 redirect to /login if user is inactive
    """
    cursor = db.cursor()
    cursor.execute(
        "SELECT is_active FROM users WHERE id = %s",
        (current_user["user_id"],)
    )
    result = cursor.fetchone()
    cursor.close()
    
    if not result or not result[0]:
        # User inactive - redirect to login
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    
    return current_user


async def require_admin(
    current_user: dict = Depends(get_current_active_user)
) -> dict:
    """
    Admin-only route protection.
    Raises HTTPException if user is not an admin.
    
    Args:
        current_user: User data from token
        
    Returns:
        User data dict
        
    Raises:
        HTTPException: 403 if user is not admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this action.",
        )
    
    return current_user


async def get_user_companies_filter(
    current_user: dict = Depends(get_current_active_user)
) -> dict:
    """
    Returns SQL filter for user's companies.
    Admins see all companies, regular users see only their own.
    
    Args:
        current_user: User data from token
        
    Returns:
        Dict with filter SQL and parameters
    """
    if current_user.get("role") == "admin":
        # Admin sees all companies
        return {
            "where_clause": "",
            "params": {}
        }
    else:
        # Regular user sees only their companies
        return {
            "where_clause": "WHERE user_id = %(user_id)s",
            "params": {"user_id": current_user["user_id"]}
        }


def log_user_activity(
    db: psycopg.Connection,
    user_id: int,
    activity_type: str,
    details: Optional[dict] = None
):
    """
    Log user activity to database.
    
    Args:
        db: Database connection
        user_id: User ID
        activity_type: Type of activity (use ActivityType constants)
        details: Optional JSON details
    """
    import json
    
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO user_activity (user_id, activity_type, details)
        VALUES (%s, %s, %s)
        """,
        (user_id, activity_type, json.dumps(details) if details else None)
    )
    db.commit()
    cursor.close()
