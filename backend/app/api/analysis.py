import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import AnalysisHistory, Company, Comparison, Project, Report, ResearchSession, SourceEvidence, User, WebSource
from app.schemas import AnalysisRequest, ReportResponse
from app.services.agent_service import agent_workflow
from app.services.audit_service import audit
from app.services.evaluation_service import evaluate_report
from app.services.report_service import format_business_report
from app.services.security_service import validate_prompt_safety

router = APIRouter(prefix="/analysis", tags=["analysis"])
settings = get_settings()


@router.post("", response_model=ReportResponse)
async def create_analysis(payload: AnalysisRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        validate_prompt_safety(db, user.id, payload.query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    project = Project(
        owner_id=user.id,
        name=payload.project_name or payload.query[:80],
        description=payload.query,
        industry=payload.industry or "General",
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    research_session = ResearchSession(
        user_id=user.id,
        query=payload.query,
        mode=payload.mode,
        provider=settings.search_provider,
        status="running",
    )
    db.add(research_session)
    db.commit()
    db.refresh(research_session)

    report = Report(
        project_id=project.id,
        user_id=user.id,
        title=payload.query[:80],
        mode=payload.mode,
        input_text=payload.query,
        content={},
        viability_score=0.0,
        confidence_score=0.0,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    started = time.perf_counter()
    try:
        raw_content = await agent_workflow.run(db, payload.query, payload.mode, report_id=report.id)
    except Exception:
        research_session.status = "failed"
        research_session.completed_at = datetime.utcnow()
        db.delete(report)
        db.commit()
        raise
    latency_ms = int((time.perf_counter() - started) * 1000)
    content = format_business_report(raw_content)

    report.title = content["title"]
    report.content = content
    report.viability_score = content["viability_score"]
    report.confidence_score = content["confidence_score"]
    db.commit()
    db.refresh(report)

    entities = raw_content.get("entities", [])
    for entity in entities:
        exists = db.query(Company).filter(Company.name == entity).first()
        if not exists:
            db.add(Company(name=entity))

    for item in raw_content.get("citations", []):
        db.add(
            SourceEvidence(
                report_id=report.id,
                title=item.get("source", "Unknown source")[:255],
                url=item.get("url", ""),
                snippet=item.get("text", "")[:900],
                confidence=item.get("confidence", 0.5),
            )
        )
    for item in raw_content.get("web_sources", []):
        db.add(
            WebSource(
                research_session_id=research_session.id,
                report_id=report.id,
                title=item.get("title", "Unknown source")[:255],
                url=item.get("url", ""),
                snippet=item.get("snippet", "")[:900],
                source_type=item.get("source_type", "web"),
                confidence_score=item.get("confidence_score", 0.5),
            )
        )
    db.add(
        Comparison(
            user_id=user.id,
            report_id=report.id,
            query=payload.query,
            entities={"items": entities},
            summary=content.get("executive_summary", ""),
        )
    )
    research_session.status = "completed"
    research_session.sources_collected = len(raw_content.get("web_sources", []))
    research_session.rejected_sources = len(raw_content.get("rejected_sources", []))
    research_session.confidence_score = content.get("confidence_score", 0)
    research_session.completed_at = datetime.utcnow()
    db.add(AnalysisHistory(user_id=user.id, mode=payload.mode, query=payload.query, report_id=report.id))
    db.commit()
    evaluate_report(db, report.id, content, latency_ms)
    audit(db, user.id, "create_analysis", "reports", {"report_id": report.id, "mode": payload.mode})
    return report


@router.get("/reports", response_model=list[ReportResponse])
def list_reports(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Report).order_by(Report.created_at.desc())
    if user.role != "admin":
        query = query.filter(Report.user_id == user.id)
    return query.limit(100).all()


@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if user.role != "admin" and report.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    report.content = format_business_report(report.content)
    return report
