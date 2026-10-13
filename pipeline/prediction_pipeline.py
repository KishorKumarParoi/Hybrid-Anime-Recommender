from config.paths_config import *
from utils.helpers import *

def hybrid_recommendation(user_id, user_weight=0.5, content_weight=0.5):
    try:
        ## 1. User Recommendation (Collaborative Filtering)
        similar_users = find_similar_users(user_id, USER_WEIGHTS_PATH, USER2USER_ENCODED, USER2USER_DECODED)
        user_pref = get_user_preferences(user_id, RATING_DF, DF)
        user_recommended_animes = get_user_recommendations(similar_users, user_pref, DF, SYNOPSIS_DF, RATING_DF)

        user_recommended_anime_list = (
            user_recommended_animes["anime_name"].tolist()
            if user_recommended_animes is not None and not user_recommended_animes.empty and "anime_name" in user_recommended_animes.columns
            else []
        )

        ## 2. Content Recommendation
        content_recommended_animes = []
        source_animes = user_recommended_anime_list
        if not source_animes and user_pref is not None and not user_pref.empty and "eng_version" in user_pref.columns:
            source_animes = user_pref["eng_version"].head(5).tolist()

        for anime in source_animes:
            similar_animes = find_similar_animes(anime, ANIME_WEIGHTS_PATH, ANIME2ANIME_ENCODED, ANIME2ANIME_DECODED, DF)
            if similar_animes is not None and not similar_animes.empty and "name" in similar_animes.columns:
                content_recommended_animes.extend(similar_animes["name"].tolist())

        ## 3. Score Combination
        combined_scores = {}
        for anime in user_recommended_anime_list:
            combined_scores[anime] = combined_scores.get(anime, 0) + user_weight

        for anime in content_recommended_animes:
            combined_scores[anime] = combined_scores.get(anime, 0) + content_weight

        # 4. Fallback for cold-start / unknown user with no overlapping items
        if not combined_scores:
            df = pd.read_csv(DF)
            top_animes = df.sort_values(by="Score", ascending=False)["eng_version"].dropna().head(10).tolist()
            return top_animes

        sorted_animes = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        return [anime for anime, score in sorted_animes[:10]]
    except Exception as e:
        print(f"Error in hybrid_recommendation: {e}")
        df = pd.read_csv(DF)
        return df.sort_values(by="Score", ascending=False)["eng_version"].dropna().head(10).tolist()

