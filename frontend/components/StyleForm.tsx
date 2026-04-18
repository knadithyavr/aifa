"use client";

import { useState } from "react";
import { FORM_FIELDS, REQUIRED_KEYS, type FieldDef } from "@/lib/formSchema";

type Props = {
  onSubmit: (data: Record<string, string>) => void;
  loading: boolean;
};

function FieldCard({ field, value, onChange }: {
  field: FieldDef;
  value: string;
  onChange: (v: string) => void;
}) {
  const badge = field.required
    ? <span className="text-xs font-medium text-red-600 bg-red-50 px-2 py-0.5 rounded">Required</span>
    : field.recommended
    ? <span className="text-xs font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded">Recommended</span>
    : <span className="text-xs font-medium text-gray-400 bg-gray-100 px-2 py-0.5 rounded">Optional</span>;

  return (
    <div className="bg-white border border-[var(--brand-border)] rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <label className="font-medium text-sm">{field.label}</label>
        {badge}
      </div>
      <p className="text-xs text-[var(--brand-muted)] leading-relaxed">{field.help}</p>
      <div className="flex flex-wrap gap-2">
        {field.values.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(value === opt.value ? "" : opt.value)}
            className={`px-3 py-1.5 rounded-lg text-sm border transition-all ${
              value === opt.value
                ? "bg-[var(--brand-primary)] text-white border-[var(--brand-primary)]"
                : "bg-white text-[var(--brand-text)] border-[var(--brand-border)] hover:border-[var(--brand-primary)]"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function StyleForm({ onSubmit, loading }: Props) {
  const defaults: Record<string, string> = {};
  FORM_FIELDS.forEach((f) => { if (f.default) defaults[f.key] = f.default; });

  const [values, setValues] = useState<Record<string, string>>(defaults);
  const [errors, setErrors] = useState<string[]>([]);

  const set = (key: string, val: string) =>
    setValues((prev) => ({ ...prev, [key]: val }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const missing = REQUIRED_KEYS.filter((k) => !values[k]);
    if (missing.length) {
      setErrors(missing);
      document.getElementById(`field-${missing[0]}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    setErrors([]);
    onSubmit(values);
  };

  const required  = FORM_FIELDS.filter((f) => f.required);
  const recommended = FORM_FIELDS.filter((f) => f.recommended);
  const optional  = FORM_FIELDS.filter((f) => !f.required && !f.recommended);

  const Section = ({ title, note, fields }: { title: string; note?: string; fields: FieldDef[] }) => (
    <div className="space-y-3">
      <div>
        <h2 className="font-semibold text-base">{title}</h2>
        {note && <p className="text-xs text-[var(--brand-muted)] mt-0.5">{note}</p>}
      </div>
      {fields.map((f) => (
        <div key={f.key} id={`field-${f.key}`}>
          <FieldCard
            field={f}
            value={values[f.key] ?? ""}
            onChange={(v) => set(f.key, v)}
          />
          {errors.includes(f.key) && (
            <p className="text-xs text-red-600 mt-1 ml-1">Please select an option</p>
          )}
        </div>
      ))}
    </div>
  );

  const filled = Object.values(values).filter(Boolean).length;
  const total  = FORM_FIELDS.length;

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Progress */}
      <div className="text-xs text-[var(--brand-muted)] flex items-center gap-3">
        <div className="flex-1 bg-gray-100 rounded-full h-1.5">
          <div
            className="h-1.5 rounded-full bg-[var(--brand-accent)] transition-all"
            style={{ width: `${(filled / total) * 100}%` }}
          />
        </div>
        <span>{filled}/{total} filled</span>
      </div>

      <Section
        title="Body Measurements"
        note="Required — these 5 fields drive all recommendations."
        fields={required}
      />
      <Section
        title="Additional Details"
        note="Recommended — improves color and styling accuracy significantly."
        fields={recommended}
      />
      <Section
        title="More About You"
        note="Optional — adds further personalisation."
        fields={optional}
      />

      <button
        type="submit"
        disabled={loading}
        className="w-full py-3.5 rounded-xl font-semibold text-white bg-[var(--brand-primary)] hover:opacity-90 disabled:opacity-50 transition-opacity text-sm"
      >
        {loading ? "Generating your style guide…" : "Generate My Style Guide →"}
      </button>
    </form>
  );
}
