"""
AIFA Scoring Engine — v1.0
Deterministic scoring of 35 garment params against user body inputs.
stdlib only — no pip packages needed.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent  # knowledgeBase/
RULES_DIR = BASE_DIR / "rules"
SCORING_RULES_PATH = RULES_DIR / "scoring-rules.json"
COLOR_RULES_PATH = RULES_DIR / "color-rules.json"
PAIRING_RULES_PATH = RULES_DIR / "pairing-rules.json"
TEMPLATES_PATH = BASE_DIR / "templates" / "outfit-templates.json"
RAG_CHUNKS_DIR = BASE_DIR / "rag-chunks" / "chunks"
RAG_INDEX_PATH = BASE_DIR / "rag-chunks" / "chunk-index.json"
BRAND_REF_PATH = RULES_DIR / "brand-reference.json"  # loaded but NOT used in V1 output

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class UserProfile:
    # Required
    build: str          # slim, average, athletic, stocky, heavy
    height: str         # short, average, tall
    # Optional body
    body_shape: Optional[str] = None        # trapezoid, inverted_triangle, rectangle, triangle, oval, rhomboid
    face_shape: Optional[str] = None        # small_delicate, average, wide_broad, thin_narrow
    neck: Optional[str] = None              # short, average, long, thick
    torso_vs_leg_ratio: Optional[str] = None  # long_torso, balanced, long_legs
    waist_definition: Optional[str] = None  # defined, moderate, undefined, prominent
    facial_hair: Optional[str] = None       # clean_shaven, stubble, short_beard, full_beard, long_beard
    hair_style: Optional[str] = None        # buzz_short, medium, long, bald_balding
    glasses_style: Optional[str] = None     # none, thin_frame, bold_thick_frame, round, rectangular
    head_size: Optional[str] = None         # small, proportional, large
    # Optional color
    skin_undertone: Optional[str] = None    # warm, cool, neutral
    overall_contrast: Optional[str] = None  # low, medium, high
    skin_depth: Optional[str] = None        # light, medium_light, medium, medium_dark, dark
    # Preference
    style_track: str = "casual"             # casual, smart_casual


@dataclass
class ScoredValue:
    value: str
    score: int
    label: str
    reason: Optional[str] = None


@dataclass
class ScoredParam:
    garment: str
    param: str
    values: List[ScoredValue]
    is_optional: bool = False


@dataclass
class PairingResult:
    base_item: str
    category: str
    pairs: List[Tuple]


@dataclass
class ScoreSheet:
    user_profile: dict
    garment_scores: List[ScoredParam]
    top_pairings: List[PairingResult]
    color_palette: dict
    conflicts: List[str]
    relevant_templates: List[dict]
    relevant_rag_chunks: List[dict]


# ---------------------------------------------------------------------------
# Factor resolution map
# ---------------------------------------------------------------------------

FACTOR_MAP: Dict[str, str] = {
    "D01.build":             "build",
    "D01.height":            "height",
    "D01.body_shape":        "body_shape",
    "D01.face_shape":        "face_shape",
    "D01.neck":              "neck",
    "D01.torso_vs_leg_ratio": "torso_vs_leg_ratio",
    "D01.waist_definition":  "waist_definition",
    "D01.facial_hair":       "facial_hair",
    "D01.hair_style":        "hair_style",
    "D01.glasses_style":     "glasses_style",
    "D01.head_size":         "head_size",
    "D03.skin_depth":        "skin_depth",
    "D05.style_track":       "style_track",
}

NEAR_FACE_GARMENTS  = {"tshirt", "polo", "casual_shirt"}
LOWER_BODY_GARMENTS = {"jeans", "chinos", "shorts"}
FOOTWEAR_GARMENTS   = {"sneakers", "casual_shoes", "sandals"}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ScoringEngine:
    def __init__(self):
        self.scoring_rules = json.loads(SCORING_RULES_PATH.read_text(encoding="utf-8"))
        self.color_rules   = json.loads(COLOR_RULES_PATH.read_text(encoding="utf-8"))
        self.pairing_rules = json.loads(PAIRING_RULES_PATH.read_text(encoding="utf-8"))
        self.templates_data = json.loads(TEMPLATES_PATH.read_text(encoding="utf-8"))
        self.rag_index     = json.loads(RAG_INDEX_PATH.read_text(encoding="utf-8"))
        # brand_reference loaded but not used in V1 output
        self.brand_ref     = json.loads(BRAND_REF_PATH.read_text(encoding="utf-8")) if BRAND_REF_PATH.exists() else {}

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _resolve_factor(self, factor_key: str, profile: UserProfile) -> Optional[str]:
        attr = FACTOR_MAP.get(factor_key)
        if attr:
            return getattr(profile, attr, None)
        return None

    def _get_label(self, score: int) -> str:
        if score >= 9: return "best"
        if score >= 7: return "great"
        if score >= 5: return "okay"
        if score >= 3: return "caution"
        return "avoid"

    def _get_tier(self, score: int) -> str:
        if score >= 9: return "recommend"
        if score >= 7: return "good_alternatives"
        if score >= 5: return "acceptable"
        return "avoid"

    def _get_valid_colors(self, garment: str, color_palette: dict) -> List[str]:
        """
        CRITICAL FIX #2: Pre-attach colors per garment zone, filtered by avoid list.
        Without this, warm colors like olive leak into cool-undertone recommendations.
        """
        if not color_palette:
            return []

        avoid_colors = set(color_palette.get("avoid_colors", []))

        def filter_avoid(colors: List[str]) -> List[str]:
            return [c for c in colors if c not in avoid_colors]

        best_colors = color_palette.get("best_colors", [])
        good_colors = color_palette.get("good_colors", [])

        if garment in NEAR_FACE_GARMENTS:
            # Colors near face matter most — full palette, avoid filtered
            return filter_avoid(best_colors + good_colors)

        elif garment in LOWER_BODY_GARMENTS:
            # Base: neutral universals + palette darks (first 5 best colors)
            universal_safe = ["navy", "charcoal", "dark_denim", "black", "olive"]
            palette_darks = best_colors[:5]
            combined = list(dict.fromkeys(universal_safe + palette_darks))  # dedup, order preserved
            return filter_avoid(combined)  # THIS FILTERING IS CRITICAL — removes olive for cool undertones

        elif garment in FOOTWEAR_GARMENTS:
            universal_safe = ["white", "black", "brown", "navy", "grey"]
            return filter_avoid(universal_safe)

        elif garment == "casual_jacket":
            # Layers frame upper body — treat like near-face but add neutrals
            neutral_base = ["black", "navy", "charcoal", "olive", "grey"]
            return filter_avoid(list(dict.fromkeys(best_colors[:5] + neutral_base)))

        else:
            return filter_avoid(best_colors)

    # -----------------------------------------------------------------------
    # Scoring
    # -----------------------------------------------------------------------

    def _score_param(self, garment: str, param: str, param_data: dict, profile: UserProfile) -> ScoredParam:
        primary_factor = param_data.get("primary_factor", "")
        primary_value  = self._resolve_factor(primary_factor, profile)
        base_scores    = param_data.get("base_scores", {})
        adjustments    = param_data.get("adjustments", [])
        reasons        = param_data.get("reasons", {})
        values         = param_data.get("values", [])

        scored_values: List[ScoredValue] = []

        for value in values:
            # Step 3-4: Base score from primary factor (default 5 if not provided)
            if primary_value is not None:
                base = base_scores.get(value, {}).get(primary_value, 5)
            else:
                base = 5

            # Step 5: Apply adjustments from secondary factors
            total = base
            for adj in adjustments:
                factor_key   = adj.get("factor", "")
                factor_value = self._resolve_factor(factor_key, profile)
                if factor_value is not None:
                    delta = adj.get("scores", {}).get(factor_value, {}).get(value, 0)
                    total += delta

            # Step 6: Clamp to 1-10
            final_score = max(1, min(10, total))

            # Step 7: Label
            label = self._get_label(final_score)

            # Step 8: Reason — try combo keys in priority order
            reason = None
            candidates = [
                f"{value}+{primary_value}" if primary_value else None,
                f"{value}+{profile.build}",
                f"{value}+{profile.height}",
                f"{value}+{profile.body_shape}" if profile.body_shape else None,
                f"{value}+{profile.face_shape}" if profile.face_shape else None,
            ]
            for key in candidates:
                if key and key in reasons:
                    reason = reasons[key]
                    break

            scored_values.append(ScoredValue(
                value=value,
                score=final_score,
                label=label,
                reason=reason
            ))

        # Step 9: Sort descending by score
        scored_values.sort(key=lambda sv: sv.score, reverse=True)

        return ScoredParam(
            garment=garment,
            param=param,
            values=scored_values,
            is_optional=False
        )

    # -----------------------------------------------------------------------
    # Color palette
    # -----------------------------------------------------------------------

    def get_color_palette(self, profile: UserProfile) -> dict:
        if not profile.skin_undertone:
            return {}

        undertone  = profile.skin_undertone
        palette    = self.color_rules["undertone_palettes"].get(undertone, {})
        color_rules = self.color_rules

        result: dict = {
            "undertone":         undertone,
            "best_colors":       palette.get("best_colors", []),
            "good_colors":       palette.get("good_colors", []),
            "avoid_colors":      palette.get("avoid_colors", []),
            "metal":             palette.get("metal", ""),
            "avoid_metal":       palette.get("avoid_metal", ""),
            "near_face_priority": palette.get("near_face_priority", ""),
        }

        # Contrast approach
        if profile.overall_contrast:
            contrast_key_map = {"high": "high_contrast", "medium": "medium_contrast", "low": "low_contrast"}
            contrast_key = contrast_key_map.get(profile.overall_contrast, "medium_contrast")
            contrast_info = color_rules["contrast_palettes"].get(contrast_key, {})
            result["contrast_approach"] = contrast_info.get("outfit_approach", "")
            result["contrast_combinations"] = contrast_info.get("recommended_combinations", [])

        # Indian skin specific — match by undertone in profile description
        if profile.skin_depth:
            for indian_profile in color_rules.get("indian_skin_specific", {}).get("common_profiles", []):
                if undertone in indian_profile.get("undertone", ""):
                    result["indian_profile_note"] = indian_profile.get("note", "")
                    result["best_near_face_indian"] = indian_profile.get("best_near_face", [])
                    break

        result["zone_guidance"] = color_rules.get("garment_zone_priority", {})

        return result

    # -----------------------------------------------------------------------
    # Pairings
    # -----------------------------------------------------------------------

    def get_pairings(self, garment_scores: List[ScoredParam]) -> List[PairingResult]:
        pr = self.pairing_rules
        results: List[PairingResult] = []

        # 1. top_x_bottom — top 5 pairs per entry
        for base_item, pairs_dict in pr.get("top_x_bottom", {}).items():
            if base_item == "description":
                continue
            numeric = {k: v for k, v in pairs_dict.items() if isinstance(v, (int, float))}
            top5 = sorted(numeric.items(), key=lambda x: x[1], reverse=True)[:5]
            results.append(PairingResult(base_item=base_item, category="top_x_bottom", pairs=top5))

        # 2. bottom_x_footwear — top 5 pairs per entry
        for base_item, pairs_dict in pr.get("bottom_x_footwear", {}).items():
            if base_item == "description":
                continue
            numeric = {k: v for k, v in pairs_dict.items() if isinstance(v, (int, float))}
            top5 = sorted(numeric.items(), key=lambda x: x[1], reverse=True)[:5]
            results.append(PairingResult(base_item=base_item, category="bottom_x_footwear", pairs=top5))

        # 3. optional_layers — top 3 pairs per layer
        for layer_name, layer_data in pr.get("optional_layers", {}).items():
            if layer_name in ("description", "is_always_optional"):
                continue
            if not isinstance(layer_data, dict):
                continue
            pairs_dict = layer_data.get("pairs_best_with", {})
            numeric = {k: v for k, v in pairs_dict.items() if isinstance(v, (int, float))}
            top3 = sorted(numeric.items(), key=lambda x: x[1], reverse=True)[:3]
            results.append(PairingResult(base_item=layer_name, category="optional_layers", pairs=top3))

        # 4. color_pairing_guidance — top 5 safe combos
        safe_combos = pr.get("color_pairing_guidance", {}).get("safe_combinations", [])
        top_colors = sorted(safe_combos, key=lambda x: x.get("score", 0), reverse=True)[:5]
        color_pairs = [
            (c.get("top", ""), c.get("bottom", ""), c.get("footwear", ""),
             c.get("score", 0), c.get("note", ""))
            for c in top_colors
        ]
        results.append(PairingResult(base_item="color_combinations", category="color_pairing_guidance", pairs=color_pairs))

        # 5. anti_pairings — all rules
        anti_rules = pr.get("anti_pairings", {}).get("rules", [])
        anti_pairs = [
            (r.get("combo", ""), r.get("score", 0), r.get("reason", ""))
            for r in anti_rules
        ]
        results.append(PairingResult(base_item="anti_pairings", category="anti_pairings", pairs=anti_pairs))

        return results

    # -----------------------------------------------------------------------
    # Conflict detection (7 body-only patterns)
    # -----------------------------------------------------------------------

    def detect_conflicts(self, profile: UserProfile) -> List[str]:
        conflicts: List[str] = []
        b = profile.build
        h = profile.height
        bs = profile.body_shape
        fs = profile.face_shape
        nk = profile.neck

        if h == "short" and b == "heavy":
            conflicts.append("Prioritize monochrome dark outfits")
        if h == "tall" and b == "slim":
            conflicts.append("Add horizontal elements without going oversized")
        if h == "short" and b == "slim":
            conflicts.append("Fitted clothes with structure, avoid oversized")
        if h == "tall" and b == "heavy":
            conflicts.append("Most styles work, ensure correct fit")
        if b == "athletic" and bs == "inverted_triangle":
            conflicts.append("Avoid adding shoulder width, use tapered bottoms")
        if fs == "wide_broad" and nk == "short":
            conflicts.append("V-necklines critical")
        if fs == "thin_narrow" and nk == "long":
            conflicts.append("Crew/mock necks work, avoid deep V")

        return conflicts

    # -----------------------------------------------------------------------
    # Template selection
    # -----------------------------------------------------------------------

    def select_templates(self, profile: UserProfile, max_templates: int = 8) -> List[dict]:
        adjacent_tracks = {"casual": ["smart_casual"], "smart_casual": ["casual"]}
        scored: List[Tuple[int, dict]] = []

        for tmpl in self.templates_data.get("templates", []):
            score = 0
            tmpl_track = tmpl.get("style_track", "")

            if tmpl_track == profile.style_track:
                score += 3
            elif tmpl_track in adjacent_tracks.get(profile.style_track, []):
                score += 1

            body_adap = tmpl.get("body_adaptations", {})
            if profile.build and profile.build in body_adap:
                score += 2
            if profile.height and profile.height in body_adap:
                score += 2

            scored.append((score, tmpl))

        scored.sort(key=lambda x: x[0], reverse=True)

        result: List[dict] = []
        for _, tmpl in scored[:max_templates]:
            t = dict(tmpl)
            body_adap = t.get("body_adaptations", {})
            your_adaptations: dict = {}
            if profile.build and profile.build in body_adap:
                your_adaptations["build"] = body_adap[profile.build]
            if profile.height and profile.height in body_adap:
                your_adaptations["height"] = body_adap[profile.height]
            t["your_adaptations"] = your_adaptations
            result.append(t)

        return result

    # -----------------------------------------------------------------------
    # RAG chunk selection
    # -----------------------------------------------------------------------

    def select_rag_chunks(self, profile: UserProfile, max_chunks: int = 5) -> List[dict]:
        always_include = {
            "body-type-dressing.md": 5,
            "fit-guide-casual.md":   4,
        }

        scored: List[Tuple[int, dict]] = []

        for chunk in self.rag_index.get("chunks", []):
            base = always_include.get(chunk["file"], 0)
            tags = [t.lower() for t in chunk.get("retrieval_tags", [])]
            style_tracks = chunk.get("style_tracks", [])

            # +3 color/skin chunks if user has undertone
            if profile.skin_undertone and any(t in tags for t in ["color", "colour", "skin", "undertone", "indian skin"]):
                base += 3

            # +2 face/glasses chunks if user has face_shape
            if profile.face_shape and any(t in tags for t in ["face", "face shape", "sunglasses", "glasses", "eyewear"]):
                base += 2

            # +2 if chunk tags match user's build
            if profile.build and any(profile.build in t for t in tags):
                base += 2

            # +1 if chunk tags match height or style_track
            if profile.height and any(profile.height in t for t in tags):
                base += 1
            if profile.style_track and profile.style_track in style_tracks:
                base += 1

            scored.append((base, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)

        result: List[dict] = []
        for _, chunk in scored[:max_chunks]:
            chunk_file = RAG_CHUNKS_DIR / chunk["file"]
            content = chunk_file.read_text(encoding="utf-8") if chunk_file.exists() else ""
            result.append({
                "id":      chunk["id"],
                "title":   chunk["title"],
                "file":    chunk["file"],
                "content": content,
            })

        return result

    # -----------------------------------------------------------------------
    # Main entry point
    # -----------------------------------------------------------------------

    def generate_score_sheet(self, profile: UserProfile) -> ScoreSheet:
        garment_scores: List[ScoredParam] = []

        for garment, params in self.scoring_rules["garment_categories"].items():
            for param, param_data in params.items():
                sp = self._score_param(garment, param, param_data, profile)
                garment_scores.append(sp)

        color_palette = self.get_color_palette(profile)
        pairings      = self.get_pairings(garment_scores)
        conflicts     = self.detect_conflicts(profile)
        templates     = self.select_templates(profile)
        rag_chunks    = self.select_rag_chunks(profile)

        return ScoreSheet(
            user_profile=vars(profile),
            garment_scores=garment_scores,
            top_pairings=pairings,
            color_palette=color_palette,
            conflicts=conflicts,
            relevant_templates=templates,
            relevant_rag_chunks=rag_chunks,
        )

    # -----------------------------------------------------------------------
    # Serialization
    # -----------------------------------------------------------------------

    def score_sheet_to_dict(self, score_sheet: ScoreSheet) -> dict:
        """
        CRITICAL FIX #1: Output pre-classified tiers (not raw value lists).
        CRITICAL FIX #3: No brand_reference in output.
        """
        color_palette = score_sheet.color_palette

        garment_scores_out = []
        for sp in score_sheet.garment_scores:
            tiers: Dict[str, list] = {
                "recommend":        [],
                "good_alternatives": [],
                "acceptable":       [],
                "avoid":            [],
            }
            for sv in sp.values:
                tier = self._get_tier(sv.score)
                entry: dict = {"value": sv.value, "score": sv.score}
                if sv.reason:
                    entry["reason"] = sv.reason
                tiers[tier].append(entry)

            valid_colors = self._get_valid_colors(sp.garment, color_palette)

            garment_scores_out.append({
                "garment":     sp.garment,
                "param":       sp.param,
                "tiers":       tiers,
                "your_colors": valid_colors,
            })

        return {
            "user_profile":       score_sheet.user_profile,
            "conflicts":          score_sheet.conflicts,
            "garment_scores":     garment_scores_out,
            "pairings": [
                {
                    "base_item": p.base_item,
                    "category":  p.category,
                    "pairs":     [list(pair) for pair in p.pairs],
                }
                for p in score_sheet.top_pairings
            ],
            "color_palette":      color_palette,
            "relevant_templates": score_sheet.relevant_templates,
            "rag_knowledge":      score_sheet.relevant_rag_chunks,
            # brand_reference intentionally excluded (CRITICAL FIX #3)
        }


# ---------------------------------------------------------------------------
# Demo / CLI
# ---------------------------------------------------------------------------

def demo():
    profile = UserProfile(
        build="heavy",
        height="short",
        body_shape="oval",
        face_shape="wide_broad",
        neck="short",
        facial_hair="full_beard",
        hair_style="bald_balding",
        glasses_style="none",
        head_size="proportional",
        skin_undertone="warm",
        overall_contrast="medium",
        skin_depth="medium_dark",
        style_track="casual",
    )

    engine = ScoringEngine()
    score_sheet = engine.generate_score_sheet(profile)
    sheet_dict  = engine.score_sheet_to_dict(score_sheet)

    print("=== AIFA Scoring Engine Demo ===")
    print(f"\nProfile: {profile.build} build, {profile.height} height, {profile.style_track} track")
    print(f"Conflicts ({len(sheet_dict['conflicts'])}):")
    for c in sheet_dict["conflicts"]:
        print(f"  • {c}")

    cp = sheet_dict["color_palette"]
    print(f"\nColor palette: {cp.get('undertone', 'N/A')} undertone")
    print(f"  Best colors: {cp.get('best_colors', [])[:5]}")
    print(f"  Avoid:       {cp.get('avoid_colors', [])[:4]}")
    print(f"  Metal:       {cp.get('metal', 'N/A')}")

    print(f"\nGarment scores ({len(sheet_dict['garment_scores'])} params):")
    for gs in sheet_dict["garment_scores"]:
        recs   = [r["value"] for r in gs["tiers"]["recommend"]]
        avoids = [r["value"] for r in gs["tiers"]["avoid"]]
        print(f"  {gs['garment']}.{gs['param']:20s}  recommend={recs}  avoid={avoids}")

    print(f"\nTemplates selected: {len(sheet_dict['relevant_templates'])}")
    for t in sheet_dict["relevant_templates"]:
        print(f"  [{t['id']}] {t['name']}  (adaptations: {list(t.get('your_adaptations', {}).keys())})")

    print(f"\nRAG chunks selected: {len(sheet_dict['rag_knowledge'])}")
    for r in sheet_dict["rag_knowledge"]:
        print(f"  {r['id']}: {r['title']}")

    # Save full JSON (without rag content for readability)
    save_dict = {k: v for k, v in sheet_dict.items() if k != "rag_knowledge"}
    save_dict["rag_knowledge_titles"] = [c["title"] for c in sheet_dict.get("rag_knowledge", [])]

    output_path = Path(__file__).parent / "sample_output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(save_dict, f, indent=2, ensure_ascii=False)
    print(f"\nSaved full output → {output_path}")


if __name__ == "__main__":
    demo()
