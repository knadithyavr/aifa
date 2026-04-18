"use client";

import { useState } from "react";
import StyleForm from "@/components/StyleForm";
import ReportView from "@/components/ReportView";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type AppState = "form" | "loading" | "report" | "error";

const LOADING_MESSAGES = [
  "Analysing your body proportions…",
  "Scoring 35 garment parameters…",
  "Mapping your colour palette…",
  "Selecting outfit templates…",
  "Generating your personalised style guide…",
  "Almost there…",
];

export default function Home() {
  const [state, setState]   = useState<AppState>("form");
  const [report, setReport] = useState("");
  const [error, setError]   = useState("");
  const [msgIdx, setMsgIdx] = useState(0);

  const handleSubmit = async (data: Record<string, string>) => {
    setState("loading");
    setMsgIdx(0);

    // Cycle loading messages
    const interval = setInterval(() => {
      setMsgIdx((i) => Math.min(i + 1, LOADING_MESSAGES.length - 1));
    }, 15000);

    try {
      const res = await fetch(`${API_URL}/api/generate-style-guide`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(data),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `Server error ${res.status}`);
      }

      const json = await res.json();
      setReport(json.report);
      setState("report");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong. Please try again.");
      setState("error");
    } finally {
      clearInterval(interval);
    }
  };

  const reset = () => {
    setState("form");
    setReport("");
    setError("");
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="no-print border-b border-[var(--brand-border)] bg-white px-4 py-4">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div>
            <span className="font-bold tracking-tight text-lg">AIFA</span>
            <span className="ml-2 text-xs text-[var(--brand-muted)]">AI Fashion Advisor</span>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Form */}
        {state === "form" && (
          <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Your Style Profile</h1>
              <p className="text-sm text-[var(--brand-muted)] mt-1">
                Answer a few questions and get a personalised style guide — what to wear, what to avoid, and why.
              </p>
            </div>
            <StyleForm onSubmit={handleSubmit} loading={false} />
          </div>
        )}

        {/* Loading */}
        {state === "loading" && (
          <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center gap-6">
            <div className="w-10 h-10 border-2 border-[var(--brand-accent)] border-t-transparent rounded-full animate-spin" />
            <div>
              <p className="font-medium">{LOADING_MESSAGES[msgIdx]}</p>
              <p className="text-xs text-[var(--brand-muted)] mt-1">This takes up to 2 minutes</p>
            </div>
          </div>
        )}

        {/* Report */}
        {state === "report" && (
          <ReportView report={report} onReset={reset} />
        )}

        {/* Error */}
        {state === "error" && (
          <div className="max-w-2xl mx-auto px-4 py-16 text-center space-y-4">
            <p className="text-red-600 font-medium">{error}</p>
            <button
              onClick={reset}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-[var(--brand-primary)] text-white"
            >
              Try again
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
