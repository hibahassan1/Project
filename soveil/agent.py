"""Layer 4: chatbot / agent.
100% free by default: a rule-based explainer that reads the real numbers from the optimizer.
Optional: add a FREE Groq API key (console.groq.com, no credit card) to get a tool-calling LLM
that answers in natural language using the same tools."""
import json
import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


# ---------- tools (shared by the LLM and the rule-based fallback) ----------
def t_fleet_status(ctx):
    rows = []
    for s in ctx["sites"]:
        tr = ctx["opt"]["traj"][s]
        rows.append({"site": s, "loss_today_pct": ctx["initial"][s], "loss_end_of_week_pct": round(float(tr[-1]), 2),
                     "cleans_planned": int(ctx["schedule"][s].sum()), "forecast_source": ctx["source"]})
    return rows


def t_site_forecast(ctx, site):
    df = ctx["forecast"][site]
    return [{"date": str(r.date), "pm10_mean": round(r.pm10_mean), "pm10_max": round(r.pm10_max),
             "rain_mm": round(r.rain_mm, 1)} for r in df.itertuples()]


def t_schedule(ctx):
    dates = [str(d) for d in ctx["forecast"][ctx["sites"][0]]["date"]]
    return {s: [dates[i] for i, v in enumerate(ctx["schedule"][s]) if v] for s in ctx["sites"]}


def t_explain_clean(ctx, site):
    sch, df = ctx["schedule"][site], ctx["forecast"][site]
    days = [i for i, v in enumerate(sch) if v]
    if not days:
        return {"site": site, "answer": "No clean planned this week: forecast losses stay below the break-even point "
                f"(loss today {ctx['initial'][site]}%, end of week {ctx['opt']['traj'][site][-1]:.1f}% with rain/dust as forecast)."}
    d = days[0]
    tr = ctx["opt"]["traj"][site]
    before = ctx["initial"][site] if d == 0 else float(tr[d - 1])
    daily_cost = before / 100 * ctx["mw"] * 6 * ctx["price"]
    return {"site": site, "first_clean_date": str(df["date"].iloc[d]), "soiling_before_clean_pct": round(before, 2),
            "pm10_that_day": round(float(df["pm10_mean"].iloc[d])), "daily_energy_loss_aed_at_that_level": round(daily_cost),
            "clean_cost_aed": ctx["clean_cost"], "rain_days": [str(x) for x in df["date"][df["rain_mm"] >= 3]]}


def run_tool(ctx, name, args):
    return {"get_fleet_status": lambda: t_fleet_status(ctx),
            "get_site_forecast": lambda: t_site_forecast(ctx, args["site"]),
            "get_schedule": lambda: t_schedule(ctx),
            "explain_clean": lambda: t_explain_clean(ctx, args["site"])}[name]()


TOOLS = [
    {"type": "function", "function": {"name": "get_fleet_status", "description": "Soiling loss now and end of week for every site", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_schedule", "description": "The optimized cleaning dates per site", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_site_forecast", "description": "Daily PM10 and rain forecast for a site", "parameters": {"type": "object", "properties": {"site": {"type": "string"}}, "required": ["site"]}}},
    {"type": "function", "function": {"name": "explain_clean", "description": "Why/when a site is cleaned, with numbers", "parameters": {"type": "object", "properties": {"site": {"type": "string"}}, "required": ["site"]}}},
]
SYSTEM = ("You are Soveil AI, an assistant for solar O&M teams in the UAE. Answer ONLY from tool results; never invent numbers. "
          "Be concise (max 5 sentences). Site names: {sites}")


# ---------- LLM path (free Groq tier) ----------
def _llm(question, ctx, api_key):
    msgs = [{"role": "system", "content": SYSTEM.format(sites=ctx["sites"])}, {"role": "user", "content": question}]
    for _ in range(4):
        r = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {api_key}"}, timeout=30,
                          json={"model": GROQ_MODEL, "messages": msgs, "tools": TOOLS, "temperature": 0.2})
        r.raise_for_status()
        msg = r.json()["choices"][0]["message"]
        if not msg.get("tool_calls"):
            return msg["content"]
        msgs.append(msg)
        for tc in msg["tool_calls"]:
            out = run_tool(ctx, tc["function"]["name"], json.loads(tc["function"]["arguments"] or "{}"))
            msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(out)})
    return "I couldn't finish that; try rephrasing."


# ---------- zero-cost path ----------
def _rule_based(question, ctx):
    q = question.lower()
    def _keys(name):
        # "Solar Plant 3" -> match on "plant 3", "3", or the full lowercase name
        num = name.split()[-1]
        return {name.lower(), f"plant {num}", num}
    site = next((s for s in ctx["sites"] if any(k in q for k in _keys(s))), None)
    if any(w in q for w in ["why", "explain", "reason"]) and site:
        e = t_explain_clean(ctx, site)
        if "answer" in e:
            return e["answer"]
        payback = max(1, -(-e["clean_cost_aed"] // max(e["daily_energy_loss_aed_at_that_level"], 1)))
        return (f"{site} is first cleaned on {e['first_clean_date']}: soiling reaches {e['soiling_before_clean_pct']}% by then "
                f"(forecast PM10 {e['pm10_that_day']} µg/m³), costing about AED {e['daily_energy_loss_aed_at_that_level']:,} per day in lost energy. "
                f"A AED {e['clean_cost_aed']:,} clean pays back in ~{payback} day(s). Rain days: {e['rain_days'] or 'none'}.")
    if "rain" in q or "forecast" in q or "dust" in q:
        s = site or ctx["sites"][0]
        f = t_site_forecast(ctx, s)
        worst = max(f, key=lambda r: r["pm10_mean"])
        return f"{s}: worst dust day is {worst['date']} (PM10 ≈ {worst['pm10_mean']} µg/m³). Source: {ctx['source']}."
    if "schedule" in q or "when" in q or "clean" in q:
        return "Planned cleans: " + "; ".join(f"{s}: {', '.join(d) or 'none'}" for s, d in t_schedule(ctx).items())
    st = t_fleet_status(ctx)
    worst = max(st, key=lambda r: r["loss_end_of_week_pct"])
    return (f"Fleet status: worst end-of-week soiling is {worst['site']} at {worst['loss_end_of_week_pct']}% "
            f"(planned cleans: {sum(r['cleans_planned'] for r in st)}). Ask 'why clean <site>?' or 'when is the schedule?'.")


def ask(question, ctx, api_key=""):
    if api_key:
        try:
            return _llm(question, ctx, api_key), "Groq (free tier)"
        except Exception as e:
            return _rule_based(question, ctx), f"offline explainer (LLM error: {type(e).__name__})"
    return _rule_based(question, ctx), "offline explainer (no API key)"
