"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Radio,
  Sparkles,
  Flame,
  Share2,
  Heart,
  ExternalLink,
  CheckCircle2,
  Clock,
  Building,
  Filter,
  MessageSquare,
  Cpu,
  RefreshCw
} from "lucide-react";
import { playClickSound, playSuccessChime } from "@/components/SoundFX";

export interface AnimeNewsItem {
  id: string;
  title: string;
  timestamp: string;
  studio_source: string;
  category: string;
  hype_score: number;
  verified: boolean;
  ai_summary_bullets: string[];
  character_reaction: {
    character_name: string;
    anime: string;
    avatar_gradient: string;
    quote: string;
  };
  related_anime_title: string;
  likes: number;
  shares: number;
  isLiked?: boolean;
}

interface LiveNewsroom2027Props {
  onSelectAnime?: (title: string) => void;
}

export default function LiveNewsroom2027({ onSelectAnime }: LiveNewsroom2027Props) {
  const [news, setNews] = useState<AnimeNewsItem[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>("ALL");
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    fetch("/data/anime_news_2027.json")
      .then((res) => res.json())
      .then((data: AnimeNewsItem[]) => setNews(data))
      .catch((err) => console.error("Error loading 2027 anime news:", err));
  }, []);

  const categories = ["ALL", "Movie Premiere", "Trailer Drop", "Season Renewal", "Studio Key Visual"];

  const filteredNews = useMemo(() => {
    if (activeCategory === "ALL") return news;
    return news.filter((item) => item.category === activeCategory);
  }, [news, activeCategory]);

  const handleLikeNews = (id: string) => {
    playClickSound();
    setNews((prev) =>
      prev.map((item) => {
        if (item.id === id) {
          const isLiked = !item.isLiked;
          return {
            ...item,
            isLiked,
            likes: isLiked ? item.likes + 1 : item.likes - 1
          };
        }
        return item;
      })
    );
  };

  const handleRefreshFeed = () => {
    playSuccessChime();
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
    }, 600);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* 2027 AI Newsroom Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-red-500/20 bg-gradient-to-r from-red-950/40 via-purple-950/30 to-neutral-950/80 p-6 md:p-8 backdrop-blur-2xl">
        <div className="absolute top-0 right-0 w-80 h-80 bg-red-600/10 blur-3xl rounded-full pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-300 border border-red-500/30">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
              <Radio className="w-3.5 h-3.5 text-red-400" />
              <span>MAL 2027 • 24/7 Autonomous AI Newsroom</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight">
              Live Japanese Studio <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-400 via-pink-400 to-amber-300">Intelligence Stream</span>
            </h2>
            <p className="text-sm text-neutral-300 max-w-2xl leading-relaxed">
              Synthesized 24/7 by our self-hosted <strong>vLLM Qwen2.5 GPU cluster</strong>. Autonomous scrapers ingest official studio press releases, trailer leaks, and production schedules, distilling them into 3-bullet verified intelligence briefs with live character commentary.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-neutral-900/80 border border-neutral-800 text-xs font-mono text-neutral-300">
              <Cpu className="w-4 h-4 text-emerald-400" />
              <span>vLLM Inference: <strong>Active (24/7)</strong></span>
            </div>

            <button
              onClick={handleRefreshFeed}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-600/90 hover:bg-red-500 text-white text-xs font-bold transition-all shadow-lg shadow-red-600/20 active:scale-95"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
              <span>Sync Studio Feeds</span>
            </button>
          </div>
        </div>

        {/* Category Filters */}
        <div className="flex items-center gap-2 mt-6 overflow-x-auto pb-1">
          <Filter className="w-3.5 h-3.5 text-neutral-400 flex-shrink-0 mr-1" />
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => {
                playClickSound();
                setActiveCategory(cat);
              }}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                activeCategory === cat
                  ? "bg-red-600 text-white shadow-md shadow-red-600/30"
                  : "bg-neutral-900/80 text-neutral-400 hover:text-white border border-neutral-800"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* News Feed Grid */}
      <div className="space-y-6">
        {filteredNews.map((item) => (
          <div
            key={item.id}
            className="rounded-3xl border border-white/10 bg-neutral-900/60 p-6 md:p-8 backdrop-blur-xl hover:border-red-500/40 transition-all duration-300 shadow-xl space-y-6 group"
          >
            {/* Header: Source, Time, Category, Hype Score */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/5 pb-4">
              <div className="flex items-center gap-2.5">
                <span className="p-1.5 rounded-lg bg-neutral-800 border border-neutral-700 text-neutral-300">
                  <Building className="w-3.5 h-3.5" />
                </span>
                <span className="text-xs font-bold text-neutral-200">
                  {item.studio_source}
                </span>
                {item.verified && (
                  <span className="inline-flex items-center gap-1 text-[11px] font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded-full border border-cyan-500/20">
                    <CheckCircle2 className="w-3 h-3" />
                    Verified Studio
                  </span>
                )}
                <span className="text-xs text-neutral-500 font-mono flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {item.timestamp}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-neutral-800 text-neutral-300 border border-neutral-700">
                  {item.category}
                </span>
                <span className="flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-extrabold bg-gradient-to-r from-red-600/20 to-amber-600/20 text-amber-300 border border-amber-500/30">
                  <Flame className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                  <span>{item.hype_score}% HYPE</span>
                </span>
              </div>
            </div>

            {/* Headline */}
            <h3 className="text-xl md:text-2xl font-black text-white group-hover:text-red-300 transition-colors leading-snug">
              {item.title}
            </h3>

            {/* AI 3-Bullet Summary Box */}
            <div className="p-4 md:p-5 rounded-2xl bg-neutral-950/70 border border-neutral-800/80 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-red-400" />
                  <span>vLLM Autonomous Key Takeaways</span>
                </span>
                <span className="text-[10px] font-mono text-neutral-500">Latency: 0.12s • AWQ-4bit</span>
              </div>

              <ul className="space-y-2">
                {item.ai_summary_bullets.map((bullet, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs md:text-sm text-neutral-300 leading-relaxed">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-2 flex-shrink-0" />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Character Reaction Bubble */}
            {item.character_reaction && (
              <div className="p-4 rounded-2xl bg-gradient-to-r from-purple-950/30 via-neutral-950 to-neutral-950 border border-purple-500/20 flex flex-col sm:flex-row items-start sm:items-center gap-4">
                <div className={`w-11 h-11 rounded-2xl bg-gradient-to-tr ${item.character_reaction.avatar_gradient} p-0.5 flex-shrink-0 shadow-lg`}>
                  <div className="w-full h-full rounded-2xl bg-neutral-950 flex items-center justify-center text-xs font-black text-white">
                    {item.character_reaction.character_name.split(" ").map((n) => n[0]).join("")}
                  </div>
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-purple-300">
                      {item.character_reaction.character_name}
                    </span>
                    <span className="text-[10px] font-mono text-neutral-500">
                      ({item.character_reaction.anime})
                    </span>
                    <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                      AI Character Commentary
                    </span>
                  </div>
                  <p className="italic text-xs md:text-sm text-neutral-200 mt-1 font-serif">
                    &ldquo;{item.character_reaction.quote}&rdquo;
                  </p>
                </div>
              </div>
            )}

            {/* Bottom Actions: Likes, Shares, View Anime */}
            <div className="flex items-center justify-between pt-2 border-t border-white/5 text-xs">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleLikeNews(item.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border transition-all ${
                    item.isLiked
                      ? "border-red-500/40 bg-red-500/10 text-red-400"
                      : "border-neutral-800 bg-neutral-800/40 text-neutral-400 hover:text-white"
                  }`}
                >
                  <Heart className={`w-3.5 h-3.5 ${item.isLiked ? "fill-red-400" : ""}`} />
                  <span className="font-semibold">{item.likes}</span>
                </button>

                <button
                  onClick={() => {
                    playClickSound();
                    navigator.clipboard.writeText(window.location.href);
                    alert("News briefing copied to clipboard!");
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-neutral-800 bg-neutral-800/40 text-neutral-400 hover:text-white transition-all"
                >
                  <Share2 className="w-3.5 h-3.5" />
                  <span>{item.shares}</span>
                </button>
              </div>

              {item.related_anime_title && onSelectAnime && (
                <button
                  onClick={() => {
                    playClickSound();
                    onSelectAnime(item.related_anime_title);
                  }}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-red-400 hover:text-red-300 transition-colors"
                >
                  <span>Explore {item.related_anime_title} in Catalog</span>
                  <ExternalLink className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
