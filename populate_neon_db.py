#!/usr/bin/env python3
"""
High-Performance Neon PostgreSQL Seeding & Migration Engine
Populates 17,367+ anime master records, genres, studios, 22 character trauma profiles,
cathartic prescription anime, 24/7 newsroom, and HNSW vector embeddings into Neon AWS.
"""

import os
import sys
import json
import time
import re
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

NEON_URL = (
    os.environ.get("DATABASE_URL")
    or os.environ.get("NEON_POSTGRESQL")
    or "postgresql://neondb_owner:npg_JKYCdFefmx62@ep-fragrant-cell-bc8thn5j-pooler.c-16.us-east-1.aws.neon.tech/neondb?sslmode=require"
)

if "channel_binding=require" in NEON_URL:
    NEON_URL = NEON_URL.replace("&channel_binding=require", "").replace("channel_binding=require&", "").replace("?channel_binding=require", "")


def slugify(text: str) -> str:
    """Generate clean slug identifier for genres and studios."""
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def apply_schema(conn):
    """Executes schema.sql DDL to create tables and indexes."""
    schema_path = os.path.join(os.path.dirname(__file__), "src", "db", "schema.sql")
    logger.info(f"Applying schema DDL from {schema_path}...")
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    logger.info("[✓] Database schema, extensions (vector, pg_trgm, uuid-ossp), and indexes created successfully.")


def populate_genres(conn, catalog: List[Dict[str, Any]]) -> Dict[str, int]:
    """Extract and normalize all unique genres."""
    logger.info("Extracting and seeding normalized genres...")
    all_genres = set()
    for a in catalog:
        for g in a.get("genres", []):
            g_clean = g.strip()
            if g_clean:
                all_genres.add(g_clean)

    records = [(g, slugify(g)) for g in sorted(all_genres)]
    insert_sql = """
        INSERT INTO public.genres (name, slug)
        VALUES %s
        ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
        RETURNING id, name;
    """
    with conn.cursor() as cur:
        execute_values(cur, insert_sql, records)
        rows = cur.fetchall()
    conn.commit()

    genre_map = {name.lower(): gid for gid, name in rows}
    logger.info(f"[✓] Seeded {len(genre_map)} normalized genres.")
    return genre_map


def populate_studios(conn, catalog: List[Dict[str, Any]]) -> Dict[str, int]:
    """Extract and normalize all unique animation studios."""
    logger.info("Extracting and seeding animation studios...")
    all_studios = set()
    for a in catalog:
        s = a.get("studio", "Independent Animation")
        if s and s.strip():
            all_studios.add(s.strip())

    records = [(s, slugify(s), "Japan") for s in sorted(all_studios)]
    insert_sql = """
        INSERT INTO public.studios (name, slug, country)
        VALUES %s
        ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
        RETURNING id, name;
    """
    with conn.cursor() as cur:
        execute_values(cur, insert_sql, records)
        rows = cur.fetchall()
    conn.commit()

    studio_map = {name: sid for sid, name in rows}
    logger.info(f"[✓] Seeded {len(studio_map)} animation studios.")
    return studio_map


