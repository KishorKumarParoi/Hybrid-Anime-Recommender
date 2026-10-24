"""
Persona Taste Profiler Agent
Extracts psychographic attributes, pacing preferences, aesthetic affinity, and genre weights.
"""
import logging
from typing import Dict, Any, List
from app.deep_agents.state import DeepAnimeAgentState, PersonaProfile

logger = logging.getLogger("PersonaProfiler")

GENRE_MAP = {
    "cyberpunk": ["Sci-Fi", "Cyberpunk", "Psychological", "Action"],
    "psychological": ["Psychological", "Mystery", "Thriller", "Drama"],
    "cerebral": ["Psychological", "Sci-Fi", "Mystery", "Drama"],
    "sci-fi": ["Sci-Fi", "Psychological", "Thriller", "Mystery"],
    "scifi": ["Sci-Fi", "Psychological", "Thriller"],
    "steins;gate": ["Sci-Fi", "Psychological", "Thriller", "Time Travel"],
    "dark": ["Psychological", "Dark Fantasy", "Horror", "Seinen"],
    "shonen": ["Action", "Adventure", "Shounen", "Supernatural"],
    "slice of life": ["Slice of Life", "Comedy", "Comfort", "Romance"],
    "relax": ["Slice of Life", "Iyashikei", "Comedy"],
    "mecha": ["Mecha", "Sci-Fi", "Military"],
    "mind bending": ["Psychological", "Mystery", "Sci-Fi", "Time Travel"],
    "retro": ["Classic", "90s Anime", "Neo-Noir", "Retro Sci-Fi"],
}


def infer_persona_from_text(topic: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    text = topic.lower()
    full_context = text + " " + " ".join([h.get("content", "").lower() for h in history[-3:]])

    # 1. Detect Tone
    if any(k in full_context for k in ["dark", "grim", "cyberpunk", "death", "psychological", "dystopian", "dystopia"]):
        tone = "dark_cerebral"
    elif any(k in full_context for k in ["chill", "relax", "slice of life", "wholesome", "calm", "funny", "laugh"]):
        tone = "lighthearted_comfort"
    elif any(k in full_context for k in ["hype", "battle", "epic", "tournament", "action", "shonen", "fight"]):
        tone = "epic_adrenaline"
    else:
        tone = "intellectual_narrative"

    # 2. Detect Pacing
    if any(k in full_context for k in ["fast", "action", "non-stop", "frenetic", "thrilling"]):
        pacing = "fast-paced"
    elif any(k in full_context for k in ["slow", "deep", "world building", "lore", "atmospheric", "philosophical"]):
        pacing = "slow-burn"
    else:
        pacing = "balanced"

    # 3. Detect Preferred Genres
    detected_genres = []
    for trigger, genres in GENRE_MAP.items():
        if trigger in full_context:
            detected_genres.extend(genres)
    if not detected_genres:
        detected_genres = ["Drama", "Action", "Mystery"]
    detected_genres = list(dict.fromkeys(detected_genres))[:5]

    # 4. Aesthetic
    if "cyberpunk" in full_context or "neo-tokyo" in full_context:
        aesthetic = "neon_cyberpunk"
    elif "90s" in full_context or "retro" in full_context:
        aesthetic = "vintage_cel_retro"
    elif "cinematic" in full_context or "movie" in full_context:
        aesthetic = "high_fidelity_cinematic"
    else:
        aesthetic = "modern_prestige"

    profile = PersonaProfile(
        target_tone=tone,
        pacing_preference=pacing,
        preferred_genres=detected_genres,
        aesthetic=aesthetic,
        content_rating_ok="R-17+" if "dark" in tone else "PG-13",
        sentiment="discerning_enthusiast",
    )
    return profile.model_dump()


async def persona_profiler_node(state: DeepAnimeAgentState) -> Dict[str, Any]:
    """
    Synthesizes conversational history and current intent into an affinity vector.
    """
    topic = state.get("topic", "")
    history = state.get("session_history", [])

    profile = infer_persona_from_text(topic, history)
    logger.info(f"🧬 [Persona Profiler] Synthesized affinity: Tone={profile['target_tone']}, Aesthetic={profile['aesthetic']}")

    return {"persona_profile": profile}
