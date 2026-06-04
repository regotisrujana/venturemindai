from sqlalchemy.orm import Session

from app.models import EvaluationMetric


def _report_sources(content: dict) -> list[dict]:
    sources = []
    sources.extend(content.get("citations", []) or [])
    sources.extend(content.get("evidence_panel", {}).get("sources", []) or [])
    sources.extend(content.get("sections", {}).get("sources_used", {}).get("sources", []) or [])

    unique = {}
    for item in sources:
        if not isinstance(item, dict):
            continue
        url = item.get("url") or item.get("source_url") or item.get("citation") or item.get("link")
        title = item.get("title") or item.get("source_title") or item.get("source") or url
        if not url and not title:
            continue
        key = (url or title).strip().lower()
        unique[key] = {
            "title": title,
            "url": url,
            "confidence": item.get("confidence", item.get("confidence_score", 0.65)),
        }
    return list(unique.values())


def evaluate_report(db: Session, report_id: int, content: dict, latency_ms: int) -> EvaluationMetric:
    citations = _report_sources(content)
    confidence = content.get("critic", {}).get("confidence_score", 0.7)
    citation_quality = (
        round(sum(item.get("confidence", 0.65) for item in citations) / len(citations), 2)
        if citations
        else 0
    )
    metric = EvaluationMetric(
        report_id=report_id,
        accuracy=round(confidence * 0.94, 2),
        relevance=0.9 if citations else 0.45,
        faithfulness=0.88 if citations else 0.35,
        citation_correctness=citation_quality,
        hallucination_rate=0.08 if citations else 0.18,
        latency_ms=latency_ms,
        cost_usd=round(len(str(content)) / 4000 * 0.002, 4),
        feedback_score=0,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric
