from dataclasses import dataclass
from datetime import datetime
from html import unescape
import re
from urllib.parse import quote_plus, urlparse

import httpx

from app.core.config import get_settings
from app.services.rag_service import clean_evidence_text, clean_html_text, is_boilerplate_text


TRUSTED_DOMAINS = (
    "adobe.com",
    "canva.com",
    "zomato.com",
    "swiggy.com",
    "linkedin.com",
    "naukri.com",
    "wikipedia.org",
    "crunchbase.com",
    "forbes.com",
    "business-standard.com",
    "economictimes.indiatimes.com",
    "moneycontrol.com",
    "statista.com",
    "gartner.com",
    "mckinsey.com",
    "bcg.com",
    "pwc.com",
    "deloitte.com",
    "kpmg.com",
    "sec.gov",
    "annualreports.com",
    "companiesmarketcap.com",
    "hireez.com",
    "humanly.io",
    "seekout.com",
    "eightfold.ai",
    "greenhouse.com",
    "lever.co",
    "workable.com",
    "ashbyhq.com",
    "icims.com",
    "cloudbeds.com",
    "webrezpro.com",
    "sirvoy.com",
    "beds24.com",
    "littlehotelier.com",
    "zeptonow.com",
    "blinkit.com",
    "zomato.com",
)

SOURCE_TYPE_RULES = (
    ("pricing", ("pricing", "plans", "subscription", "terms", "charges", "fees")),
    ("product", ("product", "features", "platform", "food delivery", "quick commerce", "grocery", "instamart")),
    ("official", ("about", "company", "official", "corporate", "who-we-are")),
    ("financial", ("annual", "investor", "investor-relations", "revenue", "financial", "sec.gov")),
    ("news", ("news", "business", "economictimes", "forbes", "moneycontrol")),
)

KNOWN_COMPANY_URLS = {
    "hireez": ["https://hireez.com", "https://hireez.com/pricing/"],
    "humanly": ["https://www.humanly.io", "https://www.humanly.io/platform"],
    "seekout": ["https://www.seekout.com", "https://www.seekout.com/product"],
    "eightfold ai": ["https://eightfold.ai", "https://eightfold.ai/products/"],
    "greenhouse": ["https://www.greenhouse.com", "https://www.greenhouse.com/pricing"],
    "lever": ["https://www.lever.co", "https://www.lever.co/pricing"],
    "workable": ["https://www.workable.com", "https://www.workable.com/pricing"],
    "icims": ["https://www.icims.com", "https://www.icims.com/products/"],
    "cloudbeds": ["https://www.cloudbeds.com", "https://www.cloudbeds.com/hotel-management-software/"],
    "webrezpro": ["https://webrezpro.com", "https://webrezpro.com/features/"],
    "sirvoy": ["https://sirvoy.com", "https://sirvoy.com/pricing/"],
    "beds24": ["https://www.beds24.com", "https://www.beds24.com/pricing.html"],
    "little hotelier": ["https://www.littlehotelier.com", "https://www.littlehotelier.com/pricing/"],
    "canva": ["https://www.canva.com", "https://www.canva.com/pricing/"],
    "adobe express": ["https://www.adobe.com/express/", "https://www.adobe.com/express/pricing"],
    "zomato": [
        "https://www.zomato.com",
        "https://www.zomato.com/who-we-are",
        "https://www.zomato.com/investor-relations",
        "https://www.zomato.com/policies/terms-of-service",
    ],
    "swiggy": [
        "https://www.swiggy.com",
        "https://www.swiggy.com/corporate/",
        "https://www.swiggy.com/instamart",
    ],
    "zepto": ["https://www.zeptonow.com", "https://www.zeptonow.com/about-us"],
    "blinkit": ["https://blinkit.com", "https://blinkit.com/aboutus"],
}


@dataclass
class ResearchSource:
    title: str
    url: str
    snippet: str
    source_type: str
    collected_at: str
    confidence_score: float


