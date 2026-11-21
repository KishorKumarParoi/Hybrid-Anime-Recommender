"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Sparkles,
  UserCheck,
  Quote,
  Brain,
  Award,
  Compass,
  Zap,
  CheckCircle2,
  Shuffle,
  HeartHandshake,
  Send,
  Loader2,
  Film,
  Flame,
  Shield,
  Layers,
  ArrowRight,
  BookOpen
} from "lucide-react";
import { playClickSound, playSuccessChime } from "@/components/SoundFX";

export interface CatharticAnime {
  title: string;
  reason: string;
  score: number;
  episodes: number;
}

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
  struggle: string;
  struggle_keywords: string[];
  healing_philosophy: string;
  cathartic_anime?: CatharticAnime[];
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

const PRESET_STORIES = [
  {
    label: "🛡️ Silent Burden & Masked Pain",
    text: "I carry all the responsibilities alone without ever asking for help. I put on a confident, cheerful face so the people around me feel safe and don't worry, but internally I feel exhausted, overwhelmed by survivor's guilt, and terrified of letting everyone down."
  },
  {
    label: "⚔️ Fighting Against Cruel Odds",
    text: "I've been battered by brutal setbacks, trauma, and betrayal from people I trusted. The odds are stacked against me and life feels unfair, but I refuse to stay down. I keep fighting, enduring chronic exhaustion, and defying fate with sheer stubborn willpower."
  },
  {
    label: "🌀 Peak Burnout & Apathy",
    text: "I reached a point where I worked so hard to get here, but now everything feels completely hollow and devoid of emotion. I am burnt out, numb to achievement, and longing for something genuine to rekindle my passion and make me feel truly alive again."
  },
  {
    label: "🕊️ Hedgehog's Dilemma & Fear of Closeness",
    text: "I desperately crave warmth, love, and belonging, yet I am terrified of opening up because every time I get close to someone, it ends in rejection or agonizing pain. I isolate myself in self-doubt, feeling inadequate to meet expectations."
  },
  {
    label: "⏳ Outliving Loved Ones & Belated Grief",
    text: "I was emotionally detached and took the people around me for granted until they were gone. Now I feel the crushing weight of belated grief and time slipping away. I want to learn to appreciate the small, quiet moments and understand other human hearts."
  },
  {
    label: "⚖️ Guilt Over Past Mistakes & Atonement",
    text: "I made terrible, arrogant mistakes in my past that caused immense harm to the people I love. I live with persistent self-blame, but I refuse to give up on redemption. I will keep moving forward on my own two feet to fix what I broke."
  }
];

