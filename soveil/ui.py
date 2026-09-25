"""Visual layer: CSS, HTML components. Palette is drawn from the subject: deep sky-navy ink,
clean-panel teal, dust brown, solar amber, rain blue."""
import html
import streamlit as st

C = dict(ink="#0E2233", haze="#F2F5F7", panel="#FFFFFF", line="#DDE4EA", amber="#F5A623",
         dust="#B26A2B", teal="#0F8B84", rain="#3D7DBA", alert="#C8452D", muted="#5B6B79")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Figtree:wght@400;500;600;700&display=swap');
:root{--ink:#0E2233;--haze:#F2F5F7;--line:#DDE4EA;--amber:#F5A623;--dust:#B26A2B;--teal:#0F8B84;--rain:#3D7DBA;--alert:#C8452D;--muted:#5B6B79;}
.stApp,.stMarkdown,[data-testid="stSidebar"],button,input,textarea{font-family:'Figtree',system-ui,-apple-system,'Segoe UI',sans-serif;}
.stApp{background:var(--haze);color:var(--ink);}
h1,h2,h3,.sv-display{font-family:'Bricolage Grotesque','Figtree',system-ui,sans-serif;letter-spacing:-0.01em;}
.block-container{padding-top:1.3rem;padding-bottom:3rem;max-width:1240px;}
header[data-testid="stHeader"]{background:transparent;}
[data-testid="stDecoration"],[data-testid="stAppDeployButton"],#MainMenu,footer{display:none!important;}

/* sidebar */
[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line);}
[data-testid="stSidebar"] [data-testid="stExpander"]{border:1px solid var(--line);border-radius:12px;background:#fff;}
[data-testid="stSidebar"] [data-testid="stExpander"] summary{font-weight:600;}

/* top bar */
.sv-top{display:flex;align-items:center;justify-content:space-between;margin:0 0 1rem 0;}
.sv-brand{display:flex;align-items:center;gap:.65rem;font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:1.3rem;color:var(--ink);}
.sv-brand small{font-family:'Figtree',sans-serif;font-weight:500;color:var(--muted);font-size:.9rem;}
.sv-pill{display:inline-flex;align-items:center;gap:.5rem;padding:.35rem .8rem;border-radius:999px;font-size:.82rem;font-weight:600;border:1px solid var(--line);background:#fff;color:var(--ink);}
.sv-dot{width:9px;height:9px;border-radius:50%;display:inline-block;}

/* hero */
.sv-hero{position:relative;overflow:hidden;background:var(--ink);color:#fff;border-radius:20px;padding:2rem 2.2rem;margin-bottom:1.1rem;}
.sv-hero h1{color:#fff!important;font-size:2.15rem!important;line-height:1.15!important;margin:0 0 .6rem 0!important;padding:0!important;max-width:760px;font-weight:700!important;}
.sv-hero p{color:#B9C7D3!important;font-size:1.02rem!important;margin:0!important;max-width:640px;}
.sv-hero svg{position:absolute;right:-70px;top:-70px;opacity:.9;pointer-events:none;}

/* kpis */
.sv-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;margin-bottom:1.2rem;}
.sv-kpi{background:#fff;border:1px solid var(--line);border-radius:14px;padding:1rem 1.15rem;border-top:4px solid var(--teal);}
.sv-kpi.dust{border-top-color:var(--dust);} .sv-kpi.amber{border-top-color:var(--amber);} .sv-kpi.rain{border-top-color:var(--rain);}
.sv-kpi .l{color:var(--muted);font-size:.86rem;font-weight:500;}
.sv-kpi .v{font-family:'Bricolage Grotesque',sans-serif;font-size:1.85rem;font-weight:700;line-height:1.2;margin:.2rem 0 .1rem 0;color:var(--ink);}
.sv-kpi .s{font-size:.82rem;color:var(--muted);}
@media (max-width:900px){.sv-kpis{grid-template-columns:repeat(2,1fr);}.sv-hero h1{font-size:1.6rem!important;}}

/* section titles */
.sv-h{font-family:'Bricolage Grotesque',sans-serif;font-size:1.2rem;font-weight:700;margin:.1rem 0 .1rem 0;color:var(--ink);}
.sv-sub{color:var(--muted);font-size:.9rem;margin:0 0 .5rem 0;}

/* tabs */
.stTabs [data-baseweb="tab-list"]{gap:1.8rem;border-bottom:1px solid var(--line);}
.stTabs button[data-baseweb="tab"]{padding:.6rem 0;font-weight:600;color:var(--muted);}
.stTabs button[data-baseweb="tab"][aria-selected="true"]{color:var(--ink);}
.stTabs [data-baseweb="tab-highlight"]{background:var(--teal);height:3px;}

/* cards (st.container(border=True)) */
[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border-radius:14px;border-color:var(--line);}

/* site list */
.sv-site{padding:.75rem 0;border-bottom:1px solid #EDF1F4;}
.sv-site:last-child{border-bottom:none;}
.sv-site .row{display:flex;justify-content:space-between;align-items:center;gap:.6rem;}
.sv-site .n{font-weight:600;color:var(--ink);}
.sv-site .m{font-size:.82rem;color:var(--muted);margin:.1rem 0 .4rem 0;}
.sv-bar{height:7px;background:#EDF1F4;border-radius:6px;overflow:hidden;}
.sv-bar i{display:block;height:100%;border-radius:6px;}
.sv-chip{display:inline-block;padding:.18rem .65rem;border-radius:999px;font-size:.78rem;font-weight:600;white-space:nowrap;}
.sv-chip.ok{background:#DDF1EF;color:#0B6661;} .sv-chip.wait{background:#EDF1F4;color:var(--muted);}
.sv-chip.warn{background:#FFF1D6;color:#7A4A00;} .sv-chip.bad{background:#FBE3DD;color:#8E2C18;}

/* schedule table */
.sv-sched-wrap{overflow-x:auto;}
.sv-sched{width:100%;border-collapse:separate;border-spacing:6px;min-width:720px;}
.sv-sched th{font-weight:600;font-size:.82rem;color:var(--muted);text-align:center;padding:0 0 .2rem 0;}
.sv-sched th.s,.sv-sched td.s{text-align:left;width:21%;font-weight:600;color:var(--ink);font-size:.92rem;padding-right:.5rem;}
.sv-sched td.c{height:46px;border-radius:10px;text-align:center;font-size:.82rem;font-weight:600;}
.sv-sched td.clean{background:var(--teal);color:#fff;}
.sv-sched td.warn{background:#FFF1D6;color:#7A4A00;box-shadow:inset 0 0 0 2px var(--amber);}
.sv-sched td.rain{background:#E3EEF8;color:#2C6293;}
.sv-sched td.none{background:#F2F5F7;color:#9AA7B2;font-weight:500;}
.sv-legend{display:flex;gap:1.1rem;flex-wrap:wrap;font-size:.82rem;color:var(--muted);margin-top:.6rem;}
.sv-legend b{display:inline-block;width:12px;height:12px;border-radius:4px;margin-right:.35rem;vertical-align:-1px;}

/* buttons */
.stButton>button{border-radius:10px;border:1px solid var(--line);font-weight:600;background:#fff;color:var(--ink);}
.stButton>button:hover{border-color:var(--teal);color:var(--teal);}
[data-testid="stChatMessage"]{background:#fff;border:1px solid var(--line);border-radius:14px;}
"""


def _h(s: str) -> str:
    # Markdown treats indented lines / blank lines as code or block breaks, so flatten the HTML.
    return "\n".join(line.strip() for line in s.splitlines() if line.strip())


def md(s: str):
    st.markdown(_h(s), unsafe_allow_html=True)


def inject_css():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def topbar(live: bool):
    dot, label = (C["teal"], "Live forecast") if live else (C["amber"], "Simulated forecast")
    md(f"""
    <div class="sv-top">
      <div class="sv-brand">
        <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">
          <circle cx="17" cy="17" r="6.5" fill="{C['amber']}"/>
          <g stroke="{C['ink']}" stroke-width="2" stroke-linecap="round">
            <path d="M17 3v4M17 27v4M3 17h4M27 17h4M7.1 7.1l2.8 2.8M24.1 24.1l2.8 2.8M7.1 26.9l2.8-2.8M24.1 9.9l2.8-2.8"/>
          </g>
        </svg>
        <span>Soveil AI <small>Predictive soiling management</small></span>
      </div>
      <span class="sv-pill"><span class="sv-dot" style="background:{dot}"></span>{label}</span>
    </div>""")


def hero(headline: str, sub: str):
    md(f"""
    <div class="sv-hero">
      <svg width="360" height="360" viewBox="0 0 360 360" aria-hidden="true">
        <circle cx="180" cy="180" r="70" fill="none" stroke="{C['amber']}" stroke-width="2" opacity=".55"/>
        <circle cx="180" cy="180" r="115" fill="none" stroke="{C['amber']}" stroke-width="1.5" opacity=".32"/>
        <circle cx="180" cy="180" r="160" fill="none" stroke="{C['amber']}" stroke-width="1" opacity=".18"/>
        <circle cx="180" cy="180" r="30" fill="{C['amber']}" opacity=".9"/>
      </svg>
      <h1>{html.escape(headline)}</h1>
      <p>{html.escape(sub)}</p>
    </div>""")


def kpis(items):
    """items: list of (label, value, sub, tone)"""
    cells = "".join(
        f'<div class="sv-kpi {t}"><div class="l">{html.escape(l)}</div><div class="v">{html.escape(v)}</div>'
        f'<div class="s">{html.escape(s)}</div></div>' for l, v, s, t in items)
    md(f'<div class="sv-kpis">{cells}</div>')


def section(title: str, sub: str = ""):
    md(f'<div class="sv-h">{html.escape(title)}</div>' + (f'<div class="sv-sub">{html.escape(sub)}</div>' if sub else ""))


def site_rows(rows):
    """rows: dict(name, today, end, chip_text, chip_kind)"""
    out = []
    for r in rows:
        width = min(100, r["end"] / 12 * 100)
        col = C["teal"] if r["end"] < 4 else (C["amber"] if r["end"] < 8 else C["alert"])
        out.append(f"""
        <div class="sv-site">
          <div class="row"><span class="n">{html.escape(r['name'])}</span><span class="sv-chip {r['chip_kind']}">{html.escape(r['chip_text'])}</span></div>
          <div class="m">Soiling {r['today']:.1f}% today, {r['end']:.1f}% by end of week</div>
          <div class="sv-bar"><i style="width:{width:.0f}%;background:{col}"></i></div>
        </div>""")
    md("".join(out))


def schedule_table(sites, dlabels, cell_fn):
    """cell_fn(site, i) -> (css_class, text, tooltip)"""
    head = "".join(f"<th>{html.escape(d)}</th>" for d in dlabels)
    body = []
    for s in sites:
        tds = ""
        for i in range(len(dlabels)):
            cls, txt, tip = cell_fn(s, i)
            tds += f'<td class="c {cls}" title="{html.escape(tip)}">{txt}</td>'
        body.append(f'<tr><td class="s">{html.escape(s)}</td>{tds}</tr>')
    md(f"""
    <div class="sv-sched-wrap"><table class="sv-sched"><thead><tr><th class="s"></th>{head}</tr></thead>
    <tbody>{''.join(body)}</tbody></table></div>
    <div class="sv-legend">
      <span><b style="background:{C['teal']}"></b>Clean planned</span>
      <span><b style="background:#FFF1D6;box-shadow:inset 0 0 0 2px {C['amber']}"></b>Clean planned, needs approval (dust storm)</span>
      <span><b style="background:#E3EEF8"></b>Rain cleans the panels</span>
      <span><b style="background:#F2F5F7"></b>No action</span>
    </div>""")
