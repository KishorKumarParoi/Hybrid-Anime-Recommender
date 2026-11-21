-- ==============================================================================
-- ENTERPRISE HYBRID ANIME PLATFORM - NEON POSTGRESQL PRODUCTION DDL SCHEMA
-- ==============================================================================
-- Target: PostgreSQL 18.x on Neon Cloud (AWS us-east-1)
-- Features: pgvector HNSW indexing, pg_trgm fuzzy matching, GIN Full-Text Search,
--           ACID relational normalization, and JSONB document storage.
-- ==============================================================================

-- 1. Enable Core Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. Genres Lookup Table
CREATE TABLE IF NOT EXISTS public.genres (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) UNIQUE NOT NULL,
    slug VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Studios Lookup Table
CREATE TABLE IF NOT EXISTS public.studios (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL,
    slug VARCHAR(128) UNIQUE NOT NULL,
    country VARCHAR(64) DEFAULT 'Japan',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Anime Master Catalog Table (17,367+ Complete Records)
CREATE TABLE IF NOT EXISTS public.animes (
    id INT PRIMARY KEY, -- Preserves canonical MyAnimeList anime_id
    title VARCHAR(512) NOT NULL,
    eng_title VARCHAR(512),
    synopsis TEXT,
    score NUMERIC(4, 2) DEFAULT 0.00,
    episodes INT DEFAULT 1,
    year INT,
    season VARCHAR(64),
    anime_type VARCHAR(32) DEFAULT 'TV',
    status VARCHAR(64) DEFAULT 'Finished Airing',
    members INT DEFAULT 0,
    ranked INT,
    popularity INT,
    studio_id INT REFERENCES public.studios(id) ON DELETE SET NULL,
    studio_name VARCHAR(128),
    image_url VARCHAR(1024),
    embedding vector(4), -- Latent taste vector [Action, Psychological, SciFi, WorldBuilding]
    likes INT DEFAULT 0,
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(synopsis, ''))
    ) STORED,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Anime-Genres Junction Table (Many-to-Many Normalization)
CREATE TABLE IF NOT EXISTS public.anime_genres (
    anime_id INT REFERENCES public.animes(id) ON DELETE CASCADE,
    genre_id INT REFERENCES public.genres(id) ON DELETE CASCADE,
    PRIMARY KEY (anime_id, genre_id)
);

-- 6. Character Profiles Table (Deep Struggle & Psychological Trauma Matrix)
CREATE TABLE IF NOT EXISTS public.characters (
    id VARCHAR(64) PRIMARY KEY, -- e.g. 'okabe-rintarou', 'levi-ackerman'
    name VARCHAR(128) NOT NULL,
    title VARCHAR(256),
    anime_title VARCHAR(256),
    mbti VARCHAR(16),
    quote TEXT,
    archetype VARCHAR(128),
    bio TEXT,
    struggle TEXT NOT NULL,
    struggle_keywords TEXT[],
    healing_philosophy TEXT NOT NULL,
    vector vector(4), -- Canonical personality latent vector
    avatar_gradient VARCHAR(128),
    badge_color VARCHAR(128),
    recommended_genres TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Character Traits Table
CREATE TABLE IF NOT EXISTS public.character_traits (
    id SERIAL PRIMARY KEY,
    character_id VARCHAR(64) REFERENCES public.characters(id) ON DELETE CASCADE,
    trait VARCHAR(128) NOT NULL
);

-- 8. Prescription Cathartic Anime Therapy Table
CREATE TABLE IF NOT EXISTS public.character_cathartic_anime (
    id SERIAL PRIMARY KEY,
    character_id VARCHAR(64) REFERENCES public.characters(id) ON DELETE CASCADE,
    anime_id INT REFERENCES public.animes(id) ON DELETE SET NULL,
    title VARCHAR(256) NOT NULL,
    reason TEXT NOT NULL,
    score NUMERIC(4, 2),
    episodes INT
);

-- 9. User Watchlists Table (MyAnimeList 2027 Replica)
CREATE TABLE IF NOT EXISTS public.user_watchlists (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(128) NOT NULL,
    anime_id INT REFERENCES public.animes(id) ON DELETE CASCADE,
    status VARCHAR(32) NOT NULL DEFAULT 'plan_to_watch', -- watching, completed, on_hold, dropped, plan_to_watch
    score INT DEFAULT 0 CHECK (score >= 0 AND score <= 10),
    episodes_watched INT DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_anime UNIQUE (user_id, anime_id)
);

-- 10. 24/7 AI Anime Newsroom Table
CREATE TABLE IF NOT EXISTS public.anime_news (
    id VARCHAR(64) PRIMARY KEY,
    headline TEXT NOT NULL,
    studio VARCHAR(128),
    timestamp_str VARCHAR(64),
    verified BOOLEAN DEFAULT TRUE,
    priority VARCHAR(32) DEFAULT 'Breaking',
    tags TEXT[],
    bullets JSONB DEFAULT '[]'::jsonb,
    character_commentary JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- PRODUCTION HIGH-PERFORMANCE INDEXES
-- ==============================================================================

-- Full-Text Search GIN Index (Sub-millisecond keyword lookup across 17k records)
CREATE INDEX IF NOT EXISTS idx_animes_search_vector ON public.animes USING GIN(search_vector);

-- Trigram GIN Index for fuzzy typo-tolerant autocomplete (e.g. 'titan', 'steins')
CREATE INDEX IF NOT EXISTS idx_animes_title_trgm ON public.animes USING GIN(title gin_trgm_ops);

-- B-Tree Indexes for Ranking, Filtering and Sorting
CREATE INDEX IF NOT EXISTS idx_animes_score ON public.animes(score DESC);
CREATE INDEX IF NOT EXISTS idx_animes_popularity ON public.animes(popularity ASC);
CREATE INDEX IF NOT EXISTS idx_animes_year ON public.animes(year DESC);
CREATE INDEX IF NOT EXISTS idx_animes_studio ON public.animes(studio_id);
CREATE INDEX IF NOT EXISTS idx_animes_type ON public.animes(anime_type);
CREATE INDEX IF NOT EXISTS idx_anime_genres_genre ON public.anime_genres(genre_id);
CREATE INDEX IF NOT EXISTS idx_user_watchlists_user ON public.user_watchlists(user_id);
CREATE INDEX IF NOT EXISTS idx_user_watchlists_status ON public.user_watchlists(user_id, status);

-- HNSW Native Vector Index for Latent Embeddings (pgvector cosine similarity)
CREATE INDEX IF NOT EXISTS idx_animes_embedding_hnsw ON public.animes USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_characters_vector_hnsw ON public.characters USING hnsw (vector vector_cosine_ops);

-- Auto-update updated_at trigger function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_animes_updated_at ON public.animes;
CREATE TRIGGER update_animes_updated_at
    BEFORE UPDATE ON public.animes
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_watchlists_updated_at ON public.user_watchlists;
CREATE TRIGGER update_user_watchlists_updated_at
    BEFORE UPDATE ON public.user_watchlists
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();