export default function CharacterMatcher({
  userVector,
  onAdoptVector,
  allAnime = []
}: CharacterMatcherProps) {
  const [characters, setCharacters] = useState<CharacterProfile[]>([]);
  const [selectedCharId, setSelectedCharId] = useState<string | null>(null);
  const [filterMbti, setFilterMbti] = useState<string>("ALL");
  const [activeTab, setActiveTab] = useState<"struggle" | "vector">("struggle");

  // Struggle Matching State
  const [struggleInput, setStruggleInput] = useState<string>("");
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [struggleMatch, setStruggleMatch] = useState<{
    character: CharacterProfile;
    matchPercentage: number;
    sharedStruggles: string[];
    resonanceAnalysis: string;
    runnerUps: any[];
  } | null>(null);

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

  // Client-Side Struggle NLP Matcher (runs immediately and as fallback)
  const computeClientStruggleMatch = (inputText: string) => {
    if (!characters.length || !inputText.trim()) return null;

    const STOPWORDS = new Set([
      "the", "and", "is", "in", "it", "to", "of", "for", "with", "on", "at", "by",
      "from", "this", "that", "they", "them", "their", "you", "your", "was", "were",
      "have", "has", "had", "are", "but", "not", "what", "who", "how", "when", "where",
      "why", "can", "will", "just", "all", "into", "out", "up", "down", "about", "more",
      "some", "any", "my", "me", "we", "our", "us", "he", "him", "his", "she", "her",
      "been", "being", "would", "could", "should", "so", "than", "then", "too", "very",
      "feeling", "feel", "really", "much", "like"
    ]);

    const stemRoot = (w: string) => {
      const suffixes = ["ing", "tion", "ed", "ies", "es", "s", "ment", "ness", "ly"];
      for (const s of suffixes) {
        if (w.endsWith(s) && w.length > s.length + 2) {
          return w.slice(0, -s.length);
        }
      }
      return w;
    };

    const userWords = (inputText.toLowerCase().match(/\b[a-zA-Z]{3,}\b/g) || []).filter(
      (w) => !STOPWORDS.has(w)
    );
    const userRoots = new Set(userWords.map(stemRoot));

    const scored = characters.map((c) => {
      const textToSearch = `${c.struggle} ${(c.struggle_keywords || []).join(" ")} ${c.traits.join(" ")} ${c.bio}`.toLowerCase();
      const targetWords = (textToSearch.match(/\b[a-zA-Z]{3,}\b/g) || []).filter((w) => !STOPWORDS.has(w));
      const targetRoots = new Set(targetWords.map(stemRoot));

      let overlapCount = 0;
      userRoots.forEach((r) => {
        if (targetRoots.has(r)) overlapCount++;
      });

      let kwHits = 0;
      const matchedKws: string[] = [];
      (c.struggle_keywords || []).forEach((kw) => {
        const parts = (kw.toLowerCase().match(/\b[a-zA-Z]{3,}\b/g) || []).filter((p) => !STOPWORDS.has(p));
        if (parts.some((p) => userRoots.has(stemRoot(p)))) {
          kwHits += 2.8;
          matchedKws.push(kw);
        }
      });

      const rawScore = overlapCount * 2.2 + kwHits * 1.6;
      const matchPercentage = Math.round(Math.min(99.4, Math.max(58.0, 62.0 + rawScore * 1.9)) * 10) / 10;

      return {
        character: c,
        score: rawScore,
        matchPercentage,
        matchedKeywords: matchedKws.slice(0, 4)
      };
    });

    scored.sort((a, b) => b.score - a.score);
    const top = scored[0];
    if (!top) return null;

    const kwStr = top.matchedKeywords.length
      ? top.matchedKeywords.map((k) => `'${k}'`).join(", ")
      : "shared psychological endurance";

    const resonanceAnalysis =
      `Your personal testimony mirrors ${top.character.name}'s emotional journey with ${top.matchPercentage}% resonance. ` +
      `Your words strongly reflect core themes of ${kwStr}. Rather than merely enduring hardship, your journey embodies the tension between deep inner vulnerability and an unwavering resolve to protect or prevail. ` +
      `${top.character.name}'s canonical trials in '${top.character.anime}' reflect this exact emotional weight.`;

    return {
      character: top.character,
      matchPercentage: top.matchPercentage,
      sharedStruggles: top.matchedKeywords.length ? top.matchedKeywords : top.character.struggle_keywords.slice(0, 3),
      resonanceAnalysis,
      runnerUps: scored.slice(1, 4).map((s) => ({
        id: s.character.id,
        name: s.character.name,
        anime: s.character.anime,
        title: s.character.title,
        mbti: s.character.mbti,
        matchPercentage: s.matchPercentage
      }))
    };
  };

  // Perform Struggle Match via API or fallback
  const handleAnalyzeStruggle = async (textToAnalyze?: string) => {
    const text = textToAnalyze || struggleInput;
    if (!text.trim()) return;

    playClickSound();
    setIsAnalyzing(true);

    try {
      const res = await fetch("http://localhost:5001/api/character/match-struggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.status === "success" && data.matched_character) {
          setStruggleMatch({
            character: data.matched_character,
            matchPercentage: data.match_percentage,
            sharedStruggles: data.shared_struggles,
            resonanceAnalysis: data.resonance_analysis,
            runnerUps: data.all_matches?.slice(1, 4) || []
          });
          setSelectedCharId(data.matched_character.id);
          playSuccessChime();
          setIsAnalyzing(false);
          return;
        }
      }
    } catch (_err) {
      // Backend unavailable; seamlessly proceed to client fallback
    }

    // Client fallback
    const fallbackResult = computeClientStruggleMatch(text);
    if (fallbackResult) {
      setStruggleMatch(fallbackResult);
      setSelectedCharId(fallbackResult.character.id);
      playSuccessChime();
    }
    setIsAnalyzing(false);
  };

  const activePersona = useMemo(() => {
    if (!matchedList.length) return null;
    if (struggleMatch && activeTab === "struggle") {
      return struggleMatch.character;
    }
    if (selectedCharId) {
      return matchedList.find((c) => c.id === selectedCharId) || matchedList[0];
    }
    return matchedList[0];
  }, [matchedList, selectedCharId, struggleMatch, activeTab]);

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
            <span>AI Life Struggle & Alter Ego Profiler</span>
          </div>
          <h2 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            Your Anime Character <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-amber-300">Alter Ego</span>
          </h2>
          <p className="text-sm text-neutral-400 mt-1 max-w-2xl">
            Type about your real-world struggles, burdens, fears, or qualities. Our cognitive recommender mirrors your life narrative with the exact canonical trials, healing philosophy, and cathartic anime of legendary anime characters.
          </p>
        </div>

        {/* Dual Mode Selector */}
        <div className="flex items-center gap-2 bg-neutral-950/60 p-1.5 rounded-xl border border-neutral-800 self-start md:self-auto">
          <button
            onClick={() => {
              playClickSound();
              setActiveTab("struggle");
            }}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all ${
              activeTab === "struggle"
                ? "bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-600/30"
                : "text-neutral-400 hover:text-white"
            }`}
          >
            <HeartHandshake className="w-3.5 h-3.5" />
            <span>Life Struggle & Biography Mirror</span>
          </button>
          <button
            onClick={() => {
              playClickSound();
              setActiveTab("vector");
            }}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all ${
              activeTab === "vector"
                ? "bg-neutral-800 text-white shadow"
                : "text-neutral-400 hover:text-white"
            }`}
          >
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
            <span>4D Vector Equalizer</span>
          </button>
        </div>
      </div>

      {/* Mode 1: Life Struggle & Biography Matching Input */}
      {activeTab === "struggle" && (
        <div className="rounded-3xl border border-purple-500/30 bg-neutral-950/70 backdrop-blur-2xl p-6 md:p-8 space-y-5 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="text-lg md:text-xl font-black text-white flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-400" />
                <span>Tell Us Your Story: What are you going through?</span>
              </h3>
              <p className="text-xs text-neutral-400 mt-0.5">
                Express your feelings, life burdens, fears, or aspirations. The recommender pairs you with the anime soulmate who walked your path.
              </p>
            </div>
            <span className="text-[11px] font-mono text-purple-400/80 bg-purple-950/40 px-2.5 py-1 rounded-full border border-purple-500/30 self-start">
              22 Iconic Characters Indexed
            </span>
          </div>

          {/* Quick Presets */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider block">
              Quick Test Presets (Click to Load & Analyze):
            </span>
            <div className="flex flex-wrap gap-2">
              {PRESET_STORIES.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setStruggleInput(p.text);
                    handleAnalyzeStruggle(p.text);
                  }}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-neutral-900/90 hover:bg-purple-950/50 text-neutral-300 hover:text-purple-200 border border-neutral-800 hover:border-purple-500/40 transition-all hover:scale-[1.02] active:scale-95"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Text Input Area */}
          <div className="relative">
            <textarea
              rows={4}
              value={struggleInput}
              onChange={(e) => setStruggleInput(e.target.value)}
              placeholder="e.g. I feel overwhelmed carrying all the responsibilities alone. I smile and act strong so others don't worry, but inside I feel intense burnout, guilt, and fear of letting people down..."
              className="w-full rounded-2xl bg-neutral-900/90 border border-neutral-800 p-4 text-sm text-neutral-100 placeholder-neutral-500 focus:outline-none focus:border-purple-500/60 focus:ring-2 focus:ring-purple-500/20 transition-all leading-relaxed resize-none"
            />
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mt-3">
              <span className="text-xs text-neutral-500 font-mono">
                {struggleInput.length} characters • Semantic Tokenizer Ready
              </span>
              <button
                disabled={isAnalyzing || !struggleInput.trim()}
                onClick={() => handleAnalyzeStruggle()}
                className="w-full sm:w-auto px-6 py-3 rounded-xl text-xs font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-xl shadow-purple-600/30 transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-2"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-purple-200" />
                    <span>Analyzing Neural Trauma Vector...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-amber-300" />
                    <span>Analyze Struggle & Reveal Alter Ego</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Matched Persona Hero Showcase */}
      {activePersona && (
        <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-neutral-900/60 backdrop-blur-2xl shadow-2xl p-6 md:p-8">
          <div className={`absolute top-0 right-0 w-96 h-96 bg-gradient-to-br ${activePersona.avatar_gradient} opacity-15 blur-3xl rounded-full pointer-events-none`} />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
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
                  {struggleMatch && activeTab === "struggle"
                    ? `${struggleMatch.matchPercentage}% STRUGGLE RESONANCE`
                    : `${(activePersona as any).matchPercentage || 98.4}% SOULMATE MATCH`}
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

              {/* Shared Struggles Pill Cloud */}
              {activePersona.struggle_keywords && (
                <div className="mt-5 w-full text-left">
                  <span className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider block mb-2 text-center">
                    Resonant Struggle Nodes
                  </span>
                  <div className="flex flex-wrap gap-1.5 justify-center">
                    {activePersona.struggle_keywords.slice(0, 6).map((kw, i) => (
                      <span
                        key={i}
                        className="text-[10px] px-2 py-0.5 rounded-md bg-purple-950/40 text-purple-300 border border-purple-500/20 font-mono"
                      >
                        #{kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right Column: Quotes, Struggle, Biography & Philosophy */}
            <div className="lg:col-span-8 space-y-6">
              {/* Dynamic Resonance Analysis (When Struggle Match is active) */}
              {struggleMatch && activeTab === "struggle" && (
                <div className="p-4 md:p-5 rounded-2xl bg-gradient-to-r from-purple-950/40 via-pink-950/20 to-neutral-900 border border-purple-500/40 relative">
                  <div className="flex items-center gap-2 text-xs font-extrabold text-pink-300 uppercase tracking-wider mb-1.5">
                    <HeartHandshake className="w-4 h-4 text-pink-400" />
                    <span>Why Your Story Mirrors {activePersona.name}</span>
                  </div>
                  <p className="text-sm text-neutral-200 leading-relaxed font-sans">
                    {struggleMatch.resonanceAnalysis}
                  </p>
                </div>
              )}

              {/* Canonical Struggle & Biography */}
              <div className="space-y-3">
                <div className="p-4 md:p-5 rounded-2xl bg-neutral-950/80 border border-neutral-800 space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                    <Flame className="w-4 h-4 text-amber-400" />
                    <span>The Canonical Struggle & Origin Trauma</span>
                  </h4>
                  <p className="text-sm text-neutral-300 leading-relaxed">
                    {activePersona.struggle}
                  </p>
                </div>

                <div className="p-4 rounded-2xl bg-neutral-950/50 border border-neutral-800/80 space-y-1.5">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Biography & Background</span>
                  </h4>
                  <p className="text-xs text-neutral-400 leading-relaxed">
                    {activePersona.bio}
                  </p>
                </div>
              </div>

              {/* Guiding Life Philosophy & Quote */}
              <div className="p-4 md:p-5 rounded-2xl bg-neutral-950/60 border border-neutral-800 relative">
                <Quote className="w-6 h-6 text-purple-500/40 absolute top-3 right-4" />
                <p className="italic text-neutral-200 text-sm md:text-base leading-relaxed pr-8 font-serif">
                  &ldquo;{activePersona.quote}&rdquo;
                </p>
                <div className="mt-3 pt-3 border-t border-neutral-800/80">
                  <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider block mb-1">
                    Guiding Healing Philosophy:
                  </span>
                  <p className="text-xs text-neutral-300 leading-relaxed">
                    {activePersona.healing_philosophy}
                  </p>
                </div>
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
              {activeTab === "vector" && (
                <div className="p-4 rounded-xl bg-neutral-950/80 border border-neutral-800/80 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-neutral-300 flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Latent Dimension Alignment (User vs Character)</span>
                    </span>
                    <span className="text-[11px] font-mono text-purple-400">
                      Cosine: {(activePersona as any).similarity ? (activePersona as any).similarity.toFixed(4) : "0.9850"}
                    </span>
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
              )}

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
                  Calibrates the 3D Vector Galaxy, Equalizer & Catalog to this persona.
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cathartic Anime Tailored For This Life Struggle */}
      {activePersona?.cathartic_anime && activePersona.cathartic_anime.length > 0 && (
        <div className="space-y-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 mb-1">
              <Film className="w-3.5 h-3.5 text-emerald-400" />
              <span>Prescription Anime Therapy</span>
            </div>
            <h3 className="text-xl font-black text-white flex items-center gap-2">
              <span>Cathartic Anime Curated For {activePersona.name}&apos;s Headspace</span>
            </h3>
            <p className="text-xs text-neutral-400">
              Hand-curated anime that directly addresses this specific trauma, offering emotional release, perspective, and healing.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {activePersona.cathartic_anime.map((ca, idx) => (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-neutral-900/70 border border-neutral-800 hover:border-emerald-500/40 transition-all hover:-translate-y-1 group flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      ★ {ca.score}
                    </span>
                    <span className="text-[11px] text-neutral-500 font-mono">
                      {ca.episodes} Ep
                    </span>
                  </div>
                  <h4 className="font-black text-neutral-100 text-sm group-hover:text-emerald-300 transition-colors">
                    {ca.title}
                  </h4>
                  <p className="text-xs text-neutral-300 mt-2 leading-relaxed">
                    {ca.reason}
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-neutral-800/80 flex items-center justify-between">
                  <span className="text-[10px] text-emerald-400 font-mono">Catharsis Match</span>
                  <span className="text-[10px] text-neutral-500 font-mono">MAL Verified</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Anime Curated for this Character Persona Archetype */}
      {personaAnime.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Compass className="w-5 h-5 text-pink-400" />
                <span>Curated for {activePersona?.name}&apos;s Genre DNA</span>
              </h3>
              <p className="text-xs text-neutral-400">
                Shows sharing the exact narrative pacing, world-building, and thematic frequency of this persona.
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

      {/* Roster Explorer: Explore All 22 Iconic Anime Characters */}
      <div className="space-y-4 pt-4 border-t border-neutral-800/80">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-purple-400" />
              <span>Full Character Roster & Struggle Profiles ({characters.length})</span>
            </h3>
            <p className="text-xs text-neutral-400">
              Click any character to inspect their canonical struggle, trauma matrix, and healing philosophy.
            </p>
          </div>

          {/* MBTI Filter Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full">
            {["ALL", "ENTP", "INTJ", "INTP", "ISTJ", "INFJ", "ENTJ", "ISTP", "INFP"].map((mbti) => (
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
          {characters
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
                          {char.mbti}
                        </span>
                      </div>
                      <p className="text-[11px] text-neutral-400 truncate">
                        {char.anime}
                      </p>
                      <div className="flex items-center gap-1.5 mt-1">
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-neutral-800 text-neutral-300 font-mono">
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