def populate_animes(conn, catalog: List[Dict[str, Any]], studio_map: Dict[str, int], genre_map: Dict[str, int]):
    """Batch-insert all 17,367+ master anime records and their genre relationships."""
    total = len(catalog)
    logger.info(f"Preparing batch insertion for {total:,} anime records into Neon PostgreSQL...")

    BATCH_SIZE = 1500
    anime_records = []
    junction_records = []

    for a in catalog:
        aid = int(a["id"])
        title = a.get("title", f"Anime #{aid}")
        eng_title = a.get("eng_title") or title
        synopsis = a.get("synopsis", "")
        score = float(a.get("score", 0.0))
        episodes = int(a.get("episodes", 1))
        year = int(a.get("year", 2024))
        season = a.get("season", "Spring 2024")
        atype = a.get("type", "TV")
        status = a.get("status", "Finished Airing")
        members = int(a.get("members", 0))
        ranked = int(a.get("ranked", aid))
        popularity = int(a.get("popularity", aid))
        studio_name = a.get("studio", "Independent Animation")
        studio_id = studio_map.get(studio_name)
        likes = int(a.get("likes", 0))
        
        # Native pgvector 4-dimensional vector string '[0.35,0.95,0.98,0.60]'
        vec = a.get("vector", [0.5, 0.5, 0.5, 0.5])
        vec_str = f"[{','.join(str(round(v, 4)) for v in vec)}]"
        
        metadata_json = json.dumps({
            "premiered": a.get("premiered", ""),
            "season": season,
            "status": status,
            "genres_list": a.get("genres", [])
        })

        anime_records.append((
            aid, title, eng_title, synopsis, score, episodes, year, season,
            atype, status, members, ranked, popularity, studio_id, studio_name,
            vec_str, likes, metadata_json
        ))

        # Junction records
        for g in a.get("genres", []):
            gid = genre_map.get(g.strip().lower())
            if gid:
                junction_records.append((aid, gid))

    # Batch Insert Animes
    t0 = time.time()
    anime_insert_sql = """
        INSERT INTO public.animes (
            id, title, eng_title, synopsis, score, episodes, year, season,
            anime_type, status, members, ranked, popularity, studio_id, studio_name,
            embedding, likes, metadata
        )
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            synopsis = EXCLUDED.synopsis,
            score = EXCLUDED.score,
            episodes = EXCLUDED.episodes,
            year = EXCLUDED.year,
            members = EXCLUDED.members,
            ranked = EXCLUDED.ranked,
            popularity = EXCLUDED.popularity,
            studio_id = EXCLUDED.studio_id,
            studio_name = EXCLUDED.studio_name,
            embedding = EXCLUDED.embedding,
            likes = EXCLUDED.likes,
            updated_at = NOW();
    """

    with conn.cursor() as cur:
        for i in range(0, len(anime_records), BATCH_SIZE):
            chunk = anime_records[i : i + BATCH_SIZE]
            execute_values(cur, anime_insert_sql, chunk)
            conn.commit()
            logger.info(f"  -> Inserted {min(i + BATCH_SIZE, total):,}/{total:,} anime records...")

    t1 = time.time()
    logger.info(f"[✓] Completed insertion of {total:,} anime records in {t1 - t0:.2f} seconds.")

    # Batch Insert Junction records
    logger.info(f"Seeding {len(junction_records):,} anime_genres relationships...")
    junction_insert_sql = """
        INSERT INTO public.anime_genres (anime_id, genre_id)
        VALUES %s
        ON CONFLICT (anime_id, genre_id) DO NOTHING;
    """
    with conn.cursor() as cur:
        for i in range(0, len(junction_records), BATCH_SIZE * 2):
            chunk = junction_records[i : i + BATCH_SIZE * 2]
            execute_values(cur, junction_insert_sql, chunk)
            conn.commit()
    logger.info(f"[✓] Seeded all {len(junction_records):,} anime_genres relationships.")


def populate_characters(conn):
    """Seed all 22 rich anime characters, traits, and cathartic prescription anime."""
    char_file = os.path.join(os.path.dirname(__file__), "data", "anime_characters.json")
    if not os.path.exists(char_file):
        logger.warning(f"Characters file {char_file} not found; skipping characters.")
        return

    with open(char_file, "r", encoding="utf-8") as f:
        characters = json.load(f)

    logger.info(f"Seeding {len(characters)} character profiles with deep struggle profiling...")

    char_records = []
    trait_records = []
    cathartic_records = []

    for c in characters:
        cid = c["id"]
        vec = c.get("vector", [0.5, 0.5, 0.5, 0.5])
        vec_str = f"[{','.join(str(round(v, 4)) for v in vec)}]"

        char_records.append((
            cid,
            c["name"],
            c.get("title", ""),
            c.get("anime", ""),
            c.get("mbti", "INTJ"),
            c.get("quote", ""),
            c.get("archetype", ""),
            c.get("bio", ""),
            c.get("struggle", ""),
            c.get("struggle_keywords", []),
            c.get("healing_philosophy", ""),
            vec_str,
            c.get("avatar_gradient", "from-purple-500 to-indigo-700"),
            c.get("badge_color", "border-purple-500/40 text-purple-300"),
            c.get("recommended_genres", [])
        ))

        for trait in c.get("traits", []):
            trait_records.append((cid, trait))

        for ca in c.get("cathartic_anime", []):
            cathartic_records.append((
                cid,
                ca.get("title", ""),
                ca.get("reason", ""),
                float(ca.get("score", 8.5)),
                int(ca.get("episodes", 24))
            ))

    char_sql = """
        INSERT INTO public.characters (
            id, name, title, anime_title, mbti, quote, archetype, bio,
            struggle, struggle_keywords, healing_philosophy, vector,
            avatar_gradient, badge_color, recommended_genres
        )
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            title = EXCLUDED.title,
            struggle = EXCLUDED.struggle,
            struggle_keywords = EXCLUDED.struggle_keywords,
            healing_philosophy = EXCLUDED.healing_philosophy,
            vector = EXCLUDED.vector,
            recommended_genres = EXCLUDED.recommended_genres;
    """

    with conn.cursor() as cur:
        execute_values(cur, char_sql, char_records)
        
        # Clear & reseed traits
        cur.execute("DELETE FROM public.character_traits;")
        execute_values(cur, "INSERT INTO public.character_traits (character_id, trait) VALUES %s;", trait_records)

        # Clear & reseed cathartic anime
        cur.execute("DELETE FROM public.character_cathartic_anime;")
        execute_values(cur, """
            INSERT INTO public.character_cathartic_anime (character_id, title, reason, score, episodes)
            VALUES %s;
        """, cathartic_records)

    conn.commit()
    logger.info(f"[✓] Seeded {len(characters)} characters, {len(trait_records)} traits, and {len(cathartic_records)} cathartic recommendations.")


