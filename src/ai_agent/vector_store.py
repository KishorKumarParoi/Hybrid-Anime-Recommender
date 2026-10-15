import os
import pandas as pd
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from src.logger import get_logger
from src.custom_exception import CustomException

logger = get_logger(__name__)


class VectorStoreBuilder:
    def __init__(self, csv_path: str = "", persist_dir: str = "artifacts/chroma_db"):
        self.csv_path = csv_path
        self.persist_dir = persist_dir
        self.embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    def is_vector_store_built(self) -> bool:
        if os.path.exists(self.persist_dir):
            sqlite_path = os.path.join(self.persist_dir, "chroma.sqlite3")
            if os.path.exists(sqlite_path) and os.path.getsize(sqlite_path) > 0:
                return True
        return False

    def build_and_save_vectorstore(self) -> Chroma:
        try:
            logger.info(
                f"Building Chroma vector store from {self.csv_path} into {self.persist_dir}..."
            )
            df = pd.read_csv(self.csv_path, encoding="utf-8")

            texts = df["combined_info"].tolist()
            metadatas = [
                {
                    "mal_id": int(row["MAL_ID"]) if pd.notna(row.get("MAL_ID")) else 0,
                    "title": (
                        str(row["Name"]) if pd.notna(row.get("Name")) else "Unknown"
                    ),
                    "score": str(row["Score"]) if pd.notna(row.get("Score")) else "N/A",
                    "genres": str(row["Genres"]) if pd.notna(row.get("Genres")) else "",
                }
                for _, row in df.iterrows()
            ]

            os.makedirs(self.persist_dir, exist_ok=True)
            db = Chroma.from_texts(
                texts=texts,
                embedding=self.embedding,
                metadatas=metadatas,
                persist_directory=self.persist_dir,
            )
            logger.info("Chroma vector store built and persisted successfully.")
            return db
        except Exception as e:
            logger.error(f"Error building vector store: {e}")
            raise CustomException("Failed to build vector store", e)

    def load_vector_store(self) -> Chroma:
        try:
            if not self.is_vector_store_built() and self.csv_path:
                return self.build_and_save_vectorstore()
            return Chroma(
                persist_directory=self.persist_dir, embedding_function=self.embedding
            )
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            raise CustomException("Failed to load vector store", e)

    def get_retriever(self, k: int = 4):
        db = self.load_vector_store()
        return db.as_retriever(search_kwargs={"k": k})
