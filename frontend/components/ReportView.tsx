"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Props = {
  report: string;
  onReset: () => void;
};

export default function ReportView({ report, onReset }: Props) {
  const handleDownload = async () => {
    const html2pdf = (await import("html2pdf.js")).default;
    const el = document.getElementById("report-content");
    if (!el) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const opt: any = {
      margin:      [12, 14],
      filename:    "aifa-style-guide.pdf",
      image:       { type: "jpeg", quality: 0.95 },
      html2canvas: { scale: 2, useCORS: true },
      jsPDF:       { unit: "mm", format: "a4", orientation: "portrait" },
      pagebreak:   { mode: ["avoid-all", "css"] },
    };
    html2pdf().set(opt).from(el).save();
  };

  return (
    <div className="max-w-2xl mx-auto w-full px-4 py-8 space-y-6">
      {/* Toolbar */}
      <div className="no-print flex items-center justify-between gap-4 flex-wrap">
        <button
          onClick={onReset}
          className="text-sm text-[var(--brand-muted)] hover:text-[var(--brand-text)] underline underline-offset-2"
        >
          ← Start over
        </button>
        <button
          onClick={handleDownload}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-[var(--brand-primary)] text-white hover:opacity-90 transition-opacity"
        >
          Download PDF
        </button>
      </div>

      {/* Report */}
      <div
        id="report-content"
        className="bg-white border border-[var(--brand-border)] rounded-2xl p-6 md:p-10"
      >
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {report}
        </ReactMarkdown>
      </div>

      {/* Bottom toolbar (convenience) */}
      <div className="no-print flex justify-end">
        <button
          onClick={handleDownload}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-[var(--brand-primary)] text-white hover:opacity-90 transition-opacity"
        >
          Download PDF
        </button>
      </div>
    </div>
  );
}
