import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Shell from "../components/Shell";
import { api, ApiError } from "../lib/api";
import type { Domain } from "../types";
import { DOMAIN_LABELS } from "../types";

const DOMAINS: Domain[] = [
  "rental_tenancy",
  "employment",
  "consumer_disputes",
  "cyber_fraud",
  "general_notice",
];

type Mode = "text" | "document" | "voice";

export default function NewCase() {
  const navigate = useNavigate();
  const [domain, setDomain] = useState<Domain>("rental_tenancy");
  const [mode, setMode] = useState<Mode>("text");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // --- Voice recording state ---
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  async function startRecording() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setTranscribing(true);
        try {
          const result = await api.transcribeAudio(blob, blob.type);
          setText((prev) => (prev ? `${prev}\n${result.text}` : result.text));
        } catch (e) {
          setError(e instanceof ApiError ? e.message : "Could not transcribe that recording.");
        } finally {
          setTranscribing(false);
        }
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
    } catch {
      setError("Could not access your microphone. Check your browser's permission settings.");
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }

  const canSubmit =
    consent &&
    !submitting &&
    ((mode !== "document" && text.trim().length > 10) || (mode === "document" && file));

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      // Voice mode reuses the "text" case path once the user has reviewed
      // and (optionally) edited the transcript — Section 6.2 requires the
      // transcript be shown for correction before analysis, which the
      // recording step above already did.
      const effectiveInputType = mode === "document" ? "document" : "text";

      const created = await api.createCase({
        domain,
        input_type: effectiveInputType,
        text_input: effectiveInputType === "text" ? text : undefined,
        consent,
      });

      if (mode === "document" && file) {
        await api.uploadFile(created.id, file);
      }

      await api.startAnalysis(created.id);
      navigate(`/cases/${created.id}/processing`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not create the case. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <Shell>
      <section className="mx-auto max-w-3xl px-6 py-12">
        <h1 className="font-serif text-3xl font-semibold text-ink">Start a new case</h1>
        <p className="mt-2 text-ink/70">
          Choose what this is about, then upload a document, describe what
          happened, or record a short voice note.
        </p>

        <div className="mt-8">
          <label className="block text-sm font-medium text-ink mb-2" htmlFor="domain">
            What is this about?
          </label>
          <select
            id="domain"
            value={domain}
            onChange={(e) => setDomain(e.target.value as Domain)}
            className="w-full min-h-[48px] rounded-md border border-sage bg-white px-4 text-ink"
          >
            {DOMAINS.map((d) => (
              <option key={d} value={d}>
                {DOMAIN_LABELS[d]}
              </option>
            ))}
          </select>
        </div>

        <div className="mt-8">
          <div className="flex flex-wrap rounded-md border border-sage overflow-hidden w-fit" role="tablist">
            {(["text", "document", "voice"] as Mode[]).map((m) => (
              <button
                key={m}
                role="tab"
                aria-selected={mode === m}
                onClick={() => setMode(m)}
                className={`min-h-[44px] px-5 text-sm font-medium ${
                  mode === m ? "bg-brand text-white" : "bg-white text-ink/70 hover:bg-sage/40"
                }`}
              >
                {m === "text" ? "Describe it" : m === "document" ? "Upload a document" : "Record voice note"}
              </button>
            ))}
          </div>

          {mode === "document" ? (
            <div className="mt-4">
              <label className="block text-sm font-medium text-ink mb-2" htmlFor="file">
                Upload a PDF, photo, or scanned document
              </label>
              <input
                id="file"
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.docx"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="block w-full text-sm text-ink/70 file:mr-4 file:min-h-[44px] file:px-4 file:rounded-md file:border-0 file:bg-brand file:text-white file:font-medium"
              />
              {file && <p className="mt-2 text-sm text-ink/60">Selected: {file.name}</p>}
            </div>
          ) : (
            <div className="mt-4">
              {mode === "voice" && (
                <div className="mb-4 flex items-center gap-3">
                  {!recording ? (
                    <button
                      type="button"
                      onClick={startRecording}
                      disabled={transcribing}
                      className="min-h-[44px] rounded-md bg-severity-emergency px-5 text-white font-medium hover:opacity-90 disabled:opacity-50"
                    >
                      ● Start recording
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={stopRecording}
                      className="min-h-[44px] rounded-md border border-severity-emergency px-5 text-severity-emergency font-medium animate-pulse"
                    >
                      ■ Stop & transcribe
                    </button>
                  )}
                  {transcribing && <span className="text-sm text-ink/60">Transcribing…</span>}
                </div>
              )}
              <label className="block text-sm font-medium text-ink mb-2" htmlFor="incident">
                {mode === "voice" ? "Review and edit your transcript" : "What happened?"}
              </label>
              <textarea
                id="incident"
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={8}
                placeholder={
                  mode === "voice"
                    ? "Your transcribed recording will appear here — check it over and fix anything the transcription got wrong before submitting."
                    : "Describe the notice, incident, or dispute in your own words — include any dates, amounts, and people involved that you remember."
                }
                className="w-full rounded-md border border-sage bg-white p-4 text-ink leading-relaxed"
              />
            </div>
          )}
        </div>

        <label className="mt-8 flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            className="mt-1 h-5 w-5 rounded border-sage"
          />
          <span className="text-sm text-ink/80">
            I understand this tool provides legal information, not legal
            advice, and I consent to my document or description being
            processed to analyse this case. I can delete this case at any time.
          </span>
        </label>

        {error && (
          <p className="mt-4 text-sm text-severity-emergency" role="alert">
            {error}
          </p>
        )}

        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="mt-8 min-h-[48px] w-full sm:w-auto rounded-md bg-brand px-8 text-white font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-brand-dark"
        >
          {submitting ? "Submitting…" : "Analyse this case"}
        </button>
      </section>
    </Shell>
  );
}
