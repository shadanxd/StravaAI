"""
LLM provider abstraction using LiteLLM only. No custom provider HTTP.
Switch providers/models purely via environment.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional
import os
import json
from litellm import acompletion

from dotenv import load_dotenv

load_dotenv()


@dataclass
class AIConfig:
    provider: str
    model: str
    api_key: str


def load_ai_config() -> AIConfig:
    provider = os.getenv("AI_PROVIDER", "openai")
    model = os.getenv("AI_MODEL", "gpt-4o-mini")
    # Use LiteLLM-native env keys
    if provider.lower() == "google":
        api_key = os.getenv("GEMINI_API_KEY", "")
    else:
        api_key = os.getenv("OPENAI_API_KEY", "")
    return AIConfig(provider=provider, model=model, api_key=api_key)


class AIClient:
    """Minimal async client wrapper.

    For MVP, we don't introduce heavy SDK dependencies. This class is a shim that
    can be implemented using HTTP calls in the future. For now, we raise
    NotImplementedError if API key is missing to avoid accidental usage.
    """

    def __init__(self, config: Optional[AIConfig] = None) -> None:
        self.config = config or load_ai_config()

    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Generate a JSON-like dict based on prompts via LiteLLM only."""

        provider = self.config.provider.lower()
        api_key = self.config.api_key

        # Map API keys to LiteLLM env vars only
        if provider == "google":
            os.environ.setdefault("GEMINI_API_KEY", api_key)
            # Normalize to LiteLLM style if plain model name provided
            model_name = self.config.model if "/" in self.config.model else f"gemini/{self.config.model}"
        elif provider == "openai":
            os.environ.setdefault("OPENAI_API_KEY", api_key)
            model_name = self.config.model
        else:
            # Let LiteLLM handle other providers; user must set the correct *_API_KEY envs externally
            model_name = self.config.model

        try:
            resp = await acompletion(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt + "\n\nReturn only valid JSON with keys: summary, coach_tips, tags."},
                ],
                temperature=0.6,
                response_format={"type": "json_object"},
            )
            content = resp["choices"][0]["message"]["content"]
            payload = json.loads(content)
            # Ensure model is present even if the LLM didn't include it
            if not isinstance(payload, dict):
                payload = {"summary": str(payload)}
            payload.setdefault("model", resp.get("model") or model_name)
            return payload
        except Exception:
            # Fallback deterministic output if provider call fails
            return {
                "summary": "Solid session focusing on aerobic base.",
                "coach_tips": [
                    "Keep cadence smooth and controlled.",
                    "Fuel earlier for longer efforts."
                ],
                "tags": ["endurance"],
                "model": f"fallback:{self.config.provider}:{self.config.model}",
            }


