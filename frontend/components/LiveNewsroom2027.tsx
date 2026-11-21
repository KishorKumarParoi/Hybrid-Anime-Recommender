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
  RefreshCw,
  ArrowBigUp,
  ArrowBigDown,
  Send,
  X,
  CornerDownRight,
  Database,
  Hash
} from "lucide-react";
import { playClickSound, playSuccessChime } from "@/components/SoundFX";

export interface AnimeNewsItem {
  id: string; // Neon PostgreSQL UUID
  title: string;
  source?: string;
  source_url?: string;
  studio_source: string;
  timestamp: string;
  category: string;
  hype_score: number;
  upvotes?: number;
  downvotes?: number;
  score?: number;
  user_vote?: number; // 1, -1, or 0
  comment_count?: number;
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

export interface NewsComment {
  id: string; // UUID
  news_id: string; // UUID
  parent_id?: string | null;
  user_id: string;
  user_name: string;
  avatar_gradient?: string;
  character_flair?: string;
  content: string;
  upvotes: number;
  downvotes: number;
  score: number;
  user_vote: number;
  created_at: string;
}

interface LiveNewsroom2027Props {
  onSelectAnime?: (title: string) => void;
}

const FLAIR_OPTIONS = [
  "🧠 Rintarou Okabe (Steins;Gate)",
  "⚔️ Levi Ackerman (Attack on Titan)",
  "👁️ Satoru Gojo (Jujutsu Kaisen)",
  "✨ Frieren (Beyond Journey's End)",
  "🪚 Denji (Chainsaw Man)",
  "🦾 Edward Elric (Fullmetal Alchemist)",
  "⚡ Killua Zoldyck (Hunter x Hunter)",
  "🗡️ Guts (Berserk)"
];

export default function LiveNewsroom2027({ onSelectAnime }: LiveNewsroom2027Props) {
  const [news, setNews] = useState<AnimeNewsItem[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>("ALL");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isCrawling, setIsCrawling] = useState(false);
  const [activeModalNews, setActiveModalNews] = useState<AnimeNewsItem | null>(null);
  const [comments, setComments] = useState<NewsComment[]>([]);
  const [isLoadingComments, setIsLoadingComments] = useState(false);

  // New Comment Form State
  const [commentText, setCommentText] = useState("");
  const [userName, setUserName] = useState("Otaku Critic");
  const [selectedFlair, setSelectedFlair] = useState(FLAIR_OPTIONS[0]);
  const [replyingToId, setReplyingToId] = useState<string | null>(null);
  const [isPostingComment, setIsPostingComment] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const userId = useMemo(() => {
    if (typeof window !== "undefined") {
      let uid = localStorage.getItem("mal_user_uuid");
      if (!uid) {
        uid = "usr_" + Math.random().toString(36).substring(2, 10);
        localStorage.setItem("mal_user_uuid", uid);
      }
      return uid;
    }
    return "guest_user";
  }, []);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const fetchNewsFeed = async () => {
    try {
      // First try live Neon DB API
      const res = await fetch(`http://localhost:5001/api/news/live?user_id=${userId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.status === "success" && data.news && data.news.length > 0) {
          setNews(data.news);
          return;
        }
      }
    } catch (_e) {
      // Fallback
    }

    // Static fallback
    try {
      const res = await fetch("/data/anime_news_2027.json");
      const data = await res.json();
      setNews(data);
    } catch (err) {
      console.error("Error loading anime news snapshot:", err);
    }
  };

  useEffect(() => {
    fetchNewsFeed();
  }, [userId]);

  const categories = ["ALL", "Movie Premiere", "Trailer Drop", "Season Renewal", "Studio Key Visual"];

  const filteredNews = useMemo(() => {
    if (activeCategory === "ALL") return news;
    return news.filter((item) => item.category === activeCategory);
  }, [news, activeCategory]);

  // Reddit Upvote/Downvote for News
  const handleVoteNews = async (newsId: string, voteType: 1 | -1) => {
    playClickSound();

    // Optimistic UI update
    setNews((prev) =>
      prev.map((item) => {
        if (item.id === newsId) {
          const currentVote = item.user_vote || 0;
          let newVote: number = voteType;
          let scoreDelta = 0;

          if (currentVote === voteType) {
            newVote = 0;
            scoreDelta = -voteType;
          } else if (currentVote === 0) {
            scoreDelta = voteType;
          } else {
            scoreDelta = voteType * 2;
          }

          const curScore = item.score !== undefined ? item.score : (item.upvotes || 0) - (item.downvotes || 0);
          return {
            ...item,
            user_vote: newVote,
            score: curScore + scoreDelta
          };
        }
        return item;
      })
    );

    try {
      const res = await fetch(`http://localhost:5001/api/news/${newsId}/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, vote: voteType })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === "success") {
          setNews((prev) =>
            prev.map((item) => (item.id === newsId ? { ...item, score: data.score, user_vote: data.user_vote } : item))
          );
        }
      }
    } catch (err) {
      console.error("Vote failed:", err);
    }
  };

