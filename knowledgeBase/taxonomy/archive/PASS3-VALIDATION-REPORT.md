# Pass 3: Taxonomy Validation Report

## Summary

| Metric | Count |
|--------|-------|
| Total parameters | 142 |
| Total values | 562 |
| Avg values per parameter | 4.0 |
| Cross-domain dependencies | 101 |
| Orphaned parameters (no deps) | 60 |
| - Critical (must fix) | 11 |
| - Important (should fix) | 23 |
| - Informational (acceptable) | 26 |

---

## Issue 1: 60 Orphaned Parameters (no cross-domain links)

Pass 2 added 101 cross-domain dependencies, but 60 of 142 parameters (42%) have zero inbound or outbound links. These fall into three categories:

### 1A. CRITICAL — 11 params that break recommendation chains

These are input parameters that logically determine downstream choices but have no `cross_domain_dependencies` entries.

| Parameter | Missing Link | What It Should Determine |
|-----------|-------------|-------------------------|
| `D01.arm_length` | D01 → D04 | jacket sleeve length, shirt cuff exposure |
| `D01.waist_definition` | D01 → D04 | jacket waist suppression, trouser front (pleats vs flat) |
| `D01.chest_to_waist_drop` | D01 → D04 | jacket closure (SB vs DB), jacket silhouette |
| `D01.posture` | D01 → D04 | jacket fit adjustments, collar sit |
| `D01.shoulder_vs_hip_ratio` | D01 → D02 | visual_weight_distribution (redundant with body_shape?) |
| `D03.skin_depth` | D03 → D02 | color value range for outfit (light/dark clothing choices) |
| `D03.hair_value` | D03 → D03 | feeds into overall_contrast calculation |
| `D03.hair_tone` | D03 → D03 | feeds into color_temperature_in_garments |
| `D03.eye_color_family` | D03 → D03 | feeds into color echoing, overall_contrast |
| `D03.outfit_contrast_level` | D03 → D02 | determines top_bottom_contrast appropriateness |
| `D03.flusser_complexion_subtype` | D03 → D03 | refines flusser_complexion_type rules |

**Recommendation:** Add the missing dependencies. For D03 sub-params (hair_value, hair_tone, eye_color_family), these feed into the *derived* params (overall_contrast, color_season) within D03 — consider adding intra-domain dependencies or a `feeds_into` field.

### 1B. IMPORTANT — 23 params with internal domain logic

These parameters operate within their domain's logic (e.g., pattern_type governs pattern_scale rules) but don't cross domain boundaries. They're not broken, but adding within-domain dependency chains would make the logic machine-traversable.

**D02 pattern system (6 params):** `pattern_type`, `pattern_spacing`, `pattern_orientation`, `pattern_mixing_relationship`, `pattern_scale_graduation`, `pattern_color_connection` — These form an internal pattern-mixing decision tree within D02.

**D04 garment details (9 params):** `jacket_closure`, `lapel_style`, `jacket_vent_style`, `trouser_front`, `trouser_cuff`, `trouser_waistband`, `gorge_height`, `shirt_cuff_style`, `suit_piece_count` — These are garment properties that should be determined by body params (D01) and occasion (D07) but lack explicit deps.

**D08 fabric details (8 params):** `weave_type`, `trouser_fabric`, `fabric_weight_class`, `fabric_breathability`, `wrinkle_behavior`, `fabric_blend_behavior`, `shirt_fabric_formality_hierarchy`, `texture_combination_principle` — Internal fabric knowledge that supports the main `fabric_formality_hierarchy` and `suiting_fabric` params.

**Recommendation:** Either add cross-domain deps (e.g., D01.height → D04.trouser_cuff, D07.occasion_category → D04.jacket_closure) or add a new `intra_domain_dependencies` section to each file.

### 1C. INFORMATIONAL — 26 params that are contextual knowledge

These are conceptual frameworks (D06.two_pillars), personal preference details (D09.ring_type), niche occasions (D06.smoking_jacket_context), or within-domain guidance (D07.job_interview_dress_strategy). They don't need cross-domain links — they provide knowledge context, not variables in the recommendation chain.

**Recommendation:** No action needed. Optionally tag these with `"dependency_type": "knowledge"` to distinguish them from active recommendation parameters.

---

