"""
Dynamic Multi-LoRA Client for vLLM.

Interacts with a vLLM OpenAI-compatible server configured with --enable-lora.
Enables dynamic, zero-cold-start switching between fine-tuned LoRA adapters
(e.g., anime-critic, anime-stylist) and the base model on a single GPU.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncGenerator, Generator, Optional

import httpx

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MultiLoRAClient")


@dataclass
class GenerationResult:
    """Encapsulates the response from the Multi-LoRA endpoint."""
    model_used: str
    adapter: Optional[str]
    prompt: str
    content: str
    tokens_generated: int
    latency_ms: float
    raw_response: dict[str, Any] = field(default_factory=dict)


class MultiLoRAClient:
    """High-performance client for Dynamic Multi-LoRA serving on vLLM."""

    BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct-AWQ"
    AVAILABLE_ADAPTERS = {
        "anime-critic": "Fine-tuned for deep sakuga, pacing, thematic, and directorial critique.",
        "anime-stylist": "Fine-tuned for vibrant, aesthetic, conversational otaku recommendations.",
    }

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "EMPTY",
        timeout: float = 60.0,
        mock_mode: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.mock_mode = mock_mode
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout,
        )

    def health_check(self) -> bool:
        """Check if the vLLM server is healthy and operational."""
        if self.mock_mode:
            return True
        try:
            # vLLM health endpoint is at root /health
            root_url = self.base_url.replace("/v1", "")
            resp = httpx.get(f"{root_url}/health", timeout=5.0)
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed against {self.base_url}: {e}")
            return False

    def list_models(self) -> list[str]:
        """Fetch all models currently hosted by vLLM (base model + loaded LoRA adapters)."""
        if self.mock_mode:
            return [self.BASE_MODEL] + list(self.AVAILABLE_ADAPTERS.keys())

        try:
            resp = self.client.get("/models")
            resp.raise_for_status()
            data = resp.json()
            return [item["id"] for item in data.get("data", [])]
        except Exception as e:
            logger.error(f"Failed to fetch models from vLLM: {e}")
            if self.mock_mode:
                return [self.BASE_MODEL] + list(self.AVAILABLE_ADAPTERS.keys())
            raise

    def generate(
        self,
        prompt: str,
        adapter: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> GenerationResult:
        """
        Dynamically route generation request to either the base model or a specific LoRA adapter.
        
        Args:
            prompt: User query or prompt.
            adapter: Name of the LoRA adapter ('anime-critic', 'anime-stylist') or None for base.
            system_prompt: Optional custom system prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
        """
        # Determine model identifier passed to vLLM
        target_model = adapter if adapter else self.BASE_MODEL

        # Construct messages payload
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        elif adapter == "anime-critic":
            messages.append({
                "role": "system",
                "content": "You are a senior anime industry critic specializing in sakuga analysis, narrative pacing, and thematic synthesis."
            })
        elif adapter == "anime-stylist":
            messages.append({
                "role": "system",
                "content": "You are an enthusiastic, charismatic anime curator who crafts engaging, aesthetically rich recommendations."
            })
        else:
            messages.append({
                "role": "system",
                "content": "You are a helpful and knowledgeable anime recommendation assistant."
            })

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start_time = time.perf_counter()

        if self.mock_mode:
            content = self._mock_generation(adapter, prompt)
            latency_ms = (time.perf_counter() - start_time) * 1000 + 42.0
            return GenerationResult(
                model_used=target_model,
                adapter=adapter,
                prompt=prompt,
                content=content,
                tokens_generated=len(content.split()),
                latency_ms=round(latency_ms, 2),
                raw_response={"mock": True, "model": target_model},
            )

        try:
            resp = self.client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            latency_ms = (time.perf_counter() - start_time) * 1000

            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("completion_tokens", len(content.split()))

            return GenerationResult(
                model_used=target_model,
                adapter=adapter,
                prompt=prompt,
                content=content,
                tokens_generated=tokens,
                latency_ms=round(latency_ms, 2),
                raw_response=data,
            )
        except Exception as e:
            logger.error(f"Multi-LoRA dynamic invocation failed for model={target_model}: {e}")
            raise

    def generate_critique(self, anime_title: str, focus_area: str = "directorial and animation quality") -> GenerationResult:
        """Specialized helper routing to the 'anime-critic' LoRA adapter."""
        prompt = f"Provide a critical evaluation of '{anime_title}', focusing on {focus_area}."
        return self.generate(prompt=prompt, adapter="anime-critic", temperature=0.4)

    def generate_stylized_recommendation(self, query: str) -> GenerationResult:
        """Specialized helper routing to the 'anime-stylist' LoRA adapter."""
        return self.generate(prompt=query, adapter="anime-stylist", temperature=0.75)

    def benchmark_comparison(self, prompt: str) -> dict[str, GenerationResult]:
        """
        Demonstrate zero-overhead dynamic Multi-LoRA switching.
        Executes sequential queries targeting:
        1. Base Model (General Foundation)
        2. 'anime-critic' (Domain LoRA #1)
        3. 'anime-stylist' (Domain LoRA #2)
        All executed against the SAME running vLLM server instance on ONE GPU.
        """
        results = {}
        logger.info(f"--- Benchmarking Dynamic Multi-LoRA Serving for prompt: '{prompt}' ---")

        # 1. Base Model
        t0 = time.perf_counter()
        results["base"] = self.generate(prompt, adapter=None)
        logger.info(f"[Base Model] Latency: {results['base'].latency_ms}ms")

        # 2. Anime Critic Adapter
        results["anime-critic"] = self.generate(prompt, adapter="anime-critic")
        logger.info(f"[Adapter: anime-critic] Latency: {results['anime-critic'].latency_ms}ms")

        # 3. Anime Stylist Adapter
        results["anime-stylist"] = self.generate(prompt, adapter="anime-stylist")
        logger.info(f"[Adapter: anime-stylist] Latency: {results['anime-stylist'].latency_ms}ms")

        return results

    def _mock_generation(self, adapter: Optional[str], prompt: str) -> str:
        """Generate simulated responses reflecting distinct LoRA adapter specializations."""
        if adapter == "anime-critic":
            return (
                f"### Critical Deconstruction\n"
                f"Analyzing: *{prompt}*\n\n"
                f"**Directorial & Sakuga Execution:**\n"
                f"The framing emphasizes deliberate negative space and keyframe timing, showcasing expressive character movement "
                f"reminiscent of high-impact Studio Bones / MAPPA productions. Pacing is calibrated to heighten tension without "
                f"succumbing to superficial melodrama.\n\n"
                f"**Verdict:** High thematic resonance with exceptional kinetic choreography."
            )
        elif adapter == "anime-stylist":
            return (
                f"✨ **Otaku Aesthetic Recommendation** ✨\n\n"
                f"If you're craving *{prompt}*, you are in for an unforgettable visual banquet!\n"
                f"Think electric neon vistas, heart-pounding synthwave beats, and unforgettable character dynamics. "
                f"It grabs you from episode 1 with jaw-dropping visual spectacles and never lets go. "
                f"Add this to your watchlist immediately—you will love every second! 🍿🎬"
            )
        else:
            return (
                f"Based on your query regarding '{prompt}', here are some notable anime titles that match your request. "
                f"These series feature strong narrative structures, well-developed characters, and positive viewer reception."
            )

    def close(self):
        """Close the underlying HTTP client session."""
        self.client.close()


def main():
    parser = argparse.ArgumentParser(description="vLLM Dynamic Multi-LoRA Client")
    parser.add_argument("--url", default="http://localhost:8000/v1", help="vLLM base URL")
    parser.add_argument("--adapter", choices=["anime-critic", "anime-stylist", "base"], default="anime-stylist", help="LoRA adapter target")
    parser.add_argument("--prompt", default="Recommend an intense psychological sci-fi anime with great animation", help="Prompt to generate")
    parser.add_argument("--compare", action="store_true", help="Run benchmark across base and all adapters")
    parser.add_argument("--mock", action="store_true", help="Run in mock/simulation mode without GPU cluster")

    args = parser.parse_args()

    client = MultiLoRAClient(base_url=args.url, mock_mode=args.mock)

    try:
        if args.compare:
            print("\n" + "=" * 70)
            print("🚀 DYNAMIC MULTI-LORA SERVING BENCHMARK (1 GPU, 3 ADAPTERS)")
            print("=" * 70)
            comparison = client.benchmark_comparison(args.prompt)
            for key, res in comparison.items():
                print(f"\n[{key.upper()}] (Latency: {res.latency_ms}ms)")
                print("-" * 50)
                print(res.content)
        else:
            adapter = None if args.adapter == "base" else args.adapter
            print(f"\nTargeting Model/Adapter: {adapter or client.BASE_MODEL} (Mock={args.mock})")
            res = client.generate(prompt=args.prompt, adapter=adapter)
            print(f"\nResponse ({res.latency_ms}ms):\n")
            print(res.content)
    finally:
        client.close()


if __name__ == "__main__":
    main()
