"""
Catalog Discovery Agent (Hybrid RRF Search + Studio Lineage + Web Intelligence)
Synthesizes dense vector similarity, sparse lexical relevance, and franchise lineage.
"""
import os
import httpx
import logging
from typing import Dict, Any, List
from app.deep_agents.state import DeepAnimeAgentState, AnimeCandidate

logger = logging.getLogger("CatalogDiscovery")

# Curated reference database representing the core catalog + studio lineage
CATALOG_KNOWLEDGE_BASE = [
    {
        "title": "Cyberpunk: Edgerunners",
        "studio": "Studio Trigger",
        "score": 8.6,
        "genres": ["Sci-Fi", "Cyberpunk", "Action", "Psychological"],
        "streaming": ["Netflix"],
        "synopsis": "A street kid trying to survive in Night City becomes an edgerunner, an outlaw mercenary.",
        "lineage": "Studio Trigger (founded by ex-Gainax animators Hiroyuki Imaishi and Masahiko Otsuka)",
        "vibe": "Frenetic neon gore, hyper-stylized action, tragic emotional resonance.",
    },
    {
        "title": "Steins;Gate",
        "studio": "White Fox",
        "score": 9.1,
        "genres": ["Sci-Fi", "Psychological", "Thriller", "Drama"],
        "streaming": ["Crunchyroll", "Hulu"],
        "synopsis": "Self-proclaimed mad scientist Rintaro Okabe accidentally invents a microwave that sends text messages to the past.",
        "lineage": "White Fox (famed for Re:Zero, Katanagatari, and high-tension narrative pacing)",
        "vibe": "Slow-burn psychological mystery building into relentless thriller stakes.",
    },
    {
        "title": "Psycho-Pass",
        "studio": "Production I.G",
        "score": 8.3,
        "genres": ["Sci-Fi", "Action", "Psychological", "Police"],
        "streaming": ["Crunchyroll"],
        "synopsis": "In a 22nd-century authoritarian future, the Sibyl System measures the mental state of all citizens.",
        "lineage": "Production I.G (Ghost in the Shell heritage, authored by Gen Urobuchi)",
        "vibe": "Cerebral dystopian neo-noir debating utilitarian morality.",
    },
    {
        "title": "Ghost in the Shell: Stand Alone Complex",
        "studio": "Production I.G",
        "score": 8.5,
        "genres": ["Sci-Fi", "Mecha", "Police", "Psychological"],
        "streaming": ["Adult Swim", "Crunchyroll"],
        "synopsis": "Major Motoko Kusanagi and Public Security Section 9 investigate complex cyber-terror threats.",
        "lineage": "Production I.G / Kenji Kamiyama (peak philosophical transhumanism)",
        "vibe": "Deep political intrigue, philosophical meditations on consciousness.",
    },
    {
        "title": "Neon Genesis Evangelion",
        "studio": "Gainax",
        "score": 8.6,
        "genres": ["Psychological", "Drama", "Mecha", "Sci-Fi"],
        "streaming": ["Netflix"],
        "synopsis": "Teens pilot biomechanical mecha against monstrous Angels while grappling with existential dread.",
        "lineage": "Gainax / Hideaki Anno (the foundational benchmark of psychological anime)",
        "vibe": "Deconstructed mecha tropes, raw Freudian/Jungian psychoanalysis.",
    },
    {
        "title": "Monster",
        "studio": "Madhouse",
        "score": 8.9,
        "genres": ["Drama", "Mystery", "Psychological", "Suspense"],
        "streaming": ["Netflix"],
        "synopsis": "Dr. Kenzo Tenma saves the life of a young boy who grows up to be a charismatic psychopathic killer.",
        "lineage": "Madhouse (Golden age pedigree under Masao Maruyama, Naoki Urasawa adaptation)",
        "vibe": "Masterclass slow-burn European crime thriller.",
    },
    {
        "title": "Frieren: Beyond Journey's End",
        "studio": "Madhouse",
        "score": 9.3,
        "genres": ["Adventure", "Drama", "Fantasy"],
        "streaming": ["Crunchyroll"],
        "synopsis": "An elven mage ponders the passage of time and mortal connections after her hero party disbands.",
        "lineage": "Madhouse / Keiichiro Saito (Bocchi the Rock director, flawless sakuga animation)",
        "vibe": "Melancholic, deeply touching contemplation of mortality and quiet wonders.",
    },
    {
        "title": "Bocchi the Rock!",
        "studio": "CloverWorks",
        "score": 8.8,
        "genres": ["Comedy", "Music", "Slice of Life"],
        "streaming": ["Crunchyroll"],
        "synopsis": "An extremely introverted guitarist joins a high school rock band and confronts social anxiety.",
        "lineage": "CloverWorks (A-1 Pictures offshoot, creative visual direction)",
        "vibe": "Relatable comedic hyper-inventive animation depicting introversion.",
    },
]


