import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Request, HTTPException, Depends
from jose import JWTError, jwt
from shared_schemas.rbac import RBACRole, RBACUser

# In a production environment, this should be loaded securely from env
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sovereign-local-dev-secret-do-not-use-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

class RBACGuard:
    """FastAPI dependency to enforce RBAC minimum role requirements."""
    
    def __init__(self, minimum_role: RBACRole):
        self.minimum_role = minimum_role

    async def __call__(self, request: Request) -> RBACUser:
        """Extract user from request and validate permissions."""
        # Attempt to get auth token from header
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_access_token(token)
            
            try:
                user = RBACUser(
                    user_id=payload.get("user_id"),
                    username=payload.get("username", "Unknown"),
                    role=RBACRole(payload.get("role")),
                    department=payload.get("department", "Unknown"),
                    plant_unit=payload.get("plant_unit", "Unknown")
                )
            except (ValueError, TypeError) as e:
                raise HTTPException(status_code=401, detail="Invalid token payload format")
                
        else:
            # Fallback to headers for development/testing ease
            user_id = request.headers.get("X-User-ID")
            role_val = request.headers.get("X-User-Role")
            
            if not user_id or not role_val:
                raise HTTPException(
                    status_code=401, 
                    detail="Authentication required. Missing Bearer token or X-User headers."
                )
                
            try:
                role = RBACRole(int(role_val))
                user = RBACUser(
                    user_id=user_id,
                    username=request.headers.get("X-Username", "Unknown"),
                    role=role,
                    department=request.headers.get("X-Department", "Unknown"),
                    plant_unit=request.headers.get("X-Plant-Unit", "Unknown")
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid role value in header")

        if user.role < self.minimum_role:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {self.minimum_role.name}, Current: {user.role.name}"
            )
            
        return user

def require_role(minimum_role: RBACRole):
    """Factory function for FastAPI Depends."""
    return Depends(RBACGuard(minimum_role))
