"""Authentication endpoints."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth.token import (
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_refresh_token,
    validate_access_token,
    blacklist_token,
    is_token_blacklisted,
)
from database import get_db
from models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticate user and return access + refresh tokens."""
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    token_data = {"sub": user.username, "user_id": user.id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 1800,  # 30 minutes
    }


@router.post("/refresh")
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token."""
    body = await request.json()
    refresh_token = body.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required",
        )

    # Check blacklist
    if is_token_blacklisted(refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    try:
        payload = validate_refresh_token(refresh_token)
        username = payload.get("sub")
        user_id = payload.get("user_id")

        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Check if user still exists and is active
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Blacklist old refresh token (rotation)
        blacklist_token(refresh_token)

        # Issue new token pair
        token_data = {"sub": username, "user_id": user_id}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,
        }

    except HTTPException:
        raise
    except Exception as e:
        # Log the error for debugging
        print(f"Refresh token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.post("/logout")
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
):
    """Logout user by blacklisting tokens."""
    body = await request.json()
    refresh_token = body.get("refresh_token")

    # Blacklist access token
    blacklist_token(token)

    # Blacklist refresh token if provided
    if refresh_token:
        blacklist_token(refresh_token)

    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Get current user info."""
    payload = validate_access_token(token)
    user_id = payload.get("user_id")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
    }