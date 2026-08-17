"""ARAKONAK GES — Kontrol Panosu (v4 · Açık Kurumsal / Power BI tarzı).

Sol menü rayı · KPI kartları · kombine grafik · halka gösterge · koşullu
biçimlendirmeli disiplin matrisi. İş kalemleri günlük girilir; her gün otomatik
'günlük anlık görüntü' kaydedilir ve S-eğrisi bu günlük noktalardan oluşur.
"""
from __future__ import annotations

import base64
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

import auth
import core
import charts
import exports
import storage

st.set_page_config(page_title="ARAKONAK GES — Kontrol Panosu", page_icon="⚡",
                   layout="wide", initial_sidebar_state="expanded")

_HERE = Path(__file__).parent


def _asset(*names):
    for n in names:
        for c in (_HERE / "assets" / "fonts" / n, _HERE / "assets" / n, _HERE / n):
            if c.exists():
                return c
    return _HERE / names[0]


@st.cache_data(show_spinner=False)
def _logo(color):
    try:
        svg = _asset("logo.svg").read_text(encoding="utf-8")
        if color == "black":
            svg = svg.replace("fill:#fff", "fill:#0a0a0a").replace('fill="#fff"', 'fill="#0a0a0a"')
        return base64.b64encode(svg.encode()).decode()
    except Exception:
        return None


LOGO_WHITE = _logo("white")
LOGO_BLACK = _logo("black")

TEAL = "#2dd4bf"; TEAL_D = "#14b8a6"; INDIGO = "#0e7490"
GREEN = "#34d399"; AMBER = "#fbbf24"; RED = "#fb7185"; SLATE = "#e6f4f4"; MUTED = "#7fb0b3"


# ────────────────────── STİL (Açık Kurumsal) ──────────────────────
# ────────────────────── TEMA PALETLERİ ──────────────────────
THEMES = {
    "dark": dict(
        bg="radial-gradient(760px 520px at 50% -18%, rgba(34,211,238,.16), transparent 60%),"
           "radial-gradient(700px 500px at 100% 8%, rgba(139,92,246,.10), transparent 55%),"
           "linear-gradient(160deg,#04060d,#05080f 60%,#04060d)",
        text="#dbeafe", muted="#5f7a99", panel="#0a1422", border="#12324a",
        rail="#070d18", railb="#12324a", railtxt="#5f9bbf", railhov="#0d1a2c",
        acc="#22d3ee", acc2="#0891b2", accd="#0891b2", ttl="#67e8f9",
        rowb="#0e2233", rowh="#0c1a2a", metricbg="#0a1422"),
    "light": dict(
        bg="radial-gradient(1000px 560px at 8% -8%, rgba(13,148,136,.10), transparent 60%),"
           "radial-gradient(900px 560px at 100% -4%, rgba(99,102,241,.08), transparent 55%),"
           "linear-gradient(160deg,#eef2f7 0%,#f5f8fc 60%,#eef2f7 100%)",
        text="#0f2b3a", muted="#6b8a90", panel="#ffffff", border="#e7edf3",
        rail="#ffffff", railb="#e5ecf2", railtxt="#5b7a82", railhov="#f1f6f6",
        acc="#0d9488", acc2="#6366f1", accd="#0a7268", ttl="#0f3b44",
        rowb="#eef2f6", rowh="#f7fafb", metricbg="#ffffff"),
}


