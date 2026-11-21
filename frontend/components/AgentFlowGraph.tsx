"use client";

import React, { useEffect, useState } from "react";
import { CheckCircle2, Loader2, ShieldCheck, Sparkles, Database, Search, ArrowRight } from "lucide-react";

interface AgentFlowProps {
  isRunning: boolean;
  activeStage?: number;
}

const AGENT_STAGES = [
  { id: 1, name: "Query Decomposition", icon: Search, detail: "Entity & intent extraction", time: "18ms" },
  { id: 2, name: "Dense Vector Retrieval", icon: Database, detail: "Qdrant / ChromaDB dense similarity", time: "42ms" },
  { id: 3, name: "Critic Reflection Loop", icon: ShieldCheck, detail: "Anti-hallucination & spoiler filter", time: "85ms" },
  { id: 4, name: "Dossier Synthesis", icon: Sparkles, detail: "vLLM Multi-LoRA narrative generation", time: "120ms" }
];

export default function AgentFlowGraph({ isRunning }: AgentFlowProps) {
  const [currentStage, setCurrentStage] = useState(0);

  useEffect(() => {
    if (isRunning) {
      setCurrentStage(1);
      const t1 = setTimeout(() => setCurrentStage(2), 500);
      const t2 = setTimeout(() => setCurrentStage(3), 1100);
      const t3 = setTimeout(() => setCurrentStage(4), 1800);
      return () => {
        clearTimeout(t1);
        clearTimeout(t2);
        clearTimeout(t3);
      };
    } else {
      setCurrentStage(4);
    }
  }, [isRunning]);

  return (
    <div className="rounded-xl border border-violet-500/20 bg-slate-900/60 p-4 space-y-3">
      <div className="flex items-center justify-between text-xs">
        <span className="font-bold text-violet-300 uppercase tracking-wider">LangGraph Execution State Machine</span>
        <span className="font-mono text-emerald-400 font-semibold">{isRunning ? "Running Live Cycle..." : "Workflow Complete"}</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
        {AGENT_STAGES.map((stage) => {
          const Icon = stage.icon;
          const isDone = !isRunning || currentStage > stage.id;
          const isActive = isRunning && currentStage === stage.id;

          return (
            <div
              key={stage.id}
              className={`p-3 rounded-lg border text-left transition-all duration-300 ${
                isActive
                  ? "border-violet-500 bg-violet-950/40 shadow-lg shadow-violet-500/20 ring-1 ring-violet-500"
                  : isDone
                  ? "border-emerald-500/30 bg-emerald-950/10 text-slate-200"
                  : "border-slate-800 bg-slate-900/40 text-slate-500"
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-mono font-bold text-slate-400">STAGE 0{stage.id}</span>
                {isActive ? (
                  <Loader2 className="h-3.5 w-3.5 text-violet-400 animate-spin" />
                ) : isDone ? (
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                ) : (
                  <span className="h-2 w-2 rounded-full bg-slate-700" />
                )}
              </div>
              <p className="text-xs font-bold text-white flex items-center gap-1.5">
                <Icon className={`h-3.5 w-3.5 ${isActive ? "text-violet-400" : isDone ? "text-emerald-400" : "text-slate-500"}`} />
                <span>{stage.name}</span>
              </p>
              <p className="text-[10px] text-slate-400 mt-1">{stage.detail}</p>
              <p className="text-[9px] font-mono text-slate-500 mt-1 text-right">~{stage.time}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
