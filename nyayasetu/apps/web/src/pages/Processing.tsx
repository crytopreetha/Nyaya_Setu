import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Shell from "../components/Shell";
import { api } from "../lib/api";
import type { CaseStatus } from "../types";

const STAGES: { status: CaseStatus; label: string }[] = [
  { status: "created", label: "Case created" },
  { status: "extracting", label: "Reading your document or description" },
  { status: "analyzing", label: "Checking against verified sources and building your action plan" },
  { status: "ready", label: "Ready" },
];

function stageIndex(status: CaseStatus): number {
  const idx = STAGES.findIndex((s) => s.status === status);
  return idx === -1 ? 0 : idx;
}

export default function Processing() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<CaseStatus>("created");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!caseId) return;
    let cancelled = false;

    async function poll() {
      try {
        const result = await api.getStatus(caseId!);
        if (cancelled) return;
        setStatus(result.status);
        setErrorMessage(result.error_message ?? null);

        if (result.status === "ready") {
          navigate(`/cases/${caseId}`);
          return;
        }
        if (result.status === "failed") return;
        setTimeout(poll, 1500);
      } catch {
        if (!cancelled) setTimeout(poll, 2500);
      }
    }

    poll();
    return () => {
      cancelled = true;
    };
  }, [caseId, navigate]);

  return (
    <Shell>
      <section className="mx-auto max-w-2xl px-6 py-16">
        <h1 className="font-serif text-2xl font-semibold text-ink">Working on your case</h1>
        <p className="mt-2 text-ink/70">This usually takes under a minute.</p>

        <ol className="mt-10 space-y-4">
          {STAGES.slice(0, 3).map((stage, i) => {
            const current = stageIndex(status);
            const done = i < current || status === "ready";
            const active = i === current && status !== "ready" && status !== "failed";
            return (
              <li key={stage.status} className="flex items-center gap-4">
                <span
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-sm font-medium ${
                    done
                      ? "bg-brand border-brand text-white"
                      : active
                      ? "border-brand text-brand animate-pulse"
                      : "border-sage text-ink/40"
                  }`}
                >
                  {done ? "✓" : i + 1}
                </span>
                <span className={active || done ? "text-ink" : "text-ink/40"}>{stage.label}</span>
              </li>
            );
          })}
        </ol>

        {status === "failed" && (
          <div className="mt-10 rounded-lg border border-severity-emergency/30 bg-severity-emergency/5 p-5">
            <p className="font-medium text-severity-emergency">This case couldn't be analysed.</p>
            <p className="mt-1 text-sm text-ink/70">
              {errorMessage || "Something went wrong during analysis."}
            </p>
            <button
              onClick={() => navigate("/new")}
              className="mt-4 min-h-[44px] rounded-md border border-sage px-5 text-sm font-medium hover:bg-sage/40"
            >
              Start over
            </button>
          </div>
        )}

        <p className="mt-10 text-xs text-ink/50">
          Your document stays private to this case while it's being processed.
        </p>
      </section>
    </Shell>
  );
}
