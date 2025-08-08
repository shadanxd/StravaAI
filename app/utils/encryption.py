"""
Encryption Utilities
Handles token encryption and decryption for secure storage
"""
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Use existing ENCRYPTION_KEY from .env
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY not found in .env file")

# Create Fernet cipher using existing key
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
