"""
Enterprise MongoDB & Amazon DocumentDB Modeling and Repository
=============================================================
Provides asynchronous and synchronous data modeling, index creation,
and document lifecycle management for:
  1. Anime Metadata & Catalog (collection: animes)
  2. Real-Time User Interactions & History (collection: user_interactions)
  3. Multi-Agent LangGraph Research Dossiers (collection: research_dossiers)
  4. PyRIT Red-Teaming & AI Security Audits (collection: security_audits)

Supports:
  - Amazon DocumentDB (MongoDB 4.0/5.0 API compatible over TLS)
  - MongoDB Atlas or Self-Hosted Replica Sets
  - In-memory resilient fallback repository when database is offline
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("DocumentStore")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


# ─── Pydantic Document Models ────────────────────────────────────────────────

class AnimeDoc(BaseModel):
    """Catalog document representing an anime title with genres and metadata."""
    anime_id: str = Field(..., description="Unique anime ID matching recommendation weights")
    title: str = Field(..., description="Canonical anime title")
    genres: List[str] = Field(default_factory=list, description="Categorical genres")
    type: str = Field(default="TV", description="Media format (TV, Movie, OVA, ONA)")
    episodes: Optional[int] = Field(default=None, description="Total episode count")
    rating: float = Field(default=0.0, ge=0.0, le=10.0, description="Community average score")
    synopsis: str = Field(default="", description="Plot synopsis for semantic search")
    tags: List[str] = Field(default_factory=list, description="Semantic tags / themes")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserInteractionDoc(BaseModel):
    """Document tracking user behavioral actions, ratings, and clicks."""
    interaction_id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:12]}")
    user_id: str = Field(..., description="User unique identifier")
    anime_id: str = Field(..., description="Anime unique identifier")
    rating: float = Field(default=0.0, ge=0.0, le=10.0)
    interaction_type: str = Field(default="rating", description="rating, bookmark, click, complete")
    session_id: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResearchDossierDoc(BaseModel):
    """Document storing autonomous multi-agent research outputs and evaluation scores."""
    dossier_id: str = Field(default_factory=lambda: f"dos_{uuid.uuid4().hex[:12]}")
    topic: str = Field(..., description="Research query or theme")
    session_id: str = Field(default="default-session")
    report: str = Field(..., description="Synthesized multi-page markdown dossier")
    iterations: int = Field(default=1, description="LangGraph reflection cycle count")
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="LLM-as-Judge rating")
    citations: List[str] = Field(default_factory=list)
    eval_metrics: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SecurityAuditDoc(BaseModel):
    """Document recording adversarial red-team attacks and guardrail blocks."""
    audit_id: str = Field(default_factory=lambda: f"sec_{uuid.uuid4().hex[:12]}")
    event_type: str = Field(..., description="pyrit_jailbreak, prompt_injection, pii_leak")
    prompt_snippet: str = Field(default="")
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    blocked: bool = Field(default=False)
    mitigation: str = Field(default="")
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─── Document Store Repository ────────────────────────────────────────────────

class DocumentStore:
    """
    Asynchronous Document Store for MongoDB / Amazon DocumentDB
    with resilient in-memory fallback.
    """

    def __init__(self, uri: Optional[str] = None, database_name: str = "animeresearchdb"):
        self.uri = uri or os.getenv("MONGODB_URI") or os.getenv("DOCUMENTDB_URI", "mongodb://localhost:27017")
        self.database_name = database_name
        self._client = None
        self._db = None
        self._is_online = False
        self._init_attempted = False

        # Resilient In-Memory Collections (Fallback when DocumentDB is unreachable)
        self._in_memory: Dict[str, Dict[str, Dict[str, Any]]] = {
            "animes": {},
            "user_interactions": {},
            "research_dossiers": {},
            "security_audits": {},
        }

    async def connect(self) -> bool:
        """Connect to MongoDB / DocumentDB and establish required indexes."""
        if self._is_online and self._db is not None:
            return True

        try:
            from motor.motor_asyncio import AsyncIOMotorClient

            self._client = AsyncIOMotorClient(
                self.uri,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
            )
            # Ping database to confirm connectivity
            await self._client.admin.command("ping")
            self._db = self._client[self.database_name]
            self._is_online = True
            logger.info(f"Connected to Document Database at {self.database_name}")

            # Create Indexes
            await self._ensure_indexes()
            return True
        except Exception as exc:
            self._is_online = False
            self._db = None
            logger.warning(
                f"DocumentDB/MongoDB offline ({exc}). Operating in resilient in-memory mode."
            )
            return False
        finally:
            self._init_attempted = True

    async def _ensure_indexes(self):
        """Create standard indexes across collections for high-performance querying."""
        if not self._is_online or self._db is None:
            return

        try:
            # 1. Anime catalog indexes
            await self._db.animes.create_index("anime_id", unique=True)
            await self._db.animes.create_index([("title", "text"), ("synopsis", "text")])

            # 2. User interactions indexes
            await self._db.user_interactions.create_index([("user_id", 1), ("timestamp", -1)])
            await self._db.user_interactions.create_index("anime_id")

            # 3. Research dossiers indexes
            await self._db.research_dossiers.create_index("dossier_id", unique=True)
            await self._db.research_dossiers.create_index([("session_id", 1), ("created_at", -1)])

            # 4. Security audits indexes
            await self._db.security_audits.create_index([("event_type", 1), ("timestamp", -1)])
        except Exception as e:
            logger.debug(f"Index creation note: {e}")

    # ─── CRUD Operations: Anime Metadata ─────────────────────────────────────

    async def upsert_anime(self, anime: AnimeDoc) -> Dict[str, Any]:
        """Insert or update an anime metadata document."""
        if not self._init_attempted:
            await self.connect()

        doc_dict = anime.model_dump()
        doc_dict["updated_at"] = datetime.now(timezone.utc)

        if self._is_online and self._db is not None:
            try:
                await self._db.animes.update_one(
                    {"anime_id": anime.anime_id},
                    {"$set": doc_dict},
                    upsert=True
                )
                return doc_dict
            except Exception as e:
                logger.warning(f"Error upserting anime doc: {e}. Falling back to memory.")

        self._in_memory["animes"][anime.anime_id] = doc_dict
        return doc_dict

    async def get_anime(self, anime_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an anime document by ID."""
        if not self._init_attempted:
            await self.connect()

        if self._is_online and self._db is not None:
            try:
                res = await self._db.animes.find_one({"anime_id": str(anime_id)}, {"_id": 0})
                if res:
                    return res
            except Exception:
                pass

        return self._in_memory["animes"].get(str(anime_id))

    # ─── CRUD Operations: User Interactions ──────────────────────────────────

    async def record_interaction(self, interaction: UserInteractionDoc) -> Dict[str, Any]:
        """Record a real-time interaction into DocumentDB."""
        if not self._init_attempted:
            await self.connect()

        doc_dict = interaction.model_dump()

        if self._is_online and self._db is not None:
            try:
                await self._db.user_interactions.insert_one(doc_dict)
                doc_dict.pop("_id", None)
                return doc_dict
            except Exception as e:
                logger.warning(f"Error saving interaction: {e}. Fallback to memory.")

        self._in_memory["user_interactions"][interaction.interaction_id] = doc_dict
        return doc_dict

    async def get_user_interactions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch chronological interaction history for a given user."""
        if not self._init_attempted:
            await self.connect()

        if self._is_online and self._db is not None:
            try:
                cursor = self._db.user_interactions.find(
                    {"user_id": str(user_id)}, {"_id": 0}
                ).sort("timestamp", -1).limit(limit)
                return await cursor.to_list(length=limit)
            except Exception:
                pass

        user_matches = [
            doc for doc in self._in_memory["user_interactions"].values()
            if doc.get("user_id") == str(user_id)
        ]
        user_matches.sort(key=lambda x: str(x.get("timestamp")), reverse=True)
        return user_matches[:limit]

    # ─── CRUD Operations: Research Dossiers ──────────────────────────────────

    async def save_dossier(self, dossier: ResearchDossierDoc) -> Dict[str, Any]:
        """Save a synthesized LangGraph multi-agent research dossier."""
        if not self._init_attempted:
            await self.connect()

        doc_dict = dossier.model_dump()

        if self._is_online and self._db is not None:
            try:
                await self._db.research_dossiers.update_one(
                    {"dossier_id": dossier.dossier_id},
                    {"$set": doc_dict},
                    upsert=True
                )
                return doc_dict
            except Exception as e:
                logger.warning(f"Error saving dossier: {e}. Fallback to memory.")

        self._in_memory["research_dossiers"][dossier.dossier_id] = doc_dict
        return doc_dict

    async def get_dossier(self, dossier_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific research dossier by ID."""
        if not self._init_attempted:
            await self.connect()

        if self._is_online and self._db is not None:
            try:
                res = await self._db.research_dossiers.find_one({"dossier_id": dossier_id}, {"_id": 0})
                if res:
                    return res
            except Exception:
                pass

        return self._in_memory["research_dossiers"].get(dossier_id)

    # ─── CRUD Operations: Security Audits ────────────────────────────────────

    async def record_security_audit(self, audit: SecurityAuditDoc) -> Dict[str, Any]:
        """Store a PyRIT adversarial probe or guardrail audit event."""
        if not self._init_attempted:
            await self.connect()

        doc_dict = audit.model_dump()

        if self._is_online and self._db is not None:
            try:
                await self._db.security_audits.insert_one(doc_dict)
                doc_dict.pop("_id", None)
                return doc_dict
            except Exception as e:
                logger.warning(f"Error logging security audit: {e}. Fallback to memory.")

        self._in_memory["security_audits"][audit.audit_id] = doc_dict
        return doc_dict

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic health and metrics for DocumentDB/MongoDB."""
        return {
            "online": self._is_online,
            "database_name": self.database_name,
            "counts": {
                "animes": len(self._in_memory["animes"]),
                "user_interactions": len(self._in_memory["user_interactions"]),
                "research_dossiers": len(self._in_memory["research_dossiers"]),
                "security_audits": len(self._in_memory["security_audits"]),
            }
        }


# Singleton document store instance
_global_doc_store: Optional[DocumentStore] = None


def get_document_store() -> DocumentStore:
    """Get or initialize singleton DocumentStore instance."""
    global _global_doc_store
    if _global_doc_store is None:
        _global_doc_store = DocumentStore()
    return _global_doc_store
