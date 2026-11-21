"use client";

import React, { useState, useEffect } from "react";
import { Radio, Flame, Sparkles } from "lucide-react";

export default function BreakingNewsTicker({ onNewsClick }: { onNewsClick?: () => void }) {
  const [headlines, setHeadlines] = useState<string[]>([
    "⚡ BREAKING (4m ago): Chainsaw Man 'Reze Arc' Movie Locks Worldwide Summer Theatrical Window with Studio MAPPA",
    "🔥 EXCLUSIVE (18m ago): Demon Slayer 'Infinity Castle' Trilogy Part 1 Confirms 135-Minute Runtime in IMAX",
    "🧠 REVEAL (34m ago): Steins;Gate 15th Anniversary Sequel Project 'Steins;???' Greenlit for 2027 by Chiyomaru Studio",
    "⚔️ STUDIO LEAK (1h ago): Jujutsu Kaisen Season 3 'Culling Game' Releases First Colony Key Visual & Domain Previews",
    "✨ GREENLIT (2h ago): Frieren: Beyond Journey's End Season 2 Officially Announced with Director Keiichiro Saito"
  ]);

  useEffect(() => {
    fetch("/data/anime_news_2027.json")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          const formatted = data.map(
            (item) => `⚡ BREAKING (${item.timestamp}): ${item.title}`
          );
          setHeadlines(formatted);
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div
      onClick={onNewsClick}
      className="cursor-pointer border-b border-red-500/20 bg-gradient-to-r from-red-950/80 via-neutral-950 to-red-950/80 py-2 px-4 backdrop-blur-md overflow-hidden flex items-center gap-3 text-xs font-mono group hover:bg-neutral-900 transition-colors"
    >
      <div className="flex items-center gap-2 flex-shrink-0 font-bold text-red-400 uppercase tracking-widest bg-red-500/10 px-2.5 py-0.5 rounded-full border border-red-500/30">
        <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
        <Radio className="w-3 h-3 text-red-400" />
        <span>MAL 2027 24/7 AI WIRE</span>
      </div>

      <div className="relative overflow-hidden whitespace-nowrap flex-1">
        <div className="inline-block animate-marquee group-hover:[animation-play-state:paused] text-neutral-300">
          {headlines.map((headline, idx) => (
            <span key={idx} className="mx-6 hover:text-white transition-colors">
              {headline}
            </span>
          ))}
        </div>
      </div>

      <div className="hidden sm:flex items-center gap-1.5 text-[11px] text-neutral-400 font-sans flex-shrink-0">
        <span>Click to open Newsroom</span>
        <span className="text-red-400 font-bold">→</span>
      </div>
    </div>
  );
}
