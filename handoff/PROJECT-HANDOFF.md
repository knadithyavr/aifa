# AIFA — AI Fashion Advisor for Indian Men
## Complete Project Handoff Document

**Created:** 2026-04-06
**Purpose:** This document contains everything needed to continue development in a new Claude session. The Python engine code must be REGENERATED (not copied) — this document provides the exact specification.

---

## 1. WHAT IS THIS PROJECT

AIFA is a **one-shot AI style consultation system** for Indian men. User fills a form → system generates a **comprehensive personalized style guide** (~3500 words) covering which clothing fits/styles suit their body, colors for their skin tone, what pairs with what, outfit ideas, tailoring tips, and a starter kit.

**Target user:** Indian men, 18-40, everyday casual to smart-casual wear. T-shirts, jeans, polos, chinos, sneakers — what 80% of urban Indian men wear daily.

**Flow:**
```
User fills form (15 fields: body, face, skin, preferences)
↓
Scoring Engine (Python, deterministic, ~50ms)
→ Scores 35 garment params → Pre-classifies tiers → Pre-attaches colors
→ Selects templates + RAG chunks
↓
Prompt Builder (Python)
→ Assembles system prompt + score sheet + RAG + instructions (~30K tokens)
↓
Claude Sonnet 4.6 (~120s)
→ Decides, reasons, resolves conflicts
→ Produces ~3500 word markdown report
↓
User receives personalized style guide
```

---

## 2. PROJECT STATUS

### DONE
- Knowledge base: 9 taxonomy domains, 218 params, v1.1
- Scoring rules: 35 params, 192 values, 10 garment categories
- Color rules: 3 undertone palettes, 4 Indian skin profiles
- Pairing rules: 21 top×bottom, 16 bottom×foot, 11 top×foot, 10 layers, 15 anti-pairings
- Input schema: 15 fields (5 required, 4 recommended, 6 optional)
- Output schema: 16 report sections with word targets
- Prompt templates: system prompt + user message template (loosely coupled files)
- Tested with 7 profiles, audited, fixes applied, avg score 8.2/10
- Constraints (50 rules), templates (40 outfits), RAG chunks (15 guides) — all done
- Brand reference file (kept for V2, NOT used in V1)

### TO DO (in new session)
1. **Regenerate engine code** (scoring_engine.py, prompt_builder.py, test_pipeline.py) — specs in this doc
2. **Backend API** (FastAPI) — endpoint: form input → engine → Claude → report
3. **Frontend** — form + report renderer
4. **Deploy**

### V2 (not now)
- Ethnic wear, accessories scoring, climate filtering, brand recs, glasses styling, user feedback loop

---

## 3. FILE STRUCTURE

```
aifa/
├── knowlegeBase/
│ ├── taxonomy/ ← 9 domain files v1.1 (DO NOT MODIFY)
│ │ ├── domain-01-body-proportions.json (18 params incl facial_hair, hair_style, glasses_style)
│ │ ├── domain-02-visual-balance-theory.json
│ │ ├── domain-03-color-coloring.json
│ │ ├── domain-04-garment-properties.json (58 params — largest, includes casual garments)
│ │ ├── domain-05-personal-style-profiling.json
│ │ ├── domain-06-aesthetics-style-systems.json
│ │ ├── domain-07-occasion-context-mapping.json
│ │ ├── domain-08-fabric-texture-behavior.json
│ │ └── domain-09-garment-taxonomy.json
│ │
│ ├── rules/
│ │ ├── scoring-rules.json ← 35 params scored against body inputs (THE CORE DATA)
│ │ ├── color-rules.json ← Undertone→palette, avoid lists, Indian profiles
│ │ ├── pairing-rules.json ← Compatibility matrix + anti-pairings
│ │ └── brand-reference.json ← NOT used in V1 (brands removed intentionally)
│ │
│ ├── constraints/constraints.json ← 50 rules, kept for V2
│ ├── templates/outfit-templates.json ← 40 templates with body adaptations
│ │
│ ├── rag-chunks/
│ │ ├── chunks/ (15 .md files) ← body-type-dressing, fit-guide, color, jeans, etc.
│ │ └── chunk-index.json
│ │
│ ├── schemas/
│ │ ├── input-schema.json ← 15 user input fields (single source of truth)
│ │ └── output-schema.json ← 16 report sections (single source of truth)
│ │
│ ├── prompts/
│ │ ├── prompt-config.json ← model, temperature, max_tokens
│ │ ├── system-prompt.md ← Persona "Vastra", rules, guardrails, tier interpretation
│ │ └── user-message-template.md ← Data layout, analysis steps, output format, example
│ │
│ └── engine/ ← MUST BE REGENERATED (Python code cannot be copied)
│ ├── scoring_engine.py ← Regenerate from spec below
│ ├── prompt_builder.py ← Regenerate from spec below
│ ├── test_pipeline.py ← Regenerate from spec below
│ └── .env ← Create fresh with new API key
│
├── handoff/
│ └── PROJECT-HANDOFF.md ← THIS FILE
│
├── dressing-the-man/ ← Flusser source text files
└── gentleman/ ← Roetzel source text files
```

