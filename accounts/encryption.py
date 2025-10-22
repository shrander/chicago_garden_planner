"""
Encryption utilities for sensitive data storage.

Uses Fernet symmetric encryption from the cryptography library.
The encryption key is derived from Django's SECRET_KEY.
"""
from cryptography.fernet import Fernet
from django.conf import settings
import hashlib
import base64


def get_encryption_key():
    """
    Generate a Fernet-compatible encryption key from Django's SECRET_KEY.

    Returns a consistent 32-byte base64-encoded key derived from SECRET_KEY.
    """
    # Use SHA256 to create a consistent 32-byte key from SECRET_KEY
    key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    # Base64 encode to make it Fernet-compatible
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_value(plaintext):
    """
    Encrypt a string value.

    Args:
        plaintext (str): The string to encrypt

    Returns:
        str: The encrypted value as a base64-encoded string, or empty string if input is empty
    """
    if not plaintext:
        return ''

    key = get_encryption_key()
    fernet = Fernet(key)
    encrypted_bytes = fernet.encrypt(plaintext.encode())
    return encrypted_bytes.decode()


def decrypt_value(encrypted_text):
    """
    Decrypt an encrypted string value.

    Args:
        encrypted_text (str): The encrypted base64-encoded string

    Returns:
        str: The decrypted plaintext string, or empty string if input is empty

    Raises:
        cryptography.fernet.InvalidToken: If decryption fails (wrong key or corrupted data)
    """
    if not encrypted_text:
        return ''

    key = get_encryption_key()
    fernet = Fernet(key)
    decrypted_bytes = fernet.decrypt(encrypted_text.encode())
    return decrypted_bytes.decode()
