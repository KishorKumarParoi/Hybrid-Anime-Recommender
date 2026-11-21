"use client";

import React, { useState, useMemo } from "react";
import { Award, Star, Users, Play, Plus, Check, ExternalLink, Filter, TrendingUp, Sparkles } from "lucide-react";
import { playClickSound, playSuccessChime } from "@/components/SoundFX";

interface AnimeRankingItem {
  id: number;
  title: string;
  genres: string[];
  score: number;
  episodes: number;
  year: number;
  members: number;
  ranked: number;
  type: string;
  studio?: string;
  season?: string;
  status?: string;
}

interface TopAnimeLeaderboardProps {
  animeList: AnimeRankingItem[];
  onSelectAnime?: (title: string) => void;
  onAddToList?: (anime: AnimeRankingItem) => void;
}

export default function TopAnimeLeaderboard({
  animeList,
  onSelectAnime,
  onAddToList
}: TopAnimeLeaderboardProps) {
  const [filterMode, setFilterMode] = useState<"All" | "Airing" | "TV" | "Movies" | "Popular">("All");
  const [addedIds, setAddedIds] = useState<Set<number>>(new Set());

  const rankedItems = useMemo(() => {
    let list = [...animeList];

    if (filterMode === "Airing") {
      list = list.filter((a) => a.status === "Currently Airing");
    } else if (filterMode === "TV") {
      list = list.filter((a) => a.type === "TV");
    } else if (filterMode === "Movies") {
      list = list.filter((a) => a.type === "Movie");
    } else if (filterMode === "Popular") {
      list.sort((a, b) => (b.members || 0) - (a.members || 0));
    } else {
      list.sort((a, b) => b.score - a.score);
    }

    return list.slice(0, 50);
  }, [animeList, filterMode]);

  const handleQuickAdd = (anime: AnimeRankingItem) => {
    playSuccessChime();
    setAddedIds((prev) => new Set(prev).add(anime.id));
    if (onAddToList) {
      onAddToList(anime);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header & Filter Pills */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-3xl bg-neutral-900/60 border border-white/10 backdrop-blur-xl">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30 mb-1">
            <Award className="w-3.5 h-3.5 text-amber-400" />
            <span>MAL Official Top Rankings</span>
          </div>
          <h2 className="text-2xl font-black text-white tracking-tight">
            Top Anime Leaderboard
          </h2>
          <p className="text-xs text-neutral-400 mt-0.5">
            Ranked dynamically by verified global user scores and community consensus.
          </p>
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {[
            { id: "All", label: "Top All-Time" },
            { id: "TV", label: "Top TV Series" },
            { id: "Movies", label: "Top Movies" },
            { id: "Airing", label: "Top Airing" },
            { id: "Popular", label: "Most Popular" }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                playClickSound();
                setFilterMode(tab.id as any);
              }}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                filterMode === tab.id
                  ? "bg-amber-500 text-neutral-950 font-bold shadow-lg shadow-amber-500/20"
                  : "bg-neutral-800/80 text-neutral-400 hover:text-white border border-neutral-700/60"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Rankings Table */}
      <div className="overflow-x-auto rounded-3xl border border-white/10 bg-neutral-900/40 backdrop-blur-xl shadow-2xl">
        <table className="w-full text-left text-sm text-neutral-200">
          <thead className="bg-neutral-950/80 text-xs font-mono uppercase text-neutral-400 border-b border-white/10">
            <tr>
              <th className="py-4 px-6 text-center w-20">Rank</th>
              <th className="py-4 px-6">Title &amp; Info</th>
              <th className="py-4 px-6 text-center w-36">MAL Score</th>
              <th className="py-4 px-6 text-center w-40">Community</th>
              <th className="py-4 px-6 text-right w-44">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 font-sans">
            {rankedItems.map((anime, idx) => {
              const rankNum = idx + 1;
              const isAdded = addedIds.has(anime.id);

              return (
                <tr key={anime.id} className="hover:bg-neutral-800/40 transition-colors group">
                  {/* Rank Column */}
                  <td className="py-4 px-6 text-center">
                    {rankNum === 1 ? (
                      <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-amber-400 text-neutral-950 font-black text-sm shadow-lg shadow-amber-400/40">
                        1
                      </span>
                    ) : rankNum === 2 ? (
                      <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-slate-300 text-neutral-950 font-black text-sm shadow-md">
                        2
                      </span>
                    ) : rankNum === 3 ? (
                      <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-amber-700 text-white font-black text-sm shadow-md">
                        3
                      </span>
                    ) : (
                      <span className="font-mono text-sm font-bold text-neutral-400">
                        #{rankNum}
                      </span>
                    )}
                  </td>

                  {/* Title & Metadata */}
                  <td className="py-4 px-6">
                    <div className="flex flex-col">
                      <button
                        onClick={() => onSelectAnime && onSelectAnime(anime.title)}
                        className="font-bold text-white group-hover:text-amber-300 text-left transition-colors flex items-center gap-1.5 line-clamp-1"
                      >
                        <span>{anime.title}</span>
                        <ExternalLink className="w-3 h-3 text-neutral-500 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                      </button>
                      <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-neutral-400 font-mono">
                        <span className="px-1.5 py-0.2 rounded bg-neutral-800 text-neutral-300 text-[10px]">
                          {anime.type || "TV"}
                        </span>
                        <span>•</span>
                        <span>{anime.episodes || 12} eps</span>
                        <span>•</span>
                        <span>{anime.studio || "Bones"}</span>
                        <span>•</span>
                        <span>{anime.season || "Spring"} {anime.year || 2020}</span>
                      </div>
                    </div>
                  </td>

                  {/* MAL Score */}
                  <td className="py-4 px-6 text-center">
                    <div className="inline-flex items-center gap-1 px-3 py-1 rounded-xl bg-amber-500/10 text-amber-300 border border-amber-500/20 font-black text-sm">
                      <Star className="w-3.5 h-3.5 fill-amber-300" />
                      <span>{anime.score}</span>
                    </div>
                  </td>

                  {/* Community Members */}
                  <td className="py-4 px-6 text-center font-mono text-xs text-neutral-400">
                    <div className="flex items-center justify-center gap-1.5">
                      <Users className="w-3.5 h-3.5 text-neutral-500" />
                      <span>{(anime.members || 150000).toLocaleString()}</span>
                    </div>
                  </td>

                  {/* Quick Add / Actions */}
                  <td className="py-4 px-6 text-right">
                    <button
                      onClick={() => handleQuickAdd(anime)}
                      disabled={isAdded}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                        isAdded
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-neutral-800 hover:bg-neutral-700 text-neutral-200 border border-neutral-700 hover:scale-105 active:scale-95"
                      }`}
                    >
                      {isAdded ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Added</span>
                        </>
                      ) : (
                        <>
                          <Plus className="w-3.5 h-3.5 text-amber-400" />
                          <span>Add to List</span>
                        </>
                      )}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
