export type ExtractedEntity = {
  title?: string | null;
  subtitle?: string | null;
  statement_of_responsibility?: string | null;
  authors: string[];
  edition?: string | null;
  place_of_publication?: string | null;
  publisher?: string | null;
  year?: string | null;
  isbn?: string | null;
  language: string;
  notes: string[];
  physical_description?: string | null;
};

export type Suggestion = {
  scheme: string;
  heading?: string;
  classmark?: string;
  confidence: number;
};

export type IngestResponse = {
  ocr_text: string;
  extracted: ExtractedEntity;
  subjects: Suggestion[];
  classifications: Suggestion[];
  marc: { marc21_text: string; marcxml: string };
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function ingestImages(files: File[]): Promise<IngestResponse> {
  const form = new FormData();
  for (const f of files) form.append("files", f);

  const res = await fetch(`${API_BASE}/api/v1/ingest`, {
    method: "POST",
    body: form
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`API error: ${res.status} ${txt}`);
  }
  return res.json();
}
