import secrets
from datetime import datetime, timedelta
import string # Import string module for alphabet generation

# Use one length variable for consistency
TOKEN_LENGTH = 8 
PAIRING_EXPIRE_MINUTES = 10

def generate_pairing_code() -> str:
    # Fix 1: Use the correct variable name TOKEN_LENGTH
    # Use alphanumeric characters for an exact length guarantee
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(TOKEN_LENGTH))


def generate_device_token() -> str:
    # Fix 2: Use the 8-character length for the main device token
    # This matches the function above and your requirement for shorter IDs
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(TOKEN_LENGTH))


def pairing_expiry_time():
    return datetime.utcnow() + timedelta(minutes=PAIRING_EXPIRE_MINUTES)
