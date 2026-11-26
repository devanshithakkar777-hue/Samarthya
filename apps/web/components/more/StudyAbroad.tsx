"use client";

import Link from "next/link";
import { useState } from "react";
import { call } from "@/lib/client";
import { useAction } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Labeled, Note } from "@/components/kit/Controls";

export default function StudyAbroad() {
  const [f, setF] = useState({ tuition: "", living: "", years: "2", savings: "", funding: "0", rate: "10", months: "84" });
  const [out, setOut] = useState<{ total: number; gap: number; emi: number | null } | null>(null);
  const { busy, error, run } = useAction();
  const n = (s: string) => Number(s) || 0;
  async function go(e: React.FormEvent) {
    e.preventDefault();
    const total = (n(f.tuition) + n(f.living)) * n(f.years);
    const gap = Math.max(0, total - n(f.savings) - n(f.funding));
    let emi: number | null = null;
    if (gap > 0) { const r = await run(() => call<{ monthly_payment: number }>("POST", "/v1/calc/emi", { principal: gap, annual_rate_pct: n(f.rate), months: n(f.months) })); emi = r?.monthly_payment ?? null; }
    setOut({ total, gap, emi });
  }
  const fields: [string, string, string][] = [["tuition", "Tuition per year (₹ equivalent)", "Take it from the university's official fee page"], ["living", "Living cost per year (₹)", "Use the university's own estimate"], ["years", "Years of study", ""], ["savings", "Family savings you can use (₹)", ""], ["funding", "Scholarships or funding secured (₹)", "Count only what is confirmed in writing"], ["rate", "Loan interest rate (% per year)", "Ask the lender; do not guess"], ["months", "Months to repay", ""]];
  return (
    <div className="grid max-w-2xl gap-4"><Note>This is a planning aid. You supply every figure from official pages, and it only does the arithmetic. It is not financial advice and does not know visa, exam or admission rules.</Note>
      <form onSubmit={go} className="grid gap-3">{fields.map(([k, l, h]) => <Labeled key={k} id={k} label={l} help={h || undefined}><input id={k} inputMode="decimal" className={inp} value={f[k as keyof typeof f]} onChange={(e) => setF({ ...f, [k]: e.target.value })} /></Labeled>)}
        <ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy}>Work it out</button></div></form>
      {out && <dl aria-live="polite" className="grid gap-2"><div className="rounded-md border border-ink/10 bg-white p-3"><dt className="text-sm text-slate">Total cost</dt><dd>₹{out.total.toLocaleString("en-IN")}</dd></div>
        <div className="rounded-md border border-ink/10 bg-white p-3"><dt className="text-sm text-slate">Still to arrange</dt><dd>₹{out.gap.toLocaleString("en-IN")}</dd></div>
        {out.emi !== null && <div className="rounded-md border border-ink/10 bg-white p-3"><dt className="text-sm text-slate">Monthly loan payment if you borrow the gap</dt><dd>₹{out.emi.toLocaleString("en-IN")}</dd></div>}</dl>}
      <p className="text-sm"><Link className="text-electric-blue underline" href="/opportunities?kind=higher_education">Higher education listings</Link> · <Link className="text-electric-blue underline" href="/opportunities?kind=scholarship">Scholarships</Link></p>
    </div>
  );
}