def populate_news(conn):
    """Seed 24/7 AI studio intelligence feed."""
    news_file = os.path.join(os.path.dirname(__file__), "data", "anime_news_2027.json")
    if not os.path.exists(news_file):
        return

    with open(news_file, "r", encoding="utf-8") as f:
        news_items = json.load(f)

    logger.info(f"Seeding {len(news_items)} 24/7 AI studio intelligence wire items...")
    news_records = []
    for n in news_items:
        news_records.append((
            n["id"],
            n.get("title", "Anime News Update"),
            n.get("studio_source", "Anime News Desk"),
            n.get("timestamp", "Just Now"),
            n.get("verified", True),
            n.get("category", "Breaking"),
            [n.get("category", "Anime"), n.get("related_anime_title", "General")],
            json.dumps(n.get("ai_summary_bullets", [])),
            json.dumps(n.get("character_reaction", {}))
        ))

    insert_sql = """
        INSERT INTO public.anime_news (
            id, headline, studio, timestamp_str, verified, priority, tags, bullets, character_commentary
        )
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            headline = EXCLUDED.headline,
            bullets = EXCLUDED.bullets,
            character_commentary = EXCLUDED.character_commentary;
    """
    with conn.cursor() as cur:
        execute_values(cur, insert_sql, news_records)
    conn.commit()
    logger.info(f"[✓] Seeded {len(news_items)} 24/7 AI news wire records.")


