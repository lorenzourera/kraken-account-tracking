"""Configuration and settings"""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://trading_user:password@localhost:5432/trading')
KRAKEN_API_KEY = os.getenv('KRAKEN_MAIN_API_KEY')
KRAKEN_API_SECRET = os.getenv('KRAKEN_MAIN_API_SECRET')

# Account identifier (optional - for tracking multiple accounts)
# If not set, will use last 8 chars of API key
ACCOUNT_ID = os.getenv('ACCOUNT_ID', None)


def get_account_id(api_key: str, account_name: str = None) -> str:
    """
    Generate account identifier
    
    Priority:
    1. Use ACCOUNT_ID from .env if set (e.g., "main_account", "trading_bot")
    2. Otherwise use last 8 characters of API key
    
    Args:
        api_key: The API key
        account_name: Optional override from .env
    
    Returns:
        Account identifier string
    """
    if account_name:
        return account_name
    
    # Use last 8 characters of API key as fallback
    return api_key[-8:] if len(api_key) >= 8 else api_key