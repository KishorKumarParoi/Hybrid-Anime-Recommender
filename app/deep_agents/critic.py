"""
Quality Critic Grader (Loop Engineering & Self-Correction)
Evaluates candidate relevance, diversity, and factual consistency.
Triggers iterative query reformulation if quality score falls below 75 threshold.
"""
import logging
from typing import Dict, Any, List
from app.deep_agents.state import DeepAnimeAgentState, CriticEvaluation

logger = logging.getLogger("QualityCritic")


def grade_candidates(
    candidates: List[Dict[str, Any]],
    persona: Dict[str, Any],
    iteration: int,
) -> CriticEvaluation:
    feedback: List[str] = []
    
    if not candidates:
        return CriticEvaluation(
            score=30.0,
            relevance_score=20.0,
            diversity_score=0.0,
            hallucination_detected=False,
            feedback=["No anime candidates retrieved in catalog discovery."],
            suggested_rewrite="Broaden genre constraints and query top-tier classic anime.",
            loop_status="NEEDS_REFINEMENT",
        )

    # 1. Relevance Scoring
    target_genres = set(persona.get("preferred_genres", []))
    target_tone = persona.get("target_tone", "balanced")

    relevance_points = 0.0
    for cand in candidates:
        cand_genres = set(cand.get("genres", []))
        overlap = len(target_genres.intersection(cand_genres))
        if overlap >= 2:
            relevance_points += 100.0
        elif overlap == 1:
            relevance_points += 85.0
        else:
            relevance_points += 55.0

    avg_relevance = min(100.0, relevance_points / max(1, len(candidates)))

    # 2. Diversity Scoring (Different studios or distinct sub-genres)
    studios = [c.get("studio", "") for c in candidates]
    unique_studios = len(set(studios))
    diversity_score = min(100.0, (unique_studios / max(1, len(studios))) * 100.0)

    if diversity_score < 50.0:
        feedback.append("Low studio diversity; candidates heavily skewed toward a single studio.")

    # 3. Factuality Check
    hallucination = False
    for c in candidates:
        if c.get("score", 0.0) < 5.0:
            hallucination = True
            feedback.append(f"Suspiciously low score or unknown rating for {c.get('title')}.")

    # Overall Composite Score
    overall_score = round(
        (avg_relevance * 0.55) + (diversity_score * 0.35) + (0.0 if hallucination else 10.0),
        1,
    )

    # Self-Correction Threshold Check
    if overall_score < 75.0:
        feedback.append(f"Score {overall_score} < 75.0 threshold. Triggering self-correcting query rewrite.")
        # Formulate intelligent rewrite
        primary_genre = persona.get("preferred_genres", ["Psychological"])[0]
        suggested_rewrite = (
            f"Critically acclaimed {target_tone.replace('_', ' ')} {primary_genre} anime "
            f"with deep character writing and high production values."
        )
        loop_status = "NEEDS_REFINEMENT"
    else:
        feedback.append(f"Score {overall_score} passed threshold (>= 75.0). Quality certified.")
        suggested_rewrite = None
        loop_status = "APPROVED"

    return CriticEvaluation(
        score=overall_score,
        relevance_score=avg_relevance,
        diversity_score=diversity_score,
        hallucination_detected=hallucination,
        feedback=feedback,
        suggested_rewrite=suggested_rewrite,
        loop_status=loop_status,
    )


async def quality_critic_node(state: DeepAnimeAgentState) -> Dict[str, Any]:
    """
    Evaluates catalog findings. Decides whether to proceed to CTO Gate
    or loop back with a refined query.
    """
    candidates = state.get("candidate_anime", [])
    persona = state.get("persona_profile", {})
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 2)

    evaluation = grade_candidates(candidates, persona, iteration)

    new_iteration = iteration + 1
    new_loop_status = evaluation.loop_status

    if new_loop_status == "NEEDS_REFINEMENT" and new_iteration >= max_iter:
        logger.info(f"⚠️ [Critic Grader] Max iterations reached ({new_iteration}/{max_iter}). Force approving best effort.")
        new_loop_status = "APPROVED"

    logger.info(
        f"⚖️ [Critic Grader] Iteration {new_iteration}/{max_iter}: "
        f"Score={evaluation.score}, Status={new_loop_status}"
    )

    return {
        "critic_evaluation": evaluation.model_dump(),
        "loop_status": new_loop_status,
        "iteration_count": new_iteration,
        "rewritten_query": evaluation.suggested_rewrite or state.get("rewritten_query"),
    }
