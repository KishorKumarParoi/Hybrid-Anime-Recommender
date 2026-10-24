"""
FastAPI Router for Deep Multi-Agent Mesh (LangGraph + CTO Governance)
Exposes research execution, stateful multi-turn chat, state snapshotting, and CTO HITL approval.
"""
import uuid
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.deep_agents.graph import deep_agent_mesh
from app.deep_agents.state import DeepAnimeAgentState

logger = logging.getLogger("DeepAgentRouter")
router = APIRouter(prefix="/api/v1/deep-agents", tags=["Deep Multi-Agent Mesh"])

# In-memory thread state registry for fast snapshot retrieval
SESSION_STATE_STORE: Dict[str, Dict[str, Any]] = {}


class DeepResearchRequest(BaseModel):
    topic: str = Field(..., json_schema_extra={"example": "Recommend me a dark psychological cyberpunk anime with profound worldbuilding"})
    session_id: Optional[str] = Field(default_factory=lambda: f"session-{uuid.uuid4().hex[:8]}")
    max_iterations: int = Field(default=2, ge=1, le=5)
    user_preferences: Optional[Dict[str, Any]] = None


class DeepResearchResponse(BaseModel):
    session_id: str
    status: str
    dossier: str
    persona_profile: Dict[str, Any]
    candidate_anime: List[Dict[str, Any]]
    studio_lineage: List[Dict[str, Any]]
    critic_evaluation: Dict[str, Any]
    cto_decision: Dict[str, Any]
    safety_audit: Dict[str, Any]
    execution_latency_ms: float


class DeepChatRequest(BaseModel):
    message: str = Field(..., json_schema_extra={"example": "Tell me more about the studio lineage of Psycho-Pass"})
    session_id: str = Field(..., json_schema_extra={"example": "session-abc123"})


class CTOApprovalRequest(BaseModel):
    session_id: str
    break_glass_token: str
    approved: bool
    review_notes: str = "Human-in-the-Loop Curator Review Completed"
    reviewer_id: str = "Lead-Curator-Admin"


@router.post("/research", response_model=DeepResearchResponse)
async def run_deep_agent_research(req: DeepResearchRequest):
    """
    Executes the full Deep Multi-Agent Mesh:
    Supervisor -> Safety Guardrail -> Persona Taste Profiler -> Catalog Discovery (RRF) ->
    Quality Critic (Self-Correction Loop) -> Chief Taste Officer (CTO Gate) -> Executive Dossier Synthesizer.
    """
    session_id = req.session_id or f"session-{uuid.uuid4().hex[:8]}"

    initial_state: DeepAnimeAgentState = {
        "topic": req.topic,
        "session_id": session_id,
        "session_history": [],
        "task_plan": [],
        "rewritten_query": None,
        "ltm_context": "",
        "safety_audit": {},
        "persona_profile": {},
        "search_results": [],
        "candidate_anime": [],
        "studio_lineage": [],
        "critic_evaluation": {},
        "loop_status": "PENDING",
        "iteration_count": 0,
        "max_iterations": req.max_iterations,
        "cto_decision": {},
        "final_dossier": "",
        "error": None,
        "telemetry": {},
    }

    try:
        final_state = await deep_agent_mesh.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": session_id}},
        )

        # Cache session state snapshot
        SESSION_STATE_STORE[session_id] = final_state

        latency = final_state.get("telemetry", {}).get("execution_latency_ms", 0.0)

        return DeepResearchResponse(
            session_id=session_id,
            status=final_state.get("loop_status", "APPROVED"),
            dossier=final_state.get("final_dossier", ""),
            persona_profile=final_state.get("persona_profile", {}),
            candidate_anime=final_state.get("candidate_anime", []),
            studio_lineage=final_state.get("studio_lineage", []),
            critic_evaluation=final_state.get("critic_evaluation", {}),
            cto_decision=final_state.get("cto_decision", {}),
            safety_audit=final_state.get("safety_audit", {}),
            execution_latency_ms=latency,
        )
    except Exception as e:
        logger.error(f"Error executing deep multi-agent mesh: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Deep Agent execution failure: {str(e)}")


@router.post("/chat")
async def chat_with_deep_agents(req: DeepChatRequest):
    """
    Stateful conversational chat utilizing LangGraph thread checkpointing.
    Continues research with previous conversation context.
    """
    session_id = req.session_id
    prior_state = SESSION_STATE_STORE.get(session_id)

    history = []
    if prior_state:
        history = list(prior_state.get("session_history", []))
        history.append({"role": "user", "content": req.message})

    state: DeepAnimeAgentState = {
        "topic": req.message,
        "session_id": session_id,
        "session_history": history,
        "task_plan": [],
        "rewritten_query": None,
        "ltm_context": prior_state.get("final_dossier", "") if prior_state else "",
        "safety_audit": {},
        "persona_profile": prior_state.get("persona_profile", {}) if prior_state else {},
        "search_results": [],
        "candidate_anime": [],
        "studio_lineage": [],
        "critic_evaluation": {},
        "loop_status": "PENDING",
        "iteration_count": 0,
        "max_iterations": 2,
        "cto_decision": {},
        "final_dossier": "",
        "error": None,
        "telemetry": {},
    }

    final_state = await deep_agent_mesh.ainvoke(
        state,
        config={"configurable": {"thread_id": session_id}},
    )

    history.append({"role": "assistant", "content": final_state.get("final_dossier", "")[:500]})
    final_state["session_history"] = history
    SESSION_STATE_STORE[session_id] = final_state

    return {
        "session_id": session_id,
        "response": final_state.get("final_dossier", ""),
        "critic_score": final_state.get("critic_evaluation", {}).get("score", 0.0),
        "cto_status": final_state.get("cto_decision", {}).get("status", "APPROVED"),
    }


@router.get("/state/{session_id}")
async def get_session_state(session_id: str):
    """Retrieves full state snapshot for a given research session."""
    state = SESSION_STATE_STORE.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found in active checkpointer memory.")

    return {
        "session_id": session_id,
        "loop_status": state.get("loop_status"),
        "iteration_count": state.get("iteration_count"),
        "critic_evaluation": state.get("critic_evaluation"),
        "cto_decision": state.get("cto_decision"),
        "persona_profile": state.get("persona_profile"),
        "candidates_count": len(state.get("candidate_anime", [])),
    }


@router.post("/cto/approve")
async def approve_cto_break_glass(req: CTOApprovalRequest):
    """
    Human-in-the-Loop (HITL) Break-Glass endpoint.
    Permits an authorized human curator to approve or override a quarantined session.
    """
    state = SESSION_STATE_STORE.get(req.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found.")

    cto_state = state.get("cto_decision", {})
    expected_token = cto_state.get("break_glass_token")

    if not expected_token or expected_token != req.break_glass_token:
        raise HTTPException(status_code=403, detail="Invalid or mismatched Break-Glass token.")

    # Update CTO Decision
    if req.approved:
        cto_state["status"] = "APPROVED_BY_HUMAN_CURATOR"
        cto_state["signoff_by"] = f"HITL-Curator ({req.reviewer_id})"
        cto_state["editorial_notes"] = f"Human curator override approved: {req.review_notes}"
        state["loop_status"] = "APPROVED"
    else:
        cto_state["status"] = "REJECTED_BY_HUMAN_CURATOR"
        cto_state["signoff_by"] = f"HITL-Curator ({req.reviewer_id})"
        cto_state["editorial_notes"] = f"Human curator rejected: {req.review_notes}"
        state["loop_status"] = "REJECTED"

    state["cto_decision"] = cto_state
    SESSION_STATE_STORE[req.session_id] = state

    return {
        "session_id": req.session_id,
        "cto_status": cto_state["status"],
        "reviewer": cto_state["signoff_by"],
        "notes": cto_state["editorial_notes"],
    }
