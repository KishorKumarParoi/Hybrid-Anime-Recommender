import sys
from pipeline.training_pipeline import run_training_pipeline
from pipeline.prediction_pipeline import hybrid_recommendation
from pipeline.ai_agent_pipeline import build_ai_agent_pipeline, get_agent_recommendation

def main():
    print("=" * 65)
    print("🚀 Hybrid Anime Recommender & AI Agent Platform (End-to-End)")
    print("=" * 65)

    # 1. Run full training pipeline for Collaborative + Content Hybrid
    print("\n[Step 1/4] Running Hybrid Training Pipeline (Ingestion -> Processing -> Training)...")
    run_training_pipeline()

    # 2. Test hybrid predictions
    test_user_id = 11880
    print(f"\n[Step 2/4] Testing Hybrid Recommendations for User ID: {test_user_id}...")
    recommendations = hybrid_recommendation(test_user_id)
    print(f"Top 10 Hybrid Recommendations for User {test_user_id}:")
    for idx, anime in enumerate(recommendations, 1):
        print(f"  {idx}. {anime}")

    # 3. Initialize AI Agent knowledge base & Chroma vector store
    print("\n[Step 3/4] Ensuring AI Agent Vector Store & Knowledge Base are ready...")
    build_ai_agent_pipeline()

    # 4. Test AI Agent recommendations
    test_query = "Mind games, psychological battles, and high stakes like Death Note"
    print(f"\n[Step 4/4] Testing AI Anime Agent with query: '{test_query}'...")
    agent_response = get_agent_recommendation(test_query)
    print("-" * 50)
    print(agent_response)
    print("-" * 50)

    # Success summary
    print("\n" + "=" * 65)
    print("🎉 All systems synced with uv and running end-to-end!")
    print("To launch the interactive Dual-Mode Web Application:")
    print("  uv run python application.py")
    print("=" * 65)

if __name__ == "__main__":
    main()
