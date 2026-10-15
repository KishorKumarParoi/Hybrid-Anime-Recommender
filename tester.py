from pipeline.prediction_pipeline import hybrid_recommendation
from pipeline.ai_agent_pipeline import get_agent_recommendation

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 1. Testing Hybrid Recommender (User ID: 11880)")
    print("=" * 60)
    hybrid_recs = hybrid_recommendation(11880)
    print(hybrid_recs)

    print("\n" + "=" * 60)
    print("🤖 2. Testing AI Anime Agent (Semantic RAG)")
    print("=" * 60)
    test_query = "Dark psychological thriller with high stakes and clever mind games like Death Note"
    print(f"Query: {test_query}\n")
    agent_response = get_agent_recommendation(test_query)
    print(agent_response)
    print("=" * 60)