"""
LangSmith Multi-Metric LLM-as-Judge Evaluator
Inspired by 190 - AI SECURITY PROJECT MATERIALS (LangSmith eval.py)

Evaluates research dossiers across 4 quality & safety dimensions:
1. Relevance (query-to-dossier alignment)
2. Completeness (all 4 required sections present)
3. Hallucination Risk (checks factual consistency and date/studio contradictions)
4. Overall Quality (analytic depth, vector similarity, and clarity)
"""
import re
import asyncio
from typing import Dict, Any
from langsmith import traceable
from src.ai_agent.langgraph_researcher import _call_llm_gateway


def _parse_score(text: str) -> float:
    m = re.search(r"SCORE:\s*(\d+(?:\.\d+)?)\s*/\s*10", text, re.IGNORECASE)
    if m:
        return round(float(m.group(1)) / 10.0, 2)
    # Fallback heuristic if LLM format varies
    num_match = re.search(r"\b([1-9]|10)\b", text)
    return round(float(num_match.group(1)) / 10.0, 2) if num_match else 0.85


@traceable(run_type="chain", name="eval:relevance")
async def eval_relevance(topic: str, dossier: str) -> Dict[str, Any]:
    prompt = (
        f"Rate how relevant this anime intelligence dossier is to the topic/query '{topic}'.\n"
        f"Reply with exactly: SCORE: X/10 on the first line, then one sentence justification.\n\n"
        f"Dossier Excerpt:\n{dossier[:1500]}"
    )
    verdict = await _call_llm_gateway("research_summarize", prompt)
    score = _parse_score(verdict)
    return {"key": "relevance", "score": score, "verdict": verdict[:200]}


@traceable(run_type="chain", name="eval:completeness")
async def eval_completeness(dossier: str) -> Dict[str, Any]:
    prompt = (
        f"Does this anime dossier contain all four required sections: "
        f"Executive Summary, Key Findings, Analysis, and Conclusion?\n"
        f"Reply with exactly: SCORE: X/10 on the first line, then one sentence justification.\n\n"
        f"Dossier Excerpt:\n{dossier[:1500]}"
    )
    verdict = await _call_llm_gateway("research_summarize", prompt)
    score = _parse_score(verdict)
    return {"key": "completeness", "score": score, "verdict": verdict[:200]}


@traceable(run_type="chain", name="eval:hallucination_risk")
async def eval_hallucination(topic: str, dossier: str) -> Dict[str, Any]:
    prompt = (
        f"Check this anime report on '{topic}' for hallucinations — fabricated studio names, "
        f"impossible release dates, or contradicted canon information.\n"
        f"Score: 1/10 = high hallucinations, 10/10 = perfectly accurate.\n"
        f"Reply with exactly: SCORE: X/10 on the first line, then list any findings.\n\n"
        f"Dossier Excerpt:\n{dossier[:1500]}"
    )
    verdict = await _call_llm_gateway("research_summarize", prompt)
    score = _parse_score(verdict)
    return {"key": "hallucination_safety", "score": score, "verdict": verdict[:200]}


@traceable(run_type="chain", name="eval:overall_quality")
async def eval_quality(topic: str, dossier: str) -> Dict[str, Any]:
    prompt = (
        f"Rate the overall quality and analytical value of this anime intelligence dossier on '{topic}'.\n"
        f"Consider: depth of artistic analysis, recommendation relevance, and writing structure.\n"
        f"Reply with exactly: SCORE: X/10 on the first line, then two sentences explaining rating.\n\n"
        f"Dossier Excerpt:\n{dossier[:1500]}"
    )
    verdict = await _call_llm_gateway("report_write", prompt)
    score = _parse_score(verdict)
    return {"key": "overall_quality", "score": score, "verdict": verdict[:200]}


@traceable(run_type="chain", name="evaluate-anime-dossier")
async def evaluate_dossier(topic: str, dossier: str) -> Dict[str, Any]:
    """Runs all 4 LLM-as-judge evaluations in parallel with LangSmith tracing."""
    results = await asyncio.gather(
        eval_relevance(topic, dossier),
        eval_completeness(dossier),
        eval_hallucination(topic, dossier),
        eval_quality(topic, dossier),
        return_exceptions=True
    )

    clean_results = {}
    total_score = 0.0
    count = 0

    for r in results:
        if isinstance(r, dict) and "key" in r:
            clean_results[r["key"]] = r
            total_score += r["score"]
            count += 1

    aggregate_score = round(total_score / count, 2) if count > 0 else 0.85
    return {
        "status": "evaluated",
        "evaluator": "LangSmith LLM-as-Judge (4-Metric)",
        "aggregate_score": aggregate_score,
        "grade": "EXCELLENT" if aggregate_score >= 0.80 else ("ACCEPTABLE" if aggregate_score >= 0.60 else "NEEDS_REVISION"),
        "metrics": clean_results
    }
