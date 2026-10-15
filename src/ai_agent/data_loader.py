import os
import pandas as pd
from src.logger import get_logger
from src.custom_exception import CustomException

logger = get_logger(__name__)


class AgentDataLoader:
    def __init__(self, original_csv: str, processed_csv: str, limit: int = 500):
        self.original_csv = original_csv
        self.processed_csv = processed_csv
        self.limit = limit

    def load_and_process(self) -> str:
        try:
            logger.info(f"Loading anime synopsis data from {self.original_csv}")
            frames = []

            # 1. Include curated iconic titles from ai-anime-recommender if present
            curated_path = "ai-anime-recommender/data/anime_with_synopsis.csv"
            if os.path.exists(curated_path):
                df_curated = pd.read_csv(
                    curated_path, encoding="utf-8", on_bad_lines="skip"
                )
                frames.append(df_curated)

            # 2. Include raw synopsis dataset
            if os.path.exists(self.original_csv):
                df_raw = pd.read_csv(
                    self.original_csv, encoding="utf-8", on_bad_lines="skip"
                )
                if "Score" in df_raw.columns:
                    df_raw["Score_num"] = pd.to_numeric(
                        df_raw["Score"], errors="coerce"
                    )
                    df_raw = df_raw.sort_values(by="Score_num", ascending=False)
                    if self.limit:
                        df_raw = df_raw.head(self.limit)
                    if "Score_num" in df_raw.columns:
                        df_raw = df_raw.drop(columns=["Score_num"])
                frames.append(df_raw)

            if not frames:
                raise FileNotFoundError(
                    f"Cannot find synopsis data at {self.original_csv} or {curated_path}"
                )

            df = pd.concat(frames, ignore_index=True)
            df = df.drop_duplicates(subset=["Name"]).dropna(
                subset=["Name", "Genres", "sypnopsis"]
            )

            score_str = (
                df["Score"].fillna("N/A").astype(str)
                if "Score" in df.columns
                else "N/A"
            )
            df["combined_info"] = (
                "Title: "
                + df["Name"].astype(str)
                + " | Score: "
                + score_str
                + " | Genres: "
                + df["Genres"].astype(str)
                + " | Overview: "
                + df["sypnopsis"].astype(str)
            )

            os.makedirs(os.path.dirname(self.processed_csv), exist_ok=True)
            df[["MAL_ID", "Name", "Score", "Genres", "combined_info"]].to_csv(
                self.processed_csv, index=False, encoding="utf-8"
            )
            logger.info(
                f"Successfully processed {len(df)} records into {self.processed_csv}"
            )
            return self.processed_csv
        except Exception as e:
            logger.error(f"Error in AgentDataLoader: {e}")
            raise CustomException(
                "Failed to load and process anime data for AI agent", e
            )
