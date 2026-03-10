import keyring

# Standard: Use your app's name as the service
SERVICE_NAME = "InternMonitor"
ACCOUNT_NAME = "device_token"

def get_device_id() -> int:
    """
    Reliably get hardware ID as an integer.
    """
    import uuid # Local import to check node without global dependency
    node = uuid.getnode()
    
    # RFC 4122 check: if 8th bit is 1, the ID is random/generated
    if (node >> 40) & 0x01:
        # Fallback to a fixed integer or file-based persistent integer
        # Using a hash of a unique string as a fallback integer if node is random
        return 999999999  
        
    return node

def save_device_token(token: str):
    """Store token in OS secure vault via [Keyring](https://pypi.org)."""
    keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, token)

def load_device_token():
    """Retrieve token from OS secure vault."""
    return keyring.get_password(SERVICE_NAME, ACCOUNT_NAME)