def inject_css(theme="dark"):
    t = THEMES.get(theme, THEMES["dark"])
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    .stApp{{font-family:'Inter','Segoe UI',sans-serif;}}
    [data-testid="stTextInputRevealButton"]{{display:none !important;}}
    #MainMenu, footer{{visibility:hidden;}}
    header[data-testid="stHeader"]{{display:none;}}
    [data-testid="stToolbar"]{{display:none;}}
    .stApp{{background:{t['bg']};}}
    .block-container{{padding-top:1.1rem;padding-bottom:2rem;max-width:1560px;}}
    .stApp, .stApp p, .stApp label, .stApp span, .stApp li{{color:{t['text']};}}

    /* ── SOL RAY ── */
    section[data-testid="stSidebar"]{{background:{t['rail']};border-right:1px solid {t['railb']};width:238px !important;}}
    .rail-logo{{text-align:center;padding:6px 8px 14px;border-bottom:1px solid {t['railb']};margin-bottom:10px;}}
    .rail-logo img{{height:46px;}}
    section[data-testid="stSidebar"] [role="radiogroup"]{{gap:3px;}}
    section[data-testid="stSidebar"] [role="radiogroup"] label{{
      padding:10px 13px;border-radius:11px;margin:1px 6px;cursor:pointer;font-weight:700;font-size:13.5px;
      color:{t['railtxt']};transition:background .12s;}}
    section[data-testid="stSidebar"] [role="radiogroup"] label:hover{{background:{t['railhov']};}}
    section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){{
      background:linear-gradient(120deg,{t['accd']},{t['acc']});color:#04222b;box-shadow:0 8px 18px rgba(34,211,238,.25);}}
    section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) *{{color:#04222b !important;}}
    section[data-testid="stSidebar"] .stButton button{{
      background:{t['railhov']};border:1px solid {t['railb']};color:{t['text']};font-weight:700;border-radius:10px;}}
    .rail-user{{background:{t['railhov']};border:1px solid {t['railb']};border-radius:12px;padding:10px 12px;
      font-size:11.5px;color:{t['muted']};margin:6px 0;}}
    .rail-sec{{font-size:10px;font-weight:800;color:{t['muted']};letter-spacing:.6px;margin:10px 12px 2px;}}

    /* ── ÜST BAŞLIK ── */
    .pagehd h1{{font-size:23px;font-weight:900;color:{t['text']};margin:0;background:none;}}
    .pagehd .sub{{font-size:12px;color:{t['muted']};font-weight:600;margin-top:3px;}}

    /* Kapsam dilimleyici */
    /* Kapsam dilimleyici — okunur, neon */
    [data-testid="stSegmentedControl"]{{background:transparent !important;}}
    [data-testid="stSegmentedControl"] button{{font-weight:800 !important;border-radius:10px !important;
      background:{t['railhov']} !important;border:1px solid {t['border']} !important;color:{t['text']} !important;
      padding:7px 16px !important;}}
    [data-testid="stSegmentedControl"] button *{{color:{t['text']} !important;}}
    [data-testid="stSegmentedControl"] button:hover{{border-color:{t['acc']} !important;}}
    [data-testid="stSegmentedControl"] button[aria-checked="true"],
    [data-testid="stSegmentedControl"] button[aria-selected="true"],
    [data-testid="stSegmentedControl"] button[kind="segmented_controlActive"]{{
      background:linear-gradient(120deg,{t['accd']},{t['acc']}) !important;border:none !important;
      box-shadow:0 6px 16px rgba(34,211,238,.4) !important;}}
    [data-testid="stSegmentedControl"] button[aria-checked="true"] *,
    [data-testid="stSegmentedControl"] button[aria-selected="true"] *,
    [data-testid="stSegmentedControl"] button[kind="segmented_controlActive"] *{{color:#04222b !important;}}

    /* KPI kartları */
    .kpi-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:16px;}}
    .kpi-card{{position:relative;overflow:hidden;background:{t['panel']};border:1px solid {t['border']};border-radius:16px;
      padding:15px 17px;box-shadow:0 4px 16px rgba(0,0,0,.12);transition:transform .15s,box-shadow .15s;}}
    .kpi-card::before{{content:"";position:absolute;left:0;top:0;height:3px;width:100%;background:var(--c);}}
    .kpi-card:hover{{transform:translateY(-3px);box-shadow:0 14px 28px rgba(0,0,0,.22);border-color:{t['acc']};}}
    .kpi-label{{font-size:10px;font-weight:800;color:{t['muted']};letter-spacing:.5px;}}
    .kpi-value{{font-size:25px;font-weight:900;color:{t['text']};margin-top:4px;letter-spacing:-.5px;}}
    .kpi-sub{{font-size:11px;font-weight:700;margin-top:3px;}}

    .panel-ttl{{font-size:13px;font-weight:800;color:{t['ttl']};margin:0 0 10px;display:flex;align-items:center;gap:8px;}}
    .panel-ttl::before{{content:"";width:5px;height:14px;background:linear-gradient({t['acc']},{t['acc2']});border-radius:3px;}}
    [data-testid="stVerticalBlockBorderWrapper"]{{background:{t['panel']};border-radius:16px;
      box-shadow:0 4px 16px rgba(0,0,0,.12);border:1px solid {t['border']} !important;}}

    /* Tablolar */
    table.mx{{width:100%;border-collapse:collapse;font-size:12px;}}
    table.mx th{{color:{t['muted']};font-weight:800;font-size:10px;letter-spacing:.4px;text-align:left;
      padding:8px 10px;border-bottom:2px solid {t['border']};}}
    table.mx td{{padding:9px 10px;border-bottom:1px solid {t['rowb']};color:{t['text']};}}
    table.mx tr:hover td{{background:{t['rowh']};}}
    .mx-name{{font-weight:700;color:{t['text']};}}
    .mx-bar{{border-radius:5px;height:17px;line-height:17px;padding-left:7px;font-weight:800;color:#04222b;font-size:9.5px;}}
    .mx-pill{{padding:3px 9px;border-radius:999px;font-weight:800;font-size:9.5px;}}
    .rbar{{display:inline-block;height:7px;background:rgba(251,113,133,.2);border-radius:4px;vertical-align:middle;overflow:hidden;}}
    .rbf{{height:100%;background:#fb7185;border-radius:4px;}}

    div[data-testid="stMetric"]{{background:{t['metricbg']};border:1px solid {t['border']};border-radius:14px;
      padding:12px 15px;box-shadow:0 4px 16px rgba(0,0,0,.12);}}
    div[data-testid="stMetric"] *{{color:{t['text']} !important;}}
    div[data-testid="stMetricLabel"] *{{color:{t['muted']} !important;}}

    /* ── NEON KOKPİT (Tasarım 3) ── */
    .neon-title{{font-size:24px;font-weight:900;letter-spacing:2px;color:{t['acc']};
      text-shadow:0 0 18px rgba(34,211,238,.55);margin:0;}}
    .kbox{{border:1px solid {t['border']};border-radius:14px;padding:15px 17px;margin-bottom:12px;
      background:linear-gradient(180deg,rgba(34,211,238,.05),transparent);box-shadow:inset 0 0 22px rgba(34,211,238,.05);}}
    .kbox .kl{{font-size:9.5px;font-weight:800;color:{t['muted']};letter-spacing:1px;}}
    .kbox .kv{{font-size:26px;font-weight:900;margin-top:3px;text-shadow:0 0 14px rgba(34,211,238,.35);}}
    .nchip{{display:inline-block;border:1px solid {t['border']};border-radius:10px;padding:6px 12px;
      margin:2px 5px 0 0;font-size:11.5px;font-weight:800;color:#9fc3e0;}}
    @media (max-width:1250px){{.kpi-grid{{grid-template-columns:repeat(2,1fr);}}}}
    </style>""", unsafe_allow_html=True)


theme = st.session_state.setdefault("theme", "dark")
inject_css(theme)
charts.set_theme(theme)
if not auth.login_gate():
    st.stop()

user = auth.current_user()
ADMIN = auth.is_admin()


@st.cache_resource(show_spinner=False)
def _conn():
    c = storage.get_conn()
    storage.init_db(c)
    return c


conn = _conn()
if "df" not in st.session_state:
    st.session_state.df = storage.load_progress(conn)
if "stock" not in st.session_state:
    st.session_state.stock = storage.load_stock(conn)
if "hse" not in st.session_state:
    st.session_state.hse = storage.load_hse(conn)


def persist_progress():
    storage.save_progress(conn, st.session_state.df)
    # her kayıtta bugünün günlük anlık görüntüsünü güncelle (tüm kapsamlar)
    storage.record_daily(conn, core.per_scope_kpis(core.enrich(st.session_state.df)))


def set_progress(ids, plan=None, real=None, ac=None):
    df = st.session_state.df
    m = df["id"].isin(ids)
    if plan is not None: df.loc[m, "plan"] = max(0.0, min(100.0, float(plan)))
    if real is not None: df.loc[m, "real"] = max(0.0, min(100.0, float(real)))
    if ac is not None:   df.loc[m, "ac"] = max(0.0, float(ac))
    persist_progress()


def add_item(grp, disc, name, unit, qty, up, plan=0.0, real=0.0, ac=0.0):
    df = st.session_state.df
    n = 1
    while f"user_{n}" in set(df["id"]):
        n += 1
    row = {"id": f"user_{n}", "grp": grp, "disc": disc.strip().upper(), "name": name.strip(),
           "unit": unit.strip() or "adet", "qty": float(qty), "up": float(up),
           "plan": max(0.0, min(100.0, float(plan))), "real": max(0.0, min(100.0, float(real))),
           "ac": max(0.0, float(ac))}
    st.session_state.df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    persist_progress()


def delete_items(ids):
    df = st.session_state.df
    st.session_state.df = df[~df["id"].isin(ids)].reset_index(drop=True)
    persist_progress()


meta = {
    "name": storage.get_setting(conn, "proj_name", "ARAKONAK GES"),
    "loc": storage.get_setting(conn, "proj_loc", "Muş / Bulanık"),
    "start": pd.to_datetime(storage.get_setting(conn, "start")),
    "end": pd.to_datetime(storage.get_setting(conn, "end")),
}

# günlük noktayı her açılışta da tazele (bugün için nokta garanti)
base_all = core.enrich(st.session_state.df)
try:
    storage.record_daily(conn, core.per_scope_kpis(base_all))
except Exception:
    pass

# ────────────────────── SOL RAY ──────────────────────
PAGES = ["Komuta Paneli", "İş Kalemleri", "Maliyet & EVM", "S-Eğrisi",
         "Stok", "İSG", "Dışa Aktar", "Veri", "Ayarlar"]
ICON = {"Komuta Paneli": "▦", "İş Kalemleri": "▤", "Maliyet & EVM": "₺", "S-Eğrisi": "📈",
        "Stok": "📦", "İSG": "🦺", "Dışa Aktar": "⭳", "Veri": "🗄", "Ayarlar": "⚙"}
with st.sidebar:
    _logo_b64 = LOGO_WHITE if theme == "dark" else LOGO_BLACK
    if _logo_b64:
        st.markdown(f'<div class="rail-logo"><img src="data:image/svg+xml;base64,{_logo_b64}"/></div>',
                    unsafe_allow_html=True)
    page = st.radio("Menü", [f"{ICON[p]}  {p}" for p in PAGES], label_visibility="collapsed")
    page = page.split("  ", 1)[1]

    st.markdown('<div class="rail-sec">TEMA</div>', unsafe_allow_html=True)
    light_on = st.toggle("☀️ Açık tema", value=(theme == "light"), key="light_toggle")
    want = "light" if light_on else "dark"
    if want != theme:
        st.session_state.theme = want
        st.rerun()

    st.markdown(f'<div class="rail-user">👤 <b>{user["name"]}</b><br>'
                f'<span style="opacity:.7">{user["username"]} · {user["role"]}</span></div>',
                unsafe_allow_html=True)
    if st.button("Çıkış yap", use_container_width=True):
        auth.logout(); st.rerun()
    if ADMIN:
        if st.button("↺ Verileri sıfırla", use_container_width=True):
            storage.reset_all(conn)
            for kk in ("df", "stock", "hse"):
                st.session_state.pop(kk, None)
            st.rerun()

# ────────────────────── ÜST BAŞLIK + KAPSAM ──────────────────────
head_l, head_r = st.columns([2.2, 1.4])
with head_l:
    st.markdown(f"""<div class="pagehd"><div>
      <h1>{page}</h1>
      <div class="sub">{meta['name']} · Canlı EPC İlerleme &amp; Bütçe · {date.today().strftime('%d.%m.%Y')}</div>
    </div></div>""", unsafe_allow_html=True)
with head_r:
    scope_label = st.segmented_control("Kapsam", ["Tümü", "GES-1", "GES-2", "ORTAK"],
                                       default="Tümü", key="scope", label_visibility="collapsed") or "Tümü"
scope = core.SCOPE_MAP[scope_label]

base = core.enrich(st.session_state.df)
scoped = core.scope_df(base, scope)
k = core.kpis(scoped)


# ────────────────────── ORTAK PARÇALAR ──────────────────────
def kpi_ribbon():
    spi = "—" if k["SPI"] is None else f"{k['SPI']:.2f}"
    if k["SPI"] is None:
        sc, sd = MUTED, "veri yok"
    elif k["SPI"] >= 1:
        sc, sd = TEAL_D, "▲ planında"
    else:
        sc, sd = RED, "▼ hedef altı"
    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card" style="--c:linear-gradient(90deg,#22d3ee,#2dd4bf)">
        <div class="kpi-label">TOPLAM BÜTÇE (BAC)</div><div class="kpi-value">{core.fmt_money(k['budget'])}</div>
        <div class="kpi-sub" style="color:#8aa">Sözleşme bedeli</div></div>
      <div class="kpi-card" style="--c:linear-gradient(90deg,{TEAL},#14b8a6)">
        <div class="kpi-label">KAZANILAN (EV)</div><div class="kpi-value" style="color:{TEAL}">{core.fmt_money(k['comp'])}</div>
        <div class="kpi-sub" style="color:{TEAL}">▲ %{k['ilerleme']:.1f}</div></div>
      <div class="kpi-card" style="--c:linear-gradient(90deg,#0e7490,#14b8a6)">
        <div class="kpi-label">PLANA GÖRE</div><div class="kpi-value">%{k['planPct']:.1f}</div>
        <div class="kpi-sub" style="color:{AMBER}">{abs(k['ilerleme']-k['planPct']):.0f} puan {'geride' if k['ilerleme']<k['planPct'] else 'önde'}</div></div>
      <div class="kpi-card" style="--c:linear-gradient(90deg,{AMBER},#f59e0b)">
        <div class="kpi-label">SPI · ZAMAN PERF.</div><div class="kpi-value" style="color:{sc}">{spi}</div>
        <div class="kpi-sub" style="color:{sc}">{sd}</div></div>
      <div class="kpi-card" style="--c:linear-gradient(90deg,#fb7185,{RED})">
        <div class="kpi-label">KALAN İŞ</div><div class="kpi-value">{core.fmt_money(k['kalan'])}</div>
        <div class="kpi-sub" style="color:#8aa">Bakiye</div></div>
    </div>""", unsafe_allow_html=True)


def matrix_table(g: pd.DataFrame):
    rows = ""
    for _, r in g.sort_values("budget", ascending=False).iterrows():
        rl, pl, sp = r["realPct"], r["planPct"], r["sapma"]
        col = TEAL if rl >= pl else RED
        if sp >= 0:
            pill_bg, pill_c, pill_t = "rgba(52,211,153,.15)", GREEN, "İYİ"
        elif sp >= -6:
            pill_bg, pill_c, pill_t = "rgba(251,191,36,.15)", AMBER, "İZLE"
        else:
            pill_bg, pill_c, pill_t = "rgba(251,113,133,.15)", RED, "RİSK"
        w = max(0, min(100, rl))
        rows += (f'<tr><td class="mx-name">{r["disc"]}</td>'
                 f'<td style="text-align:right;color:#9fc3e0;font-weight:700">{core.fmt_money(r["budget"])}</td>'
                 f'<td style="text-align:center;color:#5f7a99">%{pl:.0f}</td>'
                 f'<td style="min-width:170px"><div style="position:relative;background:#0e2233;border-radius:5px;'
                 f'height:18px;overflow:hidden"><div style="position:absolute;left:0;top:0;height:100%;width:{w:.0f}%;'
                 f'background:{col};border-radius:5px"></div><span style="position:absolute;left:8px;top:0;line-height:18px;'
                 f'font-size:10px;font-weight:800;color:#e8f4ff">%{rl:.0f}</span></div></td>'
                 f'<td style="text-align:center;font-weight:800;color:{col}">{sp:+.0f}</td>'
                 f'<td style="text-align:center"><span class="mx-pill" style="background:{pill_bg};color:{pill_c}">{pill_t}</span></td></tr>')
    st.markdown(f"""<table class="mx"><tr>
      <th>DİSİPLİN</th><th style="text-align:right">BÜTÇE</th><th style="text-align:center">PLAN %</th>
      <th>GERÇEK %</th><th style="text-align:center">SAPMA</th><th style="text-align:center">DURUM</th></tr>
      {rows}</table>""", unsafe_allow_html=True)


PLOT = {"displayModeBar": False}


def risk_table(dl: pd.DataFrame):
    if dl is None or dl.empty:
        st.markdown('<div style="color:#7e93b0;font-size:12px;padding:10px 0">Geride kalan kritik iş yok. 🎉</div>',
                    unsafe_allow_html=True)
        return
    mx = float(dl["riskUSD"].max()) or 1.0
    rows = ""
    for _, r in dl.head(7).iterrows():
        w = max(8, r["riskUSD"] / mx * 100)
        nm = r["name"] if len(r["name"]) <= 46 else r["name"][:44] + "…"
        rows += (f'<tr><td style="width:58%;color:#d5e6f7;font-size:11px">{nm}</td>'
                 f'<td style="width:28%"><span class="rbar" style="width:100%"><span class="rbf" style="width:{w:.0f}%;display:block"></span></span></td>'
                 f'<td style="width:14%;text-align:right;font-weight:800;color:#fca5b5;font-size:11px">{core.fmt_money(r["riskUSD"])}</td></tr>')
    st.markdown(f'<table class="mx" style="width:100%">{rows}</table>', unsafe_allow_html=True)


# ══════════════════════ SAYFALAR ══════════════════════
if page == "Komuta Paneli":
    g = core.disc_agg(base, scope)
    gag = core.group_agg(base)
    snaps = core.s_curve_from_snapshots(storage.load_snapshots(conn, scope))
    baseline = core.s_curve_baseline(k["BAC"], meta["start"], meta["end"])
    spi = "—" if k["SPI"] is None else f"{k['SPI']:.2f}"
    spi_arrow = "" if k["SPI"] is None else ("▲" if k["SPI"] >= 1 else "▼")
    spi_col = MUTED if k["SPI"] is None else (TEAL if k["SPI"] >= 1 else RED)

    hero = st.columns([1, 1.25, 1.35], gap="medium")
    with hero[0]:
        st.markdown(f"""
        <div class="kbox"><div class="kl">TOPLAM BÜTÇE</div>
          <div class="kv" style="color:#38bdf8">{core.fmt_money(k['budget'])}</div></div>
        <div class="kbox"><div class="kl">KAZANILAN (EV)</div>
          <div class="kv" style="color:#22d3ee">{core.fmt_money(k['comp'])}</div></div>
        <div class="kbox"><div class="kl">KALAN İŞ</div>
          <div class="kv" style="color:#fb7185">{core.fmt_money(k['kalan'])}</div></div>
        """, unsafe_allow_html=True)
    with hero[1]:
        with st.container(border=True):
            st.markdown('<div class="panel-ttl">Genel İlerleme</div>', unsafe_allow_html=True)
            st.plotly_chart(charts.progress_donut(k["ilerleme"], k["planPct"]),
                            use_container_width=True, config=PLOT)
            st.markdown(f'<div style="text-align:center">'
                        f'<span class="nchip">PLANA GÖRE %{k["planPct"]:.0f}</span>'
                        f'<span class="nchip" style="color:{spi_col}">SPI {spi} {spi_arrow}</span></div>',
                        unsafe_allow_html=True)
    with hero[2]:
        with st.container(border=True):
            st.markdown('<div class="panel-ttl">Grup Performans Göstergeleri</div>', unsafe_allow_html=True)
            st.plotly_chart(charts.group_gauges(gag), use_container_width=True, config=PLOT)

    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Kümülatif S-Eğrisi (günlük)</div>', unsafe_allow_html=True)
        st.plotly_chart(charts.s_curve(baseline, snaps, k["planPct"], k["ilerleme"]),
                        use_container_width=True, config=PLOT)

    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Disiplin Matrisi — Koşullu Biçimlendirme</div>', unsafe_allow_html=True)
        matrix_table(g)

elif page == "İş Kalemleri":
    kpi_ribbon()
    if ADMIN:
        st.caption("✏️ Düzenlemek için tablodaki **Plan %**, **Gerçek %** veya **Fiili Maliyet** hücresine "
                   "çift tıklayıp değeri yazın, Enter'a basın. Değer anında kaydedilir ve grafiklere yansır.")
        cadd, cdel = st.columns(2)
        with cadd:
            with st.expander("➕ Yeni İş Kalemi Ekle", expanded=False):
                with st.form("add_item_form", clear_on_submit=True):
                    ai_grp = st.selectbox("Grup", core.GROUPS)
                    disc_opts = sorted(base["disc"].unique().tolist())
                    ai_disc = st.selectbox("Disiplin", disc_opts + ["➕ Yeni disiplin…"])
                    ai_disc_new = st.text_input("Yeni disiplin adı", "")
                    ai_name = st.text_input("Poz Adı", "")
                    b1, b2, b3 = st.columns(3)
                    ai_unit = b1.text_input("Birim", "adet")
                    ai_qty = b2.number_input("Miktar", min_value=0.0, value=1.0, step=1.0)
                    ai_up = b3.number_input("Birim Fiyat ($)", min_value=0.0, value=0.0, step=100.0)
                    c1, c2 = st.columns(2)
                    ai_plan = c1.number_input("Plan %", 0, 100, 0)
                    ai_real = c2.number_input("Gerçek %", 0, 100, 0)
                    submitted = st.form_submit_button("➕ Ekle", type="primary", use_container_width=True)
                if submitted:
                    disc_final = ai_disc_new.strip() if ai_disc == "➕ Yeni disiplin…" else ai_disc
                    if not ai_name.strip() or not disc_final:
                        st.error("Poz adı ve disiplin zorunlu.")
                    else:
                        add_item(ai_grp, disc_final, ai_name, ai_unit, ai_qty, ai_up, ai_plan, ai_real)
                        st.toast("Yeni iş kalemi eklendi."); st.rerun()
        with cdel:
            with st.expander("🗑 İş Kalemi Sil", expanded=False):
                del_map = {f'{r["disc"]} — {r["name"][:50]}': r["id"] for _, r in scoped.iterrows()}
                del_sel = st.multiselect("Silinecek kalem(ler)", list(del_map.keys()))
                if st.button("Seçilenleri sil", disabled=not del_sel, use_container_width=True):
                    delete_items([del_map[x] for x in del_sel])
                    st.toast(f"{len(del_sel)} kalem silindi."); st.rerun()
    else:
        st.info("Görüntüleyici modu: tablo salt-okunur.")

    f1, f2, f3 = st.columns([1, 2, 2])
    grp_view = f1.selectbox("Grup", ["(Kapsam)"] + core.GROUPS, index=0)
    disc_view = f2.selectbox("Disiplin", ["(Tümü)"] + sorted(scoped["disc"].unique().tolist()), index=0)
    search = f3.text_input("🔎 Poz adında ara", "")
    view = scoped if grp_view == "(Kapsam)" else base[base["grp"] == grp_view]
    if disc_view != "(Tümü)":
        view = view[view["disc"] == disc_view]
    if search.strip():
        view = view[view["name"].str.contains(search.strip(), case=False, na=False)]

    # düzenlenebilir kolonlar (Plan/Gerçek/Fiili) sola yakın
    show = view[["id", "disc", "name", "plan", "real", "ac", "comp", "kalan", "unit", "qty", "up", "tutar", "durum"]].copy()
    edited = st.data_editor(
        show, use_container_width=True, hide_index=True, num_rows="fixed", key="editor", disabled=not ADMIN,
        height=460,
        column_config={
            "id": None,
            "disc": st.column_config.TextColumn("Disiplin", disabled=True),
            "name": st.column_config.TextColumn("Poz Adı", disabled=True, width="large"),
            "plan": st.column_config.NumberColumn("✏️ Plan %", min_value=0, max_value=100, step=1, format="%d"),
            "real": st.column_config.NumberColumn("✏️ Gerçek %", min_value=0, max_value=100, step=1, format="%d"),
            "ac": st.column_config.NumberColumn("✏️ Fiili Maliyet ($)", min_value=0, step=1000, format="$%d"),
            "comp": st.column_config.NumberColumn("Kazanılan ($)", disabled=True, format="$%.0f"),
            "kalan": st.column_config.NumberColumn("Kalan ($)", disabled=True, format="$%.0f"),
            "unit": st.column_config.TextColumn("Birim", disabled=True),
            "qty": st.column_config.NumberColumn("Miktar", disabled=True, format="%.2f"),
            "up": st.column_config.NumberColumn("B.Fiyat ($)", disabled=True, format="%.2f"),
            "tutar": st.column_config.NumberColumn("Toplam ($)", disabled=True, format="$%.0f"),
            "durum": st.column_config.TextColumn("Durum", disabled=True)})
    if ADMIN:
        updates = 0
        cur = st.session_state.df.set_index("id")
        for _, r in edited.iterrows():
            rid = r["id"]
            p = max(0.0, min(100.0, float(r["plan"]))); rl = max(0.0, min(100.0, float(r["real"]))); ac = max(0.0, float(r["ac"]))
            if (abs(p - cur.loc[rid, "plan"]) > 1e-9 or abs(rl - cur.loc[rid, "real"]) > 1e-9 or abs(ac - cur.loc[rid, "ac"]) > 1e-6):
                st.session_state.df.loc[st.session_state.df["id"] == rid, ["plan", "real", "ac"]] = [p, rl, ac]
                updates += 1
        if updates:
            persist_progress()
            st.toast(f"{updates} satır güncellendi · günlük kayıt yenilendi."); st.rerun()

elif page == "Maliyet & EVM":
    kpi_ribbon()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PV — Planlanan Değer", core.fmt_money(k["PV"]))
    m2.metric("EV — Kazanılan Değer", core.fmt_money(k["EV"]))
    m3.metric("SV — Zaman Sapması", core.fmt_money(k["SV"]), delta="planında" if k["SV"] >= 0 else "geride")
    m4.metric("SPI", "—" if k["SPI"] is None else f"{k['SPI']:.2f}",
              delta=None if k["SPI"] is None else f"{(k['SPI']-1)*100:+.1f}%")
    st.divider()
    if k["has_cost"]:
        c = st.columns(5)
        c[0].metric("AC — Fiili Maliyet", core.fmt_money(k["AC"]))
        c[1].metric("CV — Maliyet Sapması", core.fmt_money(k["CV"]))
        c[2].metric("CPI", f"{k['CPI']:.3f}", delta=f"{(k['CPI']-1)*100:+.1f}%")
        c[3].metric("EAC — Tahmini Toplam", core.fmt_money(k["EAC"]))
        c[4].metric("VAC — Bütçe Sapması", core.fmt_money(k["VAC"]))
        st.caption(f"ETC: **{core.fmt_money(k['ETC'])}** · TCPI: **{k['TCPI']:.3f}**")
    else:
        st.info("💡 Maliyet göstergeleri (CPI, EAC…) için İş Kalemleri'nde 'Fiili Maliyet ($)' girin. "
                "Girilmediği sürece uydurma değer gösterilmez.")
    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Bütçe Akışı — BAC → Kazanılan → Kalan</div>', unsafe_allow_html=True)
        st.plotly_chart(charts.evm_waterfall(k), use_container_width=True, config=PLOT)

elif page == "S-Eğrisi":
    snaps_raw = storage.load_snapshots(conn, scope)
    snaps = core.s_curve_from_snapshots(snaps_raw)
    baseline = core.s_curve_baseline(k["BAC"], meta["start"], meta["end"])
    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Kümülatif İlerleme S-Eğrisi (günlük noktalar)</div>', unsafe_allow_html=True)
        st.plotly_chart(charts.s_curve(baseline, snaps, k["planPct"], k["ilerleme"]),
                        use_container_width=True, config=PLOT)
    st.caption("Kesikli = tarihlerden modellenen plan baseline'ı · Yeşil = İş Kalemleri'nde "
               "her gün girdiğiniz değerlerden oluşan gerçek ilerleme.")
    if not snaps_raw.empty:
        st.dataframe(snaps_raw[["ts", "pv_pct", "ev_pct", "ac_usd", "bac", "note"]].rename(columns={
            "ts": "Tarih", "pv_pct": "Plan %", "ev_pct": "Gerçek %", "ac_usd": "Fiili $", "bac": "BAC $", "note": "Not"}),
            use_container_width=True, hide_index=True)
        if ADMIN and st.button("Günlük kayıtları temizle"):
            storage.clear_snapshots(conn); st.rerun()

elif page == "Stok":
    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Malzeme Akışı — Sipariş → Sevk → Sahada → Montaj</div>', unsafe_allow_html=True)
        st.plotly_chart(charts.stock_chart(st.session_state.stock), use_container_width=True, config=PLOT)
    sdf = st.session_state.stock.copy()
    edited_s = st.data_editor(sdf, use_container_width=True, hide_index=True, num_rows="fixed",
        disabled=not ADMIN, key="stock_editor",
        column_config={"id": None, "name": st.column_config.TextColumn("Malzeme", disabled=True, width="large"),
            "unit": st.column_config.TextColumn("Birim", disabled=True),
            "ordered": st.column_config.NumberColumn("Sipariş", format="%.0f"),
            "delivered": st.column_config.NumberColumn("Sevk", format="%.0f"),
            "onsite": st.column_config.NumberColumn("Sahada", format="%.0f"),
            "installed": st.column_config.NumberColumn("Montajlı", format="%.0f"),
            "remaining": st.column_config.NumberColumn("Kalan", disabled=True, format="%.0f")})
    if ADMIN:
        e2 = edited_s.copy(); e2["remaining"] = (e2["ordered"] - e2["installed"]).clip(lower=0)
        if not e2.equals(st.session_state.stock):
            st.session_state.stock = e2; storage.save_stock(conn, e2); st.rerun()

elif page == "İSG":
    hdf = st.session_state.hse
    cols = st.columns(len(hdf))
    for col, (_, r) in zip(cols, hdf.iterrows()):
        col.metric(r["label"], f"{r['value']:.0f} {r['unit']}")
    st.divider()
    edited_h = st.data_editor(hdf, use_container_width=True, hide_index=True, num_rows="fixed",
        disabled=not ADMIN, key="hse_editor",
        column_config={"id": None, "label": st.column_config.TextColumn("Gösterge", disabled=True),
            "value": st.column_config.NumberColumn("Değer", format="%.0f"),
            "unit": st.column_config.TextColumn("Birim", disabled=True)})
    if ADMIN and not edited_h.equals(hdf):
        st.session_state.hse = edited_h; storage.save_hse(conn, edited_h); st.rerun()

elif page == "Dışa Aktar":
    st.write("Tüm projenin güncel durumunu profesyonel Excel veya PDF olarak indirin.")
    gag = core.group_agg(base)
    state = dict(df=base, k=core.kpis(base), disc=core.disc_agg(base, "ALL"), gag=gag,
        delayed=core.delayed_items(base), stock=st.session_state.stock, hse=st.session_state.hse,
        meta=meta, baseline=core.s_curve_baseline(core.kpis(base)["BAC"], meta["start"], meta["end"]),
        snaps=core.s_curve_from_snapshots(storage.load_snapshots(conn, "ALL")))
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    d1, d2 = st.columns(2)
    with d1:
        with st.spinner("Excel hazırlanıyor…"):
            xls = exports.build_excel(state)
        st.download_button("⬇️ Excel (.xlsx) indir", xls, file_name=f"ARAKONAK_GES_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, type="primary")
        st.caption("7 sayfa: Özet · İş Kalemleri · Disiplin · Grup · Geciken İşler · Stok · İSG")
    with d2:
        with st.spinner("PDF hazırlanıyor…"):
            pdf = exports.build_pdf(state)
        st.download_button("⬇️ PDF rapor indir", pdf, file_name=f"ARAKONAK_GES_{ts}.pdf",
            mime="application/pdf", use_container_width=True, type="primary")
        st.caption("Logolu yönetici raporu: KPI · grafikler · geciken işler")

elif page == "Veri":
    st.warning("Streamlit Cloud deposu geçici olabilir. Verinizi kaybetmemek için düzenli CSV indirin.")
    csv = st.session_state.df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ İş kalemleri CSV yedeği", csv, file_name="arakonak_backup.csv",
                       mime="text/csv", use_container_width=True)
    if ADMIN:
        st.divider()
        up = st.file_uploader("CSV geri yükle", type=["csv"])
        if up is not None:
            try:
                new = pd.read_csv(up)
                if not {"id", "plan", "real"}.issubset(new.columns):
                    st.error("CSV'de gerekli sütunlar yok (id, plan, real).")
                else:
                    cur = st.session_state.df.set_index("id"); ni = new.set_index("id")
                    for c in ("plan", "real", "ac"):
                        if c in ni.columns:
                            cur.loc[ni.index, c] = ni[c].values
                    st.session_state.df = cur.reset_index(); persist_progress()
                    st.success("Geri yüklendi."); st.rerun()
            except Exception as ex:
                st.error(f"Okunamadı: {ex}")

elif page == "Ayarlar":
    if not ADMIN:
        st.info("Ayarları yalnızca admin değiştirebilir.")
    else:
        s1, s2 = st.columns(2)
        pname = s1.text_input("Proje adı", meta["name"])
        ploc = s2.text_input("Konum", meta["loc"])
        d1, d2 = st.columns(2)
        pstart = d1.date_input("Başlangıç tarihi", meta["start"].date())
        pend = d2.date_input("Bitiş tarihi (hedef)", meta["end"].date())
        if st.button("💾 Ayarları kaydet", type="primary"):
            storage.set_setting(conn, "proj_name", pname); storage.set_setting(conn, "proj_loc", ploc)
            storage.set_setting(conn, "start", pstart.strftime("%Y-%m-%d"))
            storage.set_setting(conn, "end", pend.strftime("%Y-%m-%d"))
            st.success("Kaydedildi."); st.rerun()
        st.divider()
        st.markdown("**🔐 Yeni parola hash'i üret** (Secrets'a eklemek için)")
        pw = st.text_input("Parola", type="password", key="pwgen")
        if pw:
            st.code(auth.hash_password(pw), language="text")

st.markdown("<div style='text-align:center;color:#9fb3b5;font-size:11px;margin-top:20px'>"
            "ARAKONAK GES · Kontrol Panosu v4 · verileriniz yalnızca sizin dağıtımınızda tutulur</div>",
            unsafe_allow_html=True)