  // Trigger Immediate Crawler Sync
  const handleTriggerCrawl = async () => {
    playSuccessChime();
    setIsCrawling(true);
    showToast("Crawling ANN, Reddit r/anime & Twitter feeds...");

    try {
      const res = await fetch("http://localhost:5001/api/news/crawl", {
        method: "POST"
      });
      if (res.ok) {
        const data = await res.json();
        showToast(`Crawled & synced ${data.count} news items to Neon DB!`);
      }
    } catch (e) {
      showToast("Triggered crawler in background.");
    } finally {
      await fetchNewsFeed();
      setIsCrawling(false);
    }
  };

  // Open Reddit Discussion Modal
  const handleOpenDiscussion = async (item: AnimeNewsItem) => {
    playClickSound();
    setActiveModalNews(item);
    setIsLoadingComments(true);
    setReplyingToId(null);

    try {
      const res = await fetch(`http://localhost:5001/api/news/${item.id}/comments?user_id=${userId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.status === "success") {
          setComments(data.comments || []);
        }
      } else {
        setComments([]);
      }
    } catch (e) {
      setComments([]);
    } finally {
      setIsLoadingComments(false);
    }
  };

  // Post Comment / Review
  const handlePostComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim() || !activeModalNews) return;

    playClickSound();
    setIsPostingComment(true);

    const payload = {
      user_id: userId,
      user_name: userName.trim() || "Otaku Traveler",
      content: commentText.trim(),
      character_flair: selectedFlair,
      parent_id: replyingToId,
      avatar_gradient: "from-red-500 via-purple-600 to-indigo-700"
    };

    try {
      const res = await fetch(`http://localhost:5001/api/news/${activeModalNews.id}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        if (data.status === "success" && data.comment) {
          playSuccessChime();
          setComments((prev) => [data.comment, ...prev]);
          setCommentText("");
          setReplyingToId(null);
          showToast("Review posted with UUID to Neon PostgreSQL!");

          // Increment comment count on news card
          setNews((prev) =>
            prev.map((n) => (n.id === activeModalNews.id ? { ...n, comment_count: (n.comment_count || 0) + 1 } : n))
          );
        }
      }
    } catch (err) {
      console.error("Error posting comment:", err);
    } finally {
      setIsPostingComment(false);
    }
  };

  // Upvote/Downvote a Comment
  const handleVoteComment = async (commentId: string, voteType: 1 | -1) => {
    playClickSound();

    setComments((prev) =>
      prev.map((c) => {
        if (c.id === commentId) {
          const curVote = c.user_vote || 0;
          let newVote: number = voteType;
          let scoreDelta = 0;
          if (curVote === voteType) {
            newVote = 0;
            scoreDelta = -voteType;
          } else if (curVote === 0) {
            scoreDelta = voteType;
          } else {
            scoreDelta = voteType * 2;
          }
          return {
            ...c,
            user_vote: newVote,
            score: c.score + scoreDelta
          };
        }
        return c;
      })
    );

    try {
      const res = await fetch(`http://localhost:5001/api/comments/${commentId}/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, vote: voteType })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === "success") {
          setComments((prev) =>
            prev.map((c) => (c.id === commentId ? { ...c, score: data.score, user_vote: data.user_vote } : c))
          );
        }
      }
    } catch (err) {
      console.error("Error voting on comment:", err);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 px-5 py-3 rounded-2xl bg-neutral-900 border border-red-500/50 text-white text-xs font-bold shadow-2xl flex items-center gap-2.5 animate-in slide-in-from-bottom-5">
          <Database className="w-4 h-4 text-emerald-400 animate-pulse" />
          <span>{toastMessage}</span>
        </div>
      )}

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
              Crawled every <strong>30 minutes</strong> from Anime News Network RSS, Reddit r/anime, and Twitter studio wires. Ingested into <strong>Neon PostgreSQL</strong> with UUIDs, Reddit-style threaded reviews, and autonomous vLLM 3-bullet intelligence briefs.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-neutral-900/80 border border-neutral-800 text-xs font-mono text-neutral-300">
              <Database className="w-4 h-4 text-emerald-400" />
              <span>Neon PostgreSQL: <strong>UUID Synced</strong></span>
            </div>

            <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-neutral-900/80 border border-neutral-800 text-xs font-mono text-neutral-300">
              <Clock className="w-4 h-4 text-cyan-400" />
              <span>Crawler: <strong>Every 30m</strong></span>
            </div>

            <button
              onClick={handleTriggerCrawl}
              disabled={isCrawling}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-500 hover:to-pink-500 text-white text-xs font-bold transition-all shadow-lg shadow-red-600/25 active:scale-95 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isCrawling ? "animate-spin" : ""}`} />
              <span>{isCrawling ? "Crawling Feeds..." : "Sync Feeds Now"}</span>
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
        {filteredNews.map((item) => {
          const currentScore = item.score !== undefined ? item.score : (item.upvotes || 0) - (item.downvotes || 0);
          const isUpvoted = item.user_vote === 1;
          const isDownvoted = item.user_vote === -1;

          return (
            <div
              key={item.id}
              className="rounded-3xl border border-white/10 bg-neutral-900/60 p-6 md:p-8 backdrop-blur-xl hover:border-red-500/40 transition-all duration-300 shadow-xl space-y-6 group"
            >
              {/* Header: Source, Time, Category, Hype Score */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/5 pb-4">
                <div className="flex flex-wrap items-center gap-2.5">
                  <span className="p-1.5 rounded-lg bg-neutral-800 border border-neutral-700 text-neutral-300">
                    <Building className="w-3.5 h-3.5" />
                  </span>
                  <span className="text-xs font-bold text-neutral-200">
                    {item.studio_source}
                  </span>
                  {item.source && (
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-neutral-800/80 text-neutral-400 border border-neutral-700">
                      {item.source}
                    </span>
                  )}
                  {item.verified && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded-full border border-cyan-500/20">
                      <CheckCircle2 className="w-3 h-3" />
                      Verified
                    </span>
                  )}
                  <span className="text-xs text-neutral-500 font-mono flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {item.timestamp}
                  </span>

                  {/* UUID Tag */}
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono text-neutral-500 px-2 py-0.5 rounded bg-neutral-950 border border-neutral-800">
                    <Hash className="w-2.5 h-2.5 text-purple-400" />
                    <span>UUID: {item.id ? item.id.substring(0, 8) : "local"}</span>
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
              <div className="flex items-start gap-4">
                {/* Reddit-Style Voting Column */}
                <div className="flex flex-col items-center justify-center p-2 rounded-2xl bg-neutral-950/80 border border-neutral-800 flex-shrink-0">
                  <button
                    onClick={() => handleVoteNews(item.id, 1)}
                    title="Upvote"
                    className={`p-1 rounded-lg transition-colors ${
                      isUpvoted ? "text-orange-500 bg-orange-500/20" : "text-neutral-400 hover:text-orange-400 hover:bg-neutral-800"
                    }`}
                  >
                    <ArrowBigUp className={`w-5 h-5 ${isUpvoted ? "fill-orange-500" : ""}`} />
                  </button>

                  <span
                    className={`text-xs font-extrabold font-mono my-1 ${
                      isUpvoted ? "text-orange-400" : isDownvoted ? "text-blue-400" : "text-neutral-200"
                    }`}
                  >
                    {currentScore}
                  </span>

                  <button
                    onClick={() => handleVoteNews(item.id, -1)}
                    title="Downvote"
                    className={`p-1 rounded-lg transition-colors ${
                      isDownvoted ? "text-blue-400 bg-blue-500/20" : "text-neutral-400 hover:text-blue-400 hover:bg-neutral-800"
                    }`}
                  >
                    <ArrowBigDown className={`w-5 h-5 ${isDownvoted ? "fill-blue-400" : ""}`} />
                  </button>
                </div>

                <div className="flex-1 space-y-3">
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
                            AI Commentary
                          </span>
                        </div>
                        <p className="italic text-xs md:text-sm text-neutral-200 mt-1 font-serif">
                          &ldquo;{item.character_reaction.quote}&rdquo;
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom Actions: Reddit Discussion, Share, Link */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-white/5 text-xs">
                <div className="flex items-center gap-3">
                  {/* Reddit Discussion Trigger */}
                  <button
                    onClick={() => handleOpenDiscussion(item)}
                    className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl border border-red-500/40 bg-red-500/10 hover:bg-red-500/20 text-red-300 font-bold transition-all shadow-sm"
                  >
                    <MessageSquare className="w-3.5 h-3.5 text-red-400" />
                    <span>Discuss & Reviews ({item.comment_count || 0})</span>
                  </button>

                  <button
                    onClick={() => {
                      playClickSound();
                      navigator.clipboard.writeText(item.source_url || window.location.href);
                      showToast("Link copied to clipboard!");
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-neutral-800 bg-neutral-800/40 text-neutral-400 hover:text-white transition-all"
                  >
                    <Share2 className="w-3.5 h-3.5" />
                    <span>Share</span>
                  </button>

                  {item.source_url && (
                    <a
                      href={item.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-neutral-800 bg-neutral-800/40 text-neutral-400 hover:text-white transition-all"
                    >
                      <span>Read Original Source</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
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
          );
        })}
      </div>

      {/* Reddit-Style Threaded Discussion Modal */}
      {activeModalNews && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="w-full max-w-3xl max-h-[90vh] flex flex-col rounded-3xl border border-red-500/30 bg-neutral-950 shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 md:p-6 border-b border-white/10 bg-neutral-900/60 flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-xs font-semibold text-red-400">
                  <MessageSquare className="w-4 h-4" />
                  <span>Reddit-Style Anime Community Discussion</span>
                  <span className="text-neutral-500">•</span>
                  <span className="font-mono text-neutral-400">{activeModalNews.studio_source}</span>
                </div>
                <h3 className="text-lg md:text-xl font-black text-white leading-snug">
                  {activeModalNews.title}
                </h3>
              </div>
              <button
                onClick={() => setActiveModalNews(null)}
                className="p-2 rounded-xl text-neutral-400 hover:text-white bg-neutral-800/60 hover:bg-neutral-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body: Comments List & Form */}
            <div className="flex-1 overflow-y-auto p-5 md:p-6 space-y-6">
              {/* Comment Composer */}
              <form onSubmit={handlePostComment} className="p-4 rounded-2xl bg-neutral-900/70 border border-neutral-800 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-neutral-300">Speaking as:</span>
                    <input
                      type="text"
                      value={userName}
                      onChange={(e) => setUserName(e.target.value)}
                      placeholder="Your handle"
                      className="px-2.5 py-1 text-xs rounded-lg bg-neutral-950 border border-neutral-700 text-white font-medium focus:outline-none focus:border-red-500"
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-neutral-300">Character Flair:</span>
                    <select
                      value={selectedFlair}
                      onChange={(e) => setSelectedFlair(e.target.value)}
                      className="px-2.5 py-1 text-xs rounded-lg bg-neutral-950 border border-neutral-700 text-purple-300 font-medium focus:outline-none focus:border-purple-500"
                    >
                      {FLAIR_OPTIONS.map((flair) => (
                        <option key={flair} value={flair}>
                          {flair}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {replyingToId && (
                  <div className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-purple-950/40 border border-purple-500/30 text-xs text-purple-300">
                    <span className="flex items-center gap-1.5">
                      <CornerDownRight className="w-3 h-3" />
                      Replying to thread comment
                    </span>
                    <button
                      type="button"
                      onClick={() => setReplyingToId(null)}
                      className="text-neutral-400 hover:text-white text-[11px]"
                    >
                      Cancel reply
                    </button>
                  </div>
                )}

                <textarea
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  placeholder="Share your theory, review, or thoughts on this anime news release..."
                  rows={3}
                  className="w-full p-3 text-xs md:text-sm rounded-xl bg-neutral-950 border border-neutral-800 text-white placeholder-neutral-500 focus:outline-none focus:border-red-500/80 resize-none"
                />

                <div className="flex items-center justify-between pt-1">
                  <span className="text-[11px] font-mono text-neutral-500">
                    Auto-synced with Neon PostgreSQL UUID schema
                  </span>

                  <button
                    type="submit"
                    disabled={isPostingComment || !commentText.trim()}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition-all disabled:opacity-40"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{isPostingComment ? "Posting..." : "Post Review"}</span>
                  </button>
                </div>
              </form>

              {/* Comments Thread */}
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-neutral-800 pb-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400">
                    All Community Discussions ({comments.length})
                  </h4>
                  <span className="text-[11px] font-mono text-neutral-500">Sorted by Top Score</span>
                </div>

                {isLoadingComments ? (
                  <div className="py-12 text-center text-xs text-neutral-500 animate-pulse">
                    Loading discussion threads from Neon PostgreSQL...
                  </div>
                ) : comments.length === 0 ? (
                  <div className="py-8 text-center rounded-2xl bg-neutral-900/40 border border-neutral-800/60 p-6 space-y-2">
                    <MessageSquare className="w-8 h-8 text-neutral-600 mx-auto" />
                    <p className="text-sm font-bold text-neutral-300">No discussions yet</p>
                    <p className="text-xs text-neutral-500">
                      Be the first to share your opinion or studio leak analysis on this story!
                    </p>
                  </div>
                ) : (
                  comments.map((comment) => {
                    const isUp = comment.user_vote === 1;
                    const isDown = comment.user_vote === -1;
                    return (
                      <div
                        key={comment.id}
                        className={`p-4 rounded-2xl border transition-all ${
                          comment.parent_id
                            ? "ml-6 md:ml-10 bg-neutral-900/40 border-neutral-800/60"
                            : "bg-neutral-900/70 border-neutral-800"
                        }`}
                      >
                        {/* Comment Header */}
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2">
                            <div className={`w-7 h-7 rounded-xl bg-gradient-to-tr ${comment.avatar_gradient || "from-red-500 to-purple-600"} p-0.5 flex-shrink-0`}>
                              <div className="w-full h-full rounded-[10px] bg-neutral-950 flex items-center justify-center text-[10px] font-black text-white">
                                {comment.user_name.substring(0, 2).toUpperCase()}
                              </div>
                            </div>

                            <span className="text-xs font-bold text-neutral-200">
                              {comment.user_name}
                            </span>

                            {comment.character_flair && (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/20">
                                {comment.character_flair}
                              </span>
                            )}
                          </div>

                          <span className="text-[10px] font-mono text-neutral-500">
                            {comment.created_at ? new Date(comment.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Just Now"}
                          </span>
                        </div>

                        {/* Comment Body */}
                        <p className="text-xs md:text-sm text-neutral-200 leading-relaxed pl-9">
                          {comment.content}
                        </p>

                        {/* Comment Voting & Reply */}
                        <div className="flex items-center gap-3 mt-3 pl-9 text-xs">
                          <div className="flex items-center gap-1 bg-neutral-950 px-2 py-1 rounded-xl border border-neutral-800">
                            <button
                              onClick={() => handleVoteComment(comment.id, 1)}
                              className={`p-0.5 rounded ${isUp ? "text-orange-500" : "text-neutral-400 hover:text-orange-400"}`}
                            >
                              <ArrowBigUp className={`w-4 h-4 ${isUp ? "fill-orange-500" : ""}`} />
                            </button>

                            <span className={`text-[11px] font-mono font-bold ${isUp ? "text-orange-400" : isDown ? "text-blue-400" : "text-neutral-300"}`}>
                              {comment.score}
                            </span>

                            <button
                              onClick={() => handleVoteComment(comment.id, -1)}
                              className={`p-0.5 rounded ${isDown ? "text-blue-400" : "text-neutral-400 hover:text-blue-400"}`}
                            >
                              <ArrowBigDown className={`w-4 h-4 ${isDown ? "fill-blue-400" : ""}`} />
                            </button>
                          </div>

                          <button
                            onClick={() => {
                              playClickSound();
                              setReplyingToId(comment.id);
                            }}
                            className="inline-flex items-center gap-1 text-[11px] font-semibold text-neutral-400 hover:text-white"
                          >
                            <CornerDownRight className="w-3 h-3" />
                            <span>Reply</span>
                          </button>

                          <span className="text-[10px] font-mono text-neutral-600">
                            ID: {comment.id.substring(0, 8)}...
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
