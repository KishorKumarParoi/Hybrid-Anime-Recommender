import os
from dotenv import load_dotenv
from config.paths_config import ANIMESYNOPSIS_CSV, AGENT_PROCESSED_DATA, CHROMA_DIR, AGENT_MODEL_NAME
from src.ai_agent.data_loader import AgentDataLoader
from src.ai_agent.vector_store import VectorStoreBuilder
from src.ai_agent.agent_recommender import AnimeAgentRecommender
from src.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

def build_ai_agent_pipeline(limit: int = 500, force_rebuild: bool = False) -> VectorStoreBuilder:
    vector_builder = VectorStoreBuilder(csv_path=AGENT_PROCESSED_DATA, persist_dir=CHROMA_DIR)

    if force_rebuild or not vector_builder.is_vector_store_built():
        logger.info("Chroma vector store not found or rebuild requested. Building knowledge base...")
        loader = AgentDataLoader(
            original_csv=ANIMESYNOPSIS_CSV,
            processed_csv=AGENT_PROCESSED_DATA,
            limit=limit
        )
        processed_csv = loader.load_and_process()
        vector_builder.csv_path = processed_csv
        vector_builder.build_and_save_vectorstore()
        logger.info("AI Agent knowledge base built successfully.")
    else:
        logger.info("Chroma vector store already exists. Ready to load.")

    return vector_builder

class AIAgentRecommendationPipeline:
    def __init__(self, persist_dir: str = CHROMA_DIR, api_key: str = None, model_name: str = AGENT_MODEL_NAME):
        self.persist_dir = persist_dir
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "").strip()
        self.model_name = model_name

        # Ensure vector store is available
        self.vector_builder = build_ai_agent_pipeline()
        self.retriever = self.vector_builder.get_retriever(k=4)
        self.agent = AnimeAgentRecommender(
            retriever=self.retriever,
            api_key=self.api_key,
            model_name=self.model_name
        )
        from src.ai_agent.research_agent import AutonomousAnimeResearchAgent
        self.research_agent = AutonomousAnimeResearchAgent(
            retriever=self.retriever,
            api_key=self.api_key,
            model_name=self.model_name
        )

    def recommend(self, query: str, user_api_key: str = None) -> str:
        return self.agent.get_recommendation(query, user_api_key=user_api_key)

    def research(self, topic_query: str, user_api_key: str = None) -> dict:
        return self.research_agent.research(topic_query, user_api_key=user_api_key)

_cached_agent_pipeline = None

def get_agent_recommendation(query: str, api_key: str = None) -> str:
    global _cached_agent_pipeline
    if _cached_agent_pipeline is None:
        _cached_agent_pipeline = AIAgentRecommendationPipeline()
    return _cached_agent_pipeline.recommend(query, user_api_key=api_key)

def get_research_dossier(query: str, api_key: str = None) -> dict:
    global _cached_agent_pipeline
    if _cached_agent_pipeline is None:
        _cached_agent_pipeline = AIAgentRecommendationPipeline()
    return _cached_agent_pipeline.research(query, user_api_key=api_key)

if __name__ == "__main__":
    sample_query = "cyberpunk anime with dark themes and great action"
    print(f"Testing AI Agent with query: '{sample_query}'...\n")
    response = get_agent_recommendation(sample_query)
    print(response)