---

## 4. ENGINE SPECIFICATION (for regeneration)

### 4.1 scoring_engine.py — EXACT SPEC

**Dependencies:** json, pathlib, dataclasses, typing (stdlib only - no pip packages)

**File paths (relative to engine/):**
```
BASE_DIR = Path(__file__).resolve().parent.parent # knowlegeBase/
RULES_DIR = BASE_DIR / "rules"
SCORING_RULES_PATH = RULES_DIR / "scoring-rules.json"
COLOR_RULES_PATH = RULES_DIR / "color-rules.json"
PAIRING_RULES_PATH = RULES_DIR / "pairing-rules.json"
TEMPLATES_PATH = BASE_DIR / "templates" / "outfit-templates.json"
RAG_CHUNKS_DIR = BASE_DIR / "rag-chunks" / "chunks"
RAG_INDEX_PATH = BASE_DIR / "rag-chunks" / "chunk-index.json"
BRAND_REF_PATH = RULES_DIR / "brand-reference.json" # loaded but NOT used in V1 output
```

**Dataclasses:**

```
UserProfile:
# Required
build: str # slim, average, athletic, stocky, heavy
height: str # short, average, tall
# Optional body
body_shape: Optional[str] # trapezoid, inverted_triangle, rectangle, triangle, oval, rhomboid
face_shape: Optional[str] # small_delicate, average, wide_broad, thin_narrow
neck: Optional[str] # short, average, long, thick
torso_vs_leg_ratio: Optional[str] # long_torso, balanced, long_legs
waist_definition: Optional[str] # defined, moderate, undefined, prominent
facial_hair: Optional[str] # clean_shaven, stubble, short_beard, full_beard, long_beard
hair_style: Optional[str] # buzz_short, medium, long, bald_balding
glasses_style: Optional[str] # none, thin_frame, bold_thick_frame, round, rectangular
head_size: Optional[str] # small, proportional, large
# Optional color
skin_undertone: Optional[str] # warm, cool, neutral
overall_contrast: Optional[str] # low, medium, high
skin_depth: Optional[str] # light, medium_light, medium, medium_dark, dark
# Preference
style_track: str = "casual" # casual, smart_casual

ScoredValue: value(str), score(int), label(str), reason(Optional[str])
ScoredParam: garment(str), param(str), values(list[ScoredValue]), is_optional(bool)
PairingResult: base_item(str), category(str), pairs(list[tuple])
ScoreSheet: user_profile(dict), garment_scores(list), top_pairings(list), color_palette(dict), conflicts(list), relevant_templates(list), relevant_rag_chunks(list)
```

**Scoring Algorithm (EXACT):**

```
For each garment param in scoring-rules.json:
1. Read primary_factor (e.g., "D01.build")
2. Resolve factor value from UserProfile (build → "heavy")
3. Get BASE SCORE from base_scores[value_name][factor_value]
e.g., base_scores["straight"]["heavy"] = 9
4. If factor not provided → default all to 5
5. For each adjustment in adjustments[]:
a. Resolve adjustment factor from profile
b. If provided, add delta: adjusted[value] += delta
6. CLAMP result to 1-10: max(1, min(10, score))
7. Assign LABEL: 9-10="best", 7-8="great", 5-6="okay", 3-4="caution", 1-2="avoid"
8. Get REASON text by trying combo keys: "{value}+{build}", "{value}+{height}", etc.
9. Sort values by score descending
```