## Issue 2: Incomplete Core Recommendation Chain

The core chain `D01 (body) → D02 (visual strategy) → D04 (garment choice)` has gaps:

### D01 → D02: Only 3 of 15 body params linked
- **Linked:** body_shape, build, height
- **Missing:** arm_length, waist_definition, chest_to_waist_drop, posture, shoulder_vs_hip_ratio, shoulder_width*, shoulder_slope*, face_shape*, neck*, torso_vs_leg_ratio*, foot_size*, head_size*

(*These go directly to D04, bypassing D02 — which is correct for some, but shoulder_vs_hip_ratio should feed D02.visual_weight_distribution)

### D01 → D04: 8 params linked (good)
shoulder_width, shoulder_slope, face_shape, neck, torso_vs_leg_ratio, foot_size, waist_definition*, chest_to_waist_drop*, head_size

### Missing links that should exist:
| From | To | Relationship |
|------|----|-------------|
| D01.arm_length | D04.shirt_cuff_style | determines_cuff_exposure |
| D01.waist_definition | D04.trouser_front | determines_preference |
| D01.waist_definition | D04.jacket_silhouette | determines_waist_suppression |
| D01.chest_to_waist_drop | D04.jacket_closure | determines_SB_vs_DB_suitability |
| D01.posture | D04.jacket_construction | affects_fit_requirements |
| D01.shoulder_vs_hip_ratio | D02.visual_weight_distribution | determines |
| D03.skin_depth | D03.overall_contrast | feeds_into |
| D03.hair_value | D03.overall_contrast | feeds_into |
| D03.eye_color_family | D03.overall_contrast | feeds_into |
| D03.hair_tone | D03.color_temperature_in_garments | determines |
| D03.outfit_contrast_level | D02.top_bottom_contrast | should_match |

---

## Issue 3: Missing Logically Necessary Parameters

Parameters that no source explicitly defined but are needed for a complete recommendation system:

### 3A. Should Add (high value)

| Proposed Parameter | Domain | Rationale |
|---|---|---|
| `climate_zone` | D05 or D07 | Tropical vs temperate vs cold — fundamentally changes fabric, layering, and color. Currently implicit in D08.seasonal_fabric_assignment but not an input parameter. |
| `age_range` | D01 or D05 | Flusser discusses how aging changes skin/hair (light-bright complexion), and clothing should adapt. Currently no age input. |
| `skin_sensitivity` | D03 | Some men have skin reactions to certain fibers (wool allergy). Affects D08 fiber_type selection. |
| `wardrobe_stage` | D05 | Building from scratch vs. expanding vs. refining. Affects priority of recommendations. |

### 3B. Consider Adding (moderate value)

| Proposed Parameter | Domain | Rationale |
|---|---|---|
| `hair_coverage` | D01/D03 | Bald/balding affects hat recommendations (D09) and overall contrast (D03). |
| `glasses_style` | D01 | Frames interact with face_shape the same way collars do. |
| `cultural_context` | D05/D06 | Beyond regional_dress_norm — religious dress requirements, cultural expectations. |
| `occasion_frequency` | D07 | How often the user faces each occasion type — drives wardrobe investment priority. |

### 3C. Not Needed for V1

| Proposed Parameter | Rationale for Exclusion |
|---|---|
| `brand_preference` | Implementation detail, not taxonomy |
| `color_blindness` | Niche; handle as an override |
| `disability_considerations` | Important but orthogonal to style taxonomy |

---

## Issue 4: Value Set Concerns

### 4A. Binary params that might need a middle value
- `D02.pattern_spacing`: only `close` / `wide` — add `medium`?
- `D09.watch_timepiece_type`: only `dress_wristwatch` / `pocket_watch` — add `sport_watch` / `smart_watch`?
- `D09.belt_type`: only `dress_belt` / `casual_sport_belt` — add `no_belt` (side adjusters/suspenders)?
- `D09.boutonniere_type`: only `small_carnation` / `cornflower` — add `rose` / `no_boutonniere`?

### 4B. Formality spectrum alignment
Nine parameters define formality tiers. They should use consistent tier counts and labels:

