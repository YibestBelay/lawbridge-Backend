# routers/users.py

import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
import hashlib
from jose import jwt
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import os

from database import get_db
from models import User
from schemas import UserCreate, UserResponse, UserUpdate
from auth import get_current_user

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


# ══════════════════════════════════════════
# LOGIN — POST /users/login
# (no auth required — returns a JWT token)
# ══════════════════════════════════════════
@router.post("/login")
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.email == credentials.email)
    ).scalar_one_or_none()

    if not user or user.hashed_password != hash_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    token = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
    }


# ══════════════════════════════════════════
# REGISTER — POST /users/register
# (no auth required — anyone can register)
# ══════════════════════════════════════════
@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.execute(
        select(User).where(User.email == user_data.email)
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=user_data.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ══════════════════════════════════════════
# GET ALL USERS — GET /users/
# (protected — must be logged in)
# ══════════════════════════════════════════
@router.get("/", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    users = db.execute(select(User)).scalars().all()
    return users


# ══════════════════════════════════════════
# GET ONE USER — GET /users/{user_id}
# (protected)
# ══════════════════════════════════════════
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ══════════════════════════════════════════
# UPDATE USER — PATCH /users/{user_id}
# (protected)
# ══════════════════════════════════════════
@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


# ══════════════════════════════════════════
# DELETE USER — DELETE /users/{user_id}
# (protected)
# ══════════════════════════════════════════
@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return None