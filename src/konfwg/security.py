import bcrypt
import secrets
import hashlib

from konfwg.config import configuration
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

COOKIE_NAME = "conf_auth"
COOKIE_TTL = configuration.DEFAULT_TTL

serializer = URLSafeTimedSerializer(
    secret_key=configuration.SECRET,
    salt="konfwg-conf-auth",
    signer_kwargs={"digest_method": hashlib.sha256},
)

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def generate_url_token(length: int = 25) -> str:
    return secrets.token_urlsafe(length)

def generate_password(length: int = 12) -> str:
    return secrets.token_urlsafe(length)

def create_cookie(site_id: int) -> str:
    payload = {"site_id": site_id}
    return serializer.dumps(payload)

def read_cookie(cookie_value: str | None) -> dict | None:
    if not cookie_value:
        return None
    
    try:
        data = serializer.loads(cookie_value, max_age=COOKIE_TTL)
        return data if isinstance(data, dict) else None
    except SignatureExpired:
        return None
    except BadSignature:
        return None