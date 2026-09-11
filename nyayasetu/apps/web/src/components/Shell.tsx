import { Link, useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
import { Scale, FolderClock, FilePlus2, LogOut, LogIn, UserPlus } from "lucide-react";
import { useAuth } from "../lib/auth";
import { useLanguage } from "../lib/i18n";

export default function Shell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-sage bg-paper">
        <div className="mx-auto max-w-5xl px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand text-white">
              <Scale className="h-5 w-5" aria-hidden="true" />
            </span>
            <span className="flex flex-col leading-tight">
              <span className="font-serif text-xl font-semibold text-ink">NyayaSetu</span>
              <span className="hidden sm:inline text-xs text-ink/50">
                {t("nav.tagline")}
              </span>
            </span>
          </Link>
          <nav className="flex items-center gap-1 sm:gap-3 text-sm">
            {user ? (
              <>
                <Link
                  to="/history"
                  className="flex items-center gap-1.5 rounded-md px-3 py-2 text-ink/80 hover:bg-sage/60 min-h-[44px]"
                >
                  <FolderClock className="h-4 w-4" aria-hidden="true" />
                  <span className="hidden sm:inline">{t("nav.myCases")}</span>
                </Link>
                <Link
                  to="/new"
                  className="flex items-center gap-1.5 rounded-md bg-brand px-4 py-2 text-white hover:bg-brand-dark min-h-[44px]"
                >
                  <FilePlus2 className="h-4 w-4" aria-hidden="true" />
                  <span className="hidden sm:inline">{t("nav.newCase")}</span>
                </Link>
                <button
                  onClick={() => {
                    logout();
                    navigate("/");
                  }}
                  className="flex items-center gap-1.5 rounded-md px-3 py-2 text-ink/60 hover:bg-sage/60 min-h-[44px]"
                  title={user.email}
                >
                  <LogOut className="h-4 w-4" aria-hidden="true" />
                  <span className="hidden sm:inline">{t("nav.logout")}</span>
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="flex items-center gap-1.5 rounded-md px-3 py-2 text-ink/80 hover:bg-sage/60 min-h-[44px]"
                >
                  <LogIn className="h-4 w-4" aria-hidden="true" />
                  {t("nav.login")}
                </Link>
                <Link
                  to="/signup"
                  className="flex items-center gap-1.5 rounded-md bg-brand px-4 py-2 text-white hover:bg-brand-dark min-h-[44px]"
                >
                  <UserPlus className="h-4 w-4" aria-hidden="true" />
                  {t("nav.signup")}
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-sage">
        <div className="mx-auto max-w-5xl px-6 py-6 text-sm text-ink/60">
          <p>{t("footer.disclaimer")}</p>
        </div>
      </footer>
    </div>
  );
}
