"use client";

import React, { useEffect, useRef, useState } from "react";
import { Sparkles, RotateCw, ZoomIn, Info } from "lucide-react";
import { playClickSound } from "./SoundFX";

interface VectorNode {
  id: number;
  title: string;
  genres: string[];
  score: number;
  // 3D coordinates normalized between -1 and 1
  x: number;
  y: number;
  z: number;
  color: string;
}

const GALAXY_NODES: VectorNode[] = [
  { id: 1, title: "Steins;Gate", genres: ["Sci-Fi", "Psychological"], score: 9.1, x: 0.85, y: -0.4, z: 0.65, color: "#8b5cf6" },
  { id: 2, title: "Fullmetal Alchemist: Brotherhood", genres: ["Action", "Adventure"], score: 9.2, x: -0.6, y: 0.7, z: -0.5, color: "#f59e0b" },
  { id: 3, title: "Cyberpunk: Edgerunners", genres: ["Action", "Sci-Fi", "Dystopian"], score: 8.6, x: 0.7, y: 0.5, z: 0.8, color: "#06b6d4" },
  { id: 4, title: "Death Note", genres: ["Psychological", "Suspense"], score: 8.7, x: -0.3, y: -0.8, z: 0.7, color: "#ec4899" },
  { id: 5, title: "Spirited Away", genres: ["Fantasy", "Adventure"], score: 8.9, x: -0.8, y: 0.2, z: -0.8, color: "#10b981" },
  { id: 6, title: "Jujutsu Kaisen", genres: ["Action", "Dark-Fantasy"], score: 8.6, x: -0.5, y: 0.6, z: 0.4, color: "#f97316" },
  { id: 7, title: "Monster", genres: ["Psychological", "Mystery"], score: 8.8, x: -0.1, y: -0.9, z: 0.6, color: "#a855f7" },
  { id: 8, title: "Neon Genesis Evangelion", genres: ["Mecha", "Psychological"], score: 8.5, x: 0.5, y: -0.6, z: 0.9, color: "#6366f1" },
  { id: 9, title: "Attack on Titan", genres: ["Action", "Suspense"], score: 9.0, x: -0.7, y: 0.8, z: 0.2, color: "#ef4444" },
  { id: 10, title: "Cowboy Bebop", genres: ["Sci-Fi", "Space-Western"], score: 8.9, x: 0.9, y: 0.3, z: -0.3, color: "#38bdf8" },
  { id: 11, title: "Hunter x Hunter", genres: ["Adventure", "Fantasy"], score: 9.0, x: -0.4, y: 0.5, z: -0.6, color: "#eab308" },
  { id: 12, title: "Ghost in the Shell", genres: ["Cyberpunk", "Philosophy"], score: 8.4, x: 0.75, y: -0.2, z: 0.85, color: "#22d3ee" },
];

