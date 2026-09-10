import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import Shell from "../components/Shell";
import { useAuth } from "../lib/auth";
import { ApiError } from "../lib/api";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const redirectTo = (location.state as { from?: string })?.from || "/history";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email, password);
      navigate(redirectTo);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not log in. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Shell>
      <section className="mx-auto max-w-md px-6 py-16">
        <h1 className="font-serif text-3xl font-semibold text-ink">Log in</h1>
        <p className="mt-2 text-ink/70">Your cases are only visible to you.</p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-ink mb-2">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full min-h-[48px] rounded-md border border-sage bg-white px-4 text-ink"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-ink mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full min-h-[48px] rounded-md border border-sage bg-white px-4 text-ink"
            />
          </div>

          {error && (
            <p className="text-sm text-severity-emergency" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="min-h-[48px] w-full rounded-md bg-brand text-white font-medium hover:bg-brand-dark disabled:opacity-50"
          >
            {submitting ? "Logging in…" : "Log in"}
          </button>
        </form>

        <p className="mt-6 text-sm text-ink/70">
          New here?{" "}
          <Link to="/signup" className="text-brand underline underline-offset-2">
            Create an account
          </Link>
        </p>
      </section>
    </Shell>
  );
}