class WebResearchService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def research(self, query: str, mode: str = "startup", limit: int = 14) -> tuple[list[ResearchSource], list[dict]]:
        entities = self.extract_entities(query)
        search_tasks = self.build_search_tasks(query, entities, mode)
        sources: list[ResearchSource] = []
        rejected: list[dict] = []
        seen: set[str] = set()

        async with httpx.AsyncClient(timeout=6, follow_redirects=True) as client:
            seeded_sources = await self._known_relevant_sources(client, query, entities)
            for source in seeded_sources:
                self._add_source(source, query, sources, rejected, seen)
                if len(sources) >= limit:
                    return sources, rejected

            for search in search_tasks:
                provider_results = await self._provider_search(client, search, limit=5)
                if not provider_results and not self.settings.search_api_key:
                    provider_results = await self._official_fallback(client, search, entities)
                if not provider_results:
                    provider_results = await self._duckduckgo(client, search)
                for source in provider_results:
                    self._add_source(source, query, sources, rejected, seen)
                    if len(sources) >= limit:
                        return sources, rejected
        return sources, rejected

    def _add_source(self, source: ResearchSource, query: str, sources: list[ResearchSource], rejected: list[dict], seen: set[str]) -> None:
        key = self._canonical_url(source.url)
        if key in seen:
            rejected.append({"url": source.url, "reason": "duplicate"})
            return
        if not self._is_usable_source(source, query):
            rejected.append({"url": source.url, "reason": "untrusted_empty_or_irrelevant"})
            return
        seen.add(key)
        sources.append(source)

    def extract_entities(self, query: str) -> list[str]:
        cleaned = re.sub(r"\b(my|startup|company|compare|comparison)\b", " ", query, flags=re.I)
        parts = re.split(r"\s+vs\s+|,|&|\bagainst\b", cleaned, flags=re.I)
        entities = [re.sub(r"\s+", " ", part).strip(" .") for part in parts]
        return [entity for entity in entities if len(entity) > 1][:6]

    def build_search_tasks(self, query: str, entities: list[str], mode: str) -> list[str]:
        tasks = [query]
        startup_terms = self.startup_market_terms(query)
        for term in startup_terms.get("category_terms", []):
            tasks.extend(
                [
                    f"{term} market size growth competitors",
                    f"{term} pricing product features",
                ]
            )
        if mode == "startup":
            tasks.extend(
                [
                    f"{query} existing products competitors",
                    f"{query} market competitors pricing product features",
                    f"{query} alternatives comparison",
                    f"{query} market size growth report",
                ]
            )
            for competitor in startup_terms.get("competitors", []):
                tasks.extend(
                    [
                        f"{competitor} official product pricing",
                        f"{competitor} AI recruiting platform features customers",
                    ]
                )
        for entity in entities:
            tasks.extend(
                [
                    f"{entity} official website about product pricing",
                    f"{entity} pricing plans product features",
                    f"{entity} revenue annual report investors growth",
                    f"{entity} market position competitors business news",
                ]
            )
        return self._dedupe(tasks)[:12]

    def startup_market_terms(self, query: str) -> dict[str, list[str]]:
        lowered = query.lower()
        if any(term in lowered for term in ("recruit", "hiring", "ats", "talent acquisition", "resume screening")):
            return {
                "category_terms": ["AI recruiting software", "recruitment automation", "talent acquisition platform"],
                "competitors": ["hireEZ", "Humanly", "SeekOut", "Eightfold AI", "Greenhouse", "Lever", "Workable", "iCIMS"],
            }
        if any(term in lowered for term in ("food delivery", "restaurant delivery", "delivery app")):
            return {
                "category_terms": ["food delivery platform", "restaurant delivery marketplace"],
                "competitors": ["Zomato", "Swiggy", "DoorDash", "Uber Eats"],
            }
        if any(term in lowered for term in ("zepto", "blinkit", "quick commerce", "grocery delivery", "instant delivery")):
            return {
                "category_terms": ["quick commerce", "grocery delivery", "instant delivery"],
                "competitors": ["Zepto", "Blinkit", "Instamart", "BigBasket", "Dunzo"],
            }
        if any(term in lowered for term in ("design", "presentation", "creative", "image editor")):
            return {
                "category_terms": ["online design platform", "creative design software"],
                "competitors": ["Canva", "Adobe Express", "Figma", "VistaCreate"],
            }
        if any(term in lowered for term in ("hostel", "hotel management", "property management", "pms", "booking management")):
            return {
                "category_terms": ["hostel management software", "property management system", "hotel PMS"],
                "competitors": ["Cloudbeds", "WebRezPro", "Sirvoy", "Beds24", "Little Hotelier", "HostelSystem"],
            }
        return {"category_terms": [query], "competitors": []}

    async def _provider_search(self, client: httpx.AsyncClient, query: str, limit: int) -> list[ResearchSource]:
        provider = self.settings.search_provider.lower().strip()
        if not self.settings.search_api_key:
            return []
        if provider == "tavily":
            return await self._tavily(client, query, limit)
        if provider == "serpapi":
            return await self._serpapi(client, query, limit)
        if provider == "brave":
            return await self._brave(client, query, limit)
        return []

    async def _tavily(self, client: httpx.AsyncClient, query: str, limit: int) -> list[ResearchSource]:
        try:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.settings.search_api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": limit,
                    "include_answer": False,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return []
        return [
            self._source(item.get("title", ""), item.get("url", ""), item.get("content", ""), "tavily")
            for item in response.json().get("results", [])
        ]

    async def _serpapi(self, client: httpx.AsyncClient, query: str, limit: int) -> list[ResearchSource]:
        try:
            response = await client.get(
                "https://serpapi.com/search.json",
                params={"engine": "google", "q": query, "api_key": self.settings.search_api_key, "num": limit},
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return []
        return [
            self._source(item.get("title", ""), item.get("link", ""), item.get("snippet", ""), "serpapi")
            for item in response.json().get("organic_results", [])
        ]

    async def _brave(self, client: httpx.AsyncClient, query: str, limit: int) -> list[ResearchSource]:
        try:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": limit},
                headers={"X-Subscription-Token": self.settings.search_api_key, "Accept": "application/json"},
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return []
        return [
            self._source(item.get("title", ""), item.get("url", ""), item.get("description", ""), "brave")
            for item in response.json().get("web", {}).get("results", [])
        ]

    async def _known_relevant_sources(self, client: httpx.AsyncClient, query: str, entities: list[str]) -> list[ResearchSource]:
        names = [entity.lower().strip() for entity in entities]
        market_terms = self.startup_market_terms(query)
        names.extend(name.lower() for name in market_terms.get("competitors", []))
        url_names: list[tuple[str, str]] = []
        for name in names:
            normalized = re.sub(r"\s+", " ", name).strip()
            if normalized in KNOWN_COMPANY_URLS:
                url_names.extend((url, normalized) for url in KNOWN_COMPANY_URLS[normalized])
            compact = normalized.replace(" ai", "").strip()
            if compact in KNOWN_COMPANY_URLS:
                url_names.extend((url, compact) for url in KNOWN_COMPANY_URLS[compact])

        category_terms = " ".join(market_terms.get("category_terms", [])).lower()
        if "quick commerce" in category_terms or "grocery delivery" in category_terms:
            url_names.extend([
                ("https://www.zeptonow.com", "zepto"),
                ("https://blinkit.com", "blinkit"),
                ("https://www.swiggy.com/instamart", "swiggy"),
                ("https://www.bigbasket.com", "bigbasket"),
            ])
        if "food delivery" in category_terms or "restaurant delivery" in category_terms:
            url_names.extend([
                ("https://www.zomato.com", "zomato"),
                ("https://www.swiggy.com", "swiggy"),
                ("https://www.doordash.com", "doordash"),
                ("https://www.ubereats.com", "uber eats"),
            ])

        sources: list[ResearchSource] = []
        seen_urls = set()
        for url, name in url_names[:18]:
            canonical = self._canonical_url(url)
            if canonical in seen_urls:
                continue
            seen_urls.add(canonical)
            source = await self._fetch_page_source(client, url, "known_relevant")
            sources.append(source or self._source(self._known_fallback_title(name, url), url, self._known_fallback_snippet(name, url), "known_relevant"))
        return sources

    async def _official_fallback(self, client: httpx.AsyncClient, query: str, entities: list[str]) -> list[ResearchSource]:
        candidates: list[str] = []
        known_matches: list[tuple[str, str]] = []
        for entity in entities:
            slug = re.sub(r"[^a-z0-9]", "", entity.lower())
            if slug:
                candidates.extend(
                    [
                        f"https://www.{slug}.com",
                        f"https://www.{slug}.com/about",
                        f"https://www.{slug}.com/pricing",
                    ]
                )
        lowered_query = query.lower()
        for name, urls in KNOWN_COMPANY_URLS.items():
            if name in lowered_query:
                candidates.extend(urls)
                known_matches.append((name, urls[0]))
        sources = []
        for url in self._dedupe(candidates)[:10]:
            source = await self._fetch_page_source(client, url, "official_fallback")
            if source:
                sources.append(source)
        if not sources:
            for name, url in known_matches:
                sources.append(
                    self._source(
                        f"{name.title()} official website",
                        url,
                        self._known_fallback_snippet(name, url),
                        "official_fallback",
                    )
                )
        return sources

    async def _fetch_page_source(self, client: httpx.AsyncClient, url: str, provider: str) -> ResearchSource | None:
        try:
            response = await client.get(url, headers={"User-Agent": "VentureMindAI/1.0 research bot"})
            if response.status_code >= 400:
                return None
            title = self._title(response.text) or urlparse(str(response.url)).netloc
            snippet = self._snippet(response.text)
            return self._source(title, str(response.url), snippet, provider)
        except httpx.HTTPError:
            return None

    def _known_fallback_title(self, name: str, url: str) -> str:
        if "terms" in url:
            return f"{name.title()} terms of service"
        if "investor" in url:
            return f"{name.title()} investor relations"
        if "instamart" in url:
            return "Swiggy Instamart"
        if "corporate" in url or "who-we-are" in url:
            return f"{name.title()} corporate profile"
        return f"{name.title()} official website"

    def _known_fallback_snippet(self, name: str, url: str = "") -> str:
        url_l = url.lower()
        if name == "zomato" and "terms" in url_l:
            return (
                "Zomato terms describe prices on the Zomato Platform as provided by Restaurant Partners, including packaging or handling charges where applicable. "
                "This supports pricing visibility only and does not verify revenue, margins, or market share."
            )
        if name == "zomato" and "investor" in url_l:
            return (
                "Zomato investor relations is the official source for public company investor updates and financial disclosures. "
                "Use this source only for business signals that are directly stated there."
            )
        if name == "zomato":
            return (
                "Zomato operates a public restaurant-discovery, food-ordering, delivery, and restaurant-commerce product platform with restaurant partner interactions. "
                "This supports core offering and product-position evidence, not exact financial metrics."
            )
        if name == "swiggy" and "instamart" in url_l:
            return (
                "Swiggy Instamart is presented as Swiggy's quick-commerce and grocery delivery service. "
                "This supports product focus and delivery-commerce positioning, not exact financial metrics."
            )
        if name == "swiggy":
            return (
                "Swiggy operates a public food-delivery, restaurant-ordering, quick-commerce, and consumer commerce service platform. "
                "This supports core offering and product-position evidence, not exact financial metrics."
            )
        if name in {"zepto", "blinkit"}:
            return f"Official website reference for {name.title()} in quick commerce and grocery delivery. Use this citation to verify company or product existence, not financial metrics."
        return f"Official website reference for {name.title()}. Use this citation to verify company or product existence, not financial metrics."

    async def _duckduckgo(self, client: httpx.AsyncClient, query: str) -> list[ResearchSource]:
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            response = await client.get(url, headers={"User-Agent": "VentureMindAI/1.0 research bot"})
            response.raise_for_status()
        except httpx.HTTPError:
            return []
        items = re.findall(
            r'<a rel="nofollow" class="result__a" href="(?P<url>.*?)".*?>(?P<title>.*?)</a>.*?<a class="result__snippet".*?>(?P<snippet>.*?)</a>',
            response.text,
            re.DOTALL,
        )
        return [self._source(raw_title, unescape(raw_url), raw_snippet, "duckduckgo_fallback") for raw_url, raw_title, raw_snippet in items]

    def _source(self, title: str, url: str, snippet: str, provider: str) -> ResearchSource:
        clean_url = unescape(url)
        clean_title = clean_evidence_text(self._strip_html(title))[:255] or "Untitled source"
        clean_snippet = clean_evidence_text(self._strip_html(snippet))[:900]
        source_type = self._source_type(clean_url, clean_title, clean_snippet)
        return ResearchSource(
            title=clean_title,
            url=clean_url,
            snippet=clean_snippet,
            source_type=source_type if provider != "duckduckgo_fallback" else f"{source_type}_fallback",
            collected_at=datetime.utcnow().isoformat(),
            confidence_score=self._confidence(clean_url, clean_snippet, provider),
        )

    def _title(self, html: str) -> str:
        match = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
        return self._strip_html(match.group(1)) if match else ""

    def _snippet(self, html: str) -> str:
        text = clean_html_text(html)
        return text[:900]

    def _strip_html(self, value: str) -> str:
        value = re.sub(r"<.*?>", " ", value)
        return re.sub(r"\s+", " ", unescape(value)).strip()

    def _source_type(self, url: str, title: str, snippet: str) -> str:
        haystack = f"{url} {title} {snippet}".lower()
        for source_type, markers in SOURCE_TYPE_RULES:
            if any(marker in haystack for marker in markers):
                return source_type
        if any(domain in urlparse(url).netloc.lower() for domain in TRUSTED_DOMAINS):
            return "trusted_business"
        return "web"

    def _confidence(self, url: str, snippet: str, provider: str) -> float:
        host = urlparse(url).netloc.lower()
        domain_score = 0.78 if any(domain in host for domain in TRUSTED_DOMAINS) else 0.52
        provider_score = 0.12 if provider in {"tavily", "serpapi", "brave"} else 0.02
        snippet_score = min(0.1, len(snippet) / 2000)
        return round(min(0.96, domain_score + provider_score + snippet_score), 2)

    def _is_usable_source(self, source: ResearchSource, query: str = "") -> bool:
        if not source.url or not source.snippet:
            return False
        if is_boilerplate_text(source.snippet):
            return False
        bad_markers = ("unsupported browser", "enable javascript", "access denied", "captcha", "please update your browser")
        if any(marker in source.snippet.lower() for marker in bad_markers):
            return False
        host = urlparse(source.url).netloc.lower()
        if not host:
            return False
        return self._relevant_to_query(query, source)

    def _relevant_to_query(self, query: str, source: ResearchSource) -> bool:
        if not query:
            return True
        market_terms = self.startup_market_terms(query)
        anchors = set(re.findall(r"[a-z0-9]+", query.lower()))
        anchors.update(token for term in market_terms.get("category_terms", []) for token in re.findall(r"[a-z0-9]+", term.lower()))
        anchors.update(token for name in market_terms.get("competitors", []) for token in re.findall(r"[a-z0-9]+", name.lower()))
        anchors -= {"ai", "app", "business", "company", "delivery", "for", "idea", "market", "platform", "product", "startup", "the", "vs"}
        if not anchors:
            return True
        haystack = set(re.findall(r"[a-z0-9]+", f"{source.title} {source.url} {source.snippet}".lower()))
        return bool(anchors & haystack)

    def _canonical_url(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/") or "/"
        return f"{parsed.netloc.lower()}{path}".replace("www.", "")

    def _dedupe(self, items: list[str]) -> list[str]:
        seen = set()
        result = []
        for item in items:
            key = item.strip().lower()
            if key and key not in seen:
                seen.add(key)
                result.append(item)
        return result


web_research_service = WebResearchService()
