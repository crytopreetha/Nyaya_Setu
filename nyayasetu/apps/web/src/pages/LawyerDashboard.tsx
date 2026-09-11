import { useEffect, useState } from "react";
import Shell from "../components/Shell";
import SeverityBadge from "../components/SeverityBadge";
import { api, ApiError } from "../lib/api";
import { useToast } from "../lib/toast";
import type { CaseListingOut } from "../types";
import { DOMAIN_LABELS } from "../types";

export default function LawyerDashboard() {
  const { showToast } = useToast();
  const [cases, setCases] = useState<CaseListingOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [claimingId, setClaimingId] = useState<string | null>(null);
  const [claimedDetail, setClaimedDetail] = useState<any | null>(null);

  function load() {
    setLoading(true);
    api
      .browseOpenCases()
      .then(setCases)
      .catch(() => setCases([]))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleClaim(caseId: string) {
    setClaimingId(caseId);
    try {
      await api.claimCase(caseId);
      showToast("Case claimed. Opening full details…");
      const detail = await api.getClaimedCaseDetail(caseId);
      setClaimedDetail(detail);
      load();
    } catch (e) {
      showToast(e instanceof ApiError ? e.message : "Could not claim this case.", "error");
    } finally {
      setClaimingId(null);
    }
  }

  return (
    <Shell>
      <section className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="font-serif text-3xl font-semibold text-ink">Lawyer dashboard</h1>
        <p className="mt-2 text-ink/70">
          Cases citizens have chosen to share with lawyers, matching your
          declared practice areas. Claiming a case reveals full details —
          browsing does not.
        </p>

        {loading && <p className="mt-8 text-ink/60">Loading…</p>}

        {!loading && cases.length === 0 && (
          <p className="mt-8 text-ink/60">
            No open cases in your practice areas right now. Check back later.
          </p>
        )}

        <ul className="mt-8 space-y-4">
          {cases.map((c) => (
            <li key={c.id} className="rounded-lg border border-sage bg-white p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-brand">{DOMAIN_LABELS[c.domain]}</p>
                  <p className="mt-1 font-serif text-lg font-semibold text-ink">{c.title}</p>
                  <p className="mt-1 text-xs text-ink/50">
                    Shared {new Date(c.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-2">
                  {c.highest_severity && <SeverityBadge severity={c.highest_severity} />}
                  <button
                    onClick={() => handleClaim(c.id)}
                    disabled={claimingId === c.id}
                    className="min-h-[40px] rounded-md bg-brand px-4 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
                  >
                    {claimingId === c.id ? "Claiming…" : "Claim this case"}
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>

        {claimedDetail && (
          <div className="mt-10 rounded-lg border-2 border-brand bg-white p-6">
            <h2 className="font-serif text-xl font-semibold text-ink">
              {claimedDetail.title} — full details
            </h2>
            <div className="mt-4 space-y-3">
              {claimedDetail.risk_items?.map((r: any, i: number) => (
                <div key={i} className="rounded-md border border-sage p-3">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-ink">{r.title}</p>
                    <SeverityBadge severity={r.severity} />
                  </div>
                  <p className="mt-1 text-sm text-ink/70">{r.explanation}</p>
                </div>
              ))}
            </div>
            <div className="mt-4">
              <p className="text-sm font-medium text-ink/60 mb-2">Facts extracted</p>
              <ul className="text-sm text-ink/80 space-y-1">
                {claimedDetail.facts?.map((f: any, i: number) => (
                  <li key={i}>
                    <span className="text-ink/50">{f.fact_type}:</span> {f.value}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </section>
    </Shell>
  );
}
