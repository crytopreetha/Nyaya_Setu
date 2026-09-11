import { useNavigate } from "react-router-dom";
import { Home, Briefcase, ShoppingCart, ShieldAlert, FileText, ArrowRight, PhoneCall } from "lucide-react";
import Shell from "../components/Shell";
import { useLanguage } from "../lib/i18n";
import type { Language } from "../lib/i18n";

const LANGUAGE_OPTIONS: { code: Language; label: string }[] = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "mr", label: "मराठी" },
];

export default function Landing() {
  const navigate = useNavigate();
  const { language, setLanguage, t } = useLanguage();

  const DOMAIN_CARDS = [
    { titleKey: "domain.rental", descKey: "domain.rentalDesc", icon: Home } as const,
    { titleKey: "domain.employment", descKey: "domain.employmentDesc", icon: Briefcase } as const,
    { titleKey: "domain.consumer", descKey: "domain.consumerDesc", icon: ShoppingCart } as const,
    { titleKey: "domain.cyber", descKey: "domain.cyberDesc", icon: ShieldAlert } as const,
  ];

  return (
    <Shell>
      <section className="mx-auto max-w-5xl px-6 pt-16 pb-12">
        <div className="max-w-prose">
          <p className="font-sans text-sm font-medium text-brand mb-3 inline-flex items-center gap-1.5">
            <FileText className="h-4 w-4" aria-hidden="true" />
            {t("landing.eyebrow")}
          </p>
          <h1 className="font-serif text-4xl sm:text-5xl font-semibold leading-tight text-ink">
            {t("landing.title")}
          </h1>
          <p className="mt-5 text-lg text-ink/80 leading-relaxed">{t("landing.subtitle")}</p>
        </div>

        <div className="mt-10 flex flex-wrap items-center gap-4">
          <div className="flex rounded-md border border-sage overflow-hidden" role="radiogroup" aria-label="Choose language">
            {LANGUAGE_OPTIONS.map((opt) => (
              <button
                key={opt.code}
                role="radio"
                aria-checked={language === opt.code}
                onClick={() => setLanguage(opt.code)}
                className={`min-h-[44px] px-5 text-sm font-medium transition-colors ${
                  language === opt.code ? "bg-brand text-white" : "bg-white text-ink/70 hover:bg-sage/40"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <span className="text-sm text-ink/50">{t("landing.languageNote")}</span>
        </div>

        <div className="mt-6 flex items-start gap-3 rounded-lg border border-severity-emergency/30 bg-severity-emergency/5 p-4 max-w-prose">
          <PhoneCall className="h-5 w-5 shrink-0 text-severity-emergency mt-0.5" aria-hidden="true" />
          <p className="text-sm text-ink/80">{t("landing.emergency")}</p>
        </div>

        <div className="mt-10 rounded-lg border border-sage bg-white p-5 max-w-prose">
          <h2 className="font-serif text-lg font-semibold text-ink mb-2">{t("landing.beforeTitle")}</h2>
          <p className="text-sm text-ink/70 leading-relaxed">{t("landing.beforeBody")}</p>
        </div>

        <h2 className="mt-14 font-serif text-2xl font-semibold text-ink">{t("landing.whatHelp")}</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {DOMAIN_CARDS.map((d) => {
            const Icon = d.icon;
            return (
              <button
                key={d.titleKey}
                onClick={() => navigate("/new")}
                className="group text-left rounded-lg border border-sage bg-white p-5 hover:border-brand hover:shadow-sm transition-all focus-visible:outline-brand min-h-[96px] flex items-start gap-4"
              >
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-brand/10 text-brand group-hover:bg-brand group-hover:text-white transition-colors">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </span>
                <div className="flex-1">
                  <p className="font-serif text-lg font-semibold text-ink">{t(d.titleKey)}</p>
                  <p className="mt-1 text-sm text-ink/70">{t(d.descKey)}</p>
                </div>
                <ArrowRight
                  className="h-4 w-4 text-ink/20 group-hover:text-brand group-hover:translate-x-0.5 transition-all mt-1.5 shrink-0"
                  aria-hidden="true"
                />
              </button>
            );
          })}
        </div>
      </section>
    </Shell>
  );
}
