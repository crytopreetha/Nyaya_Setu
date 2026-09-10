import { Link, useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "../lib/auth";

export default function Shell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-sage bg-paper">
        <div className="mx-auto max-w-5xl px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-baseline gap-2">
            <span className="font-serif text-xl font-semibold text-ink">NyayaSetu</span>
            <span className="hidden sm:inline text-sm text-ink/60">
              understand a risk before it becomes a case
            </span>
          </Link>
          <nav className="flex items-center gap-2 sm:gap-4 text-sm">
            {user ? (
              <>
                <Link
                  to="/history"
                  className="rounded-md px-3 py-2 text-ink/80 hover:bg-sage/60 min-h-[44px] flex items-center"
                >
                  My cases
                </Link>
                <Link
                  to="/new"
                  className="rounded-md bg-brand px-4 py-2 text-white hover:bg-brand-dark min-h-[44px] flex items-center"
                >
                  New case
                </Link>
                <button
                  onClick={() => {
                    logout();
                    navigate("/");
                  }}
                  className="rounded-md px-3 py-2 text-ink/60 hover:bg-sage/60 min-h-[44px]"
                  title={user.email}
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="rounded-md px-3 py-2 text-ink/80 hover:bg-sage/60 min-h-[44px] flex items-center"
                >
                  Log in
                </Link>
                <Link
                  to="/signup"
                  className="rounded-md bg-brand px-4 py-2 text-white hover:bg-brand-dark min-h-[44px] flex items-center"
                >
                  Sign up
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-sage">
        <div className="mx-auto max-w-5xl px-6 py-6 text-sm text-ink/60">
          <p>
            NyayaSetu gives legal information and procedural guidance, not legal
            advice. It does not decide guilt, predict a court outcome, or submit
            anything on your behalf.
          </p>
        </div>
      </footer>
    </div>
  );
}