**Factor Resolution Map:**
```python
"D01.build" → profile.build
"D01.height" → profile.height
"D01.body_shape" → profile.body_shape
"D01.face_shape" → profile.face_shape
"D01.neck" → profile.neck
"D01.torso_vs_leg_ratio" → profile.torso_vs_leg_ratio
"D01.waist_definition" → profile.waist_definition
"D01.facial_hair" → profile.facial_hair
"D01.hair_style" → profile.hair_style
"D01.glasses_style" → profile.glasses_style
"D01.head_size" → profile.head_size
"D03.skin_depth" → profile.skin_depth
"D05.style_track" → profile.style_track
```

**CRITICAL FIX #1: Pre-Classified Tiers**

The `score_sheet_to_dict()` method must output tiers, NOT raw value lists:
```json
{
"garment": "jeans",
"param": "fit",
"tiers": {
"recommend": [{"value": "straight", "score": 10, "reason": "..."}],
"good_alternatives": [{"value": "regular", "score": 8}],
"acceptable": [{"value": "tapered", "score": 6}],
"avoid": [{"value": "skinny", "score": 1, "reason": "..."}]
},
"your_colors": ["navy", "charcoal", "dark_denim", "black"]
}
```
Tier boundaries: recommend=9-10, good_alternatives=7-8, acceptable=5-6, avoid=1-4.

**CRITICAL FIX #2: Pre-Attached Colors with Avoid-list Filtering**

Each garment score includes `your_colors` — valid colors for that garment zone, filtered against the user's undertone avoid list.

```
_get_valid_colors(garment, color_palette):
avoid_colors = palette.avoid_colors

if garment is near-face (tshirt, polo, casual_shirt):
return filter_avoid(best_colors + good_colors)
elif garment is lower-body (jeans, chinos, shorts):
base = universal_safe (navy, charcoal, dark_denim, black, olive)
add palette darks
return filter_avoid(base + palette_darks) ← THIS FILTERING IS CRITICAL
elif garment is footwear:
return filter_avoid(universal_safe)

filter_avoid = remove any color in avoid_colors list
```

**WHY THIS MATTERS:** Without this filter, olive (a warm color) leaks into cool-undertone recommendations via the universal safe list. The filter removes it.

**CRITICAL FIX #3: No Brands in V1 Output**

`score_sheet_to_dict()` does NOT include brand_reference in its output. The system prompt says "Do NOT recommend specific brands or stores."

**Color Palette Method:**
```
get_color_palette(profile):
1. Look up undertone_palettes[skin_undertone] → best_colors, avoid_colors, metal
2. Look up contrast_palettes[overall_contrast] → outfit approach
3. Match indian_skin_specific profile by undertone
4. Include zone_guidance (near_face, lower_body, footwear zones)
```
**Pairing Method:**
```
get_pairings(garment_scores):
1. Read top_x_bottom from pairing-rules.json → top 5 pairs per entry
2. Read bottom_x_footwear → top 5 pairs per entry
3. Read optional_layers → top 3 pairs per layer
4. Read color_pairing_guidance → top 5 safe combos
5. Read anti_pairings → all anti-pairings (to be avoided)
```

**Conflict Detection (body-only, 7 patterns):**
```
if short + heavy → "Prioritize monochrome dark outfits"
if tall + slim → "Add horizontal elements without going oversized"
if short + slim → "Fitted clothes with structure, avoid oversized"
if tall + heavy → "Most styles work, ensure correct fit"
if athletic + inverted_triangle → "Avoid adding shoulder width, use tapered bottoms"
if wide_broad face + short neck → "V-necklines critical"
if thin_narrow face + long neck → "Crew/mock necks work, avoid deep V"
```

**Template Selection:**
```
select_templates(profile, max=8):
Score each template:
+3 if style_track matches
+1 if adjacent style_track
+2 if body_adaptations has user's build
+2 if body_adaptations has user's height
Sort by score, take top 8
Personalize: attach user's specific build/height adaptations
```

