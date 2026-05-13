"use client";

import { useState } from "react";
import { ingestImages, type IngestResponse } from "./api";
import { UploadCard } from "./components/UploadCard";
import { ResultsCard } from "./components/ResultsCard";

export default function Page() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onFilesSelected(files: File[]) {
    setError(null);
    setLoading(true);
    setData(null);
    try {
      const res = await ingestImages(files);
      setData(res);
    } catch (e: any) {
      setError(e?.message ?? "حدث خطأ غير متوقع");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid gap-6">
      <header className="rounded-2xl bg-white p-6 shadow-sm border border-slate-200">
        <h1 className="text-2xl font-bold">Arabic Cataloger</h1>
        <p className="text-slate-600 mt-2">
          رفع صور بيانات الكتاب → OCR → استخراج ذكي → MARC21/RDA → اقتراح LCC و LCSH
        </p>
      </header>

      <UploadCard onFilesSelected={onFilesSelected} loading={loading} />

      {error && (
        <div className="rounded-2xl bg-red-50 border border-red-200 p-4 text-red-800">
          {error}
        </div>
      )}

      {data && <ResultsCard data={data} />}
    </main>
  );
}
