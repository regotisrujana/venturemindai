import hashlib
import math
import re
from dataclasses import dataclass


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

    def chunk_text(self, text: str, size: int = 900, overlap: int = 120) -> list[str]:
        words = text.split()
        chunks: list[str] = []
        step = max(1, size - overlap)
        for start in range(0, len(words), step):
            chunk = " ".join(words[start : start + size]).strip()
            if chunk:
                chunks.append(chunk)
        return chunks or [text[:4000]]

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
