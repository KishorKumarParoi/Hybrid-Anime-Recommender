"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Sparkles, UserCheck, Quote, Brain, Award, Compass, Zap, CheckCircle2, ChevronRight, Shuffle } from "lucide-react";
import { playClickSound, playSuccessChime } from "@/components/SoundFX";

export interface CharacterProfile {
  id: string;
  name: string;
  title: string;
  anime: string;
  mbti: string;
  quote: string;
  traits: string[];
  vector: number[]; // [Action, Psychological, Sci-Fi, World-Building]
  bio: string;
  avatar_gradient: string;
  archetype: string;
  recommended_genres: string[];
  badge_color: string;
}

interface CharacterMatcherProps {
  userVector: number[];
  onAdoptVector?: (vector: number[], charName: string) => void;
  allAnime?: any[];
}

export default function CharacterMatcher({
  userVector,
  onAdoptVector,
  allAnime = []
}: CharacterMatcherProps) {
  const [characters, setCharacters] = useState<CharacterProfile[]>([]);
  const [selectedCharId, setSelectedCharId] = useState<string | null>(null);
  const [filterMbti, setFilterMbti] = useState<string>("ALL");

  useEffect(() => {
    fetch("/data/anime_characters.json")
      .then((res) => res.json())
      .then((data: CharacterProfile[]) => {
        setCharacters(data);
      })
      .catch((err) => console.error("Error loading character profiles:", err));
  }, []);

  // Compute Cosine Similarity between userVector and all characters
  const matchedList = useMemo(() => {
    if (!characters.length) return [];

    const normU = Math.sqrt(userVector.reduce((acc, v) => acc + v * v, 0)) || 1.0;

    const scored = characters.map((char) => {
      const normC = Math.sqrt(char.vector.reduce((acc, v) => acc + v * v, 0)) || 1.0;
      let dot = 0;
      for (let i = 0; i < 4; i++) {
        dot += (userVector[i] || 0) * (char.vector[i] || 0);
      }
      const cosSim = Math.max(0, Math.min(1, dot / (normU * normC)));
      const matchPercentage = Math.round(cosSim * 1000) / 10;
      return {
        ...char,
        matchPercentage,
        similarity: cosSim
      };
    });

    return scored.sort((a, b) => b.similarity - a.similarity);
  }, [characters, userVector]);

  const activePersona = useMemo(() => {
    if (!matchedList.length) return null;
    if (selectedCharId) {
      return matchedList.find((c) => c.id === selectedCharId) || matchedList[0];
    }
    return matchedList[0];
  }, [matchedList, selectedCharId]);

  // Curated anime recommendations based on the active persona's recommended genres
  const personaAnime = useMemo(() => {
    if (!activePersona || !allAnime.length) return [];
    const targetGenres = new Set(activePersona.recommended_genres.map((g) => g.toLowerCase()));

    const candidates = allAnime.filter((a) => {
      const gList = (a.genres || []).map((g: string) => g.toLowerCase());
      return gList.some((g: string) => targetGenres.has(g));
    });

    return candidates.slice(0, 4);
  }, [activePersona, allAnime]);

  const dimensionLabels = ["Action Intensity", "Psychological Thrill", "Sci-Fi Concepts", "World-Building"];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Top Banner / Explainer */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-purple-950/40 via-indigo-950/20 to-neutral-900/40 border border-purple-500/20 backdrop-blur-xl">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/30 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>AI Neural Persona Assignment</span>
          </div>
          <h2 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            Your Anime Character <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-amber-300">Alter Ego</span>
          </h2>
          <p className="text-sm text-neutral-400 mt-1 max-w-2xl">
            Our recommendation engine continuously projects your taste vector against high-dimensional cognitive profiles of iconic anime figures. Meet the character who shares your psychological and narrative wavelength.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              playClickSound();
              if (matchedList.length > 0) {
                const randomIdx = Math.floor(Math.random() * matchedList.length);
                const randomChar = matchedList[randomIdx];
                setSelectedCharId(randomChar.id);
                if (onAdoptVector) {
                  onAdoptVector(randomChar.vector, randomChar.name);
                }
              }
            }}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-neutral-800/80 hover:bg-neutral-700/80 text-neutral-200 border border-neutral-700/60 transition-all hover:scale-105 active:scale-95"
          >
            <Shuffle className="w-4 h-4 text-purple-400" />
            <span>Shuffle Persona</span>
          </button>
        </div>
      </div>

      {/* Main Matched Persona Hero Showcase */}
      {activePersona && (
        <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-neutral-900/60 backdrop-blur-2xl shadow-2xl p-6 md:p-8">
          <div className={`absolute top-0 right-0 w-96 h-96 bg-gradient-to-br ${activePersona.avatar_gradient} opacity-15 blur-3xl rounded-full pointer-events-none`} />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Left Column: Avatar & Match Badge */}
            <div className="lg:col-span-4 flex flex-col items-center text-center">
              <div className="relative group">
                <div className={`w-40 h-40 md:w-48 md:h-48 rounded-full bg-gradient-to-tr ${activePersona.avatar_gradient} p-1 shadow-2xl shadow-purple-500/20 flex items-center justify-center transition-transform group-hover:scale-105 duration-300`}>
                  <div className="w-full h-full rounded-full bg-neutral-950 flex flex-col items-center justify-center p-4 text-center">
                    <span className="text-4xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white to-neutral-400">
                      {activePersona.name.split(" ").map((n) => n[0]).join("")}
                    </span>
                    <span className="text-xs uppercase tracking-widest text-neutral-400 mt-1 font-mono">
                      {activePersona.archetype}
                    </span>
                  </div>
                </div>
                <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-extrabold text-xs tracking-wider shadow-lg shadow-purple-500/40 border border-white/20 whitespace-nowrap">
                  {activePersona.matchPercentage}% SOULMATE MATCH
                </div>
              </div>

              <h3 className="text-2xl font-black text-white mt-6 tracking-tight">
                {activePersona.name}
              </h3>
              <p className="text-xs text-purple-400 font-mono mt-0.5">
                {activePersona.anime}
              </p>
              <div className="flex items-center gap-2 mt-3">
                <span className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  MBTI: {activePersona.mbti}
                </span>
                <span className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-neutral-800 text-neutral-300 border border-neutral-700">
                  {activePersona.archetype}
                </span>
              </div>
            </div>

            {/* Right Column: Quotes, Psychological Profiling & Vector Telemetry */}
            <div className="lg:col-span-8 space-y-6">
              {/* Quote Block */}
              <div className="p-4 md:p-5 rounded-2xl bg-neutral-950/60 border border-neutral-800 relative">
                <Quote className="w-6 h-6 text-purple-500/40 absolute top-3 right-4" />
                <p className="italic text-neutral-200 text-sm md:text-base leading-relaxed pr-8 font-serif">
                  &ldquo;{activePersona.quote}&rdquo;
                </p>
                <p className="text-xs text-neutral-500 mt-2 font-mono">— {activePersona.name}, {activePersona.title}</p>
              </div>

              {/* Psychological Breakdown */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
                  <Brain className="w-4 h-4 text-purple-400" />
                  <span>Cognitive & Psychological Compatibility Analysis</span>
                </h4>
                <p className="text-sm text-neutral-300 leading-relaxed bg-neutral-950/40 p-4 rounded-xl border border-neutral-800/80">
                  {activePersona.bio}
                </p>
              </div>

              {/* Personality Traits */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400 mb-2">
                  Core Character Traits
                </h4>
                <div className="flex flex-wrap gap-2">
                  {activePersona.traits.map((trait, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 rounded-lg text-xs font-medium bg-neutral-800/80 text-neutral-200 border border-neutral-700/60 flex items-center gap-1.5"
                    >
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      {trait}
                    </span>
                  ))}
                </div>
              </div>

              {/* Vector Alignment Bars: User vs Character */}
              <div className="p-4 rounded-xl bg-neutral-950/80 border border-neutral-800/80 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-neutral-300 flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Latent Dimension Alignment (User vs Character)</span>
                  </span>
                  <span className="text-[11px] font-mono text-purple-400">Cosine: {activePersona.similarity.toFixed(4)}</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                  {dimensionLabels.map((label, idx) => {
                    const uVal = Math.round((userVector[idx] || 0) * 100);
                    const cVal = Math.round((activePersona.vector[idx] || 0) * 100);
                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between text-[11px] text-neutral-400 font-mono">
                          <span>{label}</span>
                          <span>
                            You: <strong className="text-cyan-300">{uVal}%</strong> | Char: <strong className="text-purple-300">{cVal}%</strong>
                          </span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-neutral-900 overflow-hidden flex">
                          <div
                            className="h-full bg-cyan-400/80 transition-all duration-500"
                            style={{ width: `${uVal}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Action Button: Adopt Character's Taste */}
              <div className="pt-2 flex flex-wrap items-center gap-3">
                <button
                  onClick={() => {
                    playSuccessChime();
                    if (onAdoptVector) {
                      onAdoptVector(activePersona.vector, activePersona.name);
                    }
                  }}
                  className="px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-600/30 transition-all hover:scale-105 active:scale-95 flex items-center gap-2"
                >
                  <Award className="w-4 h-4 text-amber-300" />
                  <span>Adopt {activePersona.name}&apos;s Taste Vector</span>
                </button>
                <span className="text-xs text-neutral-500 font-mono">
                  Syncs the Rust SIMD Equalizer & 3D Galaxy to this persona.
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recommended Anime Curated for this Character Persona */}
      {personaAnime.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Compass className="w-5 h-5 text-pink-400" />
                <span>Curated for {activePersona?.name}&apos;s Archetype</span>
              </h3>
              <p className="text-xs text-neutral-400">
                Shows sharing the exact narrative, pacing, and philosophical DNA of this persona.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {personaAnime.map((anime: any) => (
              <div
                key={anime.id}
                className="p-4 rounded-2xl bg-neutral-900/60 border border-neutral-800/80 hover:border-purple-500/40 transition-all hover:-translate-y-1 group"
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                    ★ {anime.score}
                  </span>
                  <span className="text-[11px] text-neutral-500 font-mono">
                    {anime.year}
                  </span>
                </div>
                <h4 className="font-bold text-neutral-100 text-sm group-hover:text-purple-300 transition-colors line-clamp-1">
                  {anime.title}
                </h4>
                <p className="text-xs text-neutral-400 line-clamp-2 mt-1.5 leading-relaxed">
                  {anime.synopsis}
                </p>
                <div className="flex flex-wrap gap-1 mt-3">
                  {(anime.genres || []).slice(0, 3).map((g: string, i: number) => (
                    <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-300">
                      {g}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Roster Explorer: Explore All 23 Iconic Anime Characters */}
      <div className="space-y-4 pt-4 border-t border-neutral-800/80">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-purple-400" />
              <span>Full Character Roster & Cognitive Profiles ({matchedList.length})</span>
            </h3>
            <p className="text-xs text-neutral-400">
              Click any character to inspect their psychological matrix or test your compatibility.
            </p>
          </div>

          {/* MBTI Filter Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full">
            {["ALL", "ENTP", "INTJ", "INTP", "ISTJ", "INFJ", "ENTJ"].map((mbti) => (
              <button
                key={mbti}
                onClick={() => {
                  playClickSound();
                  setFilterMbti(mbti);
                }}
                className={`px-2.5 py-1 rounded-lg text-xs font-mono font-medium transition-colors ${
                  filterMbti === mbti
                    ? "bg-purple-600 text-white"
                    : "bg-neutral-800/60 text-neutral-400 hover:text-neutral-200"
                }`}
              >
                {mbti}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {matchedList
            .filter((c) => filterMbti === "ALL" || c.mbti === filterMbti)
            .map((char) => {
              const isSelected = activePersona?.id === char.id;
              return (
                <div
                  key={char.id}
                  onClick={() => {
                    playClickSound();
                    setSelectedCharId(char.id);
                  }}
                  className={`p-3.5 rounded-2xl border cursor-pointer transition-all ${
                    isSelected
                      ? "bg-purple-950/40 border-purple-500 shadow-lg shadow-purple-500/20 scale-[1.02]"
                      : "bg-neutral-900/40 border-neutral-800/80 hover:border-neutral-700 hover:bg-neutral-800/40"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-11 h-11 rounded-xl bg-gradient-to-tr ${char.avatar_gradient} p-0.5 flex-shrink-0`}>
                      <div className="w-full h-full rounded-xl bg-neutral-950 flex items-center justify-center text-xs font-black text-white">
                        {char.name.split(" ").map((n) => n[0]).join("")}
                      </div>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-white truncate">
                          {char.name}
                        </h4>
                        <span className="text-[10px] font-mono text-purple-400 font-bold ml-1">
                          {char.matchPercentage}%
                        </span>
                      </div>
                      <p className="text-[11px] text-neutral-400 truncate">
                        {char.anime}
                      </p>
                      <div className="flex items-center gap-1.5 mt-1">
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-neutral-800 text-neutral-300 font-mono">
                          {char.mbti}
                        </span>
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-neutral-800 text-neutral-400 truncate">
                          {char.archetype}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
}
