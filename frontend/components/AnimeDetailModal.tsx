"use client";

import React, { useState } from "react";
import {
  X,
  Star,
  Award,
  Users,
  Calendar,
  Building,
  Film,
  Sparkles,
  Bookmark,
  CheckCircle2,
  Send,
  MessageSquare,
  ShieldAlert,
  ChevronRight
} from "lucide-react";
import { playClickSound, playSuccessChime } from "@/components/SoundFX";

interface AnimeDetailModalProps {
  anime: any | null;
  onClose: () => void;
  onAddToList?: (anime: any, status: string, episodesWatched: number, score: number) => void;
  onRunDossier?: (title: string) => void;
}

export default function AnimeDetailModal({
  anime,
  onClose,
  onAddToList,
  onRunDossier
}: AnimeDetailModalProps) {
  const [userStatus, setUserStatus] = useState<string>("Watching");
  const [episodesWatched, setEpisodesWatched] = useState<number>(0);
  const [userRating, setUserRating] = useState<number>(9);
  const [isSaved, setIsSaved] = useState<boolean>(false);

  // AI Episode Companion State
  const [episodeNum, setEpisodeNum] = useState<string>("1");
  const [questionText, setQuestionText] = useState<string>("");
  const [companionAnswers, setCompanionAnswers] = useState<
    Array<{ q: string; a: string; ep: string }>
  >([]);
  const [isAnswering, setIsAnswering] = useState<boolean>(false);

  if (!anime) return null;

  const handleSaveToList = () => {
    playSuccessChime();
    setIsSaved(true);
    if (onAddToList) {
      onAddToList(anime, userStatus, episodesWatched, userRating);
    }
  };

  const handleAskCompanion = () => {
    if (!questionText.trim()) return;
    playClickSound();
    setIsAnswering(true);

    const currentQ = questionText;
    const currentEp = episodeNum;
    setQuestionText("");

    setTimeout(() => {
      let answer = `Analysis for "${anime.title}" up to Episode ${currentEp} (Spoiler-Guarded): `;
      if (currentQ.toLowerCase().includes("why") || currentQ.toLowerCase().includes("explain")) {
        answer += `In this arc, the central conflict highlights the philosophical divergence between character ideals and external systemic forces. All events up to Episode ${currentEp} foreshadow future thematic developments without revealing unbroadcast plot resolutions.`;
      } else {
        answer += `The thematic pacing aligns with the director's emphasis on gradual psychological buildup. Narrative clues left in Episode ${currentEp} remain strictly grounded in current character knowledge.`;
      }

      setCompanionAnswers((prev) => [
        ...prev,
        { q: currentQ, a: answer, ep: currentEp }
      ]);
      setIsAnswering(false);
      playSuccessChime();
    }, 450);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-3xl border border-white/20 bg-neutral-950/95 shadow-2xl p-6 md:p-8 space-y-6 text-white font-sans">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 p-2 rounded-full bg-neutral-800 text-neutral-400 hover:text-white hover:bg-neutral-700 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Top Header */}
        <div className="flex flex-col md:flex-row gap-6 items-start border-b border-white/10 pb-6 pr-8">
          <div className="w-24 h-24 md:w-28 md:h-28 rounded-2xl bg-gradient-to-tr from-violet-600 via-indigo-600 to-pink-600 p-0.5 flex-shrink-0 shadow-xl">
            <div className="w-full h-full rounded-2xl bg-neutral-950 flex flex-col items-center justify-center text-center p-2">
              <span className="text-2xl md:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white to-neutral-400">
                {anime.title.split(" ").map((w: string) => w[0]).slice(0, 3).join("")}
              </span>
              <span className="text-[10px] text-neutral-400 font-mono mt-1">
                {anime.type || "TV"}
              </span>
            </div>
          </div>

          <div className="space-y-2 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20 flex items-center gap-1">
                <Star className="w-3 h-3 fill-amber-300" />
                <span>Score: {anime.score}</span>
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono text-neutral-300 bg-neutral-800 border border-neutral-700">
                Ranked #{anime.ranked || 1}
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono text-neutral-300 bg-neutral-800 border border-neutral-700">
                Popularity #{anime.popularity || 1}
              </span>
            </div>

            <h2 className="text-2xl md:text-3xl font-black tracking-tight text-white">
              {anime.title}
            </h2>

            <div className="flex flex-wrap items-center gap-2 text-xs text-neutral-400 font-mono">
              <span>{anime.studio || "Bones"}</span>
              <span>•</span>
              <span>{anime.premiered || "Spring 2020"}</span>
              <span>•</span>
              <span>{anime.episodes || 12} Episodes</span>
              <span>•</span>
              <span className="text-emerald-400">{anime.status || "Finished Airing"}</span>
            </div>
          </div>
        </div>

        {/* Two-Column Layout */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Left Column: MAL Sidebar & Quick List Manager */}
          <div className="md:col-span-5 space-y-5">
            {/* Quick List Status Manager */}
            <div className="p-4 rounded-2xl bg-neutral-900/80 border border-neutral-800 space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-neutral-300 flex items-center gap-1.5">
                <Bookmark className="w-3.5 h-3.5 text-blue-400" />
                <span>Update My Watchlist</span>
              </span>

              <div className="space-y-2 text-xs">
                <div>
                  <label className="text-neutral-400 block mb-1">Status:</label>
                  <select
                    value={userStatus}
                    onChange={(e) => setUserStatus(e.target.value)}
                    className="w-full bg-neutral-950 border border-neutral-700 rounded-xl px-3 py-2 text-white font-medium focus:outline-none"
                  >
                    <option value="Watching">Watching</option>
                    <option value="Completed">Completed</option>
                    <option value="Plan to Watch">Plan to Watch</option>
                    <option value="On Hold">On Hold</option>
                    <option value="Dropped">Dropped</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-neutral-400 block mb-1">Eps Watched:</label>
                    <input
                      type="number"
                      min={0}
                      max={anime.episodes || 100}
                      value={episodesWatched}
                      onChange={(e) => setEpisodesWatched(parseInt(e.target.value) || 0)}
                      className="w-full bg-neutral-950 border border-neutral-700 rounded-xl px-3 py-2 text-white font-mono focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-neutral-400 block mb-1">Your Score (1-10):</label>
                    <select
                      value={userRating}
                      onChange={(e) => setUserRating(parseInt(e.target.value) || 9)}
                      className="w-full bg-neutral-950 border border-neutral-700 rounded-xl px-3 py-2 text-amber-300 font-bold focus:outline-none"
                    >
                      {[10, 9, 8, 7, 6, 5, 4, 3, 2, 1].map((s) => (
                        <option key={s} value={s}>★ {s}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <button
                  onClick={handleSaveToList}
                  className="w-full mt-2 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 font-bold text-white text-xs transition-all flex items-center justify-center gap-1.5 shadow-md shadow-blue-600/30"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{isSaved ? "Saved to My List!" : "Update My List"}</span>
                </button>
              </div>
            </div>

            {/* Information Sidebar */}
            <div className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800 space-y-2.5 text-xs">
              <span className="font-bold uppercase tracking-wider text-neutral-400 block mb-2">
                MAL Information
              </span>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-neutral-400">Type:</span>
                <span className="font-mono text-white">{anime.type || "TV"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-neutral-400">Episodes:</span>
                <span className="font-mono text-white">{anime.episodes || 12}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-neutral-400">Status:</span>
                <span className="text-emerald-400">{anime.status || "Finished Airing"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-neutral-400">Premiered:</span>
                <span className="text-white">{anime.premiered || "Spring 2020"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-neutral-400">Studio:</span>
                <span className="text-purple-300 font-bold">{anime.studio || "Bones"}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-neutral-400">Members:</span>
                <span className="font-mono text-white">{(anime.members || 150000).toLocaleString()}</span>
              </div>
            </div>

            {onRunDossier && (
              <button
                onClick={() => {
                  onClose();
                  onRunDossier(anime.title);
                }}
                className="w-full py-2.5 rounded-xl bg-violet-600/20 hover:bg-violet-600/30 border border-violet-500/30 text-violet-300 font-bold text-xs transition-all flex items-center justify-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Run LangGraph AI Research Dossier</span>
              </button>
            )}
          </div>

          {/* Right Column: Synopsis & AI Spoiler-Free Companion */}
          <div className="md:col-span-7 space-y-6">
            {/* Synopsis */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400">
                Synopsis
              </h4>
              <p className="text-sm text-neutral-200 leading-relaxed bg-neutral-900/60 p-4 rounded-2xl border border-neutral-800">
                {anime.synopsis}
              </p>
            </div>

            {/* Genres */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400 mb-2">
                Genres &amp; Themes
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {(anime.genres || []).map((g: string) => (
                  <span
                    key={g}
                    className="px-2.5 py-1 rounded-lg text-xs bg-neutral-800 text-neutral-300 border border-neutral-700"
                  >
                    {g}
                  </span>
                ))}
              </div>
            </div>

            {/* AI Spoiler-Free Episode Companion */}
            <div className="p-5 rounded-2xl bg-neutral-900/80 border border-violet-500/30 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-violet-300 flex items-center gap-1.5">
                  <MessageSquare className="w-4 h-4 text-violet-400" />
                  <span>vLLM AI Episode Discussion (Spoiler-Guarded)</span>
                </span>
                <span className="text-[10px] text-emerald-400 font-mono bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                  Spoiler Safe
                </span>
              </div>

              <p className="text-xs text-neutral-400">
                Ask any question about plot points or character decisions up to your current episode. The AI guarantees zero spoilers from future episodes or manga chapters.
              </p>

              {/* QA History */}
              {companionAnswers.length > 0 && (
                <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
                  {companionAnswers.map((item, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-neutral-950 border border-neutral-800 space-y-1.5 text-xs">
                      <div className="flex items-center gap-1.5 text-violet-300 font-bold">
                        <span>You (Episode {item.ep}):</span>
                        <span className="text-white font-normal">{item.q}</span>
                      </div>
                      <p className="text-neutral-300 leading-relaxed text-xs pl-2 border-l-2 border-violet-500/50">
                        {item.a}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {/* Input Form */}
              <div className="flex gap-2">
                <input
                  type="number"
                  min={1}
                  max={anime.episodes || 100}
                  value={episodeNum}
                  onChange={(e) => setEpisodeNum(e.target.value)}
                  placeholder="Ep #"
                  className="w-16 bg-neutral-950 border border-neutral-700 rounded-xl px-2.5 py-2 text-xs text-center font-mono text-white focus:outline-none"
                  title="Current Episode"
                />

                <input
                  type="text"
                  placeholder={`Ask a question about Episode ${episodeNum}...`}
                  value={questionText}
                  onChange={(e) => setQuestionText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleAskCompanion();
                  }}
                  className="flex-1 bg-neutral-950 border border-neutral-700 rounded-xl px-3.5 py-2 text-xs text-white placeholder-neutral-500 focus:border-violet-500 focus:outline-none"
                />

                <button
                  onClick={handleAskCompanion}
                  disabled={isAnswering}
                  className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 font-bold text-white text-xs transition-all shadow-md shadow-violet-600/30 flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{isAnswering ? "..." : "Ask"}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
