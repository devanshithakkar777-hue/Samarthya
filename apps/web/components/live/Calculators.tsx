"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Labeled, Note, Tabs } from "@/components/kit/Controls";

type F = { name: string; label: string; def: string; help?: string };
const CALCS: Record<string, { label: string; fields: F[]; intro: string; show: (r: Record<string, number | string>) => [string, string][] }> = {
  emi: { label: "Loan EMI", intro: "What a loan costs you each month and in total.", fields: [{ name: "principal", label: "Loan amount (₹)", def: "100000" }, { name: "annual_rate_pct", label: "Yearly interest rate (%)", def: "10" }, { name: "months", label: "Months", def: "12" }],
    show: (r) => [["Monthly payment", `₹${r.monthly_payment}`], ["Total you pay", `₹${r.total_paid}`], ["Of which interest", `₹${r.total_interest}`]] },
  growth: { label: "Savings growth", intro: "How a saving or investment could grow at a steady rate. This is arithmetic, not a forecast.", fields: [{ name: "principal", label: "Starting amount (₹)", def: "10000" }, { name: "annual_rate_pct", label: "Yearly return (%)", def: "7" }, { name: "years", label: "Years", def: "5" }, { name: "monthly_addition", label: "Added each month (₹)", def: "1000" }],
    show: (r) => [["Final value", `₹${r.final_value}`], ["Total you put in", `₹${r.total_invested}`], ["Growth", `₹${r.growth}`]] },
  inflation: { label: "Inflation", intro: "What rising prices do to money over time.", fields: [{ name: "amount", label: "Amount today (₹)", def: "100000" }, { name: "inflation_pct", label: "Yearly inflation (%)", def: "5" }, { name: "years", label: "Years", def: "10" }],
    show: (r) => [["Same things would cost", `₹${r.future_cost_of_same_things}`], ["₹ amount later is worth today", `₹${r.todays_value_of_amount_later}`]] },
  budget: { label: "Monthly budget", intro: "A simple starting split to think with. Change it to fit your life.", fields: [{ name: "monthly_income", label: "Monthly money in (₹)", def: "20000" }, { name: "needs_pct", label: "Needs (%)", def: "50" }, { name: "wants_pct", label: "Wants (%)", def: "30" }],
    show: (r) => [["Needs", `₹${r.needs}`], ["Wants", `₹${r.wants}`], ["Savings and debt", `₹${r.savings_and_debt}`]] },
  goal: { label: "Savings goal", intro: "How long to reach what you are saving for.", fields: [{ name: "target", label: "Target (₹)", def: "50000" }, { name: "current", label: "Saved so far (₹)", def: "5000" }, { name: "monthly", label: "Save each month (₹)", def: "2000" }],
    show: (r) => { const y = r.years_and_months as unknown as number[]; return [["Months needed", String(r.months_needed)], ["That is", `${y?.[0] ?? 0} years and ${y?.[1] ?? 0} months`]]; } },
  ctc: { label: "CTC to in-hand", intro: "Turn a yearly CTC into what could reach your bank each month. Type your own income tax estimate; this tool does not guess tax.", fields: [{ name: "annual_ctc", label: "Yearly CTC (₹)", def: "600000" }, { name: "variable_pct", label: "Variable pay (% of CTC)", def: "10" }, { name: "basic_pct", label: "Basic pay (% of fixed)", def: "40" }, { name: "pf_pct", label: "PF rate (%)", def: "12" }, { name: "professional_tax_monthly", label: "Professional tax per month (₹)", def: "200" }, { name: "income_tax_annual", label: "Your income tax estimate per year (₹)", def: "0", help: "Use the official Income Tax Department calculator to get this." }],
    show: (r) => [["Fixed pay per year", `₹${r.fixed_per_year}`], ["Variable pay per year (not guaranteed)", `₹${r.variable_per_year}`], ["Gross per month", `₹${r.gross_monthly}`], ["Your PF per month", `₹${r.employee_pf_monthly}`], ["Estimated in-hand per month", `₹${r.inhand_monthly}`]] },
  offers: { label: "Compare two offers", intro: "Two yearly CTCs side by side, with the same basic share, PF rate and professional tax.", fields: [{ name: "ctc_a", label: "Offer A yearly CTC (₹)", def: "500000" }, { name: "variable_pct_a", label: "Offer A variable (%)", def: "10" }, { name: "income_tax_a", label: "Offer A income tax per year (₹)", def: "0" }, { name: "ctc_b", label: "Offer B yearly CTC (₹)", def: "600000" }, { name: "variable_pct_b", label: "Offer B variable (%)", def: "25" }, { name: "income_tax_b", label: "Offer B income tax per year (₹)", def: "0" }],
    show: (r) => { const a = r.offer_a as unknown as Record<string, number>, b = r.offer_b as unknown as Record<string, number>; return [["Offer A in-hand per month", `₹${a.inhand_monthly}`], ["Offer B in-hand per month", `₹${b.inhand_monthly}`], ["B minus A, per month", `₹${r.inhand_difference_monthly}`], ["Offer A variable per year", `₹${a.variable_per_year}`], ["Offer B variable per year", `₹${b.variable_per_year}`]]; } },
};

export default function Calculators() {
  const [k, setK] = useState("emi");
  const c = CALCS[k];
  const [vals, setVals] = useState<Record<string, string>>({});
  const [out, setOut] = useState<Record<string, number | string> | null>(null);
  const { busy, error, run } = useAction();
  async function go(e: React.FormEvent) {
    e.preventDefault();
    const body = Object.fromEntries(c.fields.map((f) => [f.name, Number(vals[`${k}.${f.name}`] ?? f.def)]));
    const r = await run(() => call<Record<string, number | string>>("POST", `/v1/calc/${k}`, body));
    if (r) setOut(r);
  }
  return (
    <div className="max-w-2xl">
      <Tabs label="Calculators" value={k} onChange={(x) => { setK(x); setOut(null); }} tabs={Object.entries(CALCS).map(([key, v]) => ({ key, label: v.label }))} />
      <p className="mb-4 text-slate">{c.intro}</p>
      <form onSubmit={go} className="grid gap-4">{c.fields.map((f) => (
        <Labeled key={f.name} id={`${k}-${f.name}`} label={f.label} help={f.help}><input id={`${k}-${f.name}`} inputMode="decimal" className={inp} value={vals[`${k}.${f.name}`] ?? f.def} onChange={(e) => setVals({ ...vals, [`${k}.${f.name}`]: e.target.value })} /></Labeled>))}
        <ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy}>Calculate</button></div></form>
      {out && <div className="mt-6" aria-live="polite"><dl className="grid gap-2">{c.show(out).map(([a, b]) => <div key={a} className="rounded-md border border-ink/10 bg-white p-3"><dt className="text-sm text-slate">{a}</dt><dd className="text-xl font-semibold">{b}</dd></div>)}</dl>
        <div className="mt-3"><Note>{String(out.assumptions)} This is not financial advice.</Note></div></div>}
    </div>
  );
}
