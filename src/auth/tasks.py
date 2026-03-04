from pydantic import BaseModel, field_validator

from .models import User
from sqlalchemy.orm import Session


def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str,email:str, hashed_password: str, role: str):
    user_db = User(username=username, email=email, hashed_password=hashed_password, role=role)
    db.add(user_db)
    db.commit()
    db.refresh(user_db)
    return user_db