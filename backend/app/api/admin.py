from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models import AgentLog, AuditLog, User
from app.schemas import UserResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserResponse])
def users(db: Session = Depends(get_db), _: User = Depends(require_roles(["admin"]))):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.get("/agent-logs")
def agent_logs(db: Session = Depends(get_db), _: User = Depends(require_roles(["admin"]))):
    rows = db.query(AgentLog).order_by(AgentLog.created_at.desc()).limit(100).all()
    return {"logs": [{"agent": r.agent_name, "status": r.status, "latency_ms": r.latency_ms, "message": r.message} for r in rows]}


@router.get("/audit-logs")
def audit_logs(db: Session = Depends(get_db), _: User = Depends(require_roles(["admin"]))):
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    return {"logs": [{"action": r.action, "resource": r.resource, "metadata": r.metadata_json, "created_at": r.created_at} for r in rows]}
