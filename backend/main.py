"""
AIFA Backend API — v1.0
FastAPI server: form input → scoring engine → LLM → style guide report
"""

import sys
import os
import time
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Add engine to path
ENGINE_DIR = Path(__file__).resolve().parents[1] / "knowledgeBase" / "engine"
sys.path.insert(0, str(ENGINE_DIR))

from scoring_engine import ScoringEngine, UserProfile
from prompt_builder import build_prompt_content
from llm_client import get_client, resolve_provider_params

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="AIFA API", version="1.0")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Single engine instance — reused across requests
engine = ScoringEngine()


# ---------------------------------------------------------------------------
# Request model with enum validation
# ---------------------------------------------------------------------------

class StyleRequest(BaseModel):
    # Required (5)
    build:         Literal["slim", "average", "athletic", "stocky", "heavy"]
    height:        Literal["short", "average", "tall"]
    face_shape:    Literal["small_delicate", "average", "wide_broad", "thin_narrow"]
    neck:          Literal["short", "average", "long", "thick"]
    skin_undertone: Literal["warm", "cool", "neutral"]

    # Recommended (4)
    body_shape:       Optional[Literal["trapezoid", "inverted_triangle", "rectangle", "triangle", "oval", "rhomboid"]] = None
    skin_depth:       Optional[Literal["light", "medium_light", "medium", "medium_dark", "dark"]] = None
    overall_contrast: Optional[Literal["low", "medium", "high"]] = None
    facial_hair:      Optional[Literal["clean_shaven", "stubble", "short_beard", "full_beard", "long_beard"]] = None

    # Optional (6)
    hair_style:          Optional[Literal["buzz_short", "medium", "long", "bald_balding"]] = None
    glasses_style:       Optional[Literal["none", "thin_frame", "bold_thick_frame", "round", "rectangular"]] = None
    torso_vs_leg_ratio:  Optional[Literal["long_torso", "balanced", "long_legs"]] = None
    waist_definition:    Optional[Literal["defined", "moderate", "undefined", "prominent"]] = None
    head_size:           Optional[Literal["small", "proportional", "large"]] = None
    style_track:         Literal["casual", "smart_casual"] = "casual"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "engine": "ready"}


@app.post("/api/generate-style-guide")
def generate_style_guide(req: StyleRequest):
    t0 = time.time()

    profile = UserProfile(
        build=req.build,
        height=req.height,
        face_shape=req.face_shape,
        neck=req.neck,
        skin_undertone=req.skin_undertone,
        body_shape=req.body_shape,
        skin_depth=req.skin_depth,
        overall_contrast=req.overall_contrast,
        facial_hair=req.facial_hair,
        hair_style=req.hair_style,
        glasses_style=req.glasses_style,
        torso_vs_leg_ratio=req.torso_vs_leg_ratio,
        waist_definition=req.waist_definition,
        head_size=req.head_size,
        style_track=req.style_track,
    )

    # Score
    score_sheet = engine.generate_score_sheet(profile)
    sheet_dict  = engine.score_sheet_to_dict(score_sheet)

    # Build prompt
    prompt = build_prompt_content(sheet_dict)

    # Call LLM
    try:
        provider, params = resolve_provider_params()
        client = get_client(provider)
        report_text, usage = client.call(prompt["system"], prompt["user"], params)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    total_s = round(time.time() - t0, 1)

    return {
        "report": report_text,
        "metadata": {
            "provider":      provider,
            "model":         params["model"],
            "input_tokens":  usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "conflicts":     sheet_dict["conflicts"],
            "total_time_s":  total_s,
        },
    }
