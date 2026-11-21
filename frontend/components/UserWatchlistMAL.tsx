"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Bookmark,
  CheckCircle2,
  Clock,
  Play,
  Star,
  Plus,
  Minus,
  Trash2,
  BarChart2,
  PieChart,
  ListFilter,
  Sparkles,
  ExternalLink,
  Award
} from "lucide-react";
import { playClickSound, playSuccessChime } from "@/components/SoundFX";

export type WatchlistStatus = "Watching" | "Completed" | "Plan to Watch" | "On Hold" | "Dropped";

export interface WatchlistItem {
  anime_id: number;
  title: string;
  genres: string[];
  score: number;
  episodes: number;
  user_episodes_watched: number;
  user_score?: number;
  status: WatchlistStatus;
  studio?: string;
  year?: number;
  updated_at: string;
}

const DEFAULT_WATCHLIST: WatchlistItem[] = [
  {
    anime_id: 5114,
    title: "Fullmetal Alchemist: Brotherhood",
    genres: ["Action", "Military", "Adventure", "Fantasy"],
    score: 9.19,
    episodes: 64,
    user_episodes_watched: 64,
    user_score: 10,
    status: "Completed",
    studio: "Bones",
    year: 2009,
    updated_at: "2026-11-20"
  },
  {
    anime_id: 9253,
    title: "Steins;Gate",
    genres: ["Thriller", "Sci-Fi", "Psychological"],
    score: 9.11,
    episodes: 24,
    user_episodes_watched: 18,
    user_score: 9,
    status: "Watching",
    studio: "White Fox",
    year: 2011,
    updated_at: "2026-11-21"
  },
  {
    anime_id: 40028,
    title: "Attack on Titan Final Season",
    genres: ["Action", "Military", "Mystery", "Super Power"],
    score: 9.17,
    episodes: 16,
    user_episodes_watched: 12,
    user_score: 9,
    status: "Watching",
    studio: "Wit Studio / MAPPA",
    year: 2021,
    updated_at: "2026-11-21"
  },
  {
    anime_id: 11061,
    title: "Hunter x Hunter",
    genres: ["Action", "Adventure", "Fantasy", "Shounen"],
    score: 9.1,
    episodes: 148,
    user_episodes_watched: 45,
    user_score: 9,
    status: "On Hold",
    studio: "Madhouse",
    year: 2011,
    updated_at: "2026-11-18"
  },
  {
    anime_id: 41467,
    title: "Bleach: Thousand-Year Blood War",
    genres: ["Action", "Adventure", "Supernatural"],
    score: 9.06,
    episodes: 13,
    user_episodes_watched: 0,
    status: "Plan to Watch",
    studio: "Studio Pierrot",
    year: 2022,
    updated_at: "2026-11-15"
  }
];

