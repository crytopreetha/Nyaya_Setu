import { Info, AlertTriangle, AlertOctagon, Siren } from "lucide-react";
import type { Severity } from "../types";
import { SEVERITY_LABELS } from "../types";

const STYLES: Record<Severity, string> = {
  informational: "bg-severity-informational/10 text-severity-informational border-severity-informational/30",
  attention: "bg-severity-attention/10 text-severity-attention border-severity-attention/30",
  urgent: "bg-severity-urgent/10 text-severity-urgent border-severity-urgent/40",
  emergency: "bg-severity-emergency/10 text-severity-emergency border-severity-emergency/50",
};

const ICONS: Record<Severity, typeof Info> = {
  informational: Info,
  attention: AlertTriangle,
  urgent: AlertOctagon,
  emergency: Siren,
};

export default function SeverityBadge({ severity }: { severity: Severity }) {
  const Icon = ICONS[severity];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-medium ${STYLES[severity]}`}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {SEVERITY_LABELS[severity]}
    </span>
  );
}