export default function VectorGalaxy3D() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [selectedNode, setSelectedNode] = useState<VectorNode | null>(GALAXY_NODES[0]);
  const [rotation, setRotation] = useState({ x: 0.3, y: 0.5 });
  const [zoom, setZoom] = useState(1.0);
  const isDraggingRef = useRef(false);
  const lastMouseRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let angleY = rotation.y;
    let angleX = rotation.x;

    const render = () => {
      if (!isDraggingRef.current) {
        angleY += 0.003; // Smooth auto-orbit rotation
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const cx = canvas.width / 2;
      const cy = canvas.height / 2;
      const scale = Math.min(cx, cy) * 0.75 * zoom;
      const fov = 400;

      // Calculate 3D projected coordinates for each node
      const projected = GALAXY_NODES.map((node) => {
        // Rotate Y
        const cosY = Math.cos(angleY);
        const sinY = Math.sin(angleY);
        let x1 = node.x * cosY - node.z * sinY;
        let z1 = node.z * cosY + node.x * sinY;

        // Rotate X
        const cosX = Math.cos(angleX);
        const sinX = Math.sin(angleX);
        let y2 = node.y * cosX - z1 * sinX;
        let z2 = z1 * cosX + node.y * sinX;

        // Perspective projection
        const pz = z2 + 2.5; // Offset camera distance
        const pers = fov / (fov + pz * 180);
        const px = cx + x1 * scale * pers;
        const py = cy + y2 * scale * pers;
        const radius = Math.max(3, (pz > 0 ? (4 - pz) * 4 : 4) * pers * 1.5);

        return { node, px, py, pz, radius };
      });

      // Draw faint constellation lines between nearest neighbors in 3D
      ctx.lineWidth = 1;
      for (let i = 0; i < projected.length; i++) {
        for (let j = i + 1; j < projected.length; j++) {
          const a = projected[i];
          const b = projected[j];
          const dist3D = Math.sqrt(
            Math.pow(a.node.x - b.node.x, 2) +
            Math.pow(a.node.y - b.node.y, 2) +
            Math.pow(a.node.z - b.node.z, 2)
          );

          if (dist3D < 1.1) {
            const alpha = Math.max(0.05, (1.1 - dist3D) * 0.4);
            ctx.strokeStyle = `rgba(139, 92, 246, ${alpha})`;
            ctx.beginPath();
            ctx.moveTo(a.px, a.py);
            ctx.lineTo(b.px, b.py);
            ctx.stroke();
          }
        }
      }

      // Sort by depth (painters algorithm)
      projected.sort((a, b) => b.pz - a.pz);

      // Draw 3D nodes
      projected.forEach((p) => {
        const isSelected = selectedNode?.id === p.node.id;

        // Outer glow
        const gradient = ctx.createRadialGradient(p.px, p.py, 0, p.px, p.py, p.radius * (isSelected ? 3.5 : 2.2));
        gradient.addColorStop(0, p.node.color);
        gradient.addColorStop(1, "transparent");

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(p.px, p.py, p.radius * (isSelected ? 3.5 : 2.2), 0, Math.PI * 2);
        ctx.fill();

        // Core star
        ctx.fillStyle = isSelected ? "#ffffff" : p.node.color;
        ctx.beginPath();
        ctx.arc(p.px, p.py, p.radius, 0, Math.PI * 2);
        ctx.fill();

        // Label
        ctx.fillStyle = isSelected ? "#ffffff" : "rgba(203, 213, 225, 0.75)";
        ctx.font = isSelected ? "bold 12px sans-serif" : "10px sans-serif";
        ctx.fillText(p.node.title, p.px + p.radius + 6, p.py + 4);
      });

      animId = requestAnimationFrame(render);
    };

    render();

    return () => cancelAnimationFrame(animId);
  }, [rotation, zoom, selectedNode]);

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    isDraggingRef.current = true;
    lastMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - lastMouseRef.current.x;
    const dy = e.clientY - lastMouseRef.current.y;
    lastMouseRef.current = { x: e.clientX, y: e.clientY };

    setRotation((prev) => ({
      x: Math.max(-1.2, Math.min(1.2, prev.x + dy * 0.006)),
      y: prev.y + dx * 0.006,
    }));
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Pick closest node
    let closest: VectorNode | null = null;
    let minDist = 30;

    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const scale = Math.min(cx, cy) * 0.75 * zoom;
    const fov = 400;

    GALAXY_NODES.forEach((node) => {
      const cosY = Math.cos(rotation.y);
      const sinY = Math.sin(rotation.y);
      let x1 = node.x * cosY - node.z * sinY;
      let z1 = node.z * cosY + node.x * sinY;
      const cosX = Math.cos(rotation.x);
      const sinX = Math.sin(rotation.x);
      let y2 = node.y * cosX - z1 * sinX;
      let z2 = z1 * cosX + node.y * sinX;
      const pz = z2 + 2.5;
      const pers = fov / (fov + pz * 180);
      const px = cx + x1 * scale * pers;
      const py = cy + y2 * scale * pers;

      const d = Math.hypot(clickX - px, clickY - py);
      if (d < minDist) {
        minDist = d;
        closest = node;
      }
    });

    if (closest) {
      setSelectedNode(closest);
      playClickSound();
    }
  };

  return (
    <div className="relative rounded-2xl border border-white/10 bg-gradient-to-b from-slate-950 via-[#070b14] to-purple-950/20 p-6 backdrop-blur-xl space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 text-xs font-semibold text-violet-400 uppercase tracking-wider">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Interactive Vector Space Explorer</span>
          </div>
          <h3 className="text-xl font-bold text-white tracking-tight">3D Latent Embedding Galaxy</h3>
          <p className="text-xs text-slate-400">Drag canvas to rotate orbit • Click any star node to inspect 3D vector coordinates</p>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 bg-slate-900/80 border border-white/10 rounded-lg px-2.5 py-1 text-xs text-slate-300">
            <ZoomIn className="h-3.5 w-3.5 text-violet-400" />
            <input
              type="range"
              min="0.7"
              max="1.5"
              step="0.05"
              value={zoom}
              onChange={(e) => setZoom(parseFloat(e.target.value))}
              className="w-16 accent-violet-500 cursor-pointer"
            />
          </div>

          <button
            onClick={() => {
              setRotation({ x: 0.3, y: 0.5 });
              setZoom(1.0);
              playClickSound();
            }}
            className="p-1.5 rounded-lg border border-white/10 bg-slate-900/80 text-slate-400 hover:text-white"
            title="Reset Galaxy Orbit"
          >
            <RotateCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <div className="relative w-full h-[460px] rounded-xl overflow-hidden border border-white/5 bg-[#050811]/90">
        <canvas
          ref={canvasRef}
          width={860}
          height={460}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onClick={handleCanvasClick}
          className="w-full h-full cursor-grab active:cursor-grabbing"
        />

        {/* Selected Node HUD Card */}
        {selectedNode && (
          <div className="absolute bottom-4 left-4 max-w-sm rounded-xl border border-violet-500/40 bg-slate-900/90 p-4 backdrop-blur-md shadow-2xl space-y-2">
            <div className="flex items-center justify-between gap-2">
              <h4 className="text-sm font-bold text-white">{selectedNode.title}</h4>
              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/20 text-amber-300">
                ★ {selectedNode.score}
              </span>
            </div>
            <div className="flex flex-wrap gap-1">
              {selectedNode.genres.map((g) => (
                <span key={g} className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                  {g}
                </span>
              ))}
            </div>
            <div className="pt-1 text-[11px] font-mono text-slate-400 space-y-0.5">
              <p>3D Vector: [{selectedNode.x.toFixed(2)}, {selectedNode.y.toFixed(2)}, {selectedNode.z.toFixed(2)}]</p>
              <p className="text-violet-300">Nearest Cluster: <strong className="text-white">Cosine 0.94 Match</strong></p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
