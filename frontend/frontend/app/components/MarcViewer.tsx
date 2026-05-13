"use client";

export function MarcViewer({
  marcText,
  marcXml
}: {
  marcText: string;
  marcXml: string;
}) {
  return (
    <div className="grid gap-4">
      <div className="rounded-2xl bg-white p-4 shadow-sm border border-slate-200">
        <h3 className="font-semibold mb-2">MARC21 (Text)</h3>
        <pre className="text-xs whitespace-pre-wrap leading-5 bg-slate-50 p-3 rounded-xl border border-slate-200">
          {marcText}
        </pre>
      </div>

      <div className="rounded-2xl bg-white p-4 shadow-sm border border-slate-200">
        <h3 className="font-semibold mb-2">MARCXML</h3>
        <pre className="text-xs whitespace-pre-wrap leading-5 bg-slate-50 p-3 rounded-xl border border-slate-200">
          {marcXml}
        </pre>
      </div>
    </div>
  );
}
