from passlib.context import CryptContext
from passlib.hash import argon2
import hashlib
from jose import jwt
from datetime import datetime, timedelta
from src.auth.models import User
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return argon2.hash(password)


def get_user(db, username: str):
    return db.query(User).filter(User.username == username).first()

def verify_password(plain: str, hashed: str) -> bool:
    return argon2.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithm=ALGORITHM)
        return payload.get("sub")
    except jwt.PyJWTError:
        return None