"""
State Schema for Industrial-Grade Deep Multi-Agent Mesh
Inspired by LangGraph State Machines (Phase 7 Agentic RAG) and AI_Security_Production_App.
"""
from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AnimeCandidate(BaseModel):
    title: str
    studio: str = "Unknown Studio"
    score: float = 8.0
    match_rate: float = 0.90
    genres: List[str] = Field(default_factory=list)
    synopsis: str = ""
    streaming_platforms: List[str] = Field(default_factory=lambda: ["Crunchyroll", "Netflix"])
    vibe: str = ""
    relevance_reason: str = ""


class PersonaProfile(BaseModel):
    target_tone: str = "balanced"  # dark, cerebral, lighthearted, melancholic, epic
    pacing_preference: str = "moderate"  # fast-paced, slow-burn, episodic
    preferred_genres: List[str] = Field(default_factory=list)
    aesthetic: str = "modern"  # cyberpunk, retro_90s, high_production, minimalist
    content_rating_ok: str = "PG-13"  # G, PG, PG-13, R-17+
    sentiment: str = "enthusiastic"


class CriticEvaluation(BaseModel):
    score: float = 85.0  # 0 to 100
    relevance_score: float = 90.0
    diversity_score: float = 80.0
    hallucination_detected: bool = False
    feedback: List[str] = Field(default_factory=list)
    suggested_rewrite: Optional[str] = None
    loop_status: str = "APPROVED"  # "APPROVED" | "NEEDS_REFINEMENT" | "REJECTED"


class CTODecision(BaseModel):
    status: str = "APPROVED"  # "APPROVED" | "PENDING_HITL" | "REJECTED" | "ESCALATED"
    signoff_by: str = "ChiefTasteOfficer-AI"
    editorial_notes: str = ""
    break_glass_token: Optional[str] = None
    is_vip_curated: bool = False


class SafetyAudit(BaseModel):
    is_safe: bool = True
    reason: str = "Clean"
    violation_types: List[str] = Field(default_factory=list)
    pii_redacted: bool = False


class DeepAnimeAgentState(TypedDict):
    """
    State dictionary flowing through the LangGraph Deep Agent Mesh.
    All sub-agents read from and mutate designated partitions.
    """
    topic: str
    session_id: str
    session_history: List[Dict[str, str]]
    task_plan: List[str]
    rewritten_query: Optional[str]
    ltm_context: str
    safety_audit: Dict[str, Any]
    persona_profile: Dict[str, Any]
    search_results: List[Dict[str, Any]]
    candidate_anime: List[Dict[str, Any]]
    studio_lineage: List[Dict[str, Any]]
    critic_evaluation: Dict[str, Any]
    loop_status: str
    iteration_count: int
    max_iterations: int
    cto_decision: Dict[str, Any]
    final_dossier: str
    error: Optional[str]
    telemetry: Dict[str, Any]
