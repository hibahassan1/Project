import numpy as np
import pandas as pd
import streamlit as st

from soveil import charts, ui
from soveil.agent import ask
from soveil.data import DAYS, DEFAULT_INITIAL_LOSS, SITES, get_forecast
from soveil.model import rain_flags, uncertainty_band
from soveil.scheduler import evaluate, fixed_cycle, optimize

st.set_page_config(page_title="Soveil AI", page_icon="☀️", layout="wide", initial_sidebar_state="expanded")
ui.inject_css()

sites = list(SITES)

# ---------------- sidebar ----------------
with st.sidebar:
    st.markdown("### Scenario")
    with st.expander("Costs and crews", expanded=True):
        price = st.number_input("Energy value (AED/MWh)", 50, 500, 200, 10)
        clean_cost = st.number_input("Cost per cleaning (AED)", 200, 10000, 1500, 100)
        crews = st.slider("Cleaning crews per day", 1, 4, 2)
        interval = st.slider("Fixed calendar: clean every N days", 2, 7, 3)
    with st.expander("Safety gate"):
        storm_pm10 = st.number_input("Dust storm threshold, PM10 (µg/m³)", 150, 800, 300, 25,
                                     help="Cleans planned on days above this need a human to approve.")
    with st.expander("Soiling today (simulated)"):
        initial = {s: st.slider(ui.html.escape(s), 0.0, 15.0, float(DEFAULT_INITIAL_LOSS[s]), 0.1) for s in sites}
    # with st.expander("Chatbot"):
    #     api_key = st.text_input("Groq API key (free, optional)", type="password",
    #                             help="Get one free at console.groq.com. Leave empty to use the built-in explainer.")
    api_key = st.secrets.get("GROQ_API_KEY", "")
# ---------------- pipeline ----------------
@st.cache_data(ttl=3600, show_spinner="Fetching the latest dust forecast…")
def load_forecasts():
    out, srcs = {}, set()
    for s in sites:
        out[s], src = get_forecast(s)
        srcs.add(src)
    return out, " / ".join(sorted(srcs))


forecasts, source = load_forecasts()
MW = SITES[sites[0]]["mw"]

schedule = optimize(sites, forecasts, initial, MW, price, clean_cost, crews)
if schedule is None:
    st.error("No feasible schedule with this many crews. Increase crews in the sidebar.")
    st.stop()
baseline = fixed_cycle(sites, DAYS, interval)
none_sched = {s: np.zeros(DAYS, dtype=bool) for s in sites}
opt = evaluate(sites, forecasts, initial, schedule, MW, price, clean_cost)
base = evaluate(sites, forecasts, initial, baseline, MW, price, clean_cost)
nothing = evaluate(sites, forecasts, initial, none_sched, MW, price, clean_cost)

dates = [str(d) for d in forecasts[sites[0]]["date"]]
dlabels = [pd.Timestamp(d).strftime("%a %d") for d in dates]
rain = {s: rain_flags(forecasts[s]) for s in sites}
ctx = dict(sites=sites, forecast=forecasts, initial=initial, schedule=schedule, opt=opt,
           mw=MW, price=price, clean_cost=clean_cost, source=source)

saved = base["total_cost"] - opt["total_cost"]
avoided = base["n_cleans"] - opt["n_cleans"]

# ---------------- header + hero + KPIs ----------------
ui.topbar(live=source.startswith("live"))
if saved > 0:
    headline = f"{opt['n_cleans']} cleans this week instead of {base['n_cleans']}, saving about AED {saved:,.0f}."
else:
    headline = f"The AI plan costs AED {opt['total_cost']:,.0f} this week against AED {base['total_cost']:,.0f} on a fixed calendar."
ui.hero(headline, f"Dust and rain forecasts decide when each of the {len(sites)} pilot sites gets cleaned. Plant data is simulated, so read the figures as a scenario.")

red = 100 * avoided / max(base["n_cleans"], 1)
ui.kpis([
    ("Cleans planned", str(opt["n_cleans"]), f"{base['n_cleans']} on the fixed calendar", "teal"),
    ("Weekly cost", f"AED {opt['total_cost']:,.0f}", f"AED {base['total_cost']:,.0f} on the fixed calendar", "amber"),
    ("Energy lost to dust", f"{opt['mwh_lost']:.0f} MWh", f"{opt['mwh_lost'] - base['mwh_lost']:+.0f} MWh vs the fixed calendar", "dust"),
    ("Cleaning cycles avoided", f"{red:.0f}%", "Target from the pitch: about 30%", "rain"),
])

tab1, tab2, tab3, tab4 = st.tabs(["Fleet outlook", "Site forecast", "Schedule and approvals", "Ask Soveil"])

