"""
AIFA LLM Client — provider abstraction layer.
Supported providers: anthropic, gemini

Provider/model resolution order (highest to lowest priority):
  1. CLI args passed explicitly (--provider, --model)
  2. Env vars: AIFA_PROVIDER, AIFA_MODEL
  3. prompt-config.json active_provider block
"""

import os
import json
from abc import ABC, abstractmethod
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_config() -> dict:
    return json.loads((PROMPTS_DIR / "prompt-config.json").read_text(encoding="utf-8"))


def resolve_provider_params(provider: str = None, model: str = None) -> tuple[str, dict]:
    """
    Returns (resolved_provider, params_dict).
    Env vars override config; explicit args override env vars.
    """
    config = load_config()

    # Resolution order
    resolved_provider = (
        provider
        or os.getenv("AIFA_PROVIDER")
        or config.get("active_provider", "anthropic")
    )

    provider_block = config.get("providers", {}).get(resolved_provider)
    if not provider_block:
        available = list(config.get("providers", {}).keys())
        raise ValueError(
            f"Provider '{resolved_provider}' not in prompt-config.json. "
            f"Available: {available}"
        )

    # Copy params, strip _notes
    params = {k: v for k, v in provider_block.items() if not k.startswith("_")}

    # Model override (env var or explicit arg)
    model_override = model or os.getenv("AIFA_MODEL")
    if model_override:
        params["model"] = model_override

    return resolved_provider, params


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class LLMClient(ABC):
    """All providers implement this interface."""

    @abstractmethod
    def call(self, system: str, user_message: str, params: dict) -> tuple[str, dict]:
        """
        Make the API call.
        Returns:
          report_text: str
          usage: {"input_tokens": int, "output_tokens": int}
        """
        ...


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------

class AnthropicClient(LLMClient):
    def __init__(self):
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY not set in .env")
        self.client = anthropic.Anthropic(api_key=api_key)

    def call(self, system: str, user_message: str, params: dict) -> tuple[str, dict]:
        kwargs = {
            "model":       params["model"],
            "max_tokens":  params["max_tokens"],
            "temperature": params["temperature"],
            "system":      system,
            "messages":    [{"role": "user", "content": user_message}],
        }
        # thinking is optional — only Claude models that support it
        if "thinking" in params:
            kwargs["thinking"] = params["thinking"]

        response = self.client.messages.create(**kwargs)

        # Skip thinking blocks, concatenate text blocks
        text = "".join(b.text for b in response.content if b.type == "text")

        usage = {
            "input_tokens":  response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        return text, usage


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

class GeminiClient(LLMClient):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not set in .env")
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self._genai = genai

    def call(self, system: str, user_message: str, params: dict) -> tuple[str, dict]:
        genai = self._genai

        config_kwargs: dict = {
            "system_instruction": system,
            "max_output_tokens":  params.get("max_output_tokens", params.get("max_tokens", 16384)),
            "temperature":        params["temperature"],
        }
        # Gemini 2.5 Pro supports thinking_budget
        if "thinking_budget" in params:
            config_kwargs["thinking_config"] = genai.types.ThinkingConfig(
                thinking_budget=params["thinking_budget"]
            )

        response = self._client.models.generate_content(
            model=params["model"],
            contents=user_message,
            config=genai.types.GenerateContentConfig(**config_kwargs),
        )

        text = response.text
        meta = response.usage_metadata
        usage = {
            "input_tokens":  meta.prompt_token_count,
            "output_tokens": meta.candidates_token_count,
        }
        return text, usage


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, type[LLMClient]] = {
    "anthropic": AnthropicClient,
    "gemini":    GeminiClient,
}


def get_client(provider: str) -> LLMClient:
    cls = _REGISTRY.get(provider)
    if not cls:
        raise ValueError(
            f"Unknown provider '{provider}'. Available: {list(_REGISTRY.keys())}"
        )
    return cls()
