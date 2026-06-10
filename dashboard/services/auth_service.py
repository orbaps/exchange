import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# Secret config for local development
SECRET_KEY = "IICPC_LOCAL_DASHBOARD_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# We'll resolve the users.json location relative to the project root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
USERS_FILE = os.path.join(ROOT_DIR, "dashboard", "users.json")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def load_users() -> Dict[str, Any]:
    if not os.path.exists(USERS_FILE):
        # Fallback defaults if file not found
        return {
            "admin": {"password": "adminpassword", "role": "admin"},
            "judge": {"password": "judgepassword", "role": "admin"},
            "public": {"password": "publicpassword", "role": "public"}
        }
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    users = load_users()
    user = users.get(username)
    if user and user["password"] == password:
        return {"username": username, "role": user["role"]}
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise JWTError()
        return {"username": username, "role": role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    return verify_token(token)

def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required."
        )
    return current_user
