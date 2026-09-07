from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models import User, UserRole
from app.schemas import LoginIn, RegisterIn, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone == body.phone).first():
        raise HTTPException(400, "Phone already registered")
    user = User(
        name=body.name,
        phone=body.phone,
        password_hash=hash_password(body.password),
        role=UserRole.farmer,
        village=body.village,
        district=body.district,
        lat=body.lat or 29.6857,
        lng=body.lng or 76.9905,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(
        access_token=create_access_token(user),
        role=user.role.value,
        name=user.name,
        user_id=user.id,
    )


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == body.phone).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid phone or password")
    return TokenOut(
        access_token=create_access_token(user),
        role=user.role.value,
        name=user.name,
        user_id=user.id,
    )


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "name": user.name,
        "phone": user.phone,
        "role": user.role.value,
        "village": user.village,
        "district": user.district,
        "lat": user.lat,
        "lng": user.lng,
    }
