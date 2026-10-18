"""
Document Database & Data Modeling Layer for MongoDB & Amazon DocumentDB.
"""

from src.database.document_store import (
    AnimeDoc,
    UserInteractionDoc,
    ResearchDossierDoc,
    SecurityAuditDoc,
    DocumentStore,
    get_document_store,
)

__all__ = [
    "AnimeDoc",
    "UserInteractionDoc",
    "ResearchDossierDoc",
    "SecurityAuditDoc",
    "DocumentStore",
    "get_document_store",
]
