"""
Authentication utilities for PE Sourcing Engine v5.1
Handles password hashing, JWT token generation/validation, and user authentication.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from email_validator import validate_email, EmailNotValidError
import os

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def validate_email_address(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email, False otherwise
    """
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets minimum security requirements.
    
    Requirements:
    - At least 8 characters long
    - Contains at least one number or special character
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    has_number_or_special = any(c.isdigit() or not c.isalnum() for c in password)
    if not has_number_or_special:
        return False, "Password must contain at least one number or special character"
    
    return True, ""


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of data to encode in token (typically user_id, email, role)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def extract_user_from_token(token: str) -> Optional[dict]:
    """
    Extract user information from a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary with user_id, email, and role if valid, None otherwise
    """
    payload = verify_token(token)
    if payload is None:
        return None
    
    user_id: int = payload.get("user_id")
    email: str = payload.get("email")
    role: str = payload.get("role")
    
    if user_id is None or email is None or role is None:
        return None
    
    return {
        "user_id": user_id,
        "email": email,
        "role": role
    }


def is_admin_user(token: str) -> bool:
    """
    Check if a token belongs to an admin user.
    
    Args:
        token: JWT token string
        
    Returns:
        True if user is admin, False otherwise
    """
    user_data = extract_user_from_token(token)
    if user_data is None:
        return False
    
    return user_data.get("role") == "admin"


# Token cookie configuration
COOKIE_NAME = "access_token"
COOKIE_MAX_AGE = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds


def get_token_from_cookie(cookies: dict) -> Optional[str]:
    """
    Extract JWT token from cookies.
    
    Args:
        cookies: Request cookies dictionary
        
    Returns:
        Token string if found, None otherwise
    """
    token = cookies.get(COOKIE_NAME)
    if token and token.startswith("Bearer "):
        return token[7:]  # Remove "Bearer " prefix
    return token
