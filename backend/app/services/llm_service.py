import asyncio
import httpx

from app.core.config import get_settings


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def complete(self, system: str, prompt: str) -> str:
        if not self.settings.groq_api_key:
            return self._no_evidence_response(prompt)

        max_retries = 3
        backoff = 2.0
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=40) as client:
                    response = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.settings.groq_api_key}"},
                        json={
                            "model": self.settings.groq_model,
                            "messages": [
                                {"role": "system", "content": system},
                                {"role": "user", "content": prompt},
                            ],
                            "temperature": 0.25,
                        },
                    )
                if response.status_code == 429:
                    try:
                        retry_after = float(response.headers.get("retry-after", backoff))
                        retry_after = min(retry_after, 6.0)
                    except ValueError:
                        retry_after = min(backoff, 6.0)
                    await asyncio.sleep(retry_after)
                    backoff *= 2
                    continue
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except httpx.HTTPError:
                if attempt == max_retries - 1:
                    return self._no_evidence_response(prompt)
                await asyncio.sleep(backoff)
                backoff *= 2

    def _no_evidence_response(self, prompt: str) -> str:
        subject = prompt[:120].strip()
        return (
            f"No LLM-backed claim was generated for {subject}. Use the cited web/RAG evidence in the report; "
            "uncited market size, revenue, pricing, and growth claims are intentionally omitted."
        )
