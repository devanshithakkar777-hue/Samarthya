"""Money calculators. Pure arithmetic with the assumptions stated back. Not financial advice."""
from math import isfinite

LIMITS = {"amount": (0, 1e10), "rate": (0, 100), "years": (0, 60), "months": (1, 720)}


def _chk(name: str, v: float, kind: str):
    lo, hi = LIMITS[kind]
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not isfinite(v) or not lo <= v <= hi:
        raise ValueError(f"{name} must be between {lo:g} and {hi:g}")
    return float(v)


def emi(principal: float, annual_rate_pct: float, months: int) -> dict:
    p, r, n = _chk("principal", principal, "amount"), _chk("annual rate", annual_rate_pct, "rate"), int(_chk("months", months, "months"))
    if p <= 0:
        raise ValueError("principal must be more than 0")
    i = r / 12 / 100
    pay = p / n if i == 0 else p * i * (1 + i) ** n / ((1 + i) ** n - 1)
    total = pay * n
    return {"monthly_payment": round(pay, 2), "total_paid": round(total, 2), "total_interest": round(total - p, 2),
            "assumptions": "Fixed rate, equal monthly instalments, interest on the reducing balance. Fees and taxes excluded."}


def compound(principal: float, annual_rate_pct: float, years: float, monthly_addition: float = 0.0) -> dict:
    p, r, y = _chk("principal", principal, "amount"), _chk("annual rate", annual_rate_pct, "rate"), _chk("years", years, "years")
    a = _chk("monthly addition", monthly_addition, "amount")
    i, months = r / 12 / 100, int(round(y * 12))
    bal = p
    for _ in range(months):
        bal = bal * (1 + i) + a
    invested = p + a * months
    return {"final_value": round(bal, 2), "total_invested": round(invested, 2), "growth": round(bal - invested, 2),
            "assumptions": "A constant return compounded monthly. Real returns vary and can be negative. This is arithmetic, not a forecast."}


def real_value(amount: float, inflation_pct: float, years: float) -> dict:
    a, r, y = _chk("amount", amount, "amount"), _chk("inflation", inflation_pct, "rate"), _chk("years", years, "years")
    f = (1 + r / 100) ** y
    return {"future_cost_of_same_things": round(a * f, 2), "todays_value_of_amount_later": round(a / f, 2),
            "assumptions": "A constant yearly inflation rate."}


def budget(monthly_income: float, needs_pct: float = 50, wants_pct: float = 30) -> dict:
    inc = _chk("income", monthly_income, "amount")
    n, w = _chk("needs", needs_pct, "rate"), _chk("wants", wants_pct, "rate")
    if n + w > 100:
        raise ValueError("needs and wants cannot add up to more than 100%")
    return {"needs": round(inc * n / 100, 2), "wants": round(inc * w / 100, 2), "savings_and_debt": round(inc * (100 - n - w) / 100, 2),
            "assumptions": "A simple split to start a conversation with yourself. Adjust it to your life; there is no single right split."}


def savings_goal(target: float, current: float, monthly: float) -> dict:
    t, c, mth = _chk("target", target, "amount"), _chk("saved so far", current, "amount"), _chk("monthly saving", monthly, "amount")
    if mth <= 0:
        raise ValueError("monthly saving must be more than 0")
    need = max(0.0, t - c)
    months = int(-(-need // mth))
    return {"months_needed": months, "years_and_months": [months // 12, months % 12],
            "assumptions": "No interest counted. Add it with the growth calculator."}


def ctc(annual_ctc: float, variable_pct: float = 10, basic_pct: float = 40, pf_pct: float = 12,
        professional_tax_monthly: float = 200, income_tax_annual: float = 0) -> dict:
    """Break a CTC into monthly pieces. Income tax is entered by the user, never estimated here."""
    c, v = _chk("annual CTC", annual_ctc, "amount"), _chk("variable share", variable_pct, "rate")
    b, p = _chk("basic share", basic_pct, "rate"), _chk("PF rate", pf_pct, "rate")
    pt, tax = _chk("professional tax", professional_tax_monthly, "amount"), _chk("income tax", income_tax_annual, "amount")
    if c <= 0:
        raise ValueError("CTC must be more than 0")
    variable = c * v / 100
    fixed = c - variable
    basic = fixed * b / 100
    employer_pf = basic * p / 100  # sits inside fixed CTC, so it is not paid out monthly
    employee_pf = basic * p / 100
    gross_year = fixed - employer_pf
    inhand_year = gross_year - employee_pf - pt * 12 - tax
    return {"fixed_per_year": round(fixed, 2), "variable_per_year": round(variable, 2), "basic_per_year": round(basic, 2),
            "employer_pf_per_year": round(employer_pf, 2), "gross_monthly": round(gross_year / 12, 2),
            "employee_pf_monthly": round(employee_pf / 12, 2), "inhand_monthly": round(inhand_year / 12, 2),
            "inhand_per_year_fixed_only": round(inhand_year, 2),
            "assumptions": "Variable pay is shown separately and is not guaranteed. Employer PF is treated as part of fixed CTC. "
                           "Gratuity, insurance and other benefits are not deducted, so ask the employer for the exact salary structure. "
                           "Income tax is the figure you type in; the tax rules change, so check the official Income Tax Department calculator."}


def offer_compare(ctc_a: float, ctc_b: float, variable_pct_a: float = 10, variable_pct_b: float = 10,
                  basic_pct: float = 40, pf_pct: float = 12, professional_tax_monthly: float = 200,
                  income_tax_a: float = 0, income_tax_b: float = 0) -> dict:
    a = ctc(ctc_a, variable_pct_a, basic_pct, pf_pct, professional_tax_monthly, income_tax_a)
    b = ctc(ctc_b, variable_pct_b, basic_pct, pf_pct, professional_tax_monthly, income_tax_b)
    return {"offer_a": a, "offer_b": b, "inhand_difference_monthly": round(b["inhand_monthly"] - a["inhand_monthly"], 2),
            "assumptions": "Same basic share, PF rate and professional tax are used for both. A bigger CTC is not always bigger monthly pay: "
                           "look at how much is variable, what is a bond or notice period, and where the job is."}
