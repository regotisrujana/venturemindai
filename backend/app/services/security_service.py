from sqlalchemy.orm import Session

from app.models import SecurityEvent

INJECTION_MARKERS = [
    "ignore previous instructions",
    "reveal system prompt",
    "developer message",
    "bypass",
    "exfiltrate",
    "print secrets",
]


def mask_sensitive(value: str) -> str:
    masked = value
    for marker in ["api_key", "password", "secret", "token"]:
        masked = masked.replace(marker, f"{marker[:2]}***")
    return masked


def validate_prompt_safety(db: Session, user_id: int | None, text: str) -> None:
    lowered = text.lower()
    hits = [marker for marker in INJECTION_MARKERS if marker in lowered]
    if hits:
        db.add(
            SecurityEvent(
                user_id=user_id,
                severity="high",
                event_type="prompt_injection_detected",
                description="Potential prompt injection markers detected",
                metadata_json={"markers": hits},
            )
        )
        db.commit()
        raise ValueError("Input contains unsafe prompt-injection patterns.")
