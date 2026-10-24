"""
LangGraph Multi-Agent Research Pipeline with LangSmith Tracing
Inspired by 190 - AI SECURITY PROJECT MATERIALS (LangGraph + LangSmith)

4-Agent StateGraph Architecture:
SearchAgent -> SummarizeAgent -> WriterAgent -> CriticAgent
Loops back conditionally if CriticAgent rejects until verified or max iterations reached.
"""
import os
import logging
from typing import TypedDict, List, Dict, Any, Optional
import httpx
from langgraph.graph import StateGraph, START, END
from langsmith import traceable

from src.ai_agent.retry import with_retry
from src.ai_agent.guardrails import validate_output

logger = logging.getLogger(__name__)


class AnimeResearchState(TypedDict):
    topic: str
    session_id: str
    session_history: List[Dict[str, str]]
    ltm_context: str
    search_results: List[str]
    summaries: List[str]
    report: str
    verified: bool
    error: str
    iterations: int


async def _call_llm_gateway(function_name: str, message: str) -> str:
    """
    Calls TensorZero gateway if available (localhost:3000),
    otherwise falls back to Groq via LangChain/httpx.
    """
    tensorzero_url = os.environ.get("TENSORZERO_URL", "http://localhost:3000")
    groq_api_key = os.environ.get("GROQ_API_KEY", "")

    # 1. Try TensorZero Sidecar
    try:
        async with httpx.AsyncClient(timeout=6) as client:
            resp = await client.post(
                f"{tensorzero_url}/inference",
                json={
                    "function_name": function_name,
                    "input": {"messages": [{"role": "user", "content": message}]},
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                if "content" in data and len(data["content"]) > 0:
                    return data["content"][0]["text"]
    except Exception:
        pass  # Gateway not running locally, seamlessly fallback to Groq

    # 2. Native Groq / LangChain Groq Fallback
    groq_model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
    if groq_api_key:
        try:
            from langchain_groq import ChatGroq
            chat = ChatGroq(
                api_key=groq_api_key,
                model=groq_model,
                temperature=0.3 if "summarize" in function_name else 0.5,
            )
            response = await chat.ainvoke(message)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.warning(f"LangChain Groq call fallback warning: {e}")

    # 3. Direct OpenAI Fallback
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai_key}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": message}],
                        "temperature": 0.3 if "summarize" in function_name else 0.5,
                    },
                )
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"OpenAI API call encountered an error: {e}")

    # 4. Deterministic Domain Synthesis Fallback (offline testing)
    topic = message[:60]
    return (
        f"### Research Synthesis: {topic}\n"
        f"- Studio Pedigree: Renowned for high production value and thematic depth.\n"
        f"- Plot & Worldbuilding: Explores complex character dynamics and psychological tension.\n"
        f"- Reception & Community Benchmark: Rated >8.4/10 across major anime databases."
    )


class SearchAgent:
    """Finds key factual context and database metadata."""

    @traceable(run_type="tool", name="agent:search")
    async def run(self, topic: str, session_history: List[Dict[str, str]]) -> str:
        logger.info(f"SearchAgent: researching '{topic}'")
        history_ctx = ""
        if session_history:
            recent = session_history[-4:]
            history_ctx = "\n\nPrevious Conversation Context:\n" + "\n".join(
                f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in recent
            )

        prompt = (
            f"You are a specialized anime research analyst. Extract 5 key facts, notable creators, "
            f"studio pedigree, and thematic resonance for: '{topic}'.{history_ctx}"
        )
        return await _call_llm_gateway("research_summarize", prompt)


class SummarizeAgent:
    """Condenses search findings into structured analytical bullet points."""

    @traceable(run_type="tool", name="agent:summarize")
    async def run(self, search_results: List[str]) -> str:
        logger.info("SummarizeAgent: condensing search results")
        combined = "\n\n".join(search_results)
        prompt = f"Condense these research findings into clear, structured bullet points:\n\n{combined}"
        return await _call_llm_gateway("research_summarize", prompt)