def reciprocal_rank_fusion(
    dense_scores: Dict[str, float],
    sparse_scores: Dict[str, float],
    k: int = 60,
) -> List[Tuple_Title_Score := Any]:
    """
    RRF algorithm: score(d) = sum(1 / (k + rank_i(d)))
    Combines dense semantic vector rank with sparse keyword BM25 rank.
    """
    dense_ranked = sorted(dense_scores.items(), key=lambda x: x[1], reverse=True)
    sparse_ranked = sorted(sparse_scores.items(), key=lambda x: x[1], reverse=True)

    rrf_totals: Dict[str, float] = {}

    for rank, (title, _) in enumerate(dense_ranked, start=1):
        rrf_totals[title] = rrf_totals.get(title, 0.0) + (1.0 / (k + rank))

    for rank, (title, _) in enumerate(sparse_ranked, start=1):
        rrf_totals[title] = rrf_totals.get(title, 0.0) + (1.0 / (k + rank))

    return sorted(rrf_totals.items(), key=lambda x: x[1], reverse=True)


async def fetch_live_web_intelligence(query: str) -> List[str]:
    """Optional Tavily API query if configured, with graceful fallback."""
    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    if not tavily_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=6) as client:
            res = await client.post(
                "https://api.tavily.com/search",
                json={"api_key": tavily_key, "query": f"{query} anime studio reception details", "max_results": 2},
            )
            if res.status_code == 200:
                results = res.json().get("results", [])
                return [r.get("content", "") for r in results if r.get("content")]
    except Exception as e:
        logger.warning(f"Web discovery skipped: {e}")
    return []


async def catalog_discovery_node(state: DeepAnimeAgentState) -> Dict[str, Any]:
    """
    Executes hybrid retrieval across catalog knowledge and studio lineage graphs.
    """
    search_query = state.get("rewritten_query") or state.get("topic", "")
    persona = state.get("persona_profile", {})
    target_genres = set(persona.get("preferred_genres", []))
    target_tone = persona.get("target_tone", "balanced")

    dense_scores: Dict[str, float] = {}
    sparse_scores: Dict[str, float] = {}

    query_tokens = search_query.lower().split()

    for item in CATALOG_KNOWLEDGE_BASE:
        title = item["title"]
        item_text = (item["title"] + " " + item["synopsis"] + " " + " ".join(item["genres"]) + " " + item["vibe"]).lower()

        # Sparse scoring (lexical overlap)
        matches = sum(1 for token in query_tokens if token in item_text)
        sparse_scores[title] = float(matches)

        # Dense-like scoring (persona genre overlap + tone affinity)
        common_genres = len(target_genres.intersection(set(item["genres"])))
        dense_score = (common_genres * 2.0) + (item["score"] / 10.0)
        if target_tone == "dark_cerebral" and any(g in item["genres"] for g in ["Psychological", "Sci-Fi", "Horror"]):
            dense_score += 1.5
        elif target_tone == "lighthearted_comfort" and any(g in item["genres"] for g in ["Slice of Life", "Comedy"]):
            dense_score += 1.5
        dense_scores[title] = dense_score

    # Compute RRF Fusion
    ranked = reciprocal_rank_fusion(dense_scores, sparse_scores)

    # Select top 3 candidates
    candidates: List[Dict[str, Any]] = []
    lineage_entries: List[Dict[str, Any]] = []

    for title, rrf_score in ranked[:3]:
        item = next(x for x in CATALOG_KNOWLEDGE_BASE if x["title"] == title)
        cand = AnimeCandidate(
            title=item["title"],
            studio=item["studio"],
            score=item["score"],
            match_rate=min(0.98, max(0.75, 0.70 + (rrf_score * 15))),
            genres=item["genres"],
            synopsis=item["synopsis"],
            streaming_platforms=item["streaming"],
            vibe=item["vibe"],
            relevance_reason=f"Matches {persona.get('target_tone', 'balanced')} tone with high pedigree from {item['studio']}.",
        )
        candidates.append(cand.model_dump())
        lineage_entries.append({
            "title": item["title"],
            "studio": item["studio"],
            "lineage": item["lineage"],
        })

    # Optional live web snippets
    web_snippets = await fetch_live_web_intelligence(search_query)

    logger.info(f"🔍 [Catalog Discovery] Retrieved top {len(candidates)} candidates via Hybrid RRF.")
    return {
        "candidate_anime": candidates,
        "studio_lineage": lineage_entries,
        "search_results": [{"web_snippets": web_snippets}],
    }
