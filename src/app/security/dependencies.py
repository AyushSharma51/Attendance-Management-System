import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from fastapi import Header

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


MONITORING_SECRET = os.getenv("SECRET_KEY", "your-secret")
ALGORITHM = "HS256"

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials 

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


#  Role-based access control
def require_role(allowed_roles: list[str]):
    def role_checker(user=Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not allowed")
        return user

    return role_checker

def require_monitoring_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Monitoring token required")

    try:
        scheme, token = authorization.split()

        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")

        payload = jwt.decode(token, MONITORING_SECRET, algorithms=[ALGORITHM])

        # 🔐 IMPORTANT: ensure it's monitoring token
        if payload.get("role") != "monitoring_officer":
            raise HTTPException(status_code=403, detail="Invalid monitoring token")

        return payload

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired monitoring token")