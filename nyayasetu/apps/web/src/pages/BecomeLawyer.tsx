import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Scale } from "lucide-react";
import Shell from "../components/Shell";
import { api, ApiError } from "../lib/api";
import type { Domain } from "../types";
import { DOMAIN_LABELS } from "../types";

const ALL_DOMAINS: Domain[] = [
  "rental_tenancy",
  "employment",
  "consumer_disputes",
  "cyber_fraud",
  "general_notice",
];

export default function BecomeLawyer() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [barNumber, setBarNumber] = useState("");
  const [domains, setDomains] = useState<Domain[]>([]);
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [phone, setPhone] = useState("");
  const [bio, setBio] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleDomain(d: Domain) {
    setDomains((prev) => (prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]));
  }

  async function handleSubmit() {
    if (!fullName || !barNumber || domains.length === 0) {
      setError("Name, bar registration number, and at least one practice area are required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await api.registerLawyer({
        full_name: fullName,
        bar_registration_number: barNumber,
        practice_domains: domains,
        city: city || undefined,
        state: state || undefined,
        languages: ["en"],
        bio: bio || undefined,
        phone: phone || undefined,
      });
      navigate("/lawyer");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not create your lawyer profile.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Shell>
      <section className="mx-auto max-w-2xl px-6 py-12">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-brand/10 text-brand">
            <Scale className="h-5 w-5" aria-hidden="true" />
          </span>
          <h1 className="font-serif text-3xl font-semibold text-ink">Register as a lawyer</h1>
        </div>
        <p className="mt-3 text-ink/70">
          Citizens can choose to share a case with lawyers once its analysis is
          ready. You'll see a redacted summary first — full details only
          after you claim a case.
        </p>
        <div className="mt-4 rounded-lg border border-severity-attention/30 bg-severity-attention/5 p-4 text-sm text-ink/70">
          This is a prototype: bar registration numbers are self-declared and
          not yet verified against the Bar Council register. Treat "Verified"
          badges accordingly until that check is wired up.
        </div>

        <div className="mt-8 space-y-5">
          <div>
            <label className="block text-sm font-medium text-ink mb-2">Full name</label>
            <input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full min-h-[48px] rounded-md border border-sage bg-white px-4 text-ink"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-2">Bar registration number</label>
            <input
              value={barNumber}
              onChange={(e) => setBarNumber(e.target.value)}
              className="w-full min-h-[48px] rounded-md border border-sage bg-white px-4 text-ink"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-2">Practice areas</label>
            <div className="flex flex-wrap gap-2">
              {ALL_DOMAINS.map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => toggleDomain(d)}
                  className={`min-h-[40px] rounded-full border px-4 text-sm font-medium ${
                    domains.includes(d)
                      ? "bg-brand text-white border-brand"
                      : "bg-white text-ink/70 border-sage hover:bg-sage/40"
                  }`}
                >
                  {DOMAIN_LABELS[d]}
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-ink mb-2">City</label>
              <input
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="w-full min-h-[48px] rounded-md border border-sage bg-white px-4 text-ink"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-ink mb-2">State</label>
              <input
                value={state}
                onChange={(e) => setState(e.target.value)}
                className="w-full min-h-[48px] rounded-md border border-sage bg-white px-4 text-ink"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-2">Phone (shown to a citizen only after you claim their case)</label>
            <input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full min-h-[48px] rounded-md border border-sage bg-white px-4 text-ink"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-2">Short bio (optional)</label>
            <textarea
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              rows={4}
              className="w-full rounded-md border border-sage bg-white p-4 text-ink"
            />
          </div>

          {error && <p className="text-sm text-severity-emergency">{error}</p>}

          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="min-h-[48px] rounded-md bg-brand px-8 text-white font-medium hover:bg-brand-dark disabled:opacity-50"
          >
            {submitting ? "Creating profile…" : "Create lawyer profile"}
          </button>
        </div>
      </section>
    </Shell>
  );
}
