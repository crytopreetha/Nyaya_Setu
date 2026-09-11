import type {
  AnalysisOut,
  CaseOut,
  CaseStatusOut,
  DraftOut,
  ReferralOut,
  SourceOut,
  Domain,
  TokenOut,
  UserOut,
  TranscriptionOut,
  CaseFileOut,
  LawyerProfileOut,
  LawyerProfileCreate,
  CaseListingOut,
  AssignedLawyerOut,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const TOKEN_KEY = "nyayasetu_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

class ApiError extends Error {
  status: number;
  requestId?: string;
  constructor(message: string, status: number, requestId?: string) {
    super(message);
    this.status = status;
    this.requestId = requestId;
  }
}

function triggerBrowserDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (res.status === 401) {
    clearToken();
  }

  if (!res.ok) {
    let detail = "Something went wrong. Please try again.";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore parse errors */
    }
    throw new ApiError(detail, res.status, res.headers.get("X-Request-Id") ?? undefined);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  // --- Auth ---
  signup: (email: string, password: string) =>
    request<TokenOut>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<TokenOut>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<UserOut>("/api/auth/me"),

  // --- Transcription (voice input) ---
  transcribeAudio: (blob: Blob, mimeType: string) => {
    const form = new FormData();
    const extension = mimeType.includes("webm") ? "webm" : mimeType.includes("mp4") ? "m4a" : "wav";
    form.append("file", blob, `recording.${extension}`);
    return request<TranscriptionOut>("/api/transcribe", { method: "POST", body: form });
  },

  // --- Cases ---
  createCase: (input: {
    domain: Domain;
    input_type: "document" | "text" | "audio";
    text_input?: string;
    title?: string;
    consent: boolean;
  }) =>
    request<CaseOut>("/api/cases", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  listCases: () => request<CaseOut[]>("/api/cases"),

  uploadFile: (caseId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ id: string; original_filename: string }>(
      `/api/cases/${caseId}/files`,
      { method: "POST", body: form }
    );
  },

  listFiles: (caseId: string) => request<CaseFileOut[]>(`/api/cases/${caseId}/files`),

  deleteFile: (caseId: string, fileId: string) =>
    request<void>(`/api/cases/${caseId}/files/${fileId}`, { method: "DELETE" }),

  // Downloads bypass `request()` because they need to trigger a browser
  // save-as, not parse JSON — but they still need the auth header attached,
  // so a plain <a href> to the API won't work here.
  downloadFile: async (caseId: string, fileId: string, filename: string) => {
    const res = await fetch(`${BASE_URL}/api/cases/${caseId}/files/${fileId}/download`, {
      headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {},
    });
    if (!res.ok) throw new ApiError("Could not download that file.", res.status);
    const blob = await res.blob();
    triggerBrowserDownload(blob, filename);
  },

  downloadDraftPdf: async (caseId: string, draftId: string, filename = "draft.pdf") => {
    const res = await fetch(`${BASE_URL}/api/cases/${caseId}/drafts/${draftId}/pdf`, {
      headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {},
    });
    if (!res.ok) throw new ApiError("Could not generate the PDF.", res.status);
    const blob = await res.blob();
    triggerBrowserDownload(blob, filename);
  },

  startAnalysis: (caseId: string) =>
    request<CaseStatusOut>(`/api/cases/${caseId}/analyze`, { method: "POST" }),

  getStatus: (caseId: string) =>
    request<CaseStatusOut>(`/api/cases/${caseId}/status`),

  getAnalysis: (caseId: string) =>
    request<AnalysisOut>(`/api/cases/${caseId}/analysis`),

  updateFact: (caseId: string, factId: string, value: string) =>
    request(`/api/cases/${caseId}/facts`, {
      method: "PATCH",
      body: JSON.stringify({ id: factId, value }),
    }),

  confirmDeadline: (caseId: string, deadlineId: string) =>
    request(`/api/cases/${caseId}/deadlines/${deadlineId}/confirm`, {
      method: "POST",
    }),

  deleteCase: (caseId: string) =>
    request<void>(`/api/cases/${caseId}`, { method: "DELETE" }),

  getReferrals: (domain: Domain) =>
    request<ReferralOut[]>(`/api/referrals?domain=${domain}`),

  listSources: () => request<SourceOut[]>("/api/sources"),

  createDraft: (
    caseId: string,
    draftType: "response_letter" | "complaint_summary" | "evidence_summary"
  ) =>
    request<DraftOut>(`/api/cases/${caseId}/drafts`, {
      method: "POST",
      body: JSON.stringify({ draft_type: draftType }),
    }),

  listDrafts: (caseId: string) =>
    request<DraftOut[]>(`/api/cases/${caseId}/drafts`),

  // --- Lawyer marketplace ---
  shareCaseWithLawyers: (caseId: string, share: boolean) =>
    request(`/api/cases/${caseId}/share-with-lawyers?share=${share}`, { method: "POST" }),

  getAssignedLawyer: (caseId: string) =>
    request<AssignedLawyerOut | null>(`/api/cases/${caseId}/lawyer`),

  registerLawyer: (payload: LawyerProfileCreate) =>
    request<LawyerProfileOut>("/api/lawyers/me", { method: "POST", body: JSON.stringify(payload) }),

  getMyLawyerProfile: () => request<LawyerProfileOut>("/api/lawyers/me"),

  browseOpenCases: () => request<CaseListingOut[]>("/api/lawyers/cases"),

  claimCase: (caseId: string) =>
    request<CaseListingOut>(`/api/lawyers/cases/${caseId}/claim`, { method: "POST" }),

  getClaimedCaseDetail: (caseId: string) =>
    request<any>(`/api/lawyers/cases/${caseId}/full`),
};

export { ApiError };
