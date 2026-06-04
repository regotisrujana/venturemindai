from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import User


def upsert_user(db, email: str, name: str, password: str, role: str) -> None:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return
    db.add(User(email=email, full_name=name, hashed_password=hash_password(password), role=role))


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        upsert_user(db, "founder@venturemind.ai", "Demo Founder", "Founder123!", "user")
        upsert_user(db, "admin@venturemind.ai", "Demo Admin", "Admin123!", "admin")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
