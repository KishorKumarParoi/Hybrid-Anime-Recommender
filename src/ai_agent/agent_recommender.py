import os
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from src.ai_agent.prompt_template import get_anime_prompt
from src.logger import get_logger

logger = get_logger(__name__)


class AnimeAgentRecommender:
    def __init__(
        self, retriever, api_key: str = None, model_name: str = "llama-3.1-8b-instant"
    ):
        self.retriever = retriever
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "").strip()
        self.model_name = model_name
        self.prompt = get_anime_prompt()

    def get_recommendation(self, query: str, user_api_key: str = None) -> str:
        active_key = user_api_key.strip() if user_api_key else self.api_key

        if active_key:
            try:
                from langchain_groq import ChatGroq

                logger.info(
                    f"Invoking Groq LLM ({self.model_name}) for query: '{query}'"
                )
                llm = ChatGroq(
                    api_key=active_key, model=self.model_name, temperature=0.2
                )

                rag_chain = (
                    {"context": self.retriever, "question": RunnablePassthrough()}
                    | self.prompt
                    | llm
                    | StrOutputParser()
                )
                return rag_chain.invoke(query)
            except Exception as e:
                logger.warning(
                    f"Groq LLM call failed ({e}). Falling back to semantic vector response."
                )

        # Fallback to intelligent semantic retrieval synthesis if no API key is available or LLM fails
        return self._semantic_fallback_recommendation(query)

    def _semantic_fallback_recommendation(self, query: str) -> str:
        logger.info(
            f"Synthesizing semantic retrieval recommendation for query: '{query}'"
        )
        try:
            docs = self.retriever.invoke(query)
            if not docs:
                return "I couldn't find any anime closely matching that description in our database. Try another genre or theme!"

            # Deduplicate by title
            seen_titles = set()
            unique_docs = []
            for doc in docs:
                t = (doc.metadata or {}).get("title", "")
                if t and t not in seen_titles:
                    seen_titles.add(t)
                    unique_docs.append(doc)
                elif not t:
                    unique_docs.append(doc)

            response_lines = [
                f"### 🤖 AI Anime Agent Recommendations\n",
                f'*Synthesized from semantic similarity matching for your query: "{query}"*\n',
            ]

            for i, doc in enumerate(unique_docs[:4], 1):
                meta = doc.metadata or {}
                title = meta.get("title", "Unknown Title")
                score = meta.get("score", "N/A")
                genres = meta.get("genres", "Anime")

                # Extract overview from content if available
                content = doc.page_content
                overview = "Exciting anime experience."
                if "| Overview: " in content:
                    overview = content.split("| Overview: ")[-1].strip()
                elif "Overview: " in content:
                    overview = content.split("Overview: ")[-1].strip()

                if len(overview) > 280:
                    overview = overview[:280] + "..."

                response_lines.append(f"{i}. **{title}** (Score: {score} ⭐)")
                response_lines.append(f"   - **Genres:** {genres}")
                response_lines.append(f"   - **Plot Summary:** {overview}")
                response_lines.append(
                    f"   - **Why You Will Love It:** Strong thematic and stylistic match for '{query}'.\n"
                )

            response_lines.append(
                "> 💡 *Tip: Provide a `GROQ_API_KEY` (in `.env` or in the UI) to unlock full conversational LLM reasoning powered by Llama 3.1!*"
            )
            return "\n".join(response_lines)
        except Exception as e:
            logger.error(f"Error in semantic fallback recommendation: {e}")
            return f"Error retrieving recommendations for '{query}'. Please check your query and try again."
