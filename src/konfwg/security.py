import bcrypt
import secrets

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def generate_url_token(length: int = 25) -> str:
    return secrets.token_urlsafe(length)

def generate_password(length: int = 12) -> str:
    return secrets.token_urlsafe(length)