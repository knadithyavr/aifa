export type FieldDef = {
  key: string;
  label: string;
  help: string;
  values: { value: string; label: string }[];
  required: boolean;
  recommended: boolean;
  default?: string;
};

const fmt = (v: string) =>
  v.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

const opts = (values: string[]) =>
  values.map((v) => ({ value: v, label: fmt(v) }));

export const FORM_FIELDS: FieldDef[] = [
  // ── Required ──────────────────────────────────────────────
  {
    key: "build", label: "Body Build", required: true, recommended: false,
    help: "Your overall frame and mass. Slim = lean/narrow. Heavy = prominent midsection.",
    values: opts(["slim", "average", "athletic", "stocky", "heavy"]),
  },
  {
    key: "height", label: "Height", required: true, recommended: false,
    help: 'Short = under 5\'7". Average = 5\'7"–6\'. Tall = above 6\'.',
    values: opts(["short", "average", "tall"]),
  },
  {
    key: "face_shape", label: "Face Shape", required: true, recommended: false,
    help: "Look in a mirror. Is your face wider than long? Narrow? Round?",
    values: opts(["small_delicate", "average", "wide_broad", "thin_narrow"]),
  },
  {
    key: "neck", label: "Neck Type", required: true, recommended: false,
    help: "Short = collars feel crowded. Long = lots of space. Thick = wide, often with athletic build.",
    values: opts(["short", "average", "long", "thick"]),
  },
  {
    key: "skin_undertone", label: "Skin Undertone", required: true, recommended: false,
    help: "Check your wrist veins: green = warm, blue/purple = cool. Gold suits you = warm, silver = cool.",
    values: opts(["warm", "cool", "neutral"]),
  },

  // ── Recommended ───────────────────────────────────────────
  {
    key: "body_shape", label: "Body Shape", required: false, recommended: true,
    help: "Trapezoid = proportional. Inverted triangle = broad shoulders. Oval = round midsection.",
    values: opts(["trapezoid", "inverted_triangle", "rectangle", "triangle", "oval", "rhomboid"]),
  },
  {
    key: "skin_depth", label: "Skin Depth", required: false, recommended: true,
    help: "How light or dark your overall skin tone is, regardless of undertone.",
    values: opts(["light", "medium_light", "medium", "medium_dark", "dark"]),
  },
  {
    key: "overall_contrast", label: "Feature Contrast", required: false, recommended: true,
    help: "Difference between skin, hair, eye color. Dark hair + light skin = high. Similar tones = low.",
    values: opts(["low", "medium", "high"]),
  },
  {
    key: "facial_hair", label: "Facial Hair", required: false, recommended: true,
    help: "Your typical facial hair. Affects neckline and collar recommendations.",
    values: opts(["clean_shaven", "stubble", "short_beard", "full_beard", "long_beard"]),
  },

  // ── Optional ──────────────────────────────────────────────
  {
    key: "style_track", label: "Style Preference", required: false, recommended: false,
    help: "Casual = tees, jeans, sneakers. Smart casual = polos, chinos, loafers.",
    values: opts(["casual", "smart_casual"]),
    default: "casual",
  },
  {
    key: "hair_style", label: "Hair Style", required: false, recommended: false,
    help: "Your typical hairstyle.",
    values: opts(["buzz_short", "medium", "long", "bald_balding"]),
  },
  {
    key: "glasses_style", label: "Glasses", required: false, recommended: false,
    help: "If you wear glasses daily, what frame style?",
    values: opts(["none", "thin_frame", "bold_thick_frame", "round", "rectangular"]),
  },
  {
    key: "head_size", label: "Head Size", required: false, recommended: false,
    help: "Relative to your shoulders.",
    values: opts(["small", "proportional", "large"]),
  },
  {
    key: "torso_vs_leg_ratio", label: "Torso–Leg Ratio", required: false, recommended: false,
    help: "Are your legs short relative to your torso, or vice versa?",
    values: opts(["long_torso", "balanced", "long_legs"]),
  },
  {
    key: "waist_definition", label: "Waist Definition", required: false, recommended: false,
    help: "How defined is your waist? Prominent = midsection is widest point.",
    values: opts(["defined", "moderate", "undefined", "prominent"]),
  },
];

export const REQUIRED_KEYS = FORM_FIELDS.filter((f) => f.required).map((f) => f.key);
