"""
StateGraph Assembly for Industrial Deep Multi-Agent Mesh
Wires supervisor, safety, persona profiling, catalog discovery,
self-correcting reflection loop, CTO gate, and executive synthesizer.
"""
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.deep_agents.state import DeepAnimeAgentState
from app.deep_agents.supervisor import supervisor_planner_node, supervisor_synthesizer_node
from app.deep_agents.safety import safety_guardrail_node
from app.deep_agents.persona import persona_profiler_node
from app.deep_agents.discovery import catalog_discovery_node
from app.deep_agents.critic import quality_critic_node
from app.deep_agents.cto_gate import cto_gate_node

logger = logging.getLogger("DeepAgentGraph")


def route_after_safety(state: DeepAnimeAgentState) -> str:
    """If prompt injection or policy violation detected, short-circuit to synthesis."""
    audit = state.get("safety_audit", {})
    if not audit.get("is_safe", True):
        logger.warning("🚨 [Graph Routing] Unsafe input intercepted. Short-circuiting to terminal synthesizer.")
        return "supervisor_synthesizer"
    return "persona_profiler"


def route_after_critic(state: DeepAnimeAgentState) -> str:
    """
    Loop Engineering: Self-Reflective Correction Gateway.
    If the critic gave score < 75 and iteration_count < max_iterations,
    loops back to catalog_discovery with reformulated query.
    Otherwise, routes to the executive CTO Gate.
    """
    status = state.get("loop_status", "APPROVED")
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 2)

    if status == "NEEDS_REFINEMENT" and iteration < max_iter:
        logger.info(
            f"🔁 [Loop Engineering: Self-Correction] Critic requested refinement. "
            f"Looping back to catalog_discovery (Iteration {iteration}/{max_iter})."
        )
        return "catalog_discovery"

    logger.info("✅ [Loop Engineering] Reflection cycle satisfied. Routing to CTO Gate.")
    return "cto_gate"


def build_deep_agent_graph():
    """
    Constructs and compiles the production Deep Agent StateGraph with memory checkpointer.
    """
    workflow = StateGraph(DeepAnimeAgentState)

    # 1. Register Nodes
    workflow.add_node("supervisor_planner", supervisor_planner_node)
    workflow.add_node("safety_guardrail", safety_guardrail_node)
    workflow.add_node("persona_profiler", persona_profiler_node)
    workflow.add_node("catalog_discovery", catalog_discovery_node)
    workflow.add_node("quality_critic", quality_critic_node)
    workflow.add_node("cto_gate", cto_gate_node)
    workflow.add_node("supervisor_synthesizer", supervisor_synthesizer_node)

    # 2. Entry Point
    workflow.set_entry_point("supervisor_planner")
    workflow.add_edge("supervisor_planner", "safety_guardrail")

    # 3. Guardrail Short-Circuit
    workflow.add_conditional_edges(
        "safety_guardrail",
        route_after_safety,
        {
            "persona_profiler": "persona_profiler",
            "supervisor_synthesizer": "supervisor_synthesizer",
        },
    )

    workflow.add_edge("persona_profiler", "catalog_discovery")
    workflow.add_edge("catalog_discovery", "quality_critic")

    # 4. Loop Engineering Edge (Critic -> Self-Correction Loop -> CatalogDiscovery OR CTO Gate)
    workflow.add_conditional_edges(
        "quality_critic",
        route_after_critic,
        {
            "catalog_discovery": "catalog_discovery",  # Reflection Loopback
            "cto_gate": "cto_gate",                    # Approved progression
        },
    )

    workflow.add_edge("cto_gate", "supervisor_synthesizer")
    workflow.add_edge("supervisor_synthesizer", END)

    # 5. Checkpointer
    checkpointer = MemorySaver()
    compiled_mesh = workflow.compile(checkpointer=checkpointer)
    return compiled_mesh


# Pre-compiled singleton for high-concurrency access
deep_agent_mesh = build_deep_agent_graph()
