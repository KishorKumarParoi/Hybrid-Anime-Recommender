"use client";

import React, { useState, useMemo } from "react";
import { Calendar, Sun, CloudSnow, Leaf, Flower2, Star, Users, Plus, Check, ExternalLink, Sparkles, Tv, Film } from "lucide-react";
import { playClickSound, playSuccessChime } from "@/components/SoundFX";

interface SeasonalAnimeItem {
  id: number;
  title: string;
  genres: string[];
  score: number;
  episodes: number;
  year: number;
  season?: string;
  premiered?: string;
  studio?: string;
  synopsis: string;
  type: string;
  members: number;
  status?: string;
}

interface SeasonalAnimeChartProps {
  animeList: SeasonalAnimeItem[];
  onSelectAnime?: (title: string) => void;
  onAddToList?: (anime: SeasonalAnimeItem) => void;
}

export default function SeasonalAnimeChart({
  animeList,
  onSelectAnime,
  onAddToList
}: SeasonalAnimeChartProps) {
  const [selectedSeason, setSelectedSeason] = useState<string>("Winter 2027");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [addedIds, setAddedIds] = useState<Set<number>>(new Set());

  const seasonsList = [
    { label: "Winter 2027", icon: CloudSnow },
    { label: "Fall 2026", icon: Leaf },
    { label: "Summer 2026", icon: Sun },
    { label: "Spring 2026", icon: Flower2 },
    { label: "Winter 2021", icon: CloudSnow },
    { label: "Spring 2011", icon: Flower2 },
    { label: "Spring 2009", icon: Flower2 }
  ];

  const seasonalItems = useMemo(() => {
    const [targetSeason, targetYearStr] = selectedSeason.split(" ");
    const targetYear = parseInt(targetYearStr);

    let filtered = animeList.filter((a) => {
      const matchYear = !targetYear || a.year === targetYear || (targetYear >= 2026 && a.year >= 2021);
      const matchSeason = !targetSeason || (a.season && a.season.toLowerCase() === targetSeason.toLowerCase());
      return matchYear && matchSeason;
    });

    if (typeFilter !== "ALL") {
      filtered = filtered.filter((a) => a.type === typeFilter);
    }

    if (filtered.length < 6) {
      // Fallback show top items if season count is small
      filtered = animeList.slice(0, 16);
    }

    return filtered.slice(0, 24);
  }, [animeList, selectedSeason, typeFilter]);

  const handleAdd = (anime: SeasonalAnimeItem) => {
    playSuccessChime();
    setAddedIds((prev) => new Set(prev).add(anime.id));
    if (onAddToList) {
      onAddToList(anime);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Seasonal Navigator Header */}
      <div className="rounded-3xl border border-white/10 bg-gradient-to-r from-emerald-950/40 via-teal-950/30 to-neutral-950/80 p-6 md:p-8 backdrop-blur-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 mb-2">
              <Calendar className="w-3.5 h-3.5 text-emerald-400" />
              <span>MAL Seasonal Broadcast Navigator</span>
            </div>
            <h2 className="text-3xl font-black text-white tracking-tight">
              Seasonal Anime <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">Archive &amp; Simulcasts</span>
            </h2>
            <p className="text-sm text-neutral-300 mt-1 max-w-xl">
              Browse broadcast schedules, studio releases, and upcoming seasons with real-time community anticipation scores.
            </p>
          </div>

          {/* Season Buttons */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 max-w-full">
            {seasonsList.map((item) => {
              const Icon = item.icon;
              const isSelected = selectedSeason === item.label;
              return (
                <button
                  key={item.label}
                  onClick={() => {
                    playClickSound();
                    setSelectedSeason(item.label);
                  }}
                  className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                    isSelected
                      ? "bg-emerald-500 text-neutral-950 shadow-lg shadow-emerald-500/30 scale-105"
                      : "bg-neutral-900/80 text-neutral-400 hover:text-white border border-neutral-800"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Sub-Filters: Type */}
        <div className="flex items-center gap-2 mt-6 pt-4 border-t border-white/5">
          <span className="text-xs font-mono text-neutral-400 mr-2">Category:</span>
          {["ALL", "TV", "Movie", "OVA"].map((t) => (
            <button
              key={t}
              onClick={() => {
                playClickSound();
                setTypeFilter(t);
              }}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                typeFilter === t
                  ? "bg-emerald-600 text-white"
                  : "bg-neutral-800 text-neutral-400 hover:text-white"
              }`}
            >
              {t === "ALL" ? "All Formats" : t}
            </button>
          ))}
        </div>
      </div>

      {/* Seasonal Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {seasonalItems.map((anime) => {
          const isAdded = addedIds.has(anime.id);

          return (
            <div
              key={anime.id}
              className="rounded-3xl border border-white/10 bg-neutral-900/60 p-6 backdrop-blur-xl hover:border-emerald-500/40 transition-all duration-300 shadow-xl flex flex-col justify-between group"
            >
              <div className="space-y-4">
                {/* Header row: Studio badge, Score, Season */}
                <div className="flex items-start justify-between gap-2">
                  <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-xs font-bold font-mono">
                    {anime.studio || "Studio"}
                  </span>

                  <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-300 border border-amber-500/20 text-xs font-black">
                    <Star className="w-3 h-3 fill-amber-300" />
                    <span>{anime.score}</span>
                  </div>
                </div>

                {/* Title */}
                <h3
                  onClick={() => onSelectAnime && onSelectAnime(anime.title)}
                  className="text-lg font-bold text-white group-hover:text-emerald-300 transition-colors cursor-pointer line-clamp-1"
                >
                  {anime.title}
                </h3>

                {/* Synopsis */}
                <p className="text-xs text-neutral-300 line-clamp-3 leading-relaxed">
                  {anime.synopsis}
                </p>

                {/* Genre Tags */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {(anime.genres || []).slice(0, 3).map((g) => (
                    <span
                      key={g}
                      className="px-2 py-0.5 rounded-md bg-neutral-800/80 text-neutral-300 border border-neutral-700/60 text-[10px] font-medium"
                    >
                      {g}
                    </span>
                  ))}
                </div>
              </div>

              {/* Bottom Info Bar */}
              <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-neutral-400 font-mono">
                  <span>{anime.type || "TV"}</span>
                  <span>•</span>
                  <span>{anime.episodes || 12} eps</span>
                  <span>•</span>
                  <span>{anime.year}</span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleAdd(anime)}
                    disabled={isAdded}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-bold transition-all ${
                      isAdded
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                        : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/20 active:scale-95"
                    }`}
                  >
                    {isAdded ? (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        <span>In List</span>
                      </>
                    ) : (
                      <>
                        <Plus className="w-3.5 h-3.5" />
                        <span>Add</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