**RAG Chunk Selection:**
```
select_rag_chunks(profile, max=5):
Always include: body-type-dressing.md (+5), fit-guide-casual.md (+4)
+3 if user has skin_undertone and chunk has "color"/"skin" tags
+2 if chunk has "face"/"sunglasses" tags and user has face_shape
+2 if chunk tags match user's build
+1 if chunk tags match user's height or style_track
Sort by score, take top 5
Load actual markdown content from chunk files
```

**Demo/CLI:**
```
Create a demo() function that:
1. Creates a sample UserProfile (heavy/short/oval/wide_broad/short_neck/warm/casual)
2. Runs generate_score_sheet()
3. Prints summary: garment scores, conflicts, color palette, templates, RAG chunks
4. Saves full JSON output to sample_output.json
```
### 4.2 prompt_builder.py — EXACT SPEC

**Dependencies:** json, pathlib, scoring_engine (local import)

**Functions:**

```
build_system_prompt() → str:
Load and return prompts/system-prompt.md as string

build_user_message(score_sheet: dict) → str:
Load prompts/user-message-template.md
Replace {{SCORE_SHEET_JSON}} with JSON of:
user_profile, conflicts, garment_scores, pairings, color_palette, relevant_templates
(everything EXCEPT rag_knowledge)
Replace {{RAG_CHUNKS_CONTENT}} with concatenated markdown from rag_knowledge[]
Return assembled string

get_api_params() → dict:
Load prompts/prompt-config.json, return api_params section

build_full_request(score_sheet: dict) → dict:
Return {
"model": from config,
"max_tokens": from config,
"temperature": from config,
"thinking": from config,
"system": build_system_prompt(),
"messages": [{"role": "user", "content": build_user_message(score_sheet)}]
}

estimate_tokens(score_sheet: dict) → dict:
Rough estimate: len(string) // 4

demo():
Run scoring engine for sample profile → build_full_request → print summary + save
```

### 4.3 test_pipeline.py — EXACT SPEC

**Dependencies:** json, time, os, pathlib, dotenv, anthropic

**For general Claude subscription:**
```python
# .env file needs only:
ANTHROPIC_API_KEY=your-key-here

# Client creation (NO base_url, NO custom certs):
client = anthropic.Anthropic(api_key=API_KEY)
```

**3 test profiles:**
```
heavy_short: build=heavy, height=short, body_shape=oval, face_shape=wide_broad,
neck=short, facial_hair=full_beard, hair_style=bald_balding, glasses_style=none,
head_size=proportional, skin_undertone=warm, overall_contrast=medium,
skin_depth=medium_dark, style_track=casual

slim_tall: build=slim, height=tall, body_shape=rectangle, face_shape=thin_narrow,
neck=long, facial_hair=clean_shaven, hair_style=medium, glasses_style=thin_frame,
head_size=small, skin_undertone=cool, overall_contrast=high,
skin_depth=light, style_track=smart_casual

athletic_average: build=athletic, height=average, body_shape=inverted_triangle,
face_shape=average, neck=thick, facial_hair=stubble, hair_style=buzz_short,
glasses_style=bold_thick_frame, head_size=proportional, skin_undertone=warm,
overall_contrast=medium, skin_depth=medium, style_track=casual
```

**For each profile:** run engine → build prompt → call Claude API → save report to test_outputs/

---

## 5. ARCHITECTURE DECISIONS (AND WHY)

### Deterministic Scoring + LLM Reasoning
Scoring is math (Python). LLM does reasoning/blending/writing. LLM receives pre-computed facts and decides.

### Pre-Classified Tiers (not raw scores)
WHY: When we sent raw scores, the LLM called score-6 items "avoid." Pre-classification eliminates this.

### Pre-Attached Colors
WHY: When colors were separate, LLM used wrong colors in outfits (olive for cool undertone). Pre-attaching colors to each garment eliminates this structurally.

### No Brands in V1
WHY: Brand knowledge wasn't from our KB, prices go stale, wrong mappings happened (NB 574 called "minimalist white"). Core value is body→style, not shopping.

### Loosely Coupled
All prompts, schemas, rules are files. Edit without code changes.