def run_benchmarks(conn):
    """Execute high-speed benchmarks on GIN Full-Text, pg_trgm fuzzy search, and HNSW vector similarity."""
    logger.info("\n" + "=" * 70)
    logger.info("⚡ BENCHMARKING NEON POSTGRESQL PRODUCTION QUERIES")
    logger.info("=" * 70)

    with conn.cursor() as cur:
        # 1. Full-Text Search Benchmark
        t0 = time.time()
        cur.execute("""
            SELECT id, title, score, ts_rank(search_vector, websearch_to_tsquery('english', 'time travel microwave')) as rank
            FROM public.animes
            WHERE search_vector @@ websearch_to_tsquery('english', 'time travel microwave')
            ORDER BY rank DESC, score DESC
            LIMIT 5;
        """)
        fts_res = cur.fetchall()
        t_fts = (time.time() - t0) * 1000
        logger.info(f"1. GIN Full-Text Search ('time travel microwave') -> {len(fts_res)} results in {t_fts:.2f} ms")
        for r in fts_res[:2]:
            logger.info(f"   - [{r[0]}] {r[1]} (Score: {r[2]}, Rank: {r[3]:.4f})")

        # 2. Fuzzy Trigram Autocomplete Benchmark
        t0 = time.time()
        cur.execute("""
            SELECT id, title, score, similarity(title, 'shingeki titan') as sim
            FROM public.animes
            WHERE title % 'shingeki titan' OR title ILIKE '%titan%'
            ORDER BY sim DESC, score DESC
            LIMIT 5;
        """)
        trgm_res = cur.fetchall()
        t_trgm = (time.time() - t0) * 1000
        logger.info(f"2. Trigram Fuzzy Autocomplete ('shingeki titan') -> {len(trgm_res)} results in {t_trgm:.2f} ms")
        for r in trgm_res[:2]:
            logger.info(f"   - [{r[0]}] {r[1]} (Score: {r[2]}, Sim: {r[3]:.4f})")

        # 3. pgvector HNSW Cosine Similarity Search Benchmark
        t0 = time.time()
        # Vector for [Action=0.95, Psychological=0.90, SciFi=0.20, WorldBuilding=0.95] (Guts / Titan style)
        sample_vec = "[0.95, 0.90, 0.20, 0.95]"
        cur.execute("""
            SELECT id, title, score, 1 - (embedding <=> %s::vector) as similarity
            FROM public.animes
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 5;
        """, (sample_vec, sample_vec))
        vec_res = cur.fetchall()
        t_vec = (time.time() - t0) * 1000
        logger.info(f"3. pgvector HNSW Cosine Similarity Search -> {len(vec_res)} results in {t_vec:.2f} ms")
        for r in vec_res[:3]:
            logger.info(f"   - [{r[0]}] {r[1]} (Score: {r[2]}, Cosine Match: {r[3]:.4f})")

        # Table Row Counts
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM public.animes) as animes,
                (SELECT COUNT(*) FROM public.genres) as genres,
                (SELECT COUNT(*) FROM public.studios) as studios,
                (SELECT COUNT(*) FROM public.characters) as characters,
                (SELECT COUNT(*) FROM public.character_cathartic_anime) as cathartic,
                (SELECT COUNT(*) FROM public.anime_news) as news;
        """)
        counts = cur.fetchone()
        logger.info("\n" + "=" * 70)
        logger.info("📊 DATABASE TELEMETRY & INVENTORY AUDIT")
        logger.info(f"   Total Anime Master Records:     {counts[0]:,}")
        logger.info(f"   Normalized Genres:             {counts[1]:,}")
        logger.info(f"   Animation Studios:             {counts[2]:,}")
        logger.info(f"   AI Character Profiles:         {counts[3]:,}")
        logger.info(f"   Cathartic Prescription Recs:   {counts[4]:,}")
        logger.info(f"   24/7 AI Newsroom Articles:     {counts[5]:,}")
        logger.info("=" * 70 + "\n")


def main():
    logger.info("Connecting to Neon PostgreSQL...")
    conn = psycopg2.connect(NEON_URL)
    conn.autocommit = False

    try:
        # Step 1: Apply Schema
        apply_schema(conn)

        # Step 2: Load Anime Catalog Full JSON
        catalog_file = os.path.join(os.path.dirname(__file__), "data", "anime_catalog_full.json")
        if not os.path.exists(catalog_file):
            logger.error(f"Catalog file {catalog_file} not found. Run generate_dataset_and_characters.py first.")
            sys.exit(1)

        with open(catalog_file, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        logger.info(f"Loaded {len(catalog):,} records from {catalog_file}")

        # Step 3: Populate Normalization Lookups
        genre_map = populate_genres(conn, catalog)
        studio_map = populate_studios(conn, catalog)

        # Step 4: Populate Animes & Junction
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM public.animes;")
            existing_animes = cur.fetchone()[0]
        if existing_animes >= 17000:
            logger.info(f"Animes already fully populated ({existing_animes:,} records). Skipping re-insertion.")
        else:
            populate_animes(conn, catalog, studio_map, genre_map)

        # Step 5: Populate Character Profiles & Cathartic Therapy
        populate_characters(conn)

        # Step 6: Populate 24/7 AI Studio News
        populate_news(conn)

        # Step 7: Analyze database tables for optimized query execution plan
        logger.info("Running VACUUM ANALYZE to optimize PostgreSQL query planner statistics...")
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("ANALYZE public.animes;")
            cur.execute("ANALYZE public.genres;")
            cur.execute("ANALYZE public.anime_genres;")
            cur.execute("ANALYZE public.characters;")
        conn.autocommit = False

        # Step 8: Benchmarks
        run_benchmarks(conn)

        logger.info("🎉 NEON POSTGRESQL MIGRATION & SEEDING COMPLETED WITH ZERO ERRORS!")

    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed with error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
