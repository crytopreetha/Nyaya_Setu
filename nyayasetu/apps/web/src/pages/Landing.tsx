import { useNavigate } from "react-router-dom";
import { useState } from "react";
import Shell from "../components/Shell";

const DOMAIN_CARDS = [
  {
    title: "Rental & tenancy",
    desc: "A rent notice, eviction notice, or deposit dispute.",
  },
  {
    title: "Employment",
    desc: "An offer letter, salary deduction, or termination notice.",
  },
  {
    title: "Consumer disputes",
    desc: "A faulty product, warranty issue, or service complaint.",
  },
  {
    title: "Cyber fraud",
    desc: "An online scam, UPI fraud, or account compromise.",
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const [language, setLanguage] = useState<"en" | "hi">("en");

  return (
    <Shell>
      <section className="mx-auto max-w-5xl px-6 pt-16 pb-12">
        <div className="max-w-prose">
          <p className="font-sans text-sm font-medium text-brand mb-3">
            A preventive legal-risk tool for everyday situations
          </p>
          <h1 className="font-serif text-4xl sm:text-5xl font-semibold leading-tight text-ink">
            Understand a legal risk before it becomes a court case.
          </h1>
          <p className="mt-5 text-lg text-ink/80 leading-relaxed">
            Upload a notice or describe what happened. NyayaSetu explains what
            it found in plain language, flags deadlines, and points you to the
            right official service — with every claim linked to its source.
          </p>
        </div>

        <div className="mt-10 flex flex-wrap items-center gap-4">
          <div className="flex rounded-md border border-sage overflow-hidden" role="radiogroup" aria-label="Choose language">
            {(["en", "hi"] as const).map((lang) => (
              <button
                key={lang}
                role="radio"
                aria-checked={language === lang}
                onClick={() => setLanguage(lang)}
                className={`min-h-[44px] px-5 text-sm font-medium ${
                  language === lang ? "bg-brand text-white" : "bg-white text-ink/70 hover:bg-sage/40"
                }`}
              >
                {lang === "en" ? "English" : "हिन्दी"}
              </button>
            ))}
          </div>
          <span className="text-sm text-ink/50">
            More languages can be added via Bhashini without changing this workflow.
          </span>
        </div>

        <div className="mt-6 rounded-lg border border-severity-emergency/30 bg-severity-emergency/5 p-4 max-w-prose">
          <p className="text-sm text-ink/80">
            <strong className="text-severity-emergency">If you are in immediate physical danger,</strong>{" "}
            call 112. For a financial cyber fraud that just happened, call{" "}
            <strong>1930</strong> right away — don't wait to use this tool first.
          </p>
        </div>

        <div className="mt-10 rounded-lg border border-sage bg-white p-5 max-w-prose">
          <h2 className="font-serif text-lg font-semibold text-ink mb-2">Before you start</h2>
          <p className="text-sm text-ink/70 leading-relaxed">
            Anything you upload or describe is used only to analyse your case.
            You can delete a case and its files at any time. This tool provides
            legal information, not legal advice — it will never decide who is
            right, predict what a court will do, or file anything for you.
          </p>
        </div>

        <h2 className="mt-14 font-serif text-2xl font-semibold text-ink">
          What would you like help with?
        </h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {DOMAIN_CARDS.map((d) => (
            <button
              key={d.title}
              onClick={() => navigate("/new", { state: { language } })}
              className="text-left rounded-lg border border-sage bg-white p-5 hover:border-brand hover:shadow-sm transition-colors focus-visible:outline-brand min-h-[96px]"
            >
              <p className="font-serif text-lg font-semibold text-ink">{d.title}</p>
              <p className="mt-1 text-sm text-ink/70">{d.desc}</p>
            </button>
          ))}
        </div>
      </section>
    </Shell>
  );
}
