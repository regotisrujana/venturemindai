import time
from typing import Any

from sqlalchemy.orm import Session

from app.models import AgentLog
from app.services.llm_service import LLMService
from app.services.rag_service import rag_service
from app.services.web_research_service import web_research_service


AGENT_SEQUENCE = [
    "supervisor",
    "web_research",
    "research",
    "competitor",
    "swot",
    "market_sizing",
    "strategy",
    "critic",
    "report",
]


class AgentWorkflow:
    def __init__(self) -> None:
        self.llm = LLMService()

    async def _call_llm_json(self, system: str, prompt: str, fallback_value: Any) -> Any:
        return fallback_value

    async def run(self, db: Session, query: str, mode: str, report_id: int | None = None) -> dict[str, Any]:
        evidence = rag_service.search(query, limit=6)
        state: dict[str, Any] = {
            "query": query,
            "mode": mode,
            "citations": [hit.__dict__ for hit in evidence],
            "web_sources": [],
            "rejected_sources": [],
            "sections": {},
            "entities": [],
            "agent_statuses": [{"agent": name, "status": "pending"} for name in AGENT_SEQUENCE],
        }

        for index, agent in enumerate(AGENT_SEQUENCE):
            started = time.perf_counter()
            state["agent_statuses"][index]["status"] = "running"
            db.add(AgentLog(report_id=report_id, agent_name=agent, status="running", message=f"{agent} running for {mode}"))
            db.commit()
            try:
                before_sections = set(state["sections"].keys())
                state = await getattr(self, f"_{agent}")(state)
                status = "completed"
                message = f"{agent} completed for {mode}"
            except Exception as exc:
                status = "failed"
                message = str(exc)
                state["agent_statuses"][index]["status"] = "failed"
                db.add(
                    AgentLog(
                        report_id=report_id,
                        agent_name=agent,
                        status=status,
                        latency_ms=int((time.perf_counter() - started) * 1000),
                        token_estimate=len(str(state)) // 4,
                        message=message,
                    )
                )
                db.commit()
                raise
            latency = int((time.perf_counter() - started) * 1000)
            state["agent_statuses"][index]["status"] = status
            after_sections = set(state["sections"].keys())
            output_keys = sorted(after_sections - before_sections)
            trace = {
                "agent": agent,
                "input": {"query": state["query"], "mode": state["mode"], "entities": state.get("entities", [])},
                "evidence_collected": len(state.get("citations", [])),
                "reasoning_summary": self._agent_reasoning(agent, state),
                "output": {key: state["sections"].get(key) for key in output_keys},
                "status": status,
                "latency_ms": latency,
            }
            state.setdefault("agent_trace", []).append(trace)
            db.add(
                AgentLog(
                    report_id=report_id,
                    agent_name=agent,
                    status=status,
                    latency_ms=latency,
                    token_estimate=len(str(state)) // 4,
                    message=message,
                    input_json=trace["input"],
                    evidence_json={"evidence_count": trace["evidence_collected"], "top_sources": state.get("citations", [])[:5]},
                    reasoning_summary=trace["reasoning_summary"],
                    output_json=trace["output"],
                )
            )
        db.commit()
        return state

    async def _supervisor(self, state: dict[str, Any]) -> dict[str, Any]:
        state["entities"] = web_research_service.extract_entities(state["query"])
        state["plan"] = [
            "Parse companies or startup idea from the user query",
            "Search official sites, pricing pages, product pages, business sources, and public financial sources",
            "Store collected web evidence and index snippets for retrieval",
            "Compare products, pricing, market position, and business signals from cited evidence",
            "Critique unsupported claims and assemble a readable sourced report",
        ]
        return state

    async def _web_research(self, state: dict[str, Any]) -> dict[str, Any]:
        sources, rejected = await web_research_service.research(state["query"], mode=state["mode"], limit=8)
        state["web_sources"] = [source.__dict__ for source in sources]
        state["rejected_sources"] = rejected
        state["citations"].extend(
            {
                "text": source.snippet,
                "source": source.title,
                "url": source.url,
                "source_type": source.source_type,
                "collection": "Web Research",
                "confidence": source.confidence_score,
                "timestamp": source.collected_at,
            }
            for source in sources
        )
        for source in sources:
            rag_service.ingest(source.title, "Web Research", f"{source.title}\n{source.url}\n{source.snippet}")
        state["market_intelligence"] = self._market_intelligence(state)
        return state

    async def _research(self, state: dict[str, Any]) -> dict[str, Any]:
        citations = state.get("citations", [])
        citations_text = "\n".join(
            f"[{i}] Source: {c.get('source')} (URL: {c.get('url')})\nSnippet: {c.get('text')}"
            for i, c in enumerate(citations)
        )

        overview_fallback = {
            "summary": self._evidence_summary(state, "Company overview"),
            "claims": self._claims_from_sources(state, "official"),
            "limitations": self._limitations(state),
        }
        overview_prompt = f"""
        Analyze the query '{state['query']}' and the following citations:
        {citations_text}

        Output a JSON object containing a detailed Overview of the company, startup idea, or comparison matching this exact structure:
        {{
          "summary": "A detailed 2-3 sentence overview of the company, idea, or entities based on the citations.",
          "claims": [
            {{
              "claim": "Direct claim or metric from a citation.",
              "source_name": "Title of the source",
              "source_url": "URL of the source",
              "source_type": "official",
              "confidence_score": 0.8,
              "reason": "Why this claim is verified"
            }}
          ],
          "limitations": ["List of any limitations or missing details in the citations."]
        }}
        """
        overview_res = await self._call_llm_json(
            "You are the Research Agent. Generate a detailed Company Overview. Output ONLY valid JSON.",
            overview_prompt,
            overview_fallback
        )

        market_fallback = {
            "summary": self._evidence_summary(state, "Market position"),
            "claims": self._claims_from_sources(state, "market"),
            "limitations": self._limitations(state),
        }
        market_prompt = f"""
        Analyze the query '{state['query']}' and the following citations:
        {citations_text}

        Output a JSON object containing a detailed Market Position analysis matching this exact structure:
        {{
          "summary": "A detailed 2-3 sentence summary of the market position, trends, or competitive positioning based on the citations.",
          "claims": [
            {{
              "claim": "Direct claim or metric from a citation about market sizing or position.",
              "source_name": "Title of the source",
              "source_url": "URL of the source",
              "source_type": "market",
              "confidence_score": 0.8,
              "reason": "Why this claim is verified"
            }}
          ],
          "limitations": ["List of any limitations or missing details in the citations."]
        }}
        """
        market_res = await self._call_llm_json(
            "You are the Research Agent. Generate a detailed Market Position overview. Output ONLY valid JSON.",
            market_prompt,
            market_fallback
        )

        state["sections"]["company_overview"] = {
            "summary": overview_res.get("summary", overview_fallback["summary"]),
            "entities": state.get("entities", []),
            "claims": overview_res.get("claims", overview_fallback["claims"]),
            "limitations": overview_res.get("limitations", overview_fallback["limitations"]),
        }
        state["sections"]["market_position"] = {
            "summary": market_res.get("summary", market_fallback["summary"]),
            "claims": market_res.get("claims", market_fallback["claims"]),
            "limitations": market_res.get("limitations", market_fallback["limitations"]),
        }
        return state

    async def _competitor(self, state: dict[str, Any]) -> dict[str, Any]:
        citations = state.get("citations", [])
        citations_text = "\n".join(
            f"[{i}] Source: {c.get('source')} (URL: {c.get('url')})\nSnippet: {c.get('text')}"
            for i, c in enumerate(citations)
        )
        entities = state.get("entities", []) or [state["query"]]

        fallback_table = self._competitor_table(state)
        fallback_gap = self._feature_gap_analysis(state)
        fallback_matrix = self._positioning_matrix(state)

        prompt = f"""
        Analyze the query '{state['query']}', entities {entities}, and the following citations:
        {citations_text}

        Compare the products and features of the entities. Output a JSON object containing:
        {{
          "product_summary": "Detailed summary comparing products or capabilities.",
          "feature_gap_analysis": [
            {{
              "gap": "Description of the product/feature gap...",
              "action": "Actionable recommendation to address the gap...",
              "citation": "Source URL",
              "confidence_score": 0.8
            }}
          ],
          "pricing_summary": "Detailed pricing structure summary or comparison.",
          "pricing_claims": [
            {{
              "claim": "Pricing claim extracted from citations...",
              "source_name": "Title of the source",
              "source_url": "URL of the source",
              "source_type": "pricing",
              "confidence_score": 0.8,
              "reason": "Why verified"
            }}
          ]
        }}
        """
        res = await self._call_llm_json(
            "You are the Competitor Agent. Benchmark products, features, and pricing. Output ONLY valid JSON.",
            prompt,
            {}
        )

        state["sections"]["product_comparison"] = {
            "summary": res.get("product_summary") or self._evidence_summary(state, "Product comparison"),
            "comparison_table": fallback_table,
            "feature_gap_analysis": res.get("feature_gap_analysis") or fallback_gap,
            "positioning_matrix": fallback_matrix,
            "competitive_advantage_score": self._evidence_score(state, "competitive advantage"),
            "competitive_threat_score": self._evidence_score(state, "competitive threat"),
            "claims": self._claims_from_sources(state, "product"),
            "limitations": self._limitations(state),
        }
        state["sections"]["pricing_comparison"] = {
            "summary": res.get("pricing_summary") or self._pricing_summary(state),
            "claims": res.get("pricing_claims") or self._claims_from_sources(state, "pricing"),
            "limitations": self._limitations(state),
        }
        return state

    async def _swot(self, state: dict[str, Any]) -> dict[str, Any]:
        citations = state.get("citations", [])
        citations_text = "\n".join(
            f"[{i}] Source: {c.get('source')} (URL: {c.get('url')})\nSnippet: {c.get('text')}"
            for i, c in enumerate(citations)
        )
        evidence_count = len(citations)

        fallback = {
            "strengths": self._scored_items("strength", state, evidence_count),
            "weaknesses": self._scored_items("weakness", state, evidence_count),
            "opportunities": self._scored_items("opportunity", state, evidence_count),
            "threats": self._scored_items("threat", state, evidence_count),
        }

        prompt = f"""
        Perform a SWOT analysis for the query '{state['query']}' using the following citations:
        {citations_text}

        Output a JSON object matching this structure:
        {{
          "strengths": [
            {{
              "item": "Strength point",
              "reason": "Reason based on citations",
              "evidence": "Source title",
              "citation": "Source URL",
              "confidence_score": 0.8
            }}
          ],
          "weaknesses": [...],
          "opportunities": [...],
          "threats": [...]
        }}
        """
        res = await self._call_llm_json(
            "You are the SWOT Agent. Structure strengths, weaknesses, opportunities, and threats based on citations. Output ONLY valid JSON.",
            prompt,
            fallback
        )

        state["sections"]["swot_comparison"] = {
            "strengths": res.get("strengths") or fallback["strengths"],
            "weaknesses": res.get("weaknesses") or fallback["weaknesses"],
            "opportunities": res.get("opportunities") or fallback["opportunities"],
            "threats": res.get("threats") or fallback["threats"],
        }
        return state

    async def _financial(self, state: dict[str, Any]) -> dict[str, Any]:
        citations = state.get("citations", [])
        citations_text = "\n".join(
            f"[{i}] Source: {c.get('source')} (URL: {c.get('url')})\nSnippet: {c.get('text')}"
            for i, c in enumerate(citations)
        )

        fallback_metrics = self._financial_metrics(state)
        fallback_summary = self._financial_summary(state)

        prompt = f"""
        Analyze the query '{state['query']}' and citations:
        {citations_text}

        Extract financial details and health. Output a JSON object containing:
        {{
          "summary": "Financial and business signals overview...",
          "metrics": {{
             "Revenue": {{ "value": "extracted value or 'not publicly verified'", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
             "Revenue Growth": {{ "value": "extracted value or 'not publicly verified'", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
             "CAGR": {{ "value": "extracted value or 'not publicly verified'", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
             "Market Cap": {{ "value": "extracted value or 'not publicly verified'", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
             "EBITDA": {{ "value": "extracted value or 'not publicly verified'", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
             "Profit Margin": {{ "value": "extracted value or 'not publicly verified'", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
             "Funding Raised": {{ "value": "extracted value or 'not publicly verified'", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
             "Burn Rate": {{ "value": "extracted value or 'not publicly verified'", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
             "Customer Growth": {{ "value": "extracted value or 'not publicly verified'", "evidence": "...", "citation": "...", "confidence_score": 0.8 }}
          }},
          "financial_health_score": {{ "score": 80, "reason": "...", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
          "growth_score": {{ "score": 80, "reason": "...", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
          "investment_score": {{ "score": 80, "reason": "...", "evidence": "...", "citation": "...", "confidence_score": 0.8 }}
        }}
        """
        res = await self._call_llm_json(
            "You are the Financial Agent. Estimate revenue, costs, growth, and investment signals. Output ONLY valid JSON.",
            prompt,
            {}
        )

        state["sections"]["financial_business_signals"] = {
            "summary": res.get("summary") or fallback_summary,
            "metrics": res.get("metrics") or fallback_metrics,
            "financial_health_score": res.get("financial_health_score") or self._evidence_score(state, "financial health"),
            "growth_score": res.get("growth_score") or self._evidence_score(state, "growth"),
            "investment_score": res.get("investment_score") or self._evidence_score(state, "investment"),
            "claims": self._claims_from_sources(state, "financial"),
            "limitations": self._limitations(state),
        }
        return state

    async def _market_sizing(self, state: dict[str, Any]) -> dict[str, Any]:
        citations = state.get("citations", [])
        citations_text = "\n".join(
            f"[{i}] Source: {c.get('source')} (URL: {c.get('url')})\nSnippet: {c.get('text')}"
            for i, c in enumerate(citations)
        )

        prompt = f"""
        Estimate the Market Sizing (TAM, SAM, SOM) for the query '{state['query']}' using the citations:
        {citations_text}

        Output a JSON object matching this structure:
        {{
          "tam": {{ "value": "estimated TAM, e.g. $10B or 'not publicly verified'", "calculation": "Method/logic used...", "citation": "Source URL", "confidence_score": 0.8 }},
          "sam": {{ "value": "estimated SAM", "calculation": "...", "citation": "Source URL", "confidence_score": 0.8 }},
          "som": {{ "value": "estimated SOM", "calculation": "...", "citation": "Source URL", "confidence_score": 0.8 }},
          "bottom_up_methodology": {{ "method": "bottom-up", "calculation": "Detailed bottom-up math/steps...", "citation": "Source URL", "confidence_score": 0.8 }},
          "top_down_methodology": {{ "method": "top-down", "calculation": "Detailed top-down math/steps...", "citation": "Source URL", "confidence_score": 0.8 }}
        }}
        """
        res = await self._call_llm_json(
            "You are the Research Agent. Estimate TAM, SAM, SOM and explain methodologies. Output ONLY valid JSON.",
            prompt,
            {}
        )

        state["sections"]["market_sizing"] = {
            "tam": res.get("tam") or self._market_size_item("TAM", state),
            "sam": res.get("sam") or self._market_size_item("SAM", state),
            "som": res.get("som") or self._market_size_item("SOM", state),
            "bottom_up_methodology": res.get("bottom_up_methodology") or self._market_methodology("bottom-up", state),
            "top_down_methodology": res.get("top_down_methodology") or self._market_methodology("top-down", state),
            "limitations": self._limitations(state),
        }
        return state

    async def _strategy(self, state: dict[str, Any]) -> dict[str, Any]:
        citations = state.get("citations", [])
        citations_text = "\n".join(
            f"[{i}] Source: {c.get('source')} (URL: {c.get('url')})\nSnippet: {c.get('text')}"
            for i, c in enumerate(citations)
        )

        prompt = f"""
        Formulate strategic recommendations for query '{state['query']}' based on the citations:
        {citations_text}

        Output a JSON object matching this structure:
        {{
          "summary": "Detailed strategic summary recommendation...",
          "go_to_market_strategy": {{ "recommendation": "...", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
          "pricing_strategy": {{ "recommendation": "...", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
          "market_entry_strategy": {{ "recommendation": "...", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
          "customer_acquisition_strategy": {{ "recommendation": "...", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
          "product_expansion_opportunities": {{ "recommendation": "...", "evidence": "...", "citation": "...", "confidence_score": 0.8 }},
          "risk_mitigation_plan": {{ "recommendation": "...", "evidence": "...", "citation": "...", "confidence_score": 0.8 }}
        }}
        """
        res = await self._call_llm_json(
            "You are the Strategy Agent. Formulate GTM, entry, acquisition, and pricing plans. Output ONLY valid JSON.",
            prompt,
            {}
        )

        state["sections"]["strategic_recommendation"] = {
            "summary": res.get("summary") or self._evidence_summary(state, "Strategic recommendation"),
            "go_to_market_strategy": res.get("go_to_market_strategy") or self._strategy_item("Go-To-Market Strategy", state),
            "pricing_strategy": res.get("pricing_strategy") or self._strategy_item("Pricing Strategy", state),
            "market_entry_strategy": res.get("market_entry_strategy") or self._strategy_item("Market Entry Strategy", state),
            "customer_acquisition_strategy": res.get("customer_acquisition_strategy") or self._strategy_item("Customer Acquisition Strategy", state),
            "product_expansion_opportunities": res.get("product_expansion_opportunities") or self._strategy_item("Product Expansion Opportunities", state),
            "risk_mitigation_plan": res.get("risk_mitigation_plan") or self._strategy_item("Risk Mitigation Plan", state),
        }
        return state

    async def _critic(self, state: dict[str, Any]) -> dict[str, Any]:
        citations = state.get("citations", [])
        citations_text = "\n".join(
            f"[{i}] Source: {c.get('source')} (URL: {c.get('url')})\nSnippet: {c.get('text')}"
            for i, c in enumerate(citations)
        )
        citation_count = len(citations)

        fallback = {
            "unsupported_claims": [] if citation_count else ["No external or uploaded evidence was available. Treat all analysis as preliminary."],
            "contradictions": [],
            "confidence_score": self._overall_confidence(state),
        }

        prompt = f"""
        Identify any unsupported claims, gaps, or contradictions in the citations relative to query '{state['query']}':
        {citations_text}

        Output a JSON object matching this structure:
        {{
          "unsupported_claims": ["List of unsupported claims or gaps in source evidence..."],
          "contradictions": ["List of direct contradictions in the source citations..."],
          "confidence_score": 0.85
        }}
        """
        res = await self._call_llm_json(
            "You are the Critic Agent. Identify contradictions, unsupported claims, and evaluate overall confidence. Output ONLY valid JSON.",
            prompt,
            fallback
        )

        state["critic"] = {
            "unsupported_claims": res.get("unsupported_claims") or fallback["unsupported_claims"],
            "contradictions": res.get("contradictions") or fallback["contradictions"],
            "confidence_score": res.get("confidence_score") or fallback["confidence_score"],
        }
        return state

    async def _report(self, state: dict[str, Any]) -> dict[str, Any]:
        citations = state.get("citations", [])
        sections_summary = "\n".join(
            f"Section: {name}\nDetails: {str(val)[:400]}..."
            for name, val in state.get("sections", {}).items()
        )

        fallback_scorecard = self._scorecard(state)
        fallback_viability = round(sum(item["score"] for item in fallback_scorecard.values()) / len(fallback_scorecard))

        prompt = f"""
        Synthesize the final report scorecard and executive summary for the query '{state['query']}' based on these generated sections:
        {sections_summary}

        Output a JSON object matching this structure:
        {{
          "title": "Professional Business Strategy Report Title",
          "executive_summary": "A high-quality 2-3 paragraph executive summary synthesizing the strategic findings.",
          "scorecard": {{
             "market_potential": {{ "score": 85, "reason": "Reason based on market potential...", "evidence": "Key sources...", "confidence": 0.8 }},
             "innovation": {{ "score": 85, "reason": "...", "evidence": "...", "confidence": 0.8 }},
             "revenue_potential": {{ "score": 85, "reason": "...", "evidence": "...", "confidence": 0.8 }},
             "competition_risk": {{ "score": 40, "reason": "High score means high risk or high severity. Reason...", "evidence": "...", "confidence": 0.8 }},
             "feasibility": {{ "score": 85, "reason": "...", "evidence": "...", "confidence": 0.8 }},
             "scalability": {{ "score": 85, "reason": "...", "evidence": "...", "confidence": 0.8 }},
             "investment_attractiveness": {{ "score": 85, "reason": "...", "evidence": "...", "confidence": 0.8 }}
          }},
          "risks": [
             {{ "item": "Risk description", "reason": "...", "evidence": "...", "citation": "...", "confidence_score": 0.8 }}
          ]
        }}
        """
        res = await self._call_llm_json(
            "You are the Report Agent. Assemble final scores, executive summary, and scorecard. Output ONLY valid JSON.",
            prompt,
            {}
        )

        scorecard = res.get("scorecard") or fallback_scorecard
        viability = round(sum(item["score"] for item in scorecard.values()) / len(scorecard)) if scorecard else fallback_viability

        state["scorecard"] = scorecard
        state["viability_score"] = viability
        state["title"] = res.get("title") or f"Business Strategy Report: {state['query'][:80]}"
        state["executive_summary"] = res.get("executive_summary") or self._evidence_summary(state, "Executive summary")
        state["sections"]["risks"] = {"items": res.get("risks") or self._scored_items("risk", state, len(citations))}
        state["sections"]["sources_used"] = {"items": citations}
        state["research_summary"] = {
            "sources_collected": len(state.get("web_sources", [])),
            "rejected_sources": len(state.get("rejected_sources", [])),
            "final_evidence_count": len(citations),
            "report_confidence": state["critic"]["confidence_score"],
        }
        return state

    def _evidence_summary(self, state: dict[str, Any], topic: str) -> str:
        citations = state.get("citations", [])
        if not citations:
            return f"{topic}: insufficient verified evidence was collected for '{state['query']}'. Upload sources or enable web access before using this for decisions."
        top = citations[:3]
        source_names = ", ".join(item.get("source", "source") for item in top)
        return f"{topic}: analysis is based on {len(citations)} collected evidence items, led by {source_names}."

    def _claims_from_sources(self, state: dict[str, Any], label: str) -> list[dict[str, Any]]:
        claims = []
        filtered = [
            item
            for item in state.get("citations", [])
            if label in (item.get("source_type", "") + " " + item.get("collection", "")).lower()
        ]
        if not filtered:
            filtered = state.get("citations", [])
        for item in filtered[:6]:
            claims.append(
                {
                    "claim": item.get("text", item.get("snippet", ""))[:260],
                    "source_name": item.get("source", "Unknown source"),
                    "source_url": item.get("url", ""),
                    "source_type": item.get("source_type", item.get("collection", "unknown")),
                    "extraction_timestamp": item.get("timestamp", ""),
                    "confidence_score": item.get("confidence", 0.5),
                    "reason": f"Collected by {label} analysis from retrieved evidence.",
                }
            )
        return claims

    def _limitations(self, state: dict[str, Any]) -> list[str]:
        if state.get("citations"):
            return ["Only cited evidence is used; exact financial figures are marked not publicly verified when unavailable."]
        return ["No cited evidence was available, so numeric market and financial claims are omitted."]

    def _pricing_summary(self, state: dict[str, Any]) -> str:
        pricing_sources = [item for item in state.get("citations", []) if "pricing" in item.get("source_type", "")]
        if not pricing_sources:
            return "Pricing data is not publicly verified from collected sources."
        return self._evidence_summary({**state, "citations": pricing_sources}, "Pricing comparison")

    def _financial_summary(self, state: dict[str, Any]) -> str:
        financial_sources = [item for item in state.get("citations", []) if "financial" in item.get("source_type", "")]
        if not financial_sources:
            return "Revenue, growth, and financial data are not publicly verified from collected sources."
        return self._evidence_summary({**state, "citations": financial_sources}, "Financial/business signals")

    def _recommendations(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        confidence = self._overall_confidence(state)
        evidence = self._top_evidence(state)
        return [
            {
                "recommendation": "Validate market demand with primary customer interviews before committing budget.",
                "evidence": evidence["source_name"],
                "citation": evidence["source_url"],
                "confidence_score": confidence,
            },
            {
                "recommendation": "Build a competitor evidence table from cited sources before setting pricing.",
                "evidence": evidence["source_name"],
                "citation": evidence["source_url"],
                "confidence_score": confidence,
            },
        ]

    def _scored_items(self, label: str, state: dict[str, Any], evidence_count: int) -> list[dict[str, Any]]:
        confidence = self._overall_confidence(state)
        citations = state.get("citations", [])
        evidence = citations[0] if citations else {}
        return [
            {
                "item": self._specific_bullet(label, state),
                "reason": "Based on collected citations; no unsupported numeric estimate was generated.",
                "evidence": evidence.get("source", "No cited evidence available"),
                "citation": evidence.get("url", ""),
                "confidence_score": confidence,
            }
        ]

    def _scorecard(self, state: dict[str, Any]) -> dict[str, dict[str, Any]]:
        citations = state.get("citations", [])
        avg_confidence = self._overall_confidence(state)
        base = min(82, 45 + len(citations) * 5)
        dimensions = [
            "market_potential",
            "innovation",
            "revenue_potential",
            "competition_risk",
            "feasibility",
            "scalability",
            "investment_attractiveness",
        ]
        return {
            dimension: {
                "score": base if dimension != "competition_risk" else max(20, 100 - base),
                "reason": "Score is derived from number and confidence of collected citations, not random values.",
                "evidence": citations[0].get("source", "No cited evidence available") if citations else "No cited evidence available",
                "confidence": avg_confidence,
            }
            for dimension in dimensions
        }

    def _overall_confidence(self, state: dict[str, Any]) -> float:
        citations = state.get("citations", [])
        if not citations:
            return 0.25
        return round(sum(item.get("confidence", 0.5) for item in citations) / len(citations), 2)

    def _top_evidence(self, state: dict[str, Any]) -> dict[str, Any]:
        citations = state.get("citations", [])
        if not citations:
            return {"source_name": "Not publicly verified", "source_url": "", "source_type": "none", "confidence_score": 0.25}
        item = sorted(citations, key=lambda source: source.get("confidence", 0), reverse=True)[0]
        return {
            "source_name": item.get("source", "Unknown source"),
            "source_url": item.get("url", ""),
            "source_type": item.get("source_type", item.get("collection", "unknown")),
            "confidence_score": item.get("confidence", 0.5),
        }

    def _agent_reasoning(self, agent: str, state: dict[str, Any]) -> str:
        evidence_count = len(state.get("citations", []))
        if evidence_count == 0:
            return f"{agent} found no verified evidence and avoided unsupported claims."
        return f"{agent} used {evidence_count} evidence items and only emitted sourced or explicitly unverified claims."

    def _specific_bullet(self, label: str, state: dict[str, Any]) -> str:
        entities = state.get("entities", [])
        subject = " vs ".join(entities) if entities else state["query"]
        if label == "strength":
            return f"{subject} has identifiable public evidence that can support differentiated positioning."
        if label == "weakness":
            return f"{subject} has gaps where public evidence is incomplete or not directly comparable."
        if label == "opportunity":
            return f"{subject} may benefit from segments or capabilities highlighted by collected sources."
        if label == "threat":
            return f"{subject} faces competitive pressure where cited sources show overlapping products or audiences."
        return f"{subject} risk depends on the strength and completeness of collected evidence."

    def _market_intelligence(self, state: dict[str, Any]) -> dict[str, Any]:
        hints = web_research_service.startup_market_terms(state["query"])
        competitors = []
        for name in hints.get("competitors", []):
            evidence = self._competitor_evidence(name, state.get("citations", []))
            if evidence:
                competitors.append({"name": name, **evidence})
        for name, evidence in self._snippet_competitors(state).items():
            if not any(item["name"].lower() == name.lower() for item in competitors):
                competitors.append({"name": name, **evidence})
        category_sources = []
        for item in state.get("citations", []):
            haystack = f"{item.get('source', '')} {item.get('text', '')} {item.get('source_type', '')}".lower()
            if any(term.lower() in haystack for term in hints.get("category_terms", [])):
                category_sources.append(
                    {
                        "title": item.get("source", "Source"),
                        "url": item.get("url", ""),
                        "snippet": item.get("text", "")[:260],
                        "confidence": item.get("confidence", 0.5),
                    }
                )
        return {
            "market_exists": bool(competitors or category_sources),
            "category_terms": hints.get("category_terms", []),
            "existing_competitors": competitors,
            "category_sources": category_sources[:6],
        }

    def _snippet_competitors(self, state: dict[str, Any]) -> dict[str, dict[str, Any]]:
        known = web_research_service.startup_market_terms(state["query"]).get("competitors", [])
        found: dict[str, dict[str, Any]] = {}
        for item in state.get("citations", []):
            text = f"{item.get('source', '')} {item.get('text', '')}"
            for name in known:
                if name.lower() in text.lower() and name.lower() not in {key.lower() for key in found}:
                    found[name] = {
                        "source_title": item.get("source", "Source"),
                        "source_url": item.get("url", ""),
                        "snippet": item.get("text", "")[:260],
                        "confidence": item.get("confidence", 0.5),
                    }
        return found

    def _competitor_evidence(self, name: str, citations: list[dict[str, Any]]) -> dict[str, Any] | None:
        lowered = name.lower()
        for item in citations:
            text = f"{item.get('source', '')} {item.get('url', '')} {item.get('text', '')}".lower()
            if lowered in text:
                return {
                    "source_title": item.get("source", "Source"),
                    "source_url": item.get("url", ""),
                    "snippet": item.get("text", "")[:260],
                    "confidence": item.get("confidence", 0.5),
                }
        return None

    def _competitor_table(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        entities = state.get("entities", []) or [state["query"]]
        rows = []
        fields = ["Market Share", "Revenue", "Funding", "Customers", "Pricing", "Key Products", "Geographic Reach", "Growth Rate"]
        for field in fields:
            row = {"feature": field}
            for entity in entities:
                evidence = self._best_entity_evidence(state, entity, field)
                row[entity] = {
                    "value": evidence.get("claim", "not publicly verified"),
                    "citation": evidence.get("source_url", ""),
                    "confidence_score": evidence.get("confidence_score", 0.25),
                }
            rows.append(row)
        return rows

    def _best_entity_evidence(self, state: dict[str, Any], entity: str, field: str) -> dict[str, Any]:
        import re
        field_terms = field.lower().split()
        candidates = []
        for item in state.get("citations", []):
            text = f"{item.get('text', '')} {item.get('source', '')}".lower()
            entity_match = re.search(rf"\b{re.escape(entity.lower())}\b", text)
            field_match = any(re.search(rf"\b{re.escape(term)}\b", text) for term in field_terms)
            if entity_match and field_match:
                candidates.append(item)
        if not candidates:
            return {"claim": "not publicly verified", "confidence_score": 0.25}
        best = sorted(candidates, key=lambda item: item.get("confidence", 0), reverse=True)[0]
        return {
            "claim": best.get("text", "")[:180],
            "source_url": best.get("url", ""),
            "confidence_score": best.get("confidence", 0.5),
        }

    def _feature_gap_analysis(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        evidence = self._top_evidence(state)
        return [
            {
                "gap": "Feature gaps require product-page evidence for each compared company.",
                "action": "Prioritize collecting official product and pricing pages before roadmap decisions.",
                "citation": evidence["source_url"],
                "confidence_score": evidence["confidence_score"],
            }
        ]

    def _positioning_matrix(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        entities = state.get("entities", []) or [state["query"]]
        confidence = self._overall_confidence(state)
        return [
            {
                "company": entity,
                "x_axis": "Product breadth",
                "y_axis": "Evidence-backed market visibility",
                "x_value": min(90, 45 + len(entity) * 3),
                "y_value": round(confidence * 100),
                "confidence_score": confidence,
            }
            for entity in entities
        ]

    def _evidence_score(self, state: dict[str, Any], label: str) -> dict[str, Any]:
        confidence = self._overall_confidence(state)
        evidence = self._top_evidence(state)
        return {
            "score": round(confidence * 100),
            "reason": f"{label.title()} score is based on cited source count and average confidence.",
            "evidence": evidence["source_name"],
            "citation": evidence["source_url"],
            "confidence_score": confidence,
        }

    def _financial_metrics(self, state: dict[str, Any]) -> dict[str, dict[str, Any]]:
        metrics = ["Revenue", "Revenue Growth", "CAGR", "Market Cap", "EBITDA", "Profit Margin", "Funding Raised", "Burn Rate", "Customer Growth"]
        return {metric: self._extract_metric(metric, state) for metric in metrics}

    def _extract_metric(self, metric: str, state: dict[str, Any]) -> dict[str, Any]:
        terms = metric.lower().split()
        for item in state.get("citations", []):
            text = item.get("text", "")
            lowered = text.lower()
            if any(term in lowered for term in terms):
                match = re_search_metric(text)
                return {
                    "value": match or "not publicly verified",
                    "evidence": text[:220],
                    "citation": item.get("url", ""),
                    "confidence_score": item.get("confidence", 0.5),
                }
        return {"value": "not publicly verified", "evidence": "No cited source contained this metric.", "citation": "", "confidence_score": 0.25}

    def _market_size_item(self, label: str, state: dict[str, Any]) -> dict[str, Any]:
        evidence = self._top_evidence(state)
        return {
            "value": "not publicly verified",
            "calculation": f"{label} calculation omitted until cited market-size inputs are available.",
            "citation": evidence["source_url"],
            "confidence_score": evidence["confidence_score"],
        }

    def _market_methodology(self, method: str, state: dict[str, Any]) -> dict[str, Any]:
        evidence = self._top_evidence(state)
        return {
            "method": method,
            "calculation": "Requires cited assumptions for customer count, ARPU, geography, and adoption rate.",
            "citation": evidence["source_url"],
            "confidence_score": evidence["confidence_score"],
        }

    def _strategy_item(self, label: str, state: dict[str, Any]) -> dict[str, Any]:
        evidence = self._top_evidence(state)
        if not evidence["source_url"]:
            recommendation = "Not enough verified evidence to make a specific recommendation."
        else:
            recommendation = f"Use cited {evidence['source_type']} evidence to validate {label.lower()} before execution."
        return {
            "recommendation": recommendation,
            "evidence": evidence["source_name"],
            "citation": evidence["source_url"],
            "confidence_score": evidence["confidence_score"],
        }


def re_search_metric(text: str) -> str:
    import re

    match = re.search(r"(\$|₹|Rs\.?)\s?[0-9][0-9,.]*(\s?(million|billion|crore|lakh|bn|m))?", text, re.I)
    if match:
        return match.group(0)
    percent = re.search(r"[0-9]+(\.[0-9]+)?\s?%", text)
    return percent.group(0) if percent else ""


agent_workflow = AgentWorkflow()
