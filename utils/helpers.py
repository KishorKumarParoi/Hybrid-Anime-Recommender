import pandas as pd
import numpy as np
import joblib
from config.paths_config import *

############# 1. GET_ANIME_FRAME

def getAnimeFrame(anime, path_df):
    df = pd.read_csv(path_df)
    if isinstance(anime, (int, np.integer)):
        return df[df.anime_id == anime]
    if isinstance(anime, str):
        match = df[df.eng_version == anime]
        if match.empty and "Name" in df.columns:
            match = df[df.Name == anime]
        return match
    return pd.DataFrame()


########## 2. GET_SYNOPSIS

def getSynopsis(anime, path_synopsis_df):
    try:
        synopsis_df = pd.read_csv(path_synopsis_df)
        if isinstance(anime, (int, np.integer)):
            res = synopsis_df[synopsis_df.MAL_ID == anime].sypnopsis.values
            return res[0] if len(res) > 0 else "No synopsis available."
        if isinstance(anime, str):
            res = synopsis_df[synopsis_df.Name == anime].sypnopsis.values
            return res[0] if len(res) > 0 else "No synopsis available."
    except Exception:
        pass
    return "No synopsis available."


########## 3. CONTENT RECOMMENDATION

def find_similar_animes(name, path_anime_weights, path_anime2anime_encoded, path_anime2anime_decoded, path_anime_df, n=10, return_dist=False, neg=False):
    try:
        # Load weights and encoded-decoded mappings
        anime_weights = joblib.load(path_anime_weights)
        anime2anime_encoded = joblib.load(path_anime2anime_encoded)
        anime2anime_decoded = joblib.load(path_anime2anime_decoded)

        # Get the anime ID for the given name
        frame = getAnimeFrame(name, path_anime_df)
        if frame is None or frame.empty:
            return pd.DataFrame()

        index = frame.anime_id.values[0]
        encoded_index = anime2anime_encoded.get(index)

        if encoded_index is None:
            return pd.DataFrame()

        # Compute similarity distances
        weights = anime_weights
        dists = np.dot(weights, weights[encoded_index])
        sorted_dists = np.argsort(dists)

        n = n + 1

        if neg:
            closest = sorted_dists[:n]
        else:
            closest = sorted_dists[-n:]

        if return_dist:
            return dists, closest

        # Build similarity array (read CSV once outside the loop)
        anime_df = pd.read_csv(path_anime_df)
        SimilarityArr = []
        for close in closest:
            decoded_id = anime2anime_decoded.get(close)
            if decoded_id is None:
                continue

            match = anime_df[anime_df.anime_id == decoded_id]
            if match.empty:
                continue

            anime_name = match.eng_version.values[0]
            genre = match.Genres.values[0] if "Genres" in match.columns else ""
            similarity = dists[close]

            SimilarityArr.append({
                "anime_id": decoded_id,
                "name": anime_name,
                "similarity": similarity,
                "genre": genre,
            })

        if not SimilarityArr:
            return pd.DataFrame()

        Frame = pd.DataFrame(SimilarityArr).sort_values(by="similarity", ascending=False)
        return Frame[Frame.anime_id != index].drop(['anime_id'], axis=1)
    except Exception as e:
        print(f"Error in find_similar_animes: {e}")
        return pd.DataFrame()


######## 4. FIND_SIMILAR_USERS

def find_similar_users(item_input, path_user_weights, path_user2user_encoded, path_user2user_decoded, n=10, return_dist=False, neg=False):
    try:
        user_weights = joblib.load(path_user_weights)
        user2user_encoded = joblib.load(path_user2user_encoded)
        user2user_decoded = joblib.load(path_user2user_decoded)

        index = item_input
        encoded_index = user2user_encoded.get(index)

        if encoded_index is None:
            return pd.DataFrame(columns=["similar_users", "similarity"])

        weights = user_weights
        dists = np.dot(weights, weights[encoded_index])
        sorted_dists = np.argsort(dists)

        n = n + 1

        if neg:
            closest = sorted_dists[:n]
        else:
            closest = sorted_dists[-n:]

        if return_dist:
            return dists, closest

        SimilarityArr = []
        for close in closest:
            similarity = dists[close]
            if isinstance(item_input, (int, np.integer)):
                decoded_id = user2user_decoded.get(close)
                if decoded_id is not None:
                    SimilarityArr.append({
                        "similar_users": decoded_id,
                        "similarity": similarity
                    })

        similar_users = pd.DataFrame(SimilarityArr).sort_values(by="similarity", ascending=False)
        if not similar_users.empty and "similar_users" in similar_users.columns:
            similar_users = similar_users[similar_users.similar_users != item_input]
        return similar_users
    except Exception as e:
        print("Error in find_similar_users:", e)
        return pd.DataFrame(columns=["similar_users", "similarity"])


################## 5. GET USER PREF

def get_user_preferences(user_id, path_rating_df, path_anime_df):
    try:
        rating_df = pd.read_csv(path_rating_df)
        df = pd.read_csv(path_anime_df)

        animes_watched_by_user = rating_df[rating_df.user_id == user_id]
        if animes_watched_by_user.empty:
            return pd.DataFrame(columns=["eng_version", "Genres"])

        user_rating_percentile = np.percentile(animes_watched_by_user.rating, 75)
        animes_watched_by_user = animes_watched_by_user[animes_watched_by_user.rating >= user_rating_percentile]

        top_animes_user = animes_watched_by_user.sort_values(by="rating", ascending=False).anime_id.values
        anime_df_rows = df[df["anime_id"].isin(top_animes_user)]
        anime_df_rows = anime_df_rows[["eng_version", "Genres"]]

        return anime_df_rows
    except Exception as e:
        print(f"Error in get_user_preferences: {e}")
        return pd.DataFrame(columns=["eng_version", "Genres"])


######## 6. USER RECOMMENDATION

def get_user_recommendations(similar_users, user_pref, path_anime_df, path_synopsis_df, path_rating_df, n=10):
    try:
        if similar_users is None or similar_users.empty:
            return pd.DataFrame(columns=["n", "anime_name", "Genres", "Synopsis"])

        recommended_animes = []
        anime_list = []

        for user_id in similar_users.similar_users.values:
            pref_list = get_user_preferences(int(user_id), path_rating_df, path_anime_df)

            if not user_pref.empty and "eng_version" in user_pref.columns:
                pref_list = pref_list[~pref_list.eng_version.isin(user_pref.eng_version.values)]

            if not pref_list.empty and "eng_version" in pref_list.columns:
                anime_list.extend(pref_list.eng_version.dropna().tolist())

        if anime_list:
            sorted_list = pd.Series(anime_list).value_counts().head(n)

            for anime_name, n_user_pref in sorted_list.items():
                if isinstance(anime_name, str):
                    frame = getAnimeFrame(anime_name, path_anime_df)
                    if frame is not None and not frame.empty:
                        anime_id = frame.anime_id.values[0]
                        genre = frame.Genres.values[0] if "Genres" in frame.columns else ""
                        synopsis = getSynopsis(int(anime_id), path_synopsis_df)

                        recommended_animes.append({
                            "n": n_user_pref,
                            "anime_name": anime_name,
                            "Genres": genre,
                            "Synopsis": synopsis
                        })

        return pd.DataFrame(recommended_animes).head(n) if recommended_animes else pd.DataFrame(columns=["n", "anime_name", "Genres", "Synopsis"])
    except Exception as e:
        print(f"Error in get_user_recommendations: {e}")
        return pd.DataFrame(columns=["n", "anime_name", "Genres", "Synopsis"])
            



    




        
        

        