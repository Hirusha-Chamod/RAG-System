"""
User authentication routes:
- POST /auth/signup
- POST /auth/login
- GET /auth/me
"""

import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from app.models.schemas import (
    UserSignupRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)
from app.auth.users_db import (
    create_user,
    get_user_by_username_or_email,
)
from app.auth.security import hash_password, verify_password, create_access_token
from app.auth.rate_limit import check_rate_limit
from app.api.deps import get_current_user
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: UserSignupRequest):
    """Register a new user account and return a JWT access token."""
    check_rate_limit(request.username)
    # Check if username or email already exists
    if get_user_by_username_or_email(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken",
        )
    if get_user_by_username_or_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    user_id = f"user_{str(uuid.uuid4())[:8]}"
    hashed_pwd = hash_password(request.password)

    user = create_user(user_id, request.username, request.email, hashed_pwd)
    token = create_access_token(user["user_id"], user["username"])

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user["user_id"],
        username=user["username"],
        email=user["email"],
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest):
    """Authenticate user credentials and return a JWT access token."""
    check_rate_limit(request.username_or_email)
    user = get_user_by_username_or_email(request.username_or_email)
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
        )

    token = create_access_token(user["user_id"], user["username"])

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user["user_id"],
        username=user["username"],
        email=user["email"],
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return UserResponse(
        user_id=current_user["user_id"],
        username=current_user["username"],
        email=current_user["email"],
        created_at=current_user["created_at"],
    )