### Permanent Style Guide
No climate/season filtering. "Straight jeans suit your heavy build" is permanent truth. Backup with filters exists for V2.

### Style Tracks
Every param has style_track tags. V1 uses casual + smart_casual only. Tags ready for formal/ethnic in V2.

---

## 6. TESTING RESULTS

7 profiles tested, audited by separate agent, verified against web sources.

**Known verified facts:** V-neck elongates (TRUE), high rise lengthens legs (TRUE), monochrome slims (TRUE), spread collar widens narrow face (TRUE), slim fit okay for stocky (TRUE — The Modest Man, Peter Manning NYC, Tapered Menswear).

**Scores:** heavy_short 9.5, slim_tall 8.5, athletic_average 9.5, blended profiles avg 8.2/10.

**Fixed bugs:** NB 574 brand error (fixed: no brands), score tier misclassification (fixed: pre-classified tiers), olive for cool undertone (fixed: color avoid-list filtering), slim fit wrongly avoided for stocky (fixed: raised to score 6).

**Remaining minor issues:** Boat neck sometimes omitted for slim (scores 7 but LLM skips for brevity). Glasses get no dedicated styling section (V2).

---

## 7. REPORT OUTPUT — 16 SECTIONS

1. Your Style Profile (~200 words)
2. Your Golden Rules (~150 words) — 3-5 body-specific rules
3. T-Shirts (~200 words) — fit, neckline, sleeve, fabric, style
4. Polos (~150 words) — fit, collar, fabric, placket
5. Casual Shirts (~200 words) — type, fit, collar, fabric
6. Jeans (~200 words) — fit, wash, rise, stretch, leg shape
7. Chinos & Trousers (~150 words)
8. Shorts (~100 words)
9. Footwear (~200 words) — sneakers + casual shoes + sandals
10. Jackets & Layers (~100 words) — OPTIONAL
11. Fabric & Texture Strategy (~150 words) — body-specific fabric advice
12. Color Playbook (~200 words) — best/safe/avoid + metal
13. What to Avoid (~150 words) — ONLY items from "avoid" tier
14. Outfit Ideas (~400 words) — 6-8 complete outfits
15. Tailoring Tips (~100 words) — Indian darzi, Rs 50-200
16. Starter Kit (~200 words) — top 10 items, NO brands/prices

---

## 8. API SETUP (new system)

```bash
# Install
pip install anthropic python-dotenv

# .env (general claude subcription)
ANTHROPIC_API_KEY=sk-ant...

# Client (simple - no base url, no certs)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

---

## 9. WHAT TO BUILD NEXT

### Backend API (FastAPI)
```
POST /api/generate-style-guide
Body: { "build": "heavy", "height": "short", ... }
Response: { "report": "## Your Personal Style Guide\n...", "metadata": {...} }
```

### Frontend
- Form page from input-schema.json
- Report page renders markdown
- Mobile-first (Indian users mostly on phone)

### Deploy
- Backend: Railway/Render
- Frontend: Vercel
- Just needs ANTHROPIC_API_KEY

---

## 10. QUICK REFERENCE

| Change... | Edit this file |
|-----------|---------------|
| LLM model/temperature | prompts/prompt-config.json |
| Persona/tone | prompts/system-prompt.md |
| Report sections | prompts/user-message-template.md + schemas/output-schema.json |
| User input fields | schemas/input-schema.json + engine UserProfile class |
| Garment scoring | rules/scoring-rules.json |
| Color palettes | rules/color-rules.json |
| Pairing matrix | rules/pairing-rules.json |
| Outfit templates | templates/outfit-templates.json |
| Knowledge chunks | rag-chunks/chunks/*.md |

---

## 11. DESIGN PRINCIPLES

1. **Loosely coupled** — schemas, prompts, rules are files, not code
2. **Deterministic where possible** — scoring engine handles math, LLM handles reasoning
3. **Indian-first** — built for Indian casual wear, not adapted from Western
4. **Body-first** — core value is matching styles to body types
5. **No hallucination by design** — pre-classified tiers, pre-attached colors
6. **Permanent advice** — reports are evergreen, no seasonal filtering

---

*This document is the complete handoff. Read this first, then explore the file structure. Regenerate the engine from Section 4's exact spec.*
