from sqlalchemy.orm import Session

from app.models import AuditLog


def audit(db: Session, user_id: int | None, action: str, resource: str, metadata: dict | None = None) -> None:
    db.add(AuditLog(user_id=user_id, action=action, resource=resource, metadata_json=metadata or {}))
    db.commit()
