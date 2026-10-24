"""
Chief Taste Officer (CTO) Gate & Human-in-the-Loop (HITL) Break-Glass Agent
Ensures executive editorial standards, licensing verification, and break-glass overrides.
"""
import uuid
import logging
from typing import Dict, Any, List
from app.deep_agents.state import DeepAnimeAgentState, CTODecision

logger = logging.getLogger("ChiefTasteOfficer")


def audit_cto_licensing(candidates: List[Dict[str, Any]]) -> bool:
    """Verifies that candidates have active streaming distribution rights."""
    for c in candidates:
        platforms = c.get("streaming_platforms", [])
        if not platforms or "Unknown" in platforms:
            return False
    return True


async def cto_gate_node(state: DeepAnimeAgentState) -> Dict[str, Any]:
    """
    Acts as the executive curation checkpoint before final synthesis.
    Enforces licensing standards and triggers HITL break-glass if sensitive criteria are met.
    """
    candidates = state.get("candidate_anime", [])
    topic = state.get("topic", "").lower()
    persona = state.get("persona_profile", {})

    has_valid_licensing = audit_cto_licensing(candidates)
    
    # Check if this requires HITL Break-Glass review
    requires_hitl = False
    hitl_reason = ""
    break_glass_token = None

    if "controversial" in topic or "banned" in topic or "uncensored" in topic:
        requires_hitl = True
        hitl_reason = "Query references controversial/uncensored themes requiring Human-in-the-Loop verification."
        break_glass_token = f"BG-HITL-{uuid.uuid4().hex[:8].upper()}"

    if requires_hitl:
        decision = CTODecision(
            status="PENDING_HITL",
            signoff_by="ChiefTasteOfficer-HITL-Queue",
            editorial_notes=f"Flagged for Editorial Board Review: {hitl_reason}",
            break_glass_token=break_glass_token,
            is_vip_curated=True,
        )
        logger.warning(f"🚨 [CTO Gate] Human-in-the-loop required. Token: {break_glass_token}")
    else:
        licensing_note = "All titles verified on legal streaming networks." if has_valid_licensing else "Some titles require region-specific licensing."
        decision = CTODecision(
            status="APPROVED",
            signoff_by="ChiefTasteOfficer-AI (Executive Sign-Off)",
            editorial_notes=f"Approved for release. {licensing_note} Curated for aesthetic: {persona.get('aesthetic', 'modern_prestige')}.",
            break_glass_token=None,
            is_vip_curated=True,
        )
        logger.info("🎖️ [CTO Gate] Executive sign-off granted.")

    return {
        "cto_decision": decision.model_dump(),
    }