# ---------------- tab 1: fleet outlook ----------------
with tab1:
    left, right = st.columns([1.55, 1], gap="medium")
    with left:
        with st.container(border=True):
            ui.section("Soiling outlook by site", "Projected panel soiling loss at the end of each day. Green outlines are cleaning days.")
            view = st.radio("Plan", ["AI plan", "Fixed calendar", "No cleaning"], horizontal=True, label_visibility="collapsed")
            chosen = {"AI plan": (opt, schedule), "Fixed calendar": (base, baseline), "No cleaning": (nothing, none_sched)}[view]
            st.plotly_chart(charts.heatmap(sites, dlabels, chosen[0]["traj"], chosen[1], rain),
                            width="stretch", config={"displayModeBar": False})
    with right:
        with st.container(border=True):
            ui.section("Sites", "Status under the AI plan")
            rows = []
            for s in sites:
                days = np.flatnonzero(schedule[s])
                rows.append(dict(name=s, today=initial[s], end=float(opt["traj"][s][-1]),
                                 chip_text=(f"Clean {dlabels[days[0]]}" if len(days) else "No clean needed"),
                                 chip_kind="ok" if len(days) else "wait"))
            ui.site_rows(rows)
    with st.container(border=True):
        ui.section("Where the sites are", "Marker colour shows soiling today: teal is low, amber is rising, red needs attention.")
        st.plotly_chart(charts.site_map(sites, {s: (SITES[s]["lat"], SITES[s]["lon"]) for s in sites}, initial),
                        width="stretch", config={"displayModeBar": False})
    st.caption("Cost is the value of energy lost plus cleaning cost over 7 days, with 3 extra days of carry-over soiling counted. It is a simulated scenario, not a measured saving.")

# ---------------- tab 2: site forecast ----------------
with tab2:
    site = st.selectbox("Site", sites, format_func=lambda s: s, label_visibility="collapsed")
    df = forecasts[site]
    p10, p50, p90 = uncertainty_band(initial[site], df)
    with st.container(border=True):
        ui.section("Soiling loss forecast", "How much output the panels lose, with and without cleaning. Shaded columns are rain days.")
        st.plotly_chart(charts.soiling_lines(dlabels, p10, p50, p90, opt["traj"][site], base["traj"][site],
                                             schedule[site], rain[site]),
                        width="stretch", config={"displayModeBar": False})
    with st.container(border=True):
        ui.section("What drives it", "Forecast dust (PM10) builds soiling. Rain over 3 mm washes it off.")
        st.plotly_chart(charts.drivers(dlabels, df["pm10_mean"], df["rain_mm"], storm_pm10),
                        width="stretch", config={"displayModeBar": False})

# ---------------- tab 3: schedule + approvals ----------------
with tab3:
    pending = []

    def cell(s, i):
        pm = forecasts[s]["pm10_mean"].iloc[i]
        tip = f"PM10 {pm:.0f} µg/m³, rain {forecasts[s]['rain_mm'].iloc[i]:.1f} mm"
        storm = forecasts[s]["pm10_max"].iloc[i] >= storm_pm10
        if schedule[s][i]:
            if storm:
                pending.append((s, dates[i], dlabels[i]))
                return "warn", "Clean ⚠", tip
            return "clean", "Clean", tip
        return ("rain", "Rain", tip) if rain[s][i] else ("none", "–", tip)

    with st.container(border=True):
        ui.section("Cleaning schedule", "Optimised with OR-Tools CP-SAT for your crews and costs. Hover a cell for the dust and rain forecast.")
        ui.schedule_table(sites, dlabels, cell)

    with st.container(border=True):
        ui.section("Human approval", "Cleans on dust-storm days are never sent to crews without a person signing off.")
        if not pending:
            ui.md('<span class="sv-chip ok">All planned cleans are inside normal limits and run automatically</span>')
        for s, dt, lab in pending:
            key = f"appr_{s}_{dt}"
            c1, c2, c3 = st.columns([3.4, 1, 1], vertical_alignment="center")
            c1.markdown(f"**{s}, {lab}**  \nForecast PM10 peaks above {storm_pm10} µg/m³. Automatic dispatch is on hold.")
            if c2.button("Approve", key=key + "a", width="stretch"):
                st.session_state[key] = "Approved"
            if c3.button("Reject", key=key + "r", width="stretch"):
                st.session_state[key] = "Rejected"
            if key in st.session_state:
                kind = "ok" if st.session_state[key] == "Approved" else "bad"
                ui.md(f'<span class="sv-chip {kind}">{st.session_state[key]} and logged</span>')

# ---------------- tab 4: chat ----------------
with tab4:
    with st.container(border=True):
        ui.section("Ask Soveil", "Answers come from the forecast and the optimiser, not from memory.")
        suggestions = ["Why clean Solar Plant 4?", "When is the schedule?", "Dust outlook for Solar Plant 1", "Fleet status"]
        cols = st.columns(len(suggestions))
        for c, text in zip(cols, suggestions):
            if c.button(text, key="sug_" + text, width="stretch"):
                st.session_state["pending_q"] = text
        if "chat" not in st.session_state:
            st.session_state.chat = []
        for role, text in st.session_state.chat:
            st.chat_message(role, avatar="☀️" if role == "assistant" else None).write(text)
        q = st.chat_input("Ask about a site, the schedule or the forecast") or st.session_state.pop("pending_q", None)
        if q:
            st.session_state.chat.append(("user", q))
            st.chat_message("user").write(q)
            ans, engine = ask(q, ctx, api_key)
            st.session_state.chat.append(("assistant", ans))
            st.chat_message("assistant", avatar="☀️").write(ans)
            st.caption(f"Answered by: {engine}")
