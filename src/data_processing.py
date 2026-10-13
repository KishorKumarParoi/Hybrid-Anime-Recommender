import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Optional, List, Tuple, Dict, Any
from src.logger import get_logger
from src.custom_exception import CustomException
from config.paths_config import *

logger = get_logger(__name__)


class DataProcessor:
    """
    Production-ready Data Processor for the Hybrid Anime Recommender System.
    Handles data loading, filtering, min-max scaling, index encoding,
    train-test splitting, and metadata preparation for collaborative & content engines.
    """

    def __init__(
        self,
        input_file: str = ANIMELIST_CSV,
        output_dir: str = PROCESSED_DIR,
        max_rows: Optional[int] = 2_000_000,
        min_user_ratings: int = 50,
        min_anime_ratings: int = 5,
        test_size: float = 0.1,
        random_state: int = 42,
    ):
        self.input_file = input_file
        self.output_dir = output_dir
        self.max_rows = max_rows
        self.min_user_ratings = min_user_ratings
        self.min_anime_ratings = min_anime_ratings
        self.test_size = test_size
        self.random_state = random_state

        self.rating_df: Optional[pd.DataFrame] = None
        self.X_train_array: Optional[List[np.ndarray]] = None
        self.X_test_array: Optional[List[np.ndarray]] = None
        self.y_train: Optional[pd.Series] = None
        self.y_test: Optional[pd.Series] = None

        self.user2user_encoded: Dict[int, int] = {}
        self.user2user_decoded: Dict[int, int] = {}
        self.anime2anime_encoded: Dict[int, int] = {}
        self.anime2anime_decoded: Dict[int, int] = {}

        self.scaler_meta: Dict[str, float] = {}
        self.summary_stats: Dict[str, Any] = {}

        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(
            f"DataProcessor Initialized (output_dir: {self.output_dir}, max_rows: {self.max_rows})"
        )

    def _resolve_input_file(self) -> str:
        """Resolves the best available ratings file between animelist.csv and rating_complete.csv."""
        if os.path.exists(self.input_file) and os.path.getsize(self.input_file) > 0:
            return self.input_file

        # Fallback to rating_complete.csv if animelist is missing
        if os.path.exists(RATING_CSV) and os.path.getsize(RATING_CSV) > 0:
            logger.info(
                f"Input file '{self.input_file}' not found. Using fallback: {RATING_CSV}"
            )
            return RATING_CSV

        # Fallback to animelist.csv if default was something else
        if os.path.exists(ANIMELIST_CSV) and os.path.getsize(ANIMELIST_CSV) > 0:
            logger.info(f"Using standard ratings file: {ANIMELIST_CSV}")
            return ANIMELIST_CSV

        raise FileNotFoundError(
            f"No valid ratings file found at '{self.input_file}', '{RATING_CSV}', or '{ANIMELIST_CSV}'."
        )

    def load_data(self, usecols: Optional[List[str]] = None):
        """Loads ratings dataset with memory-efficient dtypes and optional row limits."""
        try:
            resolved_path = self._resolve_input_file()
            self.input_file = resolved_path

            if usecols is None:
                usecols = ["user_id", "anime_id", "rating"]

            dtypes = {"user_id": np.int32, "anime_id": np.int32, "rating": np.float32}

            logger.info(
                f"Loading data from {resolved_path} (max_rows={self.max_rows})..."
            )
            self.rating_df = pd.read_csv(
                resolved_path,
                usecols=usecols,
                dtype=dtypes,
                nrows=self.max_rows,
                low_memory=False,
            )

            initial_count = len(self.rating_df)
            logger.info(f"Raw ratings loaded: {initial_count:,} records.")

            # Filter out unrated entries (rating == 0 or rating == -1 indicates no score in MyAnimeList)
            self.rating_df = self.rating_df[self.rating_df["rating"] > 0].copy()
            filtered_count = len(self.rating_df)
            logger.info(
                f"Retained {filtered_count:,} active ratings (removed {initial_count - filtered_count:,} unrated entries)."
            )

        except Exception as e:
            logger.error(f"Error loading rating data: {e}")
            raise CustomException("Failed to load rating data", e)

    def filter_users_and_anime(self):
        """
        Filters out low-activity users and infrequent anime to ensure
        dense, high-quality interaction matrices for embedding learning.
        """
        try:
            if self.rating_df is None or self.rating_df.empty:
                raise ValueError("rating_df is empty. Cannot perform filtering.")

            # 1. Filter Users
            user_counts = self.rating_df["user_id"].value_counts()
            active_users = user_counts[user_counts >= self.min_user_ratings].index

            if len(active_users) < 10:
                # Dynamically adapt threshold if dataset is a small development sample
                adaptive_user_threshold = max(2, int(user_counts.quantile(0.4)))
                logger.warning(
                    f"Fewer than 10 users had >= {self.min_user_ratings} ratings. "
                    f"Adapting user threshold to >= {adaptive_user_threshold}."
                )
                active_users = user_counts[user_counts >= adaptive_user_threshold].index

            self.rating_df = self.rating_df[
                self.rating_df["user_id"].isin(active_users)
            ].copy()

            # 2. Filter Anime (removes single-interaction noise)
            anime_counts = self.rating_df["anime_id"].value_counts()
            active_anime = anime_counts[anime_counts >= self.min_anime_ratings].index

            if len(active_anime) < 10:
                adaptive_anime_threshold = max(1, int(anime_counts.quantile(0.2)))
                logger.warning(
                    f"Fewer than 10 anime had >= {self.min_anime_ratings} ratings. "
                    f"Adapting anime threshold to >= {adaptive_anime_threshold}."
                )
                active_anime = anime_counts[
                    anime_counts >= adaptive_anime_threshold
                ].index

            self.rating_df = self.rating_df[
                self.rating_df["anime_id"].isin(active_anime)
            ].copy()

            logger.info(
                f"Filtering completed. Remaining: {len(self.rating_df):,} ratings, "
                f"{self.rating_df['user_id'].nunique():,} unique users, "
                f"{self.rating_df['anime_id'].nunique():,} unique anime."
            )
        except Exception as e:
            logger.error(f"Error filtering users and anime: {e}")
            raise CustomException("Failed to filter users and anime", e)

    def scale_ratings(self):
        """Normalizes ratings to [0, 1] using Min-Max scaling and persists scaling parameters."""
        try:
            min_r = float(self.rating_df["rating"].min())
            max_r = float(self.rating_df["rating"].max())
            denom = (max_r - min_r) if max_r != min_r else 1.0

            self.scaler_meta = {
                "min_rating": min_r,
                "max_rating": max_r,
                "denominator": denom,
            }

            self.rating_df["rating"] = (
                (self.rating_df["rating"] - min_r) / denom
            ).astype(np.float32)
            logger.info(
                f"Normalized ratings to [0, 1] range (min: {min_r}, max: {max_r})."
            )
        except Exception as e:
            logger.error(f"Error scaling ratings: {e}")
            raise CustomException("Failed to scale ratings", e)

    def encode_data(self):
        """Creates bijective dense integer mappings (0 to N-1) for User and Anime IDs."""
        try:
            # Users
            unique_users = sorted(self.rating_df["user_id"].unique().tolist())
            self.user2user_encoded = {
                raw_id: idx for idx, raw_id in enumerate(unique_users)
            }
            self.user2user_decoded = {
                idx: raw_id for idx, raw_id in enumerate(unique_users)
            }
            self.rating_df["user"] = (
                self.rating_df["user_id"].map(self.user2user_encoded).astype(np.int32)
            )

            # Anime
            unique_anime = sorted(self.rating_df["anime_id"].unique().tolist())
            self.anime2anime_encoded = {
                raw_id: idx for idx, raw_id in enumerate(unique_anime)
            }
            self.anime2anime_decoded = {
                idx: raw_id for idx, raw_id in enumerate(unique_anime)
            }
            self.rating_df["anime"] = (
                self.rating_df["anime_id"]
                .map(self.anime2anime_encoded)
                .astype(np.int32)
            )

            logger.info(
                f"Bijective encoding complete. Encoded {len(self.user2user_encoded):,} users "
                f"and {len(self.anime2anime_encoded):,} anime."
            )
        except Exception as e:
            logger.error(f"Error encoding user and anime IDs: {e}")
            raise CustomException("Failed to encode IDs", e)

    def split_data(self):
        """Shuffles and splits data into train and test sets using ratio or absolute count."""
        try:
            # Deterministic shuffle
            self.rating_df = self.rating_df.sample(
                frac=1.0, random_state=self.random_state
            ).reset_index(drop=True)
            total_samples = len(self.rating_df)

            # Determine test set size
            if isinstance(self.test_size, float) and 0.0 < self.test_size < 1.0:
                num_test = int(total_samples * self.test_size)
            else:
                num_test = int(self.test_size)

            # Safe boundary check
            num_test = max(1, min(num_test, int(total_samples * 0.5)))
            train_cutoff = total_samples - num_test

            X = self.rating_df[["user", "anime"]].values
            y = self.rating_df["rating"]

            X_train = X[:train_cutoff]
            X_test = X[train_cutoff:]
            y_train = y[:train_cutoff]
            y_test = y[train_cutoff:]

            self.X_train_array = [X_train[:, 0], X_train[:, 1]]
            self.X_test_array = [X_test[:, 0], X_test[:, 1]]
            self.y_train = y_train
            self.y_test = y_test

            logger.info(
                f"Data split successfully. Train samples: {len(y_train):,} ({len(y_train)/total_samples:.1%}), "
                f"Test samples: {len(y_test):,} ({len(y_test)/total_samples:.1%})."
            )
        except Exception as e:
            logger.error(f"Error splitting data: {e}")
            raise CustomException("Failed to split data", e)

    def save_artifacts(self):
        """Persists all processed arrays, dictionaries, scaler parameters, and metadata."""
        try:
            # 1. Encoders and Decoders
            mapping_artifacts = {
                "user2user_encoded": self.user2user_encoded,
                "user2user_decoded": self.user2user_decoded,
                "anim2anime_encoded": self.anime2anime_encoded,
                "anim2anime_decoded": self.anime2anime_decoded,
                "rating_scaler": self.scaler_meta,
            }

            for name, data in mapping_artifacts.items():
                target_path = os.path.join(self.output_dir, f"{name}.pkl")
                joblib.dump(data, target_path)

            # 2. Train and Test Arrays
            joblib.dump(self.X_train_array, X_TRAIN_ARRAY)
            joblib.dump(self.X_test_array, X_TEST_ARRAY)
            joblib.dump(self.y_train, Y_TRAIN)
            joblib.dump(self.y_test, Y_TEST)

            # 3. Processed Rating DataFrame
            self.rating_df.to_csv(RATING_DF, index=False)

            # 4. Generate Summary Statistics
            n_users = len(self.user2user_encoded)
            n_anime = len(self.anime2anime_encoded)
            n_ratings = len(self.rating_df)
            total_possible = max(1, n_users * n_anime)
            sparsity = 1.0 - (n_ratings / total_possible)

            self.summary_stats = {
                "num_ratings": n_ratings,
                "num_unique_users": n_users,
                "num_unique_anime": n_anime,
                "matrix_sparsity_percent": round(sparsity * 100, 3),
                "rating_min_original": self.scaler_meta.get("min_rating"),
                "rating_max_original": self.scaler_meta.get("max_rating"),
                "train_samples": len(self.y_train),
                "test_samples": len(self.y_test),
            }

            summary_path = os.path.join(self.output_dir, "dataset_summary.json")
            with open(summary_path, "w") as f:
                json.dump(self.summary_stats, f, indent=2)

            logger.info(
                f"All processed artifacts saved successfully to {self.output_dir}."
            )
            logger.info(f"Dataset summary: {self.summary_stats}")
        except Exception as e:
            logger.error(f"Error saving processed artifacts: {e}")
            raise CustomException("Failed to save artifacts", e)

    def process_anime_data(self):
        """
        Cleans and formats catalog anime metadata and synopses
        for downstream content-based filtering and RAG vector indexing.
        """
        try:
            if not os.path.exists(ANIME_CSV):
                raise FileNotFoundError(f"Catalog file {ANIME_CSV} not found.")

            df = pd.read_csv(ANIME_CSV)

            # Clean and standardize columns
            df = df.replace("Unknown", np.nan)
            df["anime_id"] = (
                pd.to_numeric(df["MAL_ID"], errors="coerce").fillna(0).astype(int)
            )
            df["eng_version"] = df["English name"].fillna(df["Name"]).astype(str)
            df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
            df["Members"] = (
                pd.to_numeric(df["Members"], errors="coerce").fillna(0).astype(int)
            )
            df["Genres"] = df["Genres"].fillna("Anime").astype(str)

            # Sort catalog by Score descending
            df.sort_values(
                by=["Score"],
                inplace=True,
                ascending=False,
                kind="quicksort",
                na_position="last",
            )
            df_cleaned = df[
                [
                    "anime_id",
                    "eng_version",
                    "Score",
                    "Genres",
                    "Episodes",
                    "Type",
                    "Premiered",
                    "Members",
                ]
            ]
            df_cleaned.to_csv(DF, index=False)

            # Process Synopses
            if os.path.exists(ANIMESYNOPSIS_CSV):
                cols = ["MAL_ID", "Name", "Genres"]
                sample_syn = pd.read_csv(ANIMESYNOPSIS_CSV, nrows=1)
                syn_col = (
                    "sypnopsis" if "sypnopsis" in sample_syn.columns else "synopsis"
                )
                cols.append(syn_col)

                synopsis_df = pd.read_csv(ANIMESYNOPSIS_CSV, usecols=cols)
                if syn_col != "sypnopsis":
                    synopsis_df.rename(columns={syn_col: "sypnopsis"}, inplace=True)
                synopsis_df.to_csv(SYNOPSIS_DF, index=False)
            else:
                logger.warning(
                    f"{ANIMESYNOPSIS_CSV} not found. Creating fallback synopsis file."
                )
                fallback_synopsis = pd.DataFrame(
                    {
                        "MAL_ID": df_cleaned["anime_id"],
                        "Name": df_cleaned["eng_version"],
                        "Genres": df_cleaned["Genres"],
                        "sypnopsis": "No synopsis available.",
                    }
                )
                fallback_synopsis.to_csv(SYNOPSIS_DF, index=False)

            logger.info(
                f"Cleaned anime metadata ({DF}) and synopses ({SYNOPSIS_DF}) saved successfully."
            )
        except Exception as e:
            logger.error(f"Error processing anime catalog: {e}")
            raise CustomException("Failed to process anime catalog", e)

    def run(self):
        """Executes the full end-to-end data processing workflow."""
        try:
            logger.info("Starting Data Processing Pipeline...")
            self.load_data()
            self.filter_users_and_anime()
            self.scale_ratings()
            self.encode_data()
            self.split_data()
            self.save_artifacts()
            self.process_anime_data()
            logger.info("Data Processing Pipeline completed successfully!")
        except CustomException as e:
            logger.error(f"Data Processing Pipeline encountered an error: {e}")
            raise e


if __name__ == "__main__":
    data_processor = DataProcessor(
        input_file=ANIMELIST_CSV,
        output_dir=PROCESSED_DIR,
        max_rows=2_000_000,
        min_user_ratings=50,
        min_anime_ratings=5,
        test_size=0.1,
    )
    data_processor.run()
