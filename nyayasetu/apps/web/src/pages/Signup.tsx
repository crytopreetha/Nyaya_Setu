import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Shell from "../components/Shell";
import { useAuth } from "../lib/auth";
import { ApiError } from "../lib/api";

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await signup(email, password);
      navigate("/new");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create your account. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Shell>
      <section className="mx-auto max-w-md px-6 py-16">
        <h1 className="font-serif text-3xl font-semibold text-ink">Create an account</h1>
        <p className="mt-2 text-ink/70">
          Only used to keep your cases private to you — never shared or sold.
        </p>

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
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full min-h-[48px] rounded-md border border-sage bg-white px-4 text-ink"
            />
            <p className="mt-1 text-xs text-ink/50">At least 8 characters.</p>
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
            {submitting ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-sm text-ink/70">
          Already have an account?{" "}
          <Link to="/login" className="text-brand underline underline-offset-2">
            Log in
          </Link>
        </p>
      </section>
    </Shell>
  );
}
