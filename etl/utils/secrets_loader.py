"""
PE Sourcing Engine - Secrets Loader
Always reads API keys fresh from secrets.env file.
This bypasses Docker environment variables so admin dashboard updates work.
"""

from pathlib import Path
from typing import Optional

# Path to secrets.env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRETS_FILE = BASE_DIR / "config" / "secrets.env"


def _load_secrets() -> dict:
    """Load all secrets from secrets.env file."""
    secrets = {}
    if SECRETS_FILE.exists():
        with open(SECRETS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    secrets[key.strip()] = value.strip()
    return secrets


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a secret value fresh from secrets.env file.
    
    This function reads from the file each time, so changes made via
    the admin dashboard take effect immediately without container restart.
    
    Args:
        key: The secret key (e.g., 'GOOGLE_PLACES_API_KEY')
        default: Default value if key not found
        
    Returns:
        The secret value or default
    """
    secrets = _load_secrets()
    value = secrets.get(key, default)
    # Return None for empty strings
    if value == '' or value == 'None':
        return default
    return value


def get_google_places_api_key() -> Optional[str]:
    """Get Google Places API key."""
    return get_secret('GOOGLE_PLACES_API_KEY')


def get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key."""
    return get_secret('GEMINI_API_KEY')


def get_serper_api_key() -> Optional[str]:
    """Get Serper API key."""
    return get_secret('SERPER_API_KEY')


def get_db_config() -> dict:
    """Get database configuration."""
    return {
        'host': get_secret('DB_HOST', 'db'),
        'port': get_secret('DB_PORT', '5432'),
        'name': get_secret('DB_NAME', 'pe_sourcing_db'),
        'user': get_secret('DB_USER', 'pe_sourcer'),
        'password': get_secret('DB_PASS', 'changeme'),
    }
