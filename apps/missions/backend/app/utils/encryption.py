"""API key encryption utilities using Fernet."""
from cryptography.fernet import Fernet
import os


def get_cipher() -> Fernet:
    """Get Fernet cipher instance from environment variable."""
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if not encryption_key:
        raise ValueError("ENCRYPTION_KEY environment variable not set")

    # Ensure the key is bytes
    if isinstance(encryption_key, str):
        encryption_key = encryption_key.encode()

    return Fernet(encryption_key)


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key.

    Args:
        api_key: Plain text API key

    Returns:
        Encrypted API key as base64-encoded string
    """
    cipher = get_cipher()
    encrypted = cipher.encrypt(api_key.encode())
    return encrypted.decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key.

    Args:
        encrypted_key: Base64-encoded encrypted API key

    Returns:
        Plain text API key
    """
    cipher = get_cipher()
    decrypted = cipher.decrypt(encrypted_key.encode())
    return decrypted.decode()