| Parameter | Tiers | Labels |
|-----------|-------|--------|
| D06.dress_code_level | 8 | white_tie → casual |
| D08.fabric_formality_hierarchy | 5 | tier_1 → tier_5 |
| D08.shirt_fabric_formality_hierarchy | 5 | tier_1 → tier_5 |
| D04.jacket_formality_tier | 3 | suit > blazer > sport |
| D08.fabric_texture_scale | 5 | very_smooth → rough_coarse |
| D08.fabric_sheen_level | 4 | high_sheen → matte |
| D09.shoe_formality_hierarchy | principle (not param) | patent → boat_shoe |
| D09.hat_formality_hierarchy | principle (not param) | top_hat → baseball_cap |

**Recommendation:** Add explicit mapping between D06's 8-level scale and D08's 5-tier hierarchy. E.g., white_tie/black_tie → tier_1, business_formal → tier_2, business_casual → tier_3, etc.

### 4C. Potential redundancy: D01.shoulder_vs_hip_ratio vs D01.body_shape
`shoulder_vs_hip_ratio` values (`shoulders_wider`, `balanced`, `hips_wider`) overlap directly with `body_shape` geometry. Consider marking it as a derived/computed parameter rather than an independent input.

---

## Issue 5: Cross-Domain Dependency Quality

### 5A. Relationship types are inconsistent
Current relationship values used across files:
`determines`, `determines_preference`, `determined_by`, `applied_based_on`, `should_match`, `evaluated_within`, `interacts_with`, `applied_via`, `governed_by`, `maps_to`, `maps_to_subset`, `influences_preference`, `gates`, `gates_complexity`, `constrains`, `weights_all_recommendations`, `mapped_from`, `constrains_choices`, `modifies_interpretation`, `must_align_with`, `formality_must_match`, `adjusted_for`, `references`, `selects_from`, `uses_for_transition`, `constrains_fabric_choice`, `should_match_frame_size`, `affects_color_appearance`, `must_suit_construction`, `affects_knot_behavior`, `aligned_with`, `determines_suitability`, `operationalizes`, `should_match_texture_band`, `constrained_by`, `follows`, `should_echo`, `buckle_metal_determined_by`, `metal_determined_by`, `should_match_texture`, `constructed_from`, `determines_knot_options`, `determines_metal_via_metal_compatibility`, `determines_metal_choice`, `determines_buckle_metal`, `influences_color_near_face`

**44 distinct relationship types.** This is too many for machine consumption.

**Recommendation:** Consolidate to ~8 canonical relationship types:
1. `determines` — hard constraint (A's value dictates B's value)
2. `influences` — soft preference (A's value suggests B's range)
3. `constrains` — limits options (A eliminates some B values)
4. `maps_to` — direct mapping (A value X = B value Y)
5. `references` — informational link (A mentions B's concepts)
6. `feeds_into` — A is an input to computing B
7. `must_align_with` — A and B must be at same level (formality matching)
8. `operationalizes` — A is how B gets implemented in practice

---

## Recommended Pass 3 Fixes (Priority Order)

### P0 — Must Fix (11 items)
Add the 11 critical missing cross-domain dependencies (Issue 2 table).

### P1 — Should Fix (4 items)
1. Add `climate_zone` parameter to D05 or D07
2. Add formality tier mapping between D06 and D08
3. Consolidate relationship types to ~8 canonical values
4. Add `intra_domain_dependencies` to D02, D03, D04, D08 for internal logic chains

### P2 — Nice to Have (5 items)
1. Tag informational params with `"dependency_type": "knowledge"`
2. Add `medium` value to D02.pattern_spacing
3. Add `sport_watch` to D09.watch_timepiece_type
4. Mark D01.shoulder_vs_hip_ratio as derived from body_shape
5. Add `age_range` and `wardrobe_stage` to D05

---

## Verification Checklist Status

| Check | Status |
|-------|--------|
| Parameter names unique across domains | PASS |
| No duplicate canonical principles | PASS |
| All cross-domain deps point to valid domains | PASS |
| All files valid JSON | PASS |
| Every recommendation chain complete | **FAIL** — 11 critical gaps |
| All value sets mutually exclusive | **PASS** (with 1 note on shoulder_vs_hip_ratio) |
| All value sets exhaustive | **REVIEW** — 4 binary params may need expansion |
| No logically necessary params missing | **REVIEW** — climate_zone recommended |
| Dependency relationship types standardized | **FAIL** — 44 types, should be ~8 |
