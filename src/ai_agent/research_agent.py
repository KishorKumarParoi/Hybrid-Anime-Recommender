"""
Autonomous Anime Research & Deep Curator Agent.
Inspired by the multi-agent research pipeline in 190 - AI Security Project Materials.
Performs multi-step reasoning, thematic vector search, and deep dossier synthesis.
"""

import os
import json
import logging
from typing import Dict, Any, List
from src.ai_agent.guardrails import validate_input, validate_output
from src.ai_agent.retry import with_retry
from src.logger import get_logger

logger = get_logger(__name__)


class AutonomousAnimeResearchAgent:
    """
    4-Stage Autonomous Research Agent:
    1. Intent & Trope Extraction
    2. Deep Vector Retrieval & Candidate Ranking
    3. Multi-Dimensional Analytical Dossier Generation
    4. Egress Safety & Quality Verification
    """

    def __init__(self, retriever, api_key: str = None, model_name: str = "llama-3.1-8b-instant"):
        self.retriever = retriever
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "").strip()
        self.model_name = model_name

    def research(self, topic_query: str, user_api_key: str = None) -> Dict[str, Any]:
        """
        Executes an autonomous deep research cycle on a user anime query or theme.
        Returns a structured research report dictionary.
        """
        # ─── Stage 1: Ingress Safety Guardrail ──────────────────────────────
        is_safe, error_msg, meta = validate_input(topic_query)
        if not is_safe:
            return {
                "status": "blocked",
                "topic": topic_query,
                "report": f"⚠️ Research Request Intercepted: {error_msg}",
                "guardrail_action": "BLOCKED",
                "reason": meta.get("reason", "policy_violation"),
            }

        active_key = user_api_key.strip() if user_api_key else self.api_key

        # ─── Stage 2: Deep Vector Retrieval ─────────────────────────────────
        logger.info(f"Research Agent Stage 2: Retrieving thematic context for '{topic_query}'")
        retrieved_docs = []
        try:
            if self.retriever:
                retrieved_docs = self.retriever.invoke(topic_query)
        except Exception as e:
            logger.warning(f"Retriever invocation failed ({e}), continuing with heuristic research.")

        # Extract candidates and metadata
        candidates = []
        context_snippets = []
        seen = set()

        for doc in (retrieved_docs or [])[:6]:
            meta = doc.metadata or {}
            title = meta.get("title", "Unknown")
            if title and title not in seen:
                seen.add(title)
                candidates.append({
                    "title": title,
                    "score": meta.get("score", "N/A"),
                    "genres": meta.get("genres", "Anime"),
                    "synopsis": doc.page_content[:300],
                })
                context_snippets.append(f"Title: {title} | Genres: {meta.get('genres')} | Score: {meta.get('score')}\nOverview: {doc.page_content[:300]}")

        # ─── Stage 3: LLM Synthesis with Exponential Retry ───────────────────
        raw_report = ""
        if active_key:
            try:
                from langchain_groq import ChatGroq
                from langchain_core.prompts import PromptTemplate
                from langchain_core.output_parsers import StrOutputParser

                prompt_template = PromptTemplate(
                    input_variables=["topic", "context"],
                    template="""You are an expert Chief Anime Research Analyst and Media Critic.
Conduct a rigorous, highly articulate research dossier on the following topic/query:

TOPIC: "{topic}"

VERIFIED DATABASE CONTEXT:
{context}

Format your dossier cleanly with standard GitHub markdown using the following exact sections:
# 📑 Executive Research Dossier: {topic}
## 1. 🎯 Conceptual & Thematic Core
Analyze the underlying philosophical, psychological, or stylistic themes requested.

## 2. 🏆 Premier Anime Selections & In-Depth Critique
For the top matching anime, detail:
- **Title & Studio/Artistry**: Highlight production and aesthetic execution.
- **Narrative Depth**: How the plot specifically delivers on the user's premise.
- **Why It Matters**: Cultural impact or genre-defining qualities.

## 3. 🔍 Tone, Pacing & Content Advisory
Provide objective maturity advisories (violence, psychological intensity, age rating).

## 4. 🧭 Companion Pairings & Next Steps
Recommend 2 complementary titles for post-watch exploration.

Maintain an articulate, insightful tone. Do not use generic filler.
"""
                )

                llm = ChatGroq(api_key=active_key, model=self.model_name, temperature=0.3)
                chain = prompt_template | llm | StrOutputParser()

                context_str = "\n\n---\n\n".join(context_snippets) if context_snippets else "No local database context found."

                def call_chain():
                    return chain.invoke({"topic": topic_query, "context": context_str})

                raw_report = with_retry(call_chain, max_retries=3, delay=1.0)
            except Exception as llm_err:
                logger.warning(f"Groq LLM research generation failed ({llm_err}). Falling back to heuristic synthesis.")

        # If LLM generation failed or no API key, use rich structured heuristic synthesis
        if not raw_report:
            raw_report = self._heuristic_report_synthesis(topic_query, candidates)

        # ─── Stage 4: Egress Output Guardrail ───────────────────────────────
        is_output_safe, output_err = validate_output(raw_report)
        if not is_output_safe:
            logger.critical("Output guardrail blocked research report.")
            return {
                "status": "blocked",
                "topic": topic_query,
                "report": "⚠️ Research output intercepted by safety guardrail due to policy violation.",
                "guardrail_action": "OUTPUT_BLOCKED",
            }

        return {
            "status": "success",
            "topic": topic_query,
            "candidates_found": len(candidates),
            "report": raw_report,
            "guardrail_action": "PASSED",
        }

    def _heuristic_report_synthesis(self, topic: str, candidates: List[Dict[str, Any]]) -> str:
        """Fallback high-fidelity research synthesizer when external LLM is offline."""
        lines = [
            f"# 📑 Executive Research Dossier: {topic.title()}",
            f"*Generated by Autonomous Anime Research Agent (Semantic Analysis Mode)*\n",
            "## 1. 🎯 Conceptual & Thematic Core",
            f"An analysis of the query **\"{topic}\"** reveals a demand for nuanced narrative pacing, "
            f"thematic depth, and distinctive aesthetic identity. The following titles match these criteria.\n",
            "## 2. 🏆 Premier Anime Selections & In-Depth Critique",
        ]

        if not candidates:
            lines.append("No titles closely matching that niche were indexed in the primary store. Broaden search criteria.")
        else:
            for i, c in enumerate(candidates[:4], 1):
                lines.append(f"### {i}. **{c['title']}** (Community Rating: {c['score']} ⭐)")
                lines.append(f"- **Primary Genres**: {c['genres']}")
                lines.append(f"- **Narrative Overview**: {c['synopsis']}...")
                lines.append(f"- **Thematic Alignment**: Strong thematic resonance with user focus: '{topic}'.\n")

        lines.extend([
            "## 3. 🔍 Tone, Pacing & Content Advisory",
            "- **Maturity Rating**: Recommended for general and teen audiences depending on thematic weight.",
            "- **Pacing**: Deliberate, character-driven narrative progression.\n",
            "## 4. 🧭 Companion Pairings & Next Steps",
            "> 💡 *Pro Tip: Connect a Groq Token to unlock full conversational LLM reasoning.*",
        ])

        return "\n".join(lines)
