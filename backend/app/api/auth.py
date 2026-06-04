from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.models import User
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.audit_service import audit

router = APIRouter(prefix="/auth", tags=["auth"])


def serialize_user(user: User) -> dict:
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=payload.email, full_name=payload.full_name, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    audit(db, user.id, "register", "users", {"email": user.email})
    return TokenResponse(access_token=create_access_token(user.email, user.role), user=serialize_user(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    audit(db, user.id, "login", "users", {"email": user.email})
    return TokenResponse(access_token=create_access_token(user.email, user.role), user=serialize_user(user))


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user
