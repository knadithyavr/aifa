<scoring_data>
{{SCORE_SHEET_JSON}}
</scoring_data>

<style_knowledge>
{{RAG_CHUNKS_CONTENT}}
</style_knowledge>

<analysis_approach>
Before writing the report, perform this internal analysis:

1. Identify the user's 3 most defining physical traits from the profile (e.g., heavy build + short height + wide face). These drive every recommendation.

2. Read all conflict resolutions. These are compound body challenges that MUST be addressed throughout the report — not just mentioned once.

3. For each garment category, identify the top 2-3 values (score 7+) and bottom 2-3 values (score 1-4). The top values become recommendations, the bottom become the avoid list.

4. Cross-reference the top-scored garment values with pairing scores to find the best combinations. Only recommend outfit combos where BOTH top and bottom score 7+ in pairings.

5. If color palette is provided, map the best colors to specific garment recommendations: "navy V-neck" not just "V-neck." For EVERY color you mention anywhere in the report — including outfit ideas — use ONLY colors that appear in that garment's `your_colors` list in the scoring data. Do not introduce any color from your own knowledge that is not in `your_colors`. If a color is not in the list, do not recommend it.

6. Check every outfit idea against the anti-pairings list. If any outfit contains an anti-pairing, fix it before including.

7. Adapt outfit templates to this user's body: apply the "your_adaptations" overrides from each template.

Ground every recommendation to at least one data point from the scoring data.
</analysis_approach>

<output_format>
Generate the report with EXACTLY these sections in this order:

## Your Personal Style Guide

### 1. Your Style Profile
(~200 words) Warm summary of who this person is — body type, face shape, coloring. What these traits mean for their style. Make the user feel understood. End with their key strength ("your build gives you..." or "your coloring means...").

### 2. Your Golden Rules
(~150 words) 3-5 numbered rules specific to THIS user's body challenges. Derived from conflicts and top-scoring patterns. These are the rules they should memorize. Concise, punchy, actionable.

### 3. T-Shirts
(~200 words) Best fit + neckline + sleeve + fabric weight. Top 2-3 picks with one-line reason each. What to avoid with reason. If facial_hair or glasses affect neckline choice, explain why.

### 4. Polos
(~150 words) Best fit + collar + fabric. Top picks with reasons. What to avoid.

### 5. Casual Shirts
(~200 words) Best types + fit + collar + fabric. Top picks. What to avoid. Collar recommendations should reference face shape.

### 6. Jeans
(~200 words) Best fit + wash + rise + stretch. This is critical — most users wear jeans daily. Top picks with strong reasons. Avoid list. Rise recommendation MUST reference height.

### 7. Chinos & Trousers
(~150 words) Best fit + color + type + rise. Position as the "step up from jeans" option.

### 8. Shorts
(~100 words) Best length + type + fit. Length recommendation MUST reference height.

### 9. Footwear
(~200 words) Combine sneakers + casual shoes + sandals into one section. Top sneaker types, best casual shoes, when sandals work. Material recommendation if climate data exists.

### 10. Jackets & Layers
(~100 words) OPTIONAL section — frame as "when you need a layer." Best jacket types for this build. Skip entirely if all jackets scored low or user is in hot climate.

### 11. Your Fabric & Texture Strategy
(~150 words) Body-type-specific fabric advice. This is one of the most actionable and cost-free style upgrades. Cover:
- Which fabric weights suit this build (lightweight vs midweight vs heavyweight)
- Which textures work (slim builds → textured fabrics like flannel, corduroy, chunky knits ADD visual bulk. Heavy builds → smooth, structured mid-weight fabrics MINIMIZE bulk)
- Specific fabric picks per garment: "Your best tee fabric is midweight cotton jersey at 160-180 GSM" or "Pique polos hold their shape better on your frame than jersey"
- Reference the knowledge chunks for fabric reasoning. Be specific, not generic.

### 12. Your Color Playbook
(~200 words) Only if skin_undertone was provided. Best colors near face (3-4 with why). Safe bottom colors. Colors to avoid (2-3 with why). Metal recommendation (gold/silver).

### 13. What to Avoid
(~150 words) Consolidated avoid list across ALL categories. Grouped by garment. Each with one-line reason. Punchy: "Skinny jeans — accentuates width, creates tension lines."

### 14. Outfit Ideas
(~400 words) 6-8 complete outfits. Each has: descriptive name, all pieces (top + bottom + footwear + optional layer), specific colors from their palette, and one sentence explaining why it works for their body. Every piece must be scored 7+ for this user. Every combo must pass anti-pairing check.

### 15. Tailoring Tips
(~100 words) Practical Indian-specific tailoring advice. Most Indian men don't know a local tailor can fix fit issues for Rs 50-200. Cover:
- What to get tailored (taper jeans, shorten sleeves, take in shirt waist)
- What NOT to tailor (shoulders, overall size — buy the right size instead)
- "Find a local darzi near you — a Rs 100 taper on jeans makes a Rs 1500 pair look like Rs 5000"
- This is the highest-ROI style advice for Indian men on any budget

### 16. Your Starter Kit
(~200 words) Top 10 items to buy first, numbered by priority. Each item is specific: "Navy V-neck regular fit tee in midweight cotton" not "a tee." Include fit, color, and fabric. Brief reason why it's priority. Do NOT include brands, stores, or prices.
</output_format>

<example>
<example_context>This shows the expected tone for sections 1-2, written for a DIFFERENT user (slim, tall, cool undertone). Use as style reference only — do not copy content.</example_context>

### 1. Your Style Profile
You're 6'1" with a slim frame — the kind of build that most casual clothing is designed around, which is genuinely great news. Your rectangle body shape means shoulders, waist, and hips are roughly the same width, giving you a clean, straight silhouette to work with. Your cool-toned medium skin with high contrast (dark hair, lighter skin) means you can pull off bold color combinations that would overwhelm most guys.

The one thing to watch: your height and slim frame can tip into "lanky" if everything hangs loose. The fix is simple — fitted (not tight) clothes with some structure. Think of it as giving your frame definition, not adding bulk.

### 2. Your Golden Rules
1. **Fitted, not loose** — slim and tapered cuts define your frame without clinging. Avoid oversized and relaxed fits — they make you look like you borrowed someone's clothes.
2. **Horizontal details are your friend** — unlike most guys, you WANT visual width. Layering, textured fabrics, and chest patterns add dimension to your straight frame.
3. **High contrast colors work** — your dark hair + lighter skin means navy-and-white, charcoal-and-cream combos will look intentional and sharp on you.
4. **Tapered always** — whether jeans or chinos, tapered from knee to ankle prevents the "stilt legs" effect on your tall frame.
</example>

<task>
Now analyze the scoring data above and generate the complete personalized style guide report following the exact output format. Begin directly with "## Your Personal Style Guide" — no preamble. Every recommendation must trace to the scoring data.

Word count rules — these are MINIMUMS, not targets. Do not cut a section short:
- Sections 1, 3, 5, 6, 9, 12, 14, 16: minimum 200 words each
- Sections 2, 4, 7, 11, 13: minimum 150 words each
- Section 8: minimum 100 words
- Section 10: minimum 100 words (skip only if ALL jacket types scored below 5)
- Section 14 (Outfit Ideas): minimum 400 words — write 6-8 complete outfits, each fully described
- Total report: minimum 3200 words
</task>
