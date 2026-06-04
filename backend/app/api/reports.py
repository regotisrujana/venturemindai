from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional_query
from app.models import Feedback, Report, User
from app.schemas import FeedbackRequest
from app.services.report_service import build_docx, build_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


def require_report(db: Session, report_id: int, user: User) -> Report:
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if user.role != "admin" and report.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return report


@router.get("/{report_id}/download.pdf")
def download_pdf(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional_query)):
    report = require_report(db, report_id, user)
    return Response(
        build_pdf(report.content),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="venturemind-report-{report.id}.pdf"'},
    )


@router.get("/{report_id}/download.docx")
def download_docx(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional_query)):
    report = require_report(db, report_id, user)
    return Response(
        build_docx(report.content),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="venturemind-report-{report.id}.docx"'},
    )


@router.post("/{report_id}/feedback")
def feedback(report_id: int, payload: FeedbackRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_report(db, report_id, user)
    item = Feedback(report_id=report_id, user_id=user.id, rating=payload.rating, comment=payload.comment)
    db.add(item)
    db.commit()
    return {"status": "recorded"}
