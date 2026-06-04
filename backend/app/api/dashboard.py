from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models import AgentLog, AuditLog, EvaluationMetric, Feedback, Project, Report, ResearchSession, SecurityEvent, UploadedDocument, User, WebSource

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/user")
def user_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    reports = db.query(Report).filter(Report.user_id == user.id).order_by(Report.created_at.desc()).limit(10).all()
    projects = db.query(Project).filter(Project.owner_id == user.id).count()
    avg_score = db.query(func.avg(Report.viability_score)).filter(Report.user_id == user.id).scalar() or 0
    latest_session = (
        db.query(ResearchSession)
        .filter(ResearchSession.user_id == user.id)
        .order_by(ResearchSession.created_at.desc())
        .first()
    )
    latest_agent_logs = (
        db.query(AgentLog)
        .join(Report, AgentLog.report_id == Report.id)
        .filter(Report.user_id == user.id, AgentLog.agent_name != "financial")
        .order_by(AgentLog.created_at.desc())
        .limit(40)
        .all()
    )
    latest_by_agent = {}
    status_priority = {"completed": 3, "failed": 2, "running": 1, "pending": 0}
    for log in latest_agent_logs:
        key = log.agent_name.lower().replace(" ", "_")
        current = latest_by_agent.get(key)
        if not current or status_priority.get(log.status, 0) > status_priority.get(current.status, -1):
            latest_by_agent[key] = log
    agent_order = ["web_research", "research", "competitor", "swot", "market_sizing", "strategy", "critic", "report"]
    ordered_logs = sorted(latest_by_agent.items(), key=lambda item: agent_order.index(item[0]) if item[0] in agent_order else 99)
    return {
        "saved_projects": projects,
        "generated_reports": len(reports),
        "average_viability": round(avg_score, 1),
        "downloads": len(reports) * 2,
        "recent_reports": [
            {"id": r.id, "title": r.title, "mode": r.mode, "score": r.viability_score, "created_at": r.created_at}
            for r in reports
        ],
        "research_summary": {
            "sources_collected": latest_session.sources_collected if latest_session else 0,
            "rejected_sources": latest_session.rejected_sources if latest_session else 0,
            "final_evidence_count": reports[0].content.get("research_summary", {}).get("final_evidence_count", 0) if reports else 0,
            "report_confidence": latest_session.confidence_score if latest_session else 0,
        },
        "agent_status": [{"agent": name, "status": log.status, "message": log.message} for name, log in ordered_logs],
    }


@router.get("/admin")
def admin_dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles(["admin"]))):
    agent_usage = db.query(AgentLog.agent_name, func.count(AgentLog.id)).filter(AgentLog.agent_name != "financial").group_by(AgentLog.agent_name).all()
    industries = db.query(Project.industry, func.count(Project.id)).group_by(Project.industry).all()
    return {
        "total_users": db.query(User).count(),
        "total_reports": db.query(Report).count(),
        "uploaded_documents": db.query(UploadedDocument).count(),
        "web_sources": db.query(WebSource).count(),
        "research_sessions": db.query(ResearchSession).count(),
        "feedback_count": db.query(Feedback).count(),
        "security_events": db.query(SecurityEvent).count(),
        "audit_logs": db.query(AuditLog).count(),
        "agent_usage": [{"name": name, "count": count} for name, count in agent_usage],
        "most_analyzed_industries": [{"industry": industry, "count": count} for industry, count in industries],
    }


@router.get("/evaluation")
def evaluation_dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles(["admin"]))):
    rows = db.query(EvaluationMetric).order_by(EvaluationMetric.created_at.desc()).limit(50).all()
    nonzero_citations = [r.citation_correctness for r in rows if r.citation_correctness and r.citation_correctness > 0]
    summary_rows = rows[:20]
    summary_count = len(summary_rows) or 1
    return {
        "summary": {
            "accuracy": round(sum(r.accuracy for r in summary_rows) / summary_count, 2) if rows else 0,
            "relevance": round(sum(r.relevance for r in summary_rows) / summary_count, 2) if rows else 0,
            "citation_correctness": round(sum(nonzero_citations) / len(nonzero_citations), 2) if nonzero_citations else 0,
            "latency_ms": round(sum(r.latency_ms for r in summary_rows) / summary_count) if rows else 0,
        },
        "history": [
            {
                "accuracy": r.accuracy,
                "relevance": r.relevance,
                "faithfulness": r.faithfulness,
                "citation_correctness": r.citation_correctness,
                "hallucination_rate": r.hallucination_rate,
                "latency_ms": r.latency_ms,
                "cost_usd": r.cost_usd,
                "feedback_score": r.feedback_score,
                "created_at": r.created_at,
            }
            for r in rows
        ]
    }


@router.get("/security")
def security_dashboard(db: Session = Depends(get_db), user: User = Depends(require_roles(["admin"]))):
    events = db.query(SecurityEvent).order_by(SecurityEvent.created_at.desc()).limit(50).all()
    return {
        "events": [
            {
                "severity": e.severity,
                "event_type": e.event_type,
                "description": e.description,
                "metadata": e.metadata_json,
                "created_at": e.created_at,
            }
            for e in events
        ]
    }
