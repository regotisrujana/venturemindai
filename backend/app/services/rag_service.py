import hashlib
import math
import re
from dataclasses import dataclass
from html import unescape


BOILERPLATE_PATTERNS = (
    "newsletter sign-up",
    "does my company subscribe",
    "contact sales",
    "become a client",
    "get a demo",
    "log in",
    "login",
    "cookie",
    "privacy policy",
    "terms of use",
    "all rights reserved",
    "subscribe",
    "unsupported browser",
    "enable javascript",
)

BOILERPLATE_WORDS = {
    "about",
    "advertise",
    "calendar",
    "contact",
    "demo",
    "events",
    "login",
    "newsletter",
    "pricing",
    "products",
    "resources",
    "search",
    "subscribe",
}


@dataclass
class SearchHit:
    text: str
    source: str
    collection: str
    confidence: float
    chunk_id: str = ""
    page_number: int | None = None


class RAGService:
    def __init__(self) -> None:
        self._documents: list[dict] = []

    def chunk_text(self, text: str, size: int = 420, overlap: int = 60) -> list[str]:
        text = clean_evidence_text(text)
        words = text.split()
        chunks: list[str] = []
        step = max(1, size - overlap)
        for start in range(0, len(words), step):
            chunk = clean_evidence_text(" ".join(words[start : start + size]).strip())
            if chunk and not is_boilerplate_text(chunk):
                chunks.append(chunk)
        return chunks or ([text[:1800]] if text else [])

    def ingest(self, filename: str, collection: str, text: str, page_number: int | None = None) -> int:
        chunks = self.chunk_text(text)
        for idx, chunk in enumerate(chunks):
            chunk_id = hashlib.sha256(f"{filename}:{page_number}:{idx}:{chunk}".encode()).hexdigest()
            self._documents.append(
                {
                    "id": chunk_id,
                    "chunk_id": chunk_id,
                    "filename": filename,
                    "collection": collection,
                    "text": chunk,
                    "page_number": page_number,
                    "tokens": set(re.findall(r"[a-z0-9]+", chunk.lower())),
                }
            )
        return len(chunks)

    def rewrite_query(self, query: str) -> str:
        return f"{query} market size competitors pricing SWOT financial projections go-to-market"

    def search(self, query: str, collection: str | None = None, limit: int = 5) -> list[SearchHit]:
        rewritten = self.rewrite_query(query)
        query_tokens = set(re.findall(r"[a-z0-9]+", rewritten.lower()))
        anchor_tokens = set(re.findall(r"[a-z0-9]+", query.lower())) - {
            "a",
            "an",
            "and",
            "app",
            "business",
            "company",
            "for",
            "idea",
            "market",
            "my",
            "platform",
            "product",
            "software",
            "startup",
            "system",
            "the",
            "vs",
        }
        scored = []
        for doc in self._documents:
            if collection and doc["collection"] != collection:
                continue
            if anchor_tokens and not (anchor_tokens & doc["tokens"]):
                continue
            overlap = len(query_tokens & doc["tokens"])
            score = overlap / math.sqrt(max(1, len(query_tokens) * len(doc["tokens"])))
            if score >= 0.08:
                scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            SearchHit(
                text=doc["text"],
                source=doc["filename"],
                collection=doc["collection"],
                confidence=round(min(0.98, score + 0.35), 2),
                chunk_id=doc.get("chunk_id", ""),
                page_number=doc.get("page_number"),
            )
            for score, doc in scored[:limit]
        ]


rag_service = RAGService()


def clean_evidence_text(text: str) -> str:
    text = unescape(str(text or ""))
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"\b(phone|tel)\s*:?\s*[\d().\-\s]{7,}", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()
    return _remove_boilerplate_sentences(text)


def clean_html_text(html: str) -> str:
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    html = re.sub(r"<(script|style|noscript|svg|header|footer|nav|aside|form)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    html = re.sub(r"</(p|div|li|h[1-6]|article|section|br|tr)>", ". ", html, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    return clean_evidence_text(text)


def is_boilerplate_text(text: str) -> bool:
    lowered = clean_evidence_text(text).lower()
    if not lowered or len(lowered) < 20:
        return True
    if any(pattern in lowered for pattern in BOILERPLATE_PATTERNS):
        return True
    if len(lowered) < 80:
        return False
    tokens = re.findall(r"[a-z]+", lowered)
    if not tokens:
        return True
    boilerplate_hits = sum(1 for token in tokens if token in BOILERPLATE_WORDS)
    return boilerplate_hits / max(1, len(tokens)) > 0.12


def _remove_boilerplate_sentences(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+|\s+[|•]\s+|\s{2,}", text)
    useful = []
    for part in parts:
        sentence = part.strip(" -|•")
        if len(sentence) < 35:
            continue
        lowered = sentence.lower()
        if any(pattern in lowered for pattern in BOILERPLATE_PATTERNS):
            continue
        useful.append(sentence)
    if useful:
        return " ".join(useful)
    return text[:1800]
