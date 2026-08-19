"""
JWT authentication core.

Closes the "no authN/authZ on any route" gap named in the Security
Architecture (current state) diagram and Risk Register item #1.

Scope note (state this in the viva): this is a minimal, single-role
JWT implementation suitable for a proof-of-concept. It demonstrates the
mechanism (issue token -> verify token -> protect route) required by
the target-state security architecture. A production deployment would
add: user store (not hardcoded), refresh tokens, MFA on the admin
route, and token revocation.
"""
import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-only-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# POC user store. Replace with a real users table before production use.
_DEMO_USERS = {
    "analyst": {
        "username": "analyst",
        "hashed_password": pwd_context.hash("changeme_demo_only"),
        "role": "financial_analyst",
    },
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("changeme_admin_only"),
        "role": "security_admin",
    },
}


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(username: str, password: str):
    user = _DEMO_USERS.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = _DEMO_USERS.get(username)
    if user is None:
        raise credentials_exception
    return user


def require_role(role: str):
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] != role and user["role"] != "security_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {role}",
            )
        return user

    return checker
