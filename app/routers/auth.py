"""
Authentication & Authorization API Router (OAuth2 / JWT / Keycloak OIDC)
=======================================================================
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from src.security.auth_service import (
    DEFAULT_USERS_DB,
    UserPayload,
    TokenResponse,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
    validate_keycloak_token,
    RoleChecker,
)

router = APIRouter(prefix="/auth", tags=["Authentication & IAM"])


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    roles: List[str] = ["viewer"]


class RefreshRequest(BaseModel):
    refresh_token: str


class KeycloakVerifyRequest(BaseModel):
    token: str


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, getting an access token for future requests.
    Default test users:
      - admin: admin123 (roles: admin, researcher, viewer)
      - researcher: research123 (roles: researcher, viewer)
      - user: user123 (roles: viewer)
    """
    user_record = DEFAULT_USERS_DB.get(form_data.username)
    if not user_record or not verify_password(form_data.password, user_record["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    roles = user_record.get("roles", ["viewer"])
    token_data = {
        "sub": user_record["username"],
        "email": user_record.get("email"),
        "roles": roles,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600,
        roles=roles,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(request: RefreshRequest):
    """Generate a new access token using a valid refresh token."""
    payload = decode_token(request.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided token is not a refresh token."
        )

    username = payload.get("sub")
    roles = payload.get("roles", ["viewer"])
    new_token_data = {"sub": username, "roles": roles, "email": payload.get("email")}

    return TokenResponse(
        access_token=create_access_token(new_token_data),
        refresh_token=request.refresh_token,
        expires_in=3600,
        roles=roles,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(request: RegisterRequest):
    """Register a new user in the system."""
    if request.username in DEFAULT_USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{request.username}' is already registered."
        )

    DEFAULT_USERS_DB[request.username] = {
        "username": request.username,
        "email": str(request.email),
        "hashed_password": hash_password(request.password),
        "roles": request.roles,
        "is_active": True,
    }

    return {"status": "created", "username": request.username, "roles": request.roles}


@router.get("/me", response_model=UserPayload)
async def read_current_user_profile(current_user: UserPayload = Depends(get_current_user)):
    """Return the profile and roles of the currently authenticated user."""
    return current_user


@router.post("/keycloak-verify")
async def verify_keycloak_oidc_token(request: KeycloakVerifyRequest):
    """Validate a Keycloak OIDC Bearer Token and return identity claims."""
    user = validate_keycloak_token(request.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Keycloak OIDC token format.")
    return {
        "status": "valid",
        "user": user.model_dump(),
        "provider": "Keycloak OIDC",
    }


@router.get("/admin-only")
async def admin_only_endpoint(current_user: UserPayload = Depends(RoleChecker(["admin"]))):
    """Protected endpoint requiring the 'admin' role."""
    return {
        "status": "authorized",
        "message": f"Welcome superuser {current_user.username}",
        "roles": current_user.roles,
    }
