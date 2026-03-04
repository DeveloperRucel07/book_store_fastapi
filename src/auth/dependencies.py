from fastapi import Depends, HTTPException, Request, status, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from typing import List
from .tasks import get_user
from .security import SECRET_KEY, ALGORITHM
from sqlalchemy.orm import Session
from database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(request: Request , db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Credentials was not provided"
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username: str | None = payload.get("sub")
        role: str | None = payload.get("role")

        if username is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = get_user(db, username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user

def require_roles(allowed_roles: List[str]):

    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
        return current_user

    return role_checker