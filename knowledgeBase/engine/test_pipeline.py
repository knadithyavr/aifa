"""
AIFA Test Pipeline — v2.0
Runs 3 test profiles through the full engine → LLM pipeline.
Saves markdown reports + metadata to test_outputs/.

Provider/model selection (highest priority first):
  1. CLI args:   python3 test_pipeline.py --provider gemini --model gemini-2.0-flash
  2. Env vars:   AIFA_PROVIDER=gemini AIFA_MODEL=gemini-2.0-flash python3 test_pipeline.py
  3. Config:     edit active_provider in prompts/prompt-config.json
"""

import json
import time
import os
import sys
import argparse
from pathlib import Path

# Ensure engine dir is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from scoring_engine import ScoringEngine, UserProfile
from prompt_builder import build_prompt_content
from llm_client import get_client, resolve_provider_params

# ---------------------------------------------------------------------------
# Test profiles
# ---------------------------------------------------------------------------

TEST_PROFILES = {
    "heavy_short": UserProfile(
        build="heavy", height="short", body_shape="oval", face_shape="wide_broad",
        neck="short", facial_hair="full_beard", hair_style="bald_balding",
        glasses_style="none", head_size="proportional", skin_undertone="warm",
        overall_contrast="medium", skin_depth="medium_dark", style_track="casual",
    ),
    "slim_tall": UserProfile(
        build="slim", height="tall", body_shape="rectangle", face_shape="thin_narrow",
        neck="long", facial_hair="clean_shaven", hair_style="medium",
        glasses_style="thin_frame", head_size="small", skin_undertone="cool",
        overall_contrast="high", skin_depth="light", style_track="smart_casual",
    ),
    "athletic_average": UserProfile(
        build="athletic", height="average", body_shape="inverted_triangle", face_shape="average",
        neck="thick", facial_hair="stubble", hair_style="buzz_short",
        glasses_style="bold_thick_frame", head_size="proportional", skin_undertone="warm",
        overall_contrast="medium", skin_depth="medium", style_track="casual",
    ),
}

# ---------------------------------------------------------------------------
# Run a single profile
# ---------------------------------------------------------------------------

def run_profile(
    name: str,
    profile: UserProfile,
    output_dir: Path,
    engine: ScoringEngine,
    client,
    provider: str,
    params: dict,
) -> dict:
    print(f"\n{'='*60}")
    print(f"Profile:  {name}  ({profile.build} / {profile.height} / {profile.style_track})")
    print(f"Provider: {provider}  |  Model: {params['model']}")

    # --- Score ---
    t0 = time.time()
    score_sheet = engine.generate_score_sheet(profile)
    sheet_dict  = engine.score_sheet_to_dict(score_sheet)
    score_ms    = (time.time() - t0) * 1000
    print(f"  Scored in {score_ms:.0f}ms  — {len(sheet_dict['garment_scores'])} params")
    if sheet_dict["conflicts"]:
        print(f"  Conflicts: {sheet_dict['conflicts']}")

    # --- Build prompt ---
    prompt = build_prompt_content(sheet_dict)

    # --- Call LLM ---
    print(f"  Calling API...")
    t1 = time.time()
    report_text, usage = client.call(prompt["system"], prompt["user"], params)
    api_s = time.time() - t1

    word_count = len(report_text.split())
    print(f"  Done in {api_s:.1f}s  — {word_count} words")
    print(f"  Tokens: in={usage['input_tokens']:,}  out={usage['output_tokens']:,}")

    # --- Save ---
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / f"{name}_report.md"
    report_path.write_text(report_text, encoding="utf-8")

    meta = {
        "profile":       name,
        "provider":      provider,
        "model":         params["model"],
        "build":         profile.build,
        "height":        profile.height,
        "style_track":   profile.style_track,
        "conflicts":     sheet_dict["conflicts"],
        "score_time_ms": round(score_ms),
        "api_time_s":    round(api_s, 1),
        "word_count":    word_count,
        "input_tokens":  usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
    }
    (output_dir / f"{name}_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"  Saved: {report_path.name}")
    return meta


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="AIFA Test Pipeline")
    parser.add_argument("--provider", help="LLM provider: anthropic | gemini")
    parser.add_argument("--model",    help="Model name override (e.g. gemini-2.0-flash)")
    parser.add_argument("--profile",  help="Run single profile: heavy_short | slim_tall | athletic_average")
    return parser.parse_args()


def main():
    args = parse_args()

    # Resolve provider + params (CLI > env > config)
    provider, params = resolve_provider_params(
        provider=args.provider,
        model=args.model,
    )

    output_dir = Path(__file__).resolve().parent / "test_outputs"
    engine = ScoringEngine()
    client = get_client(provider)

    profiles = (
        {args.profile: TEST_PROFILES[args.profile]}
        if args.profile and args.profile in TEST_PROFILES
        else TEST_PROFILES
    )

    print("AIFA Test Pipeline")
    print(f"Provider: {provider}  |  Model: {params['model']}")
    print(f"Profiles: {list(profiles.keys())}")
    print(f"Output:   {output_dir}")

    all_meta = []
    for name, profile in profiles.items():
        try:
            meta = run_profile(name, profile, output_dir, engine, client, provider, params)
            all_meta.append(meta)
        except Exception as e:
            print(f"\n  ERROR running {name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print("Results:")
    for m in all_meta:
        print(f"  {m['profile']:20s}  {m['word_count']:4d} words  {m['api_time_s']}s  "
              f"in={m['input_tokens']:,}  out={m['output_tokens']:,}")


if __name__ == "__main__":
    main()
