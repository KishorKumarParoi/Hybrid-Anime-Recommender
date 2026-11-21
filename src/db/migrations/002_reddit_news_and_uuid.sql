-- ==============================================================================
-- MIGRATION 002: REDDIT-STYLE DISCUSSION, UUID IDENTIFIERS, VOTING & CRAWLING
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop old anime_news table if needed to rebuild with proper UUID primary key
DROP TABLE IF EXISTS public.news_votes CASCADE;
DROP TABLE IF EXISTS public.comment_votes CASCADE;
DROP TABLE IF EXISTS public.news_comments CASCADE;
DROP TABLE IF EXISTS public.anime_news CASCADE;

-- 1. Anime News with UUID Primary Key
CREATE TABLE public.anime_news (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    source VARCHAR(64) DEFAULT 'RSS Feed', -- 'Reddit r/anime', 'Twitter / X', 'Anime News Network', 'Crunchyroll'
    source_url TEXT UNIQUE,
    studio_source VARCHAR(128) DEFAULT 'Official Desk',
    timestamp_str VARCHAR(64) DEFAULT 'Just Now',
    category VARCHAR(64) DEFAULT 'Industry',
    hype_score INT DEFAULT 85,
    upvotes INT DEFAULT 0,
    downvotes INT DEFAULT 0,
    verified BOOLEAN DEFAULT TRUE,
    ai_summary_bullets JSONB DEFAULT '[]'::jsonb,
    character_reaction JSONB DEFAULT '{}'::jsonb,
    related_anime_title VARCHAR(256),
    likes INT DEFAULT 0,
    shares INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Reddit-style Discussion Threads & Reviews on News
CREATE TABLE public.news_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    news_id UUID NOT NULL REFERENCES public.anime_news(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES public.news_comments(id) ON DELETE CASCADE, -- For nested / threaded discussions
    user_id VARCHAR(128) NOT NULL,
    user_name VARCHAR(128) NOT NULL,
    avatar_gradient VARCHAR(128) DEFAULT 'from-purple-500 to-indigo-600',
    character_flair VARCHAR(128), -- e.g. "Alter Ego: Rintarou Okabe"
    content TEXT NOT NULL,
    upvotes INT DEFAULT 0,
    downvotes INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. News Article Upvotes / Downvotes (Unique per user + news_id)
CREATE TABLE public.news_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(128) NOT NULL,
    news_id UUID NOT NULL REFERENCES public.anime_news(id) ON DELETE CASCADE,
    vote INT NOT NULL CHECK (vote IN (1, -1)), -- +1 upvote, -1 downvote
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_news_vote UNIQUE (user_id, news_id)
);

-- 4. Comment Upvotes / Downvotes (Unique per user + comment_id)
CREATE TABLE public.comment_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(128) NOT NULL,
    comment_id UUID NOT NULL REFERENCES public.news_comments(id) ON DELETE CASCADE,
    vote INT NOT NULL CHECK (vote IN (1, -1)), -- +1 upvote, -1 downvote
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_comment_vote UNIQUE (user_id, comment_id)
);

-- 5. Persistent User Character Struggle Matches (UUID Primary Key)
CREATE TABLE IF NOT EXISTS public.user_character_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(128) NOT NULL,
    character_id VARCHAR(64) REFERENCES public.characters(id) ON DELETE CASCADE,
    character_name VARCHAR(128) NOT NULL,
    match_percentage NUMERIC(5, 2) NOT NULL,
    struggle_input TEXT NOT NULL,
    shared_struggles TEXT[] DEFAULT '{}',
    resonance_analysis TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for lightning-fast Reddit thread retrieval
CREATE INDEX IF NOT EXISTS idx_anime_news_created_at ON public.anime_news(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_anime_news_hype ON public.anime_news(hype_score DESC);
CREATE INDEX IF NOT EXISTS idx_news_comments_news_id ON public.news_comments(news_id);
CREATE INDEX IF NOT EXISTS idx_news_comments_parent_id ON public.news_comments(parent_id);
CREATE INDEX IF NOT EXISTS idx_news_votes_news ON public.news_votes(news_id);
CREATE INDEX IF NOT EXISTS idx_user_character_matches_user ON public.user_character_matches(user_id);
