import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Shell from "../components/Shell";
import { api } from "../lib/api";
import type { CaseOut } from "../types";
import { DOMAIN_LABELS } from "../types";

export default function History() {
  const [cases, setCases] = useState<CaseOut[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listCases()
      .then(setCases)
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(id: string) {
    await api.deleteCase(id);
    setCases((prev) => prev.filter((c) => c.id !== id));
  }

  return (
    <Shell>
      <section className="mx-auto max-w-3xl px-6 py-12">
        <h1 className="font-serif text-3xl font-semibold text-ink">My cases</h1>

        {loading && <p className="mt-6 text-ink/60">Loading…</p>}
        {!loading && cases.length === 0 && (
          <p className="mt-6 text-ink/60">
            No cases yet.{" "}
            <Link to="/new" className="text-brand underline underline-offset-2">
              Start one
            </Link>
            .
          </p>
        )}

        <ul className="mt-6 space-y-3">
          {cases.map((c) => (
            <li
              key={c.id}
              className="flex items-center justify-between rounded-lg border border-sage bg-white p-4"
            >
              <div>
                <Link
                  to={c.status === "ready" ? `/cases/${c.id}` : `/cases/${c.id}/processing`}
                  className="font-medium text-ink hover:text-brand"
                >
                  {c.title}
                </Link>
                <p className="text-sm text-ink/60">
                  {DOMAIN_LABELS[c.domain]} · {c.status} ·{" "}
                  {new Date(c.created_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={() => handleDelete(c.id)}
                className="min-h-[40px] rounded-md border border-sage px-4 text-sm text-ink/70 hover:bg-sage/40"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      </section>
    </Shell>
  );
}
