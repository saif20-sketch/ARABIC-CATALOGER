import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Arabic Cataloger",
  description: "OCR → استخراج → MARC21/RDA → LCC/LCSH"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <div className="mx-auto max-w-6xl p-6">{children}</div>
      </body>
    </html>
  );
}
