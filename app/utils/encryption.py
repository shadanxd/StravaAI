"""
Encryption Utilities
Handles token encryption and decryption for secure storage
"""
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Get encryption key from environment or generate one
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a key for development (should be set in production)
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"Generated encryption key: {ENCRYPTION_KEY}")

# Create Fernet cipher
try:
    cipher = Fernet(ENCRYPTION_KEY.encode())
except ValueError as e:
    print(f"Invalid encryption key: {e}")
    # Generate a new key if the current one is invalid
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"Generated new encryption key: {ENCRYPTION_KEY}")
    cipher = Fernet(ENCRYPTION_KEY.encode())

def encrypt_token(token: str) -> str:
    """Encrypt a token for secure storage"""
    if not token:
        return ""
    try:
        encrypted_data = cipher.encrypt(token.encode())
        return encrypted_data.decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return ""

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a token for use"""
    if not encrypted_token:
        return ""
    try:
        decrypted_data = cipher.decrypt(encrypted_token.encode())
        return decrypted_data.decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return ""
