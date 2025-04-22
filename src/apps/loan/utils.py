from cryptography.fernet import Fernet
from django.conf import settings
from base64 import b64encode, b64decode

def get_encryption_key():
    return settings.ENCRYPTION_KEY.encode()

def encrypt_password(password):
    if not password:
        return None
    try:
        f = Fernet(get_encryption_key())
        return b64encode(f.encrypt(password.encode())).decode()
    except Exception:
        return password

def decrypt_password(encrypted_password):
    if not encrypted_password:
        return None
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(b64decode(encrypted_password)).decode()
    except Exception:
        return encrypted_password  # Return as-is if decryption fails
