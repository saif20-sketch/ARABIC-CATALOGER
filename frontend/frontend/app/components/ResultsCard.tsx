"use client";

import type { IngestResponse } from "../api";
import { MarcViewer } from "./MarcViewer";

export function ResultsCard({ data }: { data: IngestResponse }) {
  const { extracted, subjects, classifications, ocr_text, marc } = data;

  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm border border-slate-200">
      <h2 className="text-xl font-semibold mb-4">النتائج</h2>

      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <div className="rounded-2xl bg-slate-50 p-4 border border-slate-200">
          <h3 className="font-semibold mb-2">البيانات المستخرجة</h3>
          <ul className="text-sm leading-7">
            <li><b>العنوان:</b> {extracted.title ?? "—"}</li>
            <li><b>العنوان الفرعي:</b> {extracted.subtitle ?? "—"}</li>
            <li><b>المسؤولية:</b> {extracted.statement_of_responsibility ?? "—"}</li>
            <li><b>المؤلفون:</b> {extracted.authors?.length ? extracted.authors.join("؛ ") : "—"}</li>
            <li><b>الطبعة:</b> {extracted.edition ?? "—"}</li>
            <li><b>مكان النشر:</b> {extracted.place_of_publication ?? "—"}</li>
            <li><b>الناشر:</b> {extracted.publisher ?? "—"}</li>
            <li><b>السنة:</b> {extracted.year ?? "—"}</li>
            <li><b>ISBN:</b> {extracted.isbn ?? "—"}</li>
            <li><b>الوصف المادي:</b> {extracted.physical_description ?? "—"}</li>
          </ul>
        </div>

        <div className="rounded-2xl bg-slate-50 p-4 border border-slate-200">
          <h3 className="font-semibold mb-2">اقتراحات LCSH و LCC</h3>

          <div className="mb-3">
            <div className="text-sm font-semibold mb-1">LCSH:</div>
            <ul className="text-sm list-disc pr-5">
              {subjects?.length ? subjects.map((s, i) => (
                <li key={i}>{s.heading} <span className="text-slate-500">({Math.round(s.confidence*100)}%)</span></li>
              )) : <li className="text-slate-500">لا توجد اقتراحات حالياً</li>}
            </ul>
          </div>

          <div>
            <div className="text-sm font-semibold mb-1">LCC:</div>
            <ul className="text-sm list-disc pr-5">
              {classifications?.length ? classifications.map((c, i) => (
                <li key={i}>{c.classmark} <span className="text-slate-500">({Math.round(c.confidence*100)}%)</span></li>
              )) : <li className="text-slate-500">لا توجد اقتراحات حالياً</li>}
            </ul>
          </div>
        </div>
      </div>

      <div className="rounded-2xl bg-white p-4 border border-slate-200 mb-6">
        <h3 className="font-semibold mb-2">نص OCR</h3>
        <pre className="text-xs whitespace-pre-wrap leading-5 bg-slate-50 p-3 rounded-xl border border-slate-200">
          {ocr_text}
        </pre>
      </div>

      <MarcViewer marcText={marc.marc21_text} marcXml={marc.marcxml} />
    </div>
  );
}