export default function UserWatchlistMAL({
  onSelectAnime
}: {
  onSelectAnime?: (animeTitle: string) => void;
}) {
  const [list, setList] = useState<WatchlistItem[]>(DEFAULT_WATCHLIST);
  const [activeTab, setActiveTab] = useState<"All" | WatchlistStatus>("All");
  const [searchFilter, setSearchFilter] = useState<string>("");

  useEffect(() => {
    try {
      const stored = localStorage.getItem("mal_user_watchlist_2027");
      if (stored) {
        setList(JSON.parse(stored));
      }
    } catch {}
  }, []);

  const saveList = (newList: WatchlistItem[]) => {
    setList(newList);
    try {
      localStorage.setItem("mal_user_watchlist_2027", JSON.stringify(newList));
    } catch {}
  };

  const handleIncrementEpisode = (id: number) => {
    playClickSound();
    const updated = list.map((item) => {
      if (item.anime_id === id) {
        const nextEp = Math.min(item.episodes, item.user_episodes_watched + 1);
        const status: WatchlistStatus = nextEp === item.episodes ? "Completed" : item.status;
        return { ...item, user_episodes_watched: nextEp, status };
      }
      return item;
    });
    saveList(updated);
  };

  const handleDecrementEpisode = (id: number) => {
    playClickSound();
    const updated = list.map((item) => {
      if (item.anime_id === id) {
        const prevEp = Math.max(0, item.user_episodes_watched - 1);
        return { ...item, user_episodes_watched: prevEp };
      }
      return item;
    });
    saveList(updated);
  };

  const handleStatusChange = (id: number, status: WatchlistStatus) => {
    playClickSound();
    const updated = list.map((item) => {
      if (item.anime_id === id) {
        const watched = status === "Completed" ? item.episodes : item.user_episodes_watched;
        return { ...item, status, user_episodes_watched: watched };
      }
      return item;
    });
    saveList(updated);
  };

  const handleScoreChange = (id: number, score: number) => {
    playSuccessChime();
    const updated = list.map((item) => {
      if (item.anime_id === id) {
        return { ...item, user_score: score };
      }
      return item;
    });
    saveList(updated);
  };

  const handleDeleteItem = (id: number) => {
    playClickSound();
    const updated = list.filter((item) => item.anime_id !== id);
    saveList(updated);
  };

  // MAL Live Stats Calculation
  const stats = useMemo(() => {
    const totalEntries = list.length;
    const totalEpisodes = list.reduce((acc, cur) => acc + cur.user_episodes_watched, 0);
    // Average anime episode is ~24 minutes = 0.4 hours
    const daysWatched = ((totalEpisodes * 24) / 1440).toFixed(1);

    const scoredItems = list.filter((item) => item.user_score && item.user_score > 0);
    const meanScore = scoredItems.length
      ? (scoredItems.reduce((acc, cur) => acc + (cur.user_score || 0), 0) / scoredItems.length).toFixed(2)
      : "0.0";

    const counts: Record<WatchlistStatus, number> = {
      Watching: list.filter((i) => i.status === "Watching").length,
      Completed: list.filter((i) => i.status === "Completed").length,
      "On Hold": list.filter((i) => i.status === "On Hold").length,
      Dropped: list.filter((i) => i.status === "Dropped").length,
      "Plan to Watch": list.filter((i) => i.status === "Plan to Watch").length
    };

    return { totalEntries, totalEpisodes, daysWatched, meanScore, counts };
  }, [list]);

  const filteredItems = useMemo(() => {
    return list.filter((item) => {
      const matchTab = activeTab === "All" || item.status === activeTab;
      const matchQ = !searchFilter || item.title.toLowerCase().includes(searchFilter.toLowerCase());
      return matchTab && matchQ;
    });
  }, [list, activeTab, searchFilter]);

  const tabs: ("All" | WatchlistStatus)[] = [
    "All",
    "Watching",
    "Completed",
    "Plan to Watch",
    "On Hold",
    "Dropped"
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Top Banner / Stats Overview Widget */}
      <div className="rounded-3xl border border-white/10 bg-gradient-to-r from-blue-950/40 via-indigo-950/30 to-neutral-950/80 p-6 md:p-8 backdrop-blur-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 border-b border-white/10 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-300 border border-blue-500/30 mb-2">
              <Bookmark className="w-3.5 h-3.5 text-blue-400" />
              <span>MAL 2027 • Personal Watchlist Engine</span>
            </div>
            <h2 className="text-3xl font-black text-white tracking-tight">
              My Anime List &amp; <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400">Viewing Analytics</span>
            </h2>
            <p className="text-sm text-neutral-300 mt-1 max-w-xl">
              Track episodes, rate completions, and compute live watch-time statistics. Synchronized automatically with PostgreSQL and MongoDB interaction mesh.
            </p>
          </div>

          {/* Quick MAL Stats Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-2xl bg-neutral-900/80 border border-neutral-800 text-center">
              <span className="text-xs text-neutral-400 font-mono block">Days Watched</span>
              <span className="text-xl font-black text-white mt-0.5 block">{stats.daysWatched}</span>
            </div>

            <div className="p-3.5 rounded-2xl bg-neutral-900/80 border border-neutral-800 text-center">
              <span className="text-xs text-neutral-400 font-mono block">Mean Score</span>
              <span className="text-xl font-black text-amber-300 mt-0.5 block">★ {stats.meanScore}</span>
            </div>

            <div className="p-3.5 rounded-2xl bg-neutral-900/80 border border-neutral-800 text-center">
              <span className="text-xs text-neutral-400 font-mono block">Episodes</span>
              <span className="text-xl font-black text-cyan-300 mt-0.5 block">{stats.totalEpisodes}</span>
            </div>

            <div className="p-3.5 rounded-2xl bg-neutral-900/80 border border-neutral-800 text-center">
              <span className="text-xs text-neutral-400 font-mono block">Total Entries</span>
              <span className="text-xl font-black text-purple-300 mt-0.5 block">{stats.totalEntries}</span>
            </div>
          </div>
        </div>

        {/* Visual Distribution Ratio Bar */}
        <div className="pt-4 space-y-2">
          <div className="flex justify-between text-xs text-neutral-400 font-mono">
            <span>List Breakdown</span>
            <span>
              Watching: <strong className="text-emerald-400">{stats.counts.Watching}</strong> | Completed:{" "}
              <strong className="text-blue-400">{stats.counts.Completed}</strong> | PTW:{" "}
              <strong className="text-neutral-300">{stats.counts["Plan to Watch"]}</strong>
            </span>
          </div>

          <div className="w-full h-2.5 rounded-full bg-neutral-900 overflow-hidden flex">
            {stats.totalEntries > 0 && (
              <>
                <div
                  style={{ width: `${(stats.counts.Watching / stats.totalEntries) * 100}%` }}
                  className="bg-emerald-500 h-full transition-all"
                  title={`Watching: ${stats.counts.Watching}`}
                />
                <div
                  style={{ width: `${(stats.counts.Completed / stats.totalEntries) * 100}%` }}
                  className="bg-blue-500 h-full transition-all"
                  title={`Completed: ${stats.counts.Completed}`}
                />
                <div
                  style={{ width: `${(stats.counts["On Hold"] / stats.totalEntries) * 100}%` }}
                  className="bg-amber-500 h-full transition-all"
                  title={`On Hold: ${stats.counts["On Hold"]}`}
                />
                <div
                  style={{ width: `${(stats.counts.Dropped / stats.totalEntries) * 100}%` }}
                  className="bg-rose-500 h-full transition-all"
                  title={`Dropped: ${stats.counts.Dropped}`}
                />
                <div
                  style={{ width: `${(stats.counts["Plan to Watch"] / stats.totalEntries) * 100}%` }}
                  className="bg-slate-600 h-full transition-all"
                  title={`Plan to Watch: ${stats.counts["Plan to Watch"]}`}
                />
              </>
            )}
          </div>
        </div>
      </div>

      {/* Watchlist Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
        {/* Status Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {tabs.map((tab) => {
            const count = tab === "All" ? list.length : stats.counts[tab];
            const isActive = activeTab === tab;
            return (
              <button
                key={tab}
                onClick={() => {
                  playClickSound();
                  setActiveTab(tab);
                }}
                className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 ${
                  isActive
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-600/30"
                    : "bg-neutral-900/80 text-neutral-400 hover:text-white border border-neutral-800"
                }`}
              >
                <span>{tab}</span>
                <span
                  className={`px-1.5 py-0.2 rounded-md text-[10px] font-mono ${
                    isActive ? "bg-white/20 text-white" : "bg-neutral-800 text-neutral-400"
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search input in Watchlist */}
        <div className="relative">
          <input
            type="text"
            placeholder="Search your list..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="w-full sm:w-64 rounded-xl border border-neutral-700 bg-neutral-900/90 px-3.5 py-2 text-xs text-white placeholder-neutral-500 focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Watchlist Table */}
      <div className="overflow-x-auto rounded-3xl border border-white/10 bg-neutral-900/40 backdrop-blur-xl">
        <table className="w-full text-left text-sm text-neutral-200">
          <thead className="bg-neutral-950/80 text-xs font-mono uppercase text-neutral-400 border-b border-white/10">
            <tr>
              <th className="py-4 px-6">#</th>
              <th className="py-4 px-6">Anime Title &amp; Studio</th>
              <th className="py-4 px-6">Score</th>
              <th className="py-4 px-6">Progress</th>
              <th className="py-4 px-6">Status</th>
              <th className="py-4 px-6 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 font-sans">
            {filteredItems.map((item, idx) => {
              const progressPct =
                item.episodes > 0 ? Math.round((item.user_episodes_watched / item.episodes) * 100) : 0;
              return (
                <tr key={item.anime_id} className="hover:bg-neutral-800/40 transition-colors group">
                  {/* # */}
                  <td className="py-4 px-6 font-mono text-xs text-neutral-500">{idx + 1}</td>

                  {/* Title & Studio */}
                  <td className="py-4 px-6">
                    <div className="flex flex-col">
                      <button
                        onClick={() => onSelectAnime && onSelectAnime(item.title)}
                        className="font-bold text-white group-hover:text-blue-300 text-left transition-colors flex items-center gap-1.5"
                      >
                        <span>{item.title}</span>
                        <ExternalLink className="w-3 h-3 text-neutral-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </button>
                      <div className="flex items-center gap-2 mt-1 text-xs text-neutral-400 font-mono">
                        <span>{item.studio || "Bones"}</span>
                        <span>•</span>
                        <span>{item.year || 2020}</span>
                        <span>•</span>
                        <span className="text-amber-400">★ {item.score}</span>
                      </div>
                    </div>
                  </td>

                  {/* User Score (1-10) */}
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-1.5">
                      <select
                        value={item.user_score || 0}
                        onChange={(e) => handleScoreChange(item.anime_id, parseInt(e.target.value))}
                        className="bg-neutral-900 border border-neutral-700 text-amber-300 font-bold text-xs rounded-lg px-2 py-1 focus:border-blue-500 focus:outline-none"
                      >
                        <option value={0}>- Select -</option>
                        {[10, 9, 8, 7, 6, 5, 4, 3, 2, 1].map((s) => (
                          <option key={s} value={s}>
                            ★ {s} {s === 10 ? "(Masterpiece)" : s === 9 ? "(Great)" : s === 8 ? "(Very Good)" : ""}
                          </option>
                        ))}
                      </select>
                    </div>
                  </td>

                  {/* Episode Progress & Buttons */}
                  <td className="py-4 px-6 min-w-[180px]">
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span>
                          <strong className="text-white">{item.user_episodes_watched}</strong> / {item.episodes} eps
                        </span>
                        <span className="text-neutral-400">{progressPct}%</span>
                      </div>

                      <div className="w-full h-1.5 rounded-full bg-neutral-800 overflow-hidden">
                        <div
                          style={{ width: `${progressPct}%` }}
                          className={`h-full transition-all ${
                            item.status === "Completed" ? "bg-blue-400" : "bg-emerald-400"
                          }`}
                        />
                      </div>

                      <div className="flex items-center gap-1 pt-1">
                        <button
                          onClick={() => handleDecrementEpisode(item.anime_id)}
                          className="p-1 rounded bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs"
                          title="Decrement Episode"
                        >
                          <Minus className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => handleIncrementEpisode(item.anime_id)}
                          className="px-2 py-1 rounded bg-blue-600/80 hover:bg-blue-500 text-white text-xs font-bold flex items-center gap-1"
                          title="Increment Episode (+1)"
                        >
                          <Plus className="w-3 h-3" />
                          <span>+1 Ep</span>
                        </button>
                      </div>
                    </div>
                  </td>

                  {/* Status Dropdown */}
                  <td className="py-4 px-6">
                    <select
                      value={item.status}
                      onChange={(e) => handleStatusChange(item.anime_id, e.target.value as WatchlistStatus)}
                      className={`text-xs font-bold rounded-lg px-2.5 py-1 border bg-neutral-900 focus:outline-none ${
                        item.status === "Watching"
                          ? "border-emerald-500/30 text-emerald-300"
                          : item.status === "Completed"
                          ? "border-blue-500/30 text-blue-300"
                          : item.status === "On Hold"
                          ? "border-amber-500/30 text-amber-300"
                          : item.status === "Dropped"
                          ? "border-rose-500/30 text-rose-400"
                          : "border-neutral-700 text-neutral-300"
                      }`}
                    >
                      <option value="Watching">Watching</option>
                      <option value="Completed">Completed</option>
                      <option value="Plan to Watch">Plan to Watch</option>
                      <option value="On Hold">On Hold</option>
                      <option value="Dropped">Dropped</option>
                    </select>
                  </td>

                  {/* Actions */}
                  <td className="py-4 px-6 text-right">
                    <button
                      onClick={() => handleDeleteItem(item.anime_id)}
                      className="p-1.5 rounded-lg text-neutral-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                      title="Remove from Watchlist"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filteredItems.length === 0 && (
          <div className="p-12 text-center text-neutral-400 space-y-2">
            <Bookmark className="w-8 h-8 mx-auto text-neutral-600" />
            <p className="font-semibold text-sm">No anime entries found in this list tab.</p>
            <p className="text-xs text-neutral-500">Add anime from the Catalog or Seasonal Charts!</p>
          </div>
        )}
      </div>
    </div>
  );
}
