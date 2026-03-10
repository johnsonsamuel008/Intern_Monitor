from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta

from app.schemas.auth import LoginRequest, Token
from app.schemas.users import UserResponse
from app.database import get_db
from app.models import User  # Required for DB queries
from app.security import verify_password, create_access_token, decode_access_token
from app.dependencies import get_current_user, security

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    POST /auth/login: Exchange credentials for a JWT (Functional Requirement 3.1).
    """
    user = db.query(User).filter(User.username == data.username).first()

    if not user or not verify_password(data.password, user.password_hash) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials or inactive user"
        )

    access_token_expires = timedelta(minutes=30)
    # user.id is now an integer; str() is still fine for the 'sub' claim in JWT
    token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires,
    )

    return {"access_token": token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """
    POST /auth/refresh: Keep dashboard sessions alive (Functional Requirement 3.1).
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id_raw = payload.get("sub")
        if not user_id_raw:
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        try:
            user_id = int(user_id_raw)
        except (ValueError, TypeError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user identifier")

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or non-existent user")

        access_token_expires = timedelta(minutes=30)
        new_token = create_access_token(
            subject=str(user.id),
            expires_delta=access_token_expires,
        )
        return {"access_token": new_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    GET /auth/me: Returns current user role and profile (Functional Requirement 3.1).
    Note: current_user is the SQLAlchemy model, response_model handles serialization.
    """
    return current_user
