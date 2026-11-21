"use client";

import React, { useState } from "react";
import { ThumbsUp, ThumbsDown, CheckCircle2, Sparkles, RefreshCw } from "lucide-react";
import { playClickSound, playSuccessChime } from "./SoundFX";

interface SwipeAnime {
  id: number;
  title: string;
  genres: string[];
  score: number;
  synopsis: string;
  vectorImpact: [number, number, number, number]; // [Action, Drama, SciFi, Psychology]
}

const SWIPE_STACK: SwipeAnime[] = [
  {
    id: 101,
    title: "Steins;Gate",
    genres: ["Sci-Fi", "Psychological", "Suspense"],
    score: 9.1,
    synopsis: "Microwave telephone experiments trigger unexpected temporal paradoxes across diverging timeline attractor fields.",
    vectorImpact: [0.1, 0.4, 0.9, 0.9]
  },
  {
    id: 102,
    title: "Attack on Titan",
    genres: ["Action", "Suspense", "Dark-Fantasy"],
    score: 9.0,
    synopsis: "Humanity fights for survival against towering humanoid Titans within colossal concentric defensive walls.",
    vectorImpact: [0.9, 0.7, 0.3, 0.6]
  },
  {
    id: 103,
    title: "Spirited Away",
    genres: ["Adventure", "Supernatural", "Fantasy"],
    score: 8.9,
    synopsis: "A young girl navigates an otherworldly bathhouse for spirits to rescue her enchanted parents.",
    vectorImpact: [0.2, 0.8, 0.2, 0.5]
  },
  {
    id: 104,
    title: "Cyberpunk: Edgerunners",
    genres: ["Action", "Sci-Fi", "Dystopian"],
    score: 8.6,
    synopsis: "A high-stakes street kid navigates body-modification black markets and corporate tyranny in Night City.",
    vectorImpact: [0.9, 0.5, 0.9, 0.7]
  },
  {
    id: 105,
    title: "Death Note",
    genres: ["Psychological", "Mystery", "Supernatural"],
    score: 8.7,
    synopsis: "A strategic battle of intellects erupts between an anonymous supernatural vigilante and an eccentric detective.",
    vectorImpact: [0.2, 0.7, 0.1, 0.95]
  }
];

export default function ColdStartSwiper({ onComplete }: { onComplete?: (userVector: number[]) => void }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [accumulatedVector, setAccumulatedVector] = useState<[number, number, number, number]>([0.5, 0.5, 0.5, 0.5]);
  const [isDone, setIsDone] = useState(false);

  const handleVote = (liked: boolean) => {
    playClickSound();
    const current = SWIPE_STACK[currentIndex];
    const multiplier = liked ? 1.0 : -0.3;

    const newVector: [number, number, number, number] = [
      Math.max(0.05, Math.min(1.0, accumulatedVector[0] + current.vectorImpact[0] * multiplier * 0.2)),
      Math.max(0.05, Math.min(1.0, accumulatedVector[1] + current.vectorImpact[1] * multiplier * 0.2)),
      Math.max(0.05, Math.min(1.0, accumulatedVector[2] + current.vectorImpact[2] * multiplier * 0.2)),
      Math.max(0.05, Math.min(1.0, accumulatedVector[3] + current.vectorImpact[3] * multiplier * 0.2)),
    ];

    setAccumulatedVector(newVector);

    if (currentIndex + 1 >= SWIPE_STACK.length) {
      setIsDone(true);
      playSuccessChime();
      if (onComplete) onComplete(newVector);
    } else {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const handleReset = () => {
    setCurrentIndex(0);
    setAccumulatedVector([0.5, 0.5, 0.5, 0.5]);
    setIsDone(false);
    playClickSound();
  };

  const currentAnime = SWIPE_STACK[currentIndex];

  return (
    <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900/80 via-slate-950 to-purple-950/20 p-6 backdrop-blur-md space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-4">
        <div>
          <span className="text-xs uppercase tracking-wider text-amber-400 font-bold">Cold-Start Onboarding Engine</span>
          <h3 className="text-xl font-bold text-white">Interactive Taste Discovery Swiper</h3>
        </div>
        <div className="text-xs text-slate-400">
          Step {Math.min(currentIndex + 1, SWIPE_STACK.length)} of {SWIPE_STACK.length}
        </div>
      </div>

      {!isDone ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
          {/* Card Presentation */}
          <div className="relative rounded-2xl border border-violet-500/30 bg-slate-900/90 p-6 shadow-2xl space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="text-xl font-bold text-white">{currentAnime.title}</h4>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {currentAnime.genres.map((g) => (
                    <span key={g} className="px-2 py-0.5 rounded text-[11px] bg-slate-800 text-slate-300">
                      {g}
                    </span>
                  ))}
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-lg bg-amber-500/20 text-amber-300 font-bold text-xs">
                ★ {currentAnime.score}
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed min-h-[50px]">
              {currentAnime.synopsis}
            </p>

            <div className="flex items-center justify-center space-x-4 pt-4 border-t border-white/5">
              <button
                onClick={() => handleVote(false)}
                className="flex-1 inline-flex items-center justify-center space-x-2 py-3 rounded-xl border border-slate-700 bg-slate-800/60 text-slate-300 hover:bg-rose-500/10 hover:border-rose-500/40 hover:text-rose-400 transition-all font-semibold text-xs"
              >
                <ThumbsDown className="h-4 w-4" />
                <span>Pass / Dislike</span>
              </button>

              <button
                onClick={() => handleVote(true)}
                className="flex-1 inline-flex items-center justify-center space-x-2 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-500 hover:to-purple-500 transition-all font-semibold text-xs shadow-lg shadow-violet-600/30"
              >
                <ThumbsUp className="h-4 w-4" />
                <span>Like This Show</span>
              </button>
            </div>
          </div>

          {/* Dynamic Vector Gauge */}
          <div className="p-5 rounded-2xl border border-white/5 bg-slate-950/60 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">Live User Vector Real-Time Normalization</h4>
            <div className="space-y-2.5 text-xs font-mono">
              <div>
                <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                  <span>Action / Pacing</span>
                  <span className="text-violet-300">{(accumulatedVector[0] * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-gradient-to-r from-violet-500 to-indigo-500 h-full transition-all duration-300" style={{ width: `${accumulatedVector[0] * 100}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                  <span>Drama / Emotion</span>
                  <span className="text-violet-300">{(accumulatedVector[1] * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-gradient-to-r from-violet-500 to-pink-500 h-full transition-all duration-300" style={{ width: `${accumulatedVector[1] * 100}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                  <span>Sci-Fi / Worldbuilding</span>
                  <span className="text-violet-300">{(accumulatedVector[2] * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full transition-all duration-300" style={{ width: `${accumulatedVector[2] * 100}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                  <span>Psychological Depth</span>
                  <span className="text-violet-300">{(accumulatedVector[3] * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-gradient-to-r from-amber-500 to-purple-500 h-full transition-all duration-300" style={{ width: `${accumulatedVector[3] * 100}%` }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 space-y-4">
          <div className="inline-flex p-3 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="h-8 w-8" />
          </div>
          <h4 className="text-xl font-bold text-white">Cold-Start Profile Successfully Calibrated!</h4>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Your dynamic 4-dimensional latent embedding vector is minted and synchronized with the Rust SIMD ranking kernel.
          </p>
          <div className="pt-2">
            <button
              onClick={handleReset}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg border border-white/10 bg-slate-800 text-xs font-semibold text-slate-200 hover:text-white"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Recalibrate Swiper</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
