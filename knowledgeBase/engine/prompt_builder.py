"""
AIFA Prompt Builder — v2.0
Assembles system prompt + user message from score sheet + RAG chunks.
Provider-neutral: returns content dict, not a provider-shaped request.
"""

import json
import sys
from pathlib import Path

# Ensure engine dir is on path when imported from elsewhere
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scoring_engine import ScoringEngine, UserProfile

BASE_DIR    = Path(__file__).resolve().parent.parent  # knowledgeBase/
PROMPTS_DIR = BASE_DIR / "prompts"


def build_system_prompt() -> str:
    """Load and return system-prompt.md as a string."""
    return (PROMPTS_DIR / "system-prompt.md").read_text(encoding="utf-8")


def build_user_message(score_sheet: dict) -> str:
    """
    Load user-message-template.md and inject:
      {{SCORE_SHEET_JSON}}    → everything except rag_knowledge
      {{RAG_CHUNKS_CONTENT}}  → concatenated markdown from rag_knowledge[].content
    """
    template = (PROMPTS_DIR / "user-message-template.md").read_text(encoding="utf-8")

    # Score sheet JSON excludes rag_knowledge (that goes into RAG_CHUNKS_CONTENT)
    score_data = {k: v for k, v in score_sheet.items() if k != "rag_knowledge"}
    score_sheet_json = json.dumps(score_data, indent=2, ensure_ascii=False)

    # Concatenate RAG chunk content
    rag_chunks = score_sheet.get("rag_knowledge", [])
    rag_parts = []
    for chunk in rag_chunks:
        title   = chunk.get("title", "")
        content = chunk.get("content", "")
        rag_parts.append(f"## {title}\n\n{content}")
    rag_content = "\n\n---\n\n".join(rag_parts)

    message = template.replace("{{SCORE_SHEET_JSON}}", score_sheet_json)
    message = message.replace("{{RAG_CHUNKS_CONTENT}}", rag_content)

    return message


def build_prompt_content(score_sheet: dict) -> dict:
    """
    Returns provider-neutral prompt content.
    The LLM client decides how to pass system/user to its API.
    """
    return {
        "system": build_system_prompt(),
        "user":   build_user_message(score_sheet),
    }


# ---------------------------------------------------------------------------
# Kept for backward compatibility and estimate_tokens
# ---------------------------------------------------------------------------

def build_full_request(score_sheet: dict) -> dict:
    """
    Legacy helper — returns Anthropic-shaped dict.
    Prefer build_prompt_content() + llm_client.get_client() for new code.
    """
    from llm_client import resolve_provider_params
    provider, params = resolve_provider_params()
    content = build_prompt_content(score_sheet)
    return {
        "model":      params["model"],
        "max_tokens": params.get("max_tokens", params.get("max_output_tokens", 16384)),
        "temperature": params["temperature"],
        "thinking":   params.get("thinking"),
        "system":     content["system"],
        "messages":   [{"role": "user", "content": content["user"]}],
    }


def estimate_tokens(score_sheet: dict) -> dict:
    """Rough token estimate: len(string) // 4."""
    content    = build_prompt_content(score_sheet)
    system_len = len(content["system"]) // 4
    user_len   = len(content["user"]) // 4
    return {
        "system_tokens_approx": system_len,
        "user_tokens_approx":   user_len,
        "total_tokens_approx":  system_len + user_len,
    }


# ---------------------------------------------------------------------------
# Demo / CLI
# ---------------------------------------------------------------------------

def demo():
    engine = ScoringEngine()
    profile = UserProfile(
        build="heavy", height="short", body_shape="oval", face_shape="wide_broad",
        neck="short", facial_hair="full_beard", hair_style="bald_balding",
        glasses_style="none", head_size="proportional", skin_undertone="warm",
        overall_contrast="medium", skin_depth="medium_dark", style_track="casual",
    )

    score_sheet = engine.generate_score_sheet(profile)
    sheet_dict  = engine.score_sheet_to_dict(score_sheet)
    request     = build_full_request(sheet_dict)
    token_est   = estimate_tokens(sheet_dict)

    print("=== AIFA Prompt Builder Demo ===")
    print(f"Model:       {request['model']}")
    print(f"Max tokens:  {request['max_tokens']}")
    print(f"Temperature: {request['temperature']}")
    print(f"Thinking:    {request['thinking']}")
    print(f"\nToken estimates:")
    print(f"  System:  ~{token_est['system_tokens_approx']:,}")
    print(f"  User:    ~{token_est['user_tokens_approx']:,}")
    print(f"  Total:   ~{token_est['total_tokens_approx']:,}")
    print(f"\nSystem prompt preview (first 300 chars):")
    print(request["system"][:300])
    print(f"\nUser message preview (first 500 chars):")
    print(request["messages"][0]["content"][:500])

    output_path = Path(__file__).parent / "sample_prompt.json"
    save = {
        "model":               request["model"],
        "max_tokens":          request["max_tokens"],
        "temperature":         request["temperature"],
        "thinking":            request["thinking"],
        "system_preview":      request["system"][:500] + "...",
        "user_message_preview": request["messages"][0]["content"][:1000] + "...",
        "token_estimates":     token_est,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(save, f, indent=2, ensure_ascii=False)
    print(f"\nSaved → {output_path}")


if __name__ == "__main__":
    demo()
