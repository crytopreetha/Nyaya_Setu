import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import Shell from "../components/Shell";
import SeverityBadge from "../components/SeverityBadge";
import { api, ApiError } from "../lib/api";
import type { AnalysisOut, ReferralOut, DraftOut, CaseFileOut } from "../types";
import { FACT_TYPE_LABELS } from "../types";

type Tab = "overview" | "facts" | "dates" | "action" | "evidence" | "draft";

export default function Dashboard() {
  const { caseId } = useParams<{ caseId: string }>();
  const [analysis, setAnalysis] = useState<AnalysisOut | null>(null);
  const [referrals, setReferrals] = useState<ReferralOut[]>([]);
  const [drafts, setDrafts] = useState<DraftOut[]>([]);
  const [files, setFiles] = useState<CaseFileOut[]>([]);
  const [tab, setTab] = useState<Tab>("overview");
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [generatingDraft, setGeneratingDraft] = useState(false);
  const [downloadingDraftId, setDownloadingDraftId] = useState<string | null>(null);
  const [editingFactId, setEditingFactId] = useState<string | null>(null);
  const [factDraftValue, setFactDraftValue] = useState("");
  const [uploadingEvidence, setUploadingEvidence] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const evidenceInputRef = useRef<HTMLInputElement>(null);

  async function loadFiles() {
    if (!caseId) return;
    try {
      setFiles(await api.listFiles(caseId));
    } catch {
      /* evidence list is a nice-to-have; ignore failures */
    }
  }

  useEffect(() => {
    if (!caseId) return;
    api
      .getAnalysis(caseId)
      .then(async (result) => {
        setAnalysis(result);
        try {
          setReferrals(await api.getReferrals(result.domain));
        } catch {
          /* referrals are a nice-to-have; ignore failures */
        }
        try {
          setDrafts(await api.listDrafts(caseId));
        } catch {
          /* no drafts yet */
        }
        await loadFiles();
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load this case."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId]);

  async function confirmDeadline(deadlineId: string) {
    if (!caseId) return;
    setConfirmingId(deadlineId);
    try {
      await api.confirmDeadline(caseId, deadlineId);
      const refreshed = await api.getAnalysis(caseId);
      setAnalysis(refreshed);
    } finally {
      setConfirmingId(null);
    }
  }

  async function saveFact(factId: string) {
    if (!caseId) return;
    await api.updateFact(caseId, factId, factDraftValue);
    const refreshed = await api.getAnalysis(caseId);
    setAnalysis(refreshed);
    setEditingFactId(null);
  }

  async function generateDraft() {
    if (!caseId) return;
    setGeneratingDraft(true);
    try {
      const draft = await api.createDraft(caseId, "response_letter");
      setDrafts((prev) => [draft, ...prev]);
      setTab("draft");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not generate a draft.");
    } finally {
      setGeneratingDraft(false);
    }
  }

  async function downloadDraft(draft: DraftOut) {
    if (!caseId) return;
    setDownloadingDraftId(draft.id);
    try {
      await api.downloadDraftPdf(caseId, draft.id, `${draft.draft_type}.pdf`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not download the PDF.");
    } finally {
      setDownloadingDraftId(null);
    }
  }

  async function handleEvidenceUpload(fileList: FileList | null) {
    if (!caseId || !fileList || fileList.length === 0) return;
    setUploadingEvidence(true);
    try {
      await api.uploadFile(caseId, fileList[0]);
      await loadFiles();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not upload that file.");
    } finally {
      setUploadingEvidence(false);
      if (evidenceInputRef.current) evidenceInputRef.current.value = "";
    }
  }

  async function deleteEvidence(fileId: string) {
    if (!caseId) return;
    await api.deleteFile(caseId, fileId);
    await loadFiles();
  }

  if (error) {
    return (
      <Shell>
        <div className="mx-auto max-w-2xl px-6 py-16 text-severity-emergency">{error}</div>
      </Shell>
    );
  }

  if (!analysis) {
    return (
      <Shell>
        <div className="mx-auto max-w-2xl px-6 py-16 text-ink/60">Loading…</div>
      </Shell>
    );
  }

  const TABS: { id: Tab; label: string }[] = [
    { id: "overview", label: "What we found" },
    { id: "facts", label: "Details we used" },
    { id: "dates", label: "Important dates" },
    { id: "action", label: "What to do next" },
    { id: "evidence", label: "Evidence locker" },
    { id: "draft", label: "Draft center" },
  ];

  return (
    <Shell>
      <section className="mx-auto max-w-4xl px-6 py-10">
        <p className="text-sm font-medium text-brand">{analysis.document_type}</p>
        <h1 className="mt-1 font-serif text-3xl font-semibold text-ink">Your case analysis</h1>

        {analysis.low_quality_pages.length > 0 && (
          <div className="mt-6 rounded-lg border border-severity-attention/30 bg-severity-attention/5 p-4">
            <p className="text-sm text-ink/80">
              <strong className="text-severity-attention">Some pages were hard to read automatically</strong>{" "}
              — page{analysis.low_quality_pages.length > 1 ? "s" : ""}{" "}
              {analysis.low_quality_pages.join(", ")} may have scanned poorly. Double-check the
              details from those pages before relying on this analysis.
            </p>
          </div>
        )}

        <div className="mt-8 flex flex-wrap gap-2 border-b border-sage">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`min-h-[44px] px-4 border-b-2 text-sm font-medium ${
                tab === t.id ? "border-brand text-brand" : "border-transparent text-ink/60 hover:text-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === "overview" && (
          <div className="mt-8 space-y-8">
            <div>
              <h2 className="font-serif text-xl font-semibold text-ink">Why it matters</h2>
              <div className="mt-4 space-y-4">
                {analysis.risk_items.length === 0 && (
                  <p className="text-ink/60">No specific issues were flagged for this case.</p>
                )}
                {analysis.risk_items.map((item) => (
                  <div key={item.id} className="rounded-lg border border-sage bg-white p-5">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="font-serif text-lg font-semibold text-ink">{item.title}</h3>
                      <SeverityBadge severity={item.severity} />
                    </div>
                    <p className="mt-2 text-ink/80 leading-relaxed">{item.explanation}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {item.is_inference && item.citations.length === 0 ? (
                        <span className="text-xs text-ink/50 italic">
                          Inference — not verified against a source. Confirm before relying on this.
                        </span>
                      ) : (
                        item.citations.map((c) => (
                          <a
                            key={c.source_id}
                            href={c.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs text-brand underline underline-offset-2 hover:text-brand-dark"
                          >
                            Source: {c.title}
                          </a>
                        ))
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {referrals.length > 0 && (
              <div>
                <h2 className="font-serif text-xl font-semibold text-ink">Official routes</h2>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {referrals.map((r) => (
                    <a
                      key={r.source.id}
                      href={r.source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-lg border border-sage bg-white p-4 hover:border-brand"
                    >
                      <p className="text-sm font-medium text-ink">{r.need}</p>
                      <p className="mt-1 text-sm text-ink/70">{r.action}</p>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {analysis.disclaimer && (
              <p className="text-sm text-ink/50 border-t border-sage pt-4">{analysis.disclaimer}</p>
            )}
          </div>
        )}

        {tab === "facts" && (
          <div className="mt-8 space-y-4">
            <p className="text-sm text-ink/60">
              This is what we understood from your document or description. Fix anything
              that's wrong — it's used to explain your case, not submitted anywhere.
            </p>
            {analysis.facts.length === 0 && (
              <p className="text-ink/60">No specific details were extracted for this case.</p>
            )}
            {analysis.facts.map((fact) => (
              <div key={fact.id} className="rounded-lg border border-sage bg-white p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-ink/40">
                  {FACT_TYPE_LABELS[fact.fact_type] || fact.fact_type}
                </p>
                {editingFactId === fact.id ? (
                  <div className="mt-2 flex flex-wrap gap-2">
                    <input
                      value={factDraftValue}
                      onChange={(e) => setFactDraftValue(e.target.value)}
                      className="min-h-[40px] flex-1 rounded-md border border-sage px-3 text-ink"
                      autoFocus
                    />
                    <button
                      onClick={() => saveFact(fact.id)}
                      className="min-h-[40px] rounded-md bg-brand px-4 text-sm font-medium text-white"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setEditingFactId(null)}
                      className="min-h-[40px] rounded-md border border-sage px-4 text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <div className="mt-1 flex items-center justify-between gap-3">
                    <p className="text-ink">
                      {fact.value}
                      {fact.user_edited && (
                        <span className="ml-2 text-xs text-brand">(edited by you)</span>
                      )}
                    </p>
                    <button
                      onClick={() => {
                        setEditingFactId(fact.id);
                        setFactDraftValue(fact.value);
                      }}
                      className="text-sm text-brand underline underline-offset-2 shrink-0"
                    >
                      Edit
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {tab === "dates" && (
          <div className="mt-8 space-y-4">
            {analysis.important_dates.length === 0 && (
              <p className="text-ink/60">No specific dates were identified in this case.</p>
            )}
            {analysis.important_dates.map((d) => (
              <div
                key={d.id}
                className="flex items-center justify-between rounded-lg border border-sage bg-white p-5"
              >
                <div>
                  <p className="font-medium text-ink">{d.label}</p>
                  <p className="mt-1 text-sm text-ink/70">
                    {d.date ?? "Date could not be confirmed automatically"}{" "}
                    <span className="text-ink/40">· confidence: {d.confidence}</span>
                  </p>
                  {d.basis && <p className="mt-1 text-xs text-ink/40">{d.basis}</p>}
                </div>
                {d.status === "confirmed" ? (
                  <span className="text-sm font-medium text-brand">Confirmed ✓</span>
                ) : (
                  <button
                    onClick={() => confirmDeadline(d.id)}
                    disabled={confirmingId === d.id}
                    className="min-h-[40px] rounded-md border border-sage px-4 text-sm font-medium hover:bg-sage/40 disabled:opacity-50"
                  >
                    {confirmingId === d.id ? "Confirming…" : "Confirm"}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {tab === "action" && (
          <ol className="mt-8 space-y-4">
            {analysis.next_steps.length === 0 && (
              <p className="text-ink/60">No action items were generated for this case.</p>
            )}
            {analysis.next_steps.map((step, i) => (
              <li key={step.id} className="flex gap-4 rounded-lg border border-sage bg-white p-5">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand text-white text-sm font-medium">
                  {i + 1}
                </span>
                <div>
                  <p className="font-medium text-ink">{step.text}</p>
                  {step.reason && <p className="mt-1 text-sm text-ink/70">{step.reason}</p>}
                  {step.official_url && (
                    <a
                      href={step.official_url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block text-sm text-brand underline underline-offset-2"
                    >
                      Open official link
                    </a>
                  )}
                </div>
              </li>
            ))}
          </ol>
        )}

        {tab === "evidence" && (
          <div className="mt-8">
            <label className="inline-flex">
              <span className="min-h-[44px] cursor-pointer rounded-md bg-brand px-5 text-white font-medium hover:bg-brand-dark flex items-center">
                {uploadingEvidence ? "Uploading…" : "Add evidence"}
              </span>
              <input
                ref={evidenceInputRef}
                type="file"
                className="hidden"
                onChange={(e) => handleEvidenceUpload(e.target.files)}
                disabled={uploadingEvidence}
              />
            </label>

            <ul className="mt-6 space-y-3">
              {files.map((f) => (
                <li
                  key={f.id}
                  className="flex items-center justify-between rounded-lg border border-sage bg-white p-4"
                >
                  <div>
                    <p className="font-medium text-ink">{f.original_filename}</p>
                    <p className="text-sm text-ink/60">
                      {(f.size / 1024).toFixed(0)} KB · added {new Date(f.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => caseId && api.downloadFile(caseId, f.id, f.original_filename)}
                      className="min-h-[40px] rounded-md border border-sage px-4 text-sm font-medium hover:bg-sage/40"
                    >
                      Download
                    </button>
                    <button
                      onClick={() => deleteEvidence(f.id)}
                      className="min-h-[40px] rounded-md border border-sage px-4 text-sm text-ink/70 hover:bg-sage/40"
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
              {files.length === 0 && (
                <p className="text-ink/60">No evidence files attached to this case yet.</p>
              )}
            </ul>
          </div>
        )}

        {tab === "draft" && (
          <div className="mt-8">
            <button
              onClick={generateDraft}
              disabled={generatingDraft}
              className="min-h-[44px] rounded-md bg-brand px-5 text-white font-medium hover:bg-brand-dark disabled:opacity-50"
            >
              {generatingDraft ? "Generating…" : "Generate a draft response letter"}
            </button>

            <div className="mt-6 space-y-6">
              {drafts.map((d) => (
                <div key={d.id} className="rounded-lg border border-sage bg-white p-5">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-ink/60">
                      {d.draft_type.replace("_", " ")} · {new Date(d.created_at).toLocaleString()}
                    </p>
                    <div className="flex gap-3 shrink-0">
                      <button
                        onClick={() => navigator.clipboard.writeText(d.content)}
                        className="text-sm text-brand underline underline-offset-2"
                      >
                        Copy
                      </button>
                      <button
                        onClick={() => downloadDraft(d)}
                        disabled={downloadingDraftId === d.id}
                        className="text-sm text-brand underline underline-offset-2 disabled:opacity-50"
                      >
                        {downloadingDraftId === d.id ? "Preparing…" : "Download PDF"}
                      </button>
                    </div>
                  </div>
                  <pre className="mt-3 whitespace-pre-wrap font-sans text-sm text-ink/80 leading-relaxed">
                    {d.content}
                  </pre>
                </div>
              ))}
              {drafts.length === 0 && (
                <p className="text-ink/60">No draft generated yet — this draft is never sent for you.</p>
              )}
            </div>
          </div>
        )}
      </section>
    </Shell>
  );
}
