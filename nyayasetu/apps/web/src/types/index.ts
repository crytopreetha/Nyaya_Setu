export type Domain =
  | "rental_tenancy"
  | "employment"
  | "consumer_disputes"
  | "cyber_fraud"
  | "general_notice";

export type CaseStatus =
  | "created"
  | "extracting"
  | "analyzing"
  | "ready"
  | "failed"
  | "deleted";

export type Severity = "informational" | "attention" | "urgent" | "emergency";

export interface CaseOut {
  id: string;
  title: string;
  domain: Domain;
  input_type: "document" | "text" | "audio";
  status: CaseStatus;
  created_at: string;
}

export interface CaseStatusOut {
  id: string;
  status: CaseStatus;
  error_message?: string | null;
}

export interface FactOut {
  id: string;
  fact_type: string;
  value: string;
  source_page?: number | null;
  confidence: string;
  user_edited: boolean;
}

export interface CitationOut {
  source_id: string;
  title: string;
  url: string;
  quote?: string | null;
  page?: number | null;
}

export interface RiskItemOut {
  id: string;
  title: string;
  severity: Severity;
  explanation: string;
  is_inference: boolean;
  citations: CitationOut[];
}

export interface DeadlineOut {
  id: string;
  label: string;
  date: string | null;
  confidence: string;
  basis: string | null;
  status: "unconfirmed" | "confirmed" | "dismissed";
}

export interface ActionItemOut {
  id: string;
  position: number;
  text: string;
  reason: string | null;
  official_url: string | null;
  completed: boolean;
}

export interface AnalysisOut {
  case_id: string;
  status: CaseStatus;
  domain: Domain;
  summary?: string | null;
  document_type?: string | null;
  facts: FactOut[];
  risk_items: RiskItemOut[];
  important_dates: DeadlineOut[];
  next_steps: ActionItemOut[];
  low_quality_pages: number[];
  disclaimer?: string | null;
}

export interface SourceOut {
  id: string;
  title: string;
  url: string;
  publisher?: string | null;
  jurisdiction?: string | null;
  topic?: string | null;
  verification_status: string;
}

export interface ReferralOut {
  need: string;
  action: string;
  source: SourceOut;
}

export interface DraftOut {
  id: string;
  draft_type: string;
  content: string;
  created_at: string;
}

export interface UserOut {
  id: string;
  email: string;
  preferred_language: string;
  role: "citizen" | "lawyer";
  created_at: string;
}

export interface TokenOut {
  access_token: string;
  token_type: string;
  user: UserOut;
}

export interface TranscriptionOut {
  text: string;
  language?: string | null;
}

export const DOMAIN_LABELS: Record<Domain, string> = {
  rental_tenancy: "Rental & tenancy",
  employment: "Employment",
  consumer_disputes: "Consumer disputes",
  cyber_fraud: "Cyber fraud",
  general_notice: "General legal notice",
};

export const SEVERITY_LABELS: Record<Severity, string> = {
  informational: "Informational",
  attention: "Attention",
  urgent: "Urgent",
  emergency: "Emergency",
};

export const FACT_TYPE_LABELS: Record<string, string> = {
  party: "Person involved",
  date: "Date",
  amount: "Amount",
  location: "Location",
  demand: "Demand",
  document_type: "Document type",
  organization: "Organization",
  channel: "Communication channel",
  harm: "Harm described",
  desired_outcome: "What you want to happen",
  immediate_danger: "Immediate danger",
  other: "Other detail",
};

export interface CaseFileOut {
  id: string;
  original_filename: string;
  mime_type: string;
  size: number;
  created_at: string;
}

export interface LawyerProfileOut {
  id: string;
  full_name: string;
  bar_registration_number: string;
  practice_domains: Domain[];
  city?: string | null;
  state?: string | null;
  languages: string[];
  bio?: string | null;
  phone?: string | null;
  verified: boolean;
}

export interface LawyerProfileCreate {
  full_name: string;
  bar_registration_number: string;
  practice_domains: Domain[];
  city?: string;
  state?: string;
  languages: string[];
  bio?: string;
  phone?: string;
}

export interface CaseListingOut {
  id: string;
  domain: Domain;
  title: string;
  summary?: string | null;
  highest_severity?: Severity | null;
  created_at: string;
}

export interface AssignedLawyerOut {
  id: string;
  full_name: string;
  city?: string | null;
  state?: string | null;
  languages: string[];
  bio?: string | null;
  phone?: string | null;
  verified: boolean;
  claimed_at: string;
}
