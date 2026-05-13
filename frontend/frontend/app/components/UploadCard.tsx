"use client";

import { useCallback, useRef } from "react";

export function UploadCard({
  onFilesSelected,
  loading
}: {
  onFilesSelected: (files: File[]) => void;
  loading: boolean;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  const onPick = useCallback(() => inputRef.current?.click(), []);

  const onChange = useCallback(() => {
    const files = Array.from(inputRef.current?.files ?? []);
    if (files.length) onFilesSelected(files);
  }, [onFilesSelected]);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (loading) return;
      const files = Array.from(e.dataTransfer.files).filter((f) =>
        f.type.startsWith("image/")
      );
      if (files.length) onFilesSelected(files);
    },
    [onFilesSelected, loading]
  );

  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm border border-slate-200">
      <h2 className="text-xl font-semibold mb-2">رفع صور بيانات الكتاب</h2>
      <p className="text-sm text-slate-600 mb-4">
        ارفع صورة صفحة العنوان/البيانات الببليوجرافية. يمكنك رفع أكثر من صورة (عنوان، ظهر العنوان…).
      </p>

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        className={`rounded-2xl border-2 border-dashed p-8 text-center ${
          loading ? "opacity-60" : "hover:bg-slate-50"
        }`}
      >
        <p className="text-slate-700 mb-4">
          اسحب الصور هنا أو اخترها من جهازك
        </p>

        <button
          disabled={loading}
          onClick={onPick}
          className="rounded-xl bg-slate-900 text-white px-4 py-2 text-sm hover:bg-slate-800 disabled:opacity-60"
        >
          {loading ? "جاري المعالجة..." : "اختيار صور"}
        </button>

        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={onChange}
        />
      </div>
    </div>
  );
}