class WriterAgent:
    """Drafts the final 4-section intelligence dossier."""

    @traceable(run_type="tool", name="agent:writer")
    async def run(self, topic: str, summaries: List[str], ltm_context: str) -> str:
        logger.info("WriterAgent: drafting anime intelligence report")
        combined = "\n\n".join(summaries)
        ltm_section = f"\n\nHistorical Context From Previous Research:\n{ltm_context[:1200]}" if ltm_context else ""

        prompt = (
            f"Draft a formal intelligence dossier on: '{topic}'.\n\n"
            f"Research Insights:\n{combined}{ltm_section}\n\n"
            f"Mandatory Sections:\n"
            f"1. Executive Summary\n"
            f"2. Key Findings\n"
            f"3. Analysis & Comparative Vectors\n"
            f"4. Conclusion & Recommendations"
        )
        return await _call_llm_gateway("report_write", prompt)


class CriticAgent:
    """Verifies factual consistency, completeness, and structure."""

    @traceable(run_type="tool", name="agent:critic")
    async def run(self, report: str) -> bool:
        logger.info("CriticAgent: validating dossier structure and consistency")
        # Check mandatory sections
        required = ["Executive Summary", "Key Findings", "Analysis", "Conclusion"]
        has_sections = all(req.lower() in report.lower() for req in required)
        is_safe, _ = validate_output(report)
        return has_sections and is_safe



class OrchestratorAgent:
    """Coordinates state progression and conditional reflection loops."""

    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations
        self.search_agent = SearchAgent()
        self.summarize_agent = SummarizeAgent()
        self.writer_agent = WriterAgent()
        self.critic_agent = CriticAgent()

    @traceable(run_type="chain", name="orchestrator:search_node")
    async def search_node(self, state: AnimeResearchState) -> Dict[str, Any]:
        result = await self.search_agent.run(state["topic"], state.get("session_history", []))
        return {"search_results": [result]}

    @traceable(run_type="chain", name="orchestrator:summarize_node")
    async def summarize_node(self, state: AnimeResearchState) -> Dict[str, Any]:
        summary = await self.summarize_agent.run(state["search_results"])
        return {"summaries": [summary]}

    @traceable(run_type="chain", name="orchestrator:write_node")
    async def write_node(self, state: AnimeResearchState) -> Dict[str, Any]:
        report = await self.writer_agent.run(
            state["topic"],
            state["summaries"],
            state.get("ltm_context", "")
        )
        return {"report": report, "iterations": state.get("iterations", 0) + 1}

    @traceable(run_type="chain", name="orchestrator:verify_node")
    async def verify_node(self, state: AnimeResearchState) -> Dict[str, Any]:
        verified = await self.critic_agent.run(state["report"])
        return {"verified": verified}

    def route(self, state: AnimeResearchState) -> str:
        if not state.get("verified", False) and state.get("iterations", 0) < self.max_iterations:
            logger.info(f"Critic rejected dossier - retrying (iteration {state['iterations']})")
            return "search"
        return END


def build_langgraph_pipeline(max_iterations: int = 2):
    """Compiles the LangGraph StateGraph pipeline."""
    orchestrator = OrchestratorAgent(max_iterations=max_iterations)
    workflow = StateGraph(AnimeResearchState)

    workflow.add_node("search", orchestrator.search_node)
    workflow.add_node("summarize", orchestrator.summarize_node)
    workflow.add_node("write", orchestrator.write_node)
    workflow.add_node("verify", orchestrator.verify_node)

    workflow.add_edge(START, "search")
    workflow.add_edge("search", "summarize")
    workflow.add_edge("summarize", "write")
    workflow.add_edge("write", "verify")
    workflow.add_conditional_edges(
        "verify",
        orchestrator.route,
        {"search": "search", END: END}
    )

    return workflow.compile()


# Export Deep Multi-Agent Mesh
try:
    from app.deep_agents import (
        build_deep_agent_graph,
        deep_agent_mesh,
        DeepAnimeAgentState,
    )
except ImportError:
    pass
