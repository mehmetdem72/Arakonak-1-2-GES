"""ARAKONAK GES — Kontrol Panosu (v4 · Açık Kurumsal / Power BI tarzı).

Sol menü rayı · KPI kartları · kombine grafik · halka gösterge · koşullu
biçimlendirmeli disiplin matrisi. İş kalemleri günlük girilir; her gün otomatik
'günlük anlık görüntü' kaydedilir ve S-eğrisi bu günlük noktalardan oluşur.
"""
from __future__ import annotations

import base64
import json
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

    /* Kapsam butonları — okunur, tamamen kontrol bizde (primaryColor'dan bağımsız) */
    div[data-testid="stButton"] button[kind="secondary"],
    div[data-testid="stFormSubmitButton"] button[kind="secondary"],
    div[data-testid="stDownloadButton"] button{{
      font-weight:800 !important;border-radius:10px !important;
      background:{t['railhov']} !important;border:1px solid {t['border']} !important;
      color:{t['text']} !important;box-shadow:none !important;}}
    div[data-testid="stButton"] button[kind="secondary"]:hover,
    div[data-testid="stDownloadButton"] button:hover{{
      border-color:{t['acc']} !important;color:{t['acc']} !important;}}
    div[data-testid="stButton"] button[kind="primary"],
    div[data-testid="stFormSubmitButton"] button[kind="primary"]{{
      font-weight:800 !important;border-radius:10px !important;
      background:linear-gradient(120deg,{t['accd']},{t['acc']}) !important;
      color:#04222b !important;border:none !important;
      box-shadow:0 6px 16px rgba(34,211,238,.35) !important;}}
    div[data-testid="stButton"] button[kind="primary"] *,
    div[data-testid="stFormSubmitButton"] button[kind="primary"] *{{color:#04222b !important;}}
    div[data-testid="stButton"] button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover{{filter:brightness(1.08);}}

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
    table.mx tbody tr:nth-child(even) td, table.mx tr:nth-child(even) td{{background:rgba(255,255,255,.018);}}
    table.mx tr:hover td{{background:{t['rowh']};transition:background .12s ease;}}
    .mx-name{{font-weight:700;color:{t['text']};}}
    .mx-bar{{border-radius:5px;height:17px;line-height:17px;padding-left:7px;font-weight:800;color:#04222b;font-size:9.5px;}}
    .mx-pill{{padding:3px 9px;border-radius:999px;font-weight:800;font-size:9.5px;}}
    .rbar{{display:inline-block;height:7px;background:rgba(251,113,133,.2);border-radius:4px;vertical-align:middle;overflow:hidden;}}
    .rbf{{height:100%;background:#fb7185;border-radius:4px;}}

    div[data-testid="stMetric"]{{background:{t['metricbg']};border:1px solid {t['border']};border-radius:14px;
      padding:13px 16px;box-shadow:0 4px 16px rgba(0,0,0,.12);position:relative;overflow:hidden;
      background-image:linear-gradient(180deg,rgba(34,211,238,.045),transparent);}}
    div[data-testid="stMetric"]::before{{content:"";position:absolute;left:0;top:0;height:3px;width:100%;
      background:linear-gradient(90deg,{t['accd']},{t['acc']});}}
    div[data-testid="stMetric"] *{{color:{t['text']} !important;}}
    div[data-testid="stMetricValue"] *{{color:{t['ttl']} !important;font-weight:900 !important;}}
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
    /* Yerel giriş alanlarını koyu temaya uydur */
    [data-testid="stNumberInput"] input, [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea{{
      background:{t['railhov']} !important;color:{t['text']} !important;border:1px solid {t['border']} !important;}}
    [data-testid="stNumberInput"] button{{background:{t['railhov']} !important;color:{t['text']} !important;
      border:1px solid {t['border']} !important;}}
    [data-baseweb="select"] > div{{background:{t['railhov']} !important;border:1px solid {t['border']} !important;
      color:{t['text']} !important;}}
    [data-baseweb="select"] *{{color:{t['text']} !important;}}
    [data-baseweb="popover"] li{{background:{t['panel']} !important;color:{t['text']} !important;}}
    .row-edit{{border-bottom:1px solid {t['rowb']};padding:2px 0;}}
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

# ────────────────────── SOL RAY ──────────────────────
PAGES = ["Komuta Paneli", "İş Kalemleri", "Maliyet & EVM", "S-Eğrisi", "Nakit & Hakediş",
         "Risk & Kalite", "Baseline", "Stok", "İSG", "Dışa Aktar", "Kayıt Defteri", "Veri", "Ayarlar"]
ICON = {"Komuta Paneli": "▦", "İş Kalemleri": "▤", "Maliyet & EVM": "₺", "S-Eğrisi": "📈",
        "Nakit & Hakediş": "💵", "Risk & Kalite": "⚠", "Baseline": "📌", "Stok": "📦", "İSG": "🦺",
        "Dışa Aktar": "⭳", "Kayıt Defteri": "📝", "Veri": "🗄", "Ayarlar": "⚙"}
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
    if st.button("Çıkış yap", width="stretch"):
        auth.logout(); st.rerun()
    if ADMIN:
        if st.button("↺ Verileri sıfırla", width="stretch"):
            storage.reset_all(conn)
            for kk in ("df", "stock", "hse"):
                st.session_state.pop(kk, None)
            for kk in [x for x in list(st.session_state.keys())
                       if str(x).startswith(("ep_", "er_", "ea_"))]:
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
    if "scope_sel" not in st.session_state:
        st.session_state.scope_sel = "Tümü"
    st.markdown('<div class="scope-btns">', unsafe_allow_html=True)
    sc_cols = st.columns(4, gap="small")
    for _i, _lb in enumerate(["Tümü", "GES-1", "GES-2", "ORTAK"]):
        _typ = "primary" if st.session_state.scope_sel == _lb else "secondary"
        if sc_cols[_i].button(_lb, key=f"scb_{_lb}", type=_typ, width="stretch"):
            st.session_state.scope_sel = _lb
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    scope_label = st.session_state.scope_sel
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


def gran_buttons(key: str, default: str = "Günlük") -> str:
    """Grafik üstünde Günlük / Haftalık / Aylık seçim butonları. Seçili granülariteyi döndürür."""
    sk = f"gran_{key}"
    if sk not in st.session_state:
        st.session_state[sk] = default
    cols = st.columns([1, 1, 1, 5])
    for i, lb in enumerate(["Günlük", "Haftalık", "Aylık"]):
        typ = "primary" if st.session_state[sk] == lb else "secondary"
        if cols[i].button(lb, key=f"{sk}_{lb}", type=typ, use_container_width=True):
            st.session_state[sk] = lb
            st.rerun()
    return st.session_state[sk]


def items_table_html(view: pd.DataFrame, limit: int = 400):
    rows = ""
    for _, r in view.head(limit).iterrows():
        rl = r["real"]; col = TEAL if rl >= r["plan"] else RED
        w = max(0, min(100, rl))
        dcol = {"TAMAMLANDI": TEAL, "DEVAM": "#38bdf8", "GERİDE": RED, "BAŞLAMADI": "#5f7a99"}.get(r["durum"], "#5f7a99")
        rows += (f'<tr><td class="mx-name" style="max-width:420px">{r["name"][:90]}</td>'
                 f'<td style="color:#5f7a99;font-size:10px">{r["disc"]}</td>'
                 f'<td style="text-align:right;color:#9fc3e0">{core.fmt_money(r["tutar"])}</td>'
                 f'<td style="text-align:center;color:#5f7a99">%{r["plan"]:.0f}</td>'
                 f'<td style="min-width:130px"><div style="position:relative;background:#0e2233;border-radius:5px;'
                 f'height:16px;overflow:hidden"><div style="position:absolute;left:0;top:0;height:100%;width:{w:.0f}%;'
                 f'background:{col};border-radius:5px"></div><span style="position:absolute;left:7px;top:0;line-height:16px;'
                 f'font-size:9.5px;font-weight:800;color:#e8f4ff">%{rl:.0f}</span></div></td>'
                 f'<td style="text-align:center"><span style="color:{dcol};font-weight:800;font-size:10px">{r["durum"]}</span></td></tr>')
    st.markdown(f"""<table class="mx"><tr>
      <th>POZ ADI</th><th>DİSİPLİN</th><th style="text-align:right">TUTAR</th>
      <th style="text-align:center">PLAN %</th><th>GERÇEK %</th><th style="text-align:center">DURUM</th></tr>
      {rows}</table>""", unsafe_allow_html=True)


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
    snaps_items = core.s_curve_from_snapshots(storage.load_snapshots(conn, scope))
    _plan = storage.load_table(conn, "planline", core.month_rows(meta["start"], meta["end"]))
    _bm, _ = core.manual_curve(_plan, k["BAC"])
    baseline = _bm            # plan = yalnızca elle girilen Plan Programı
    snaps = snaps_items       # gerçek = İş Kalemleri verisi
    spi = "—" if k["SPI"] is None else f"{k['SPI']:.2f}"
    spi_arrow = "" if k["SPI"] is None else ("▲" if k["SPI"] >= 1 else "▼")
    spi_col = MUTED if k["SPI"] is None else (TEAL if k["SPI"] >= 1 else RED)

    # Yönetici özeti + uyarılar
    st.markdown(f'<div style="background:linear-gradient(90deg,rgba(34,211,238,.10),rgba(139,92,246,.06));'
                f'border:1px solid {THEMES[theme]["border"]};border-radius:12px;padding:10px 15px;'
                f'font-size:12.5px;color:{THEMES[theme]["text"]};margin-bottom:10px">🧭 <b>Yönetici Özeti:</b> '
                f'{core.narrative(k, scope_label)}</div>', unsafe_allow_html=True)
    al = core.alerts(scoped, k)
    acol = {"risk": ("#fb7185", "rgba(251,113,133,.12)"), "izle": ("#fbbf24", "rgba(251,191,36,.12)"),
            "iyi": ("#34d399", "rgba(52,211,153,.12)")}
    chips = "".join(f'<span style="display:inline-block;background:{acol[l][1]};border:1px solid {acol[l][0]};'
                    f'color:{acol[l][0]};padding:5px 11px;border-radius:8px;font-size:11px;font-weight:700;'
                    f'margin:0 6px 6px 0">{"●" if l=="risk" else "▲" if l=="izle" else "✓"} {m}</span>'
                    for l, m in al)
    st.markdown(f'<div style="margin-bottom:12px">{chips}</div>', unsafe_allow_html=True)

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
                            width="stretch", config=PLOT)
            st.markdown(f'<div style="text-align:center">'
                        f'<span class="nchip">PLANA GÖRE %{k["planPct"]:.0f}</span>'
                        f'<span class="nchip" style="color:{spi_col}">SPI {spi} {spi_arrow}</span></div>',
                        unsafe_allow_html=True)
    with hero[2]:
        with st.container(border=True):
            st.markdown('<div class="panel-ttl">Grup Performans Göstergeleri</div>', unsafe_allow_html=True)
            st.plotly_chart(charts.group_gauges(gag), width="stretch", config=PLOT)

    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Kümülatif S-Eğrisi</div>', unsafe_allow_html=True)
        gran = gran_buttons("dash_scurve")
        snaps_g = core.scurve_series_gran(storage.load_snapshots(conn, scope), gran)
        snaps_use = snaps_g if not snaps_g.empty else snaps
        st.plotly_chart(charts.s_curve(baseline, snaps_use, k["planPct"], k["ilerleme"],
                                       xstart=meta["start"], xend=meta["end"]),
                        width="stretch", config=PLOT)

    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Disiplin Matrisi — Koşullu Biçimlendirme</div>', unsafe_allow_html=True)
        matrix_table(g)

elif page == "İş Kalemleri":
    kpi_ribbon()
    if ADMIN:
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
                    submitted = st.form_submit_button("➕ Ekle", type="primary", width="stretch")
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
                if st.button("Seçilenleri sil", disabled=not del_sel, width="stretch"):
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

    st.markdown(f'<div style="color:#7fb0b3;font-size:12px;margin:6px 0">Görüntülenen: '
                f'<b>{len(view)}</b> kalem · Toplam <b>{core.fmt_money(view["tutar"].sum())}</b></div>',
                unsafe_allow_html=True)

    edit_mode = False
    if ADMIN:
        edit_mode = st.toggle("✏️ Düzenleme modu", value=False,
                              help="Açıkken kalemler düzenlenebilir forma dönüşür; kapalıyken salt görünüm.")

    if ADMIN and edit_mode and len(view) > 0:
        PAGE = 40
        total = len(view)
        sl = view
        if total > PAGE:
            pages = (total + PAGE - 1) // PAGE
            pg = st.number_input(f"Sayfa (her sayfada {PAGE} kalem · toplam {pages} sayfa)",
                                 min_value=1, max_value=pages, value=1, step=1)
            sl = view.iloc[(pg - 1) * PAGE: pg * PAGE]
            st.caption(f"{(pg-1)*PAGE+1}–{min(pg*PAGE, total)} arası kalemler gösteriliyor.")
        # widget değerlerini önceden session_state'e tohumla (form/value+key bayatlık sorununu önler)
        for _, r in sl.iterrows():
            st.session_state.setdefault(f"ep_{r['id']}", int(round(r["plan"])))
            st.session_state.setdefault(f"er_{r['id']}", int(round(r["real"])))
            st.session_state.setdefault(f"ea_{r['id']}", float(r["ac"]))
        with st.form("edit_items", border=False):
            h = st.columns([5, 1.3, 1.3, 1.8])
            h[0].markdown("**Poz Adı**"); h[1].markdown("**Plan %**")
            h[2].markdown("**Gerçek %**"); h[3].markdown("**Fiili Maliyet ($)**")
            ids = []
            for _, r in sl.iterrows():
                ids.append(r["id"])
                c = st.columns([5, 1.3, 1.3, 1.8])
                c[0].markdown(f'<div class="row-edit" style="font-size:12px;padding-top:8px;color:#dbeafe">'
                              f'{r["name"][:80]}</div>', unsafe_allow_html=True)
                c[1].number_input("p", 0, 100, key=f"ep_{r['id']}", label_visibility="collapsed")
                c[2].number_input("r", 0, 100, key=f"er_{r['id']}", label_visibility="collapsed")
                c[3].number_input("a", min_value=0.0, step=1000.0, key=f"ea_{r['id']}", label_visibility="collapsed")
            saved = st.form_submit_button("💾 Kaydet — grafiklere yansıt", type="primary", width="stretch")
        if saved:
            cur = st.session_state.df.set_index("id")
            n_upd = 0
            for rid in ids:
                old = cur.loc[rid]
                nm = str(old["name"])[:40]
                p = float(st.session_state.get(f"ep_{rid}", old["plan"]))
                rl = float(st.session_state.get(f"er_{rid}", old["real"]))
                ac = float(st.session_state.get(f"ea_{rid}", old["ac"]))
                p = max(0.0, min(100.0, p)); rl = max(0.0, min(100.0, rl)); ac = max(0.0, ac)
                changed = False
                if abs(p - float(old["plan"])) > 1e-9:
                    storage.log_change(conn, user["username"], nm, "Plan %", f"{old['plan']:.0f}", f"{p:.0f}"); changed = True
                if abs(rl - float(old["real"])) > 1e-9:
                    storage.log_change(conn, user["username"], nm, "Gerçek %", f"{old['real']:.0f}", f"{rl:.0f}"); changed = True
                if abs(ac - float(old["ac"])) > 1e-6:
                    storage.log_change(conn, user["username"], nm, "Fiili Maliyet", f"{old['ac']:.0f}", f"{ac:.0f}"); changed = True
                if changed:
                    st.session_state.df.loc[st.session_state.df["id"] == rid, ["plan", "real", "ac"]] = [p, rl, ac]
                    n_upd += 1
            if n_upd:
                persist_progress()
                st.success(f"✅ {n_upd} kalem kaydedildi · grafikler ve S-Eğrisi güncellendi.")
                st.toast(f"{n_upd} kalem kaydedildi.")
            else:
                st.toast("Değişiklik yok.")
            st.rerun()
    else:
        items_table_html(view)

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
        st.plotly_chart(charts.evm_waterfall(k), width="stretch", config=PLOT)
    with st.container(border=True):
        st.markdown('<div class="panel-ttl">SPI / CPI Trend (zaman içinde performans)</div>', unsafe_allow_html=True)
        gran_sc = gran_buttons("spicpi")
        st.plotly_chart(charts.spi_cpi_trend(core.spi_cpi_series_gran(storage.load_snapshots(conn, scope), gran_sc)),
                        width="stretch", config=PLOT)
        st.caption("1.0 çizgisi hedef. SPI<1 zaman geriliği, CPI<1 maliyet aşımı. Veri girdikçe eğilim oluşur.")

elif page == "S-Eğrisi":
    snaps_raw = storage.load_snapshots(conn, scope)

    st.markdown('<div class="panel-ttl">Plan Programı — aylık planlanan % (elle giriş)</div>', unsafe_allow_html=True)
    st.caption("Her ay için **planlanan kümülatif ilerleme %**'sini girin — S-eğrisinin **plan çizgisi** bundan çizilir. "
               "**Gerçekleşen** çizgi ise İş Kalemleri'ne girdiğiniz değerlerden otomatik oluşur.")
    _pl_default = [{"Ay": r["Ay"], "Plan %": r["Plan %"]} for r in core.month_rows(meta["start"], meta["end"])]
    planline = storage.load_table(conn, "planline", _pl_default)
    if "Gerçek %" in planline.columns:
        planline = planline.drop(columns=["Gerçek %"])
    pl_ed = st.data_editor(planline, width="stretch", hide_index=True, num_rows="dynamic",
                           disabled=not ADMIN, key="planline_ed",
                           column_config={
                               "Ay": st.column_config.TextColumn("Ay (YYYY-AA)"),
                               "Plan %": st.column_config.NumberColumn("Plan % (kümülatif hedef)", min_value=0, max_value=100, step=1)})
    if ADMIN and not pl_ed.equals(planline):
        storage.save_table(conn, "planline", pl_ed); st.rerun()

    base_m, _ = core.manual_curve(pl_ed, k["BAC"])
    baseline = base_m
    has_plan = not base_m.empty

    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Kümülatif İlerleme S-Eğrisi</div>', unsafe_allow_html=True)
        gran = gran_buttons("scurve_page")
        snaps = core.scurve_series_gran(snaps_raw, gran)
        st.plotly_chart(charts.s_curve(baseline, snaps, k["planPct"], k["ilerleme"],
                                       xstart=meta["start"], xend=meta["end"]),
                        width="stretch", config=PLOT)
    if not has_plan:
        st.info("💡 **Plan çizgisi** için yukarıdaki tabloya aylık **Plan %** girin. "
                "**Gerçek** çizgi İş Kalemleri'ne veri girdikçe otomatik ilerler.")
    else:
        st.caption(f"Görünüm: **{gran}** · Plan = sizin girdiğiniz hedefler · Gerçek = İş Kalemleri verisinden.")
    if not snaps_raw.empty:
        with st.expander("İş Kalemleri'nden oluşan günlük kayıtlar"):
            st.dataframe(snaps_raw[["ts", "pv_pct", "ev_pct", "ac_usd", "bac", "note"]].rename(columns={
                "ts": "Tarih", "pv_pct": "Plan %", "ev_pct": "Gerçek %", "ac_usd": "Fiili $", "bac": "BAC $", "note": "Not"}),
                width="stretch", hide_index=True)
            if ADMIN and st.button("Günlük kayıtları temizle"):
                storage.clear_snapshots(conn); st.rerun()

elif page == "Nakit & Hakediş":
    st.markdown('<div style="background:linear-gradient(90deg,rgba(34,211,238,.10),rgba(139,92,246,.06));'
                'border:1px solid #12324a;border-radius:12px;padding:12px 16px;font-size:12.5px;'
                'color:#cfe3f7;margin-bottom:14px">💵 <b>Bu sayfa projenin parasal akışını yönetir:</b> '
                'aylık <b>planlanan vs fiili harcama</b> (nakit akışı), bütçeyi değiştiren <b>ilave işler (VO)</b> '
                've dönemsel <b>hakediş/ödemeler</b>. Böylece "ne kadar harcadık, bütçe nasıl değişti, ne kadar ödeme aldık" '
                'sorularını tek yerden görürsün.</div>', unsafe_allow_html=True)

    vo = storage.load_table(conn, "vo", [])
    approved_vo = 0.0
    if not vo.empty and "Durum" in vo.columns and "Tutar ($)" in vo.columns:
        approved_vo = float(pd.to_numeric(vo[vo["Durum"] == "Onaylı"]["Tutar ($)"], errors="coerce").fillna(0).sum())
    pay = storage.load_table(conn, "payments", [])
    paid = 0.0
    if not pay.empty and "Durum" in pay.columns and "Tutar ($)" in pay.columns:
        paid = float(pd.to_numeric(pay[pay["Durum"] == "Ödendi"]["Tutar ($)"], errors="coerce").fillna(0).sum())

    c = st.columns(4)
    c[0].metric("Orijinal Bütçe (BAC)", core.fmt_money(k["BAC"]))
    c[1].metric("Onaylı İlave İş (VO)", core.fmt_money(approved_vo))
    c[2].metric("Revize Bütçe", core.fmt_money(k["BAC"] + approved_vo))
    c[3].metric("Ödenen Hakediş", core.fmt_money(paid))

    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Nakit Akışı — Aylık Planlanan vs Fiili Harcama</div>', unsafe_allow_html=True)
        bl = core.s_curve_baseline(k["BAC"], meta["start"], meta["end"])
        st.plotly_chart(charts.cashflow_chart(core.cashflow_series(bl, storage.load_snapshots(conn, scope))),
                        width="stretch", config=PLOT)
        st.caption("📊 Mor = plana göre o ay harcanması beklenen tutar · Camgöbeği = İş Kalemleri'ne girdiğiniz "
                   "Fiili Maliyet'ten oluşan gerçek harcama. Fiili harcama girmedikçe gerçek çubuklar boş kalır.")

    st.markdown('<div class="panel-ttl">Değişiklik Emirleri (VO) — keşif dışı / ilave işler</div>', unsafe_allow_html=True)
    st.caption("Sözleşme dışı ortaya çıkan ilave işleri buraya yazın. **Durum = Onaylı** yaptığınızda tutar "
               "otomatik **Revize Bütçe**'ye eklenir.")
    vo_def = [{"VO No": "VO-001", "Açıklama": "", "Tutar ($)": 0.0, "Durum": "Beklemede", "Tarih": ""}]
    vo = storage.load_table(conn, "vo", vo_def)
    vo_ed = st.data_editor(vo, width="stretch", hide_index=True, num_rows="dynamic",
                           disabled=not ADMIN, key="vo_ed",
                           column_config={"Durum": st.column_config.SelectboxColumn(options=["Beklemede", "Onaylı", "Red"]),
                                          "Tutar ($)": st.column_config.NumberColumn(format="$%d")})
    if ADMIN and not vo_ed.equals(vo):
        storage.save_table(conn, "vo", vo_ed); st.rerun()

    st.markdown('<div class="panel-ttl">Hakediş / Ödeme Takibi</div>', unsafe_allow_html=True)
    st.caption("İşverene sunulan dönemsel hakedişleri ve ödeme durumlarını izleyin. "
               "**Durum = Ödendi** olanların toplamı üstteki 'Ödenen Hakediş' kartına yansır.")
    pay_def = [{"Hakediş No": "HK-01", "Dönem": "", "Tutar ($)": 0.0, "Durum": "Hazırlanıyor", "Tarih": ""}]
    pay = storage.load_table(conn, "payments", pay_def)
    pay_ed = st.data_editor(pay, width="stretch", hide_index=True, num_rows="dynamic",
                            disabled=not ADMIN, key="pay_ed",
                            column_config={"Durum": st.column_config.SelectboxColumn(options=["Hazırlanıyor", "Onaylandı", "Ödendi"]),
                                           "Tutar ($)": st.column_config.NumberColumn(format="$%d")})
    if ADMIN and not pay_ed.equals(pay):
        storage.save_table(conn, "payments", pay_ed); st.rerun()

elif page == "Risk & Kalite":
    st.markdown('<div style="background:linear-gradient(90deg,rgba(251,113,133,.10),rgba(34,211,238,.05));'
                'border:1px solid #12324a;border-radius:12px;padding:12px 16px;font-size:12.5px;'
                'color:#cfe3f7;margin-bottom:14px">⚠️ <b>Risk kaydı</b> olası sorunları (olasılık × etki = skor) '
                've <b>kalite uygunsuzluklarını (NCR)</b> tek yerden izler. Skoru yüksek riskleri önceliklendirin.</div>',
                unsafe_allow_html=True)

    risk_def = [{"Risk": "Evirici tedarik gecikmesi", "Olasılık (1-5)": 3, "Etki (1-5)": 4,
                 "Aksiyon": "Tedarikçi ile haftalık takip", "Sorumlu": "Satınalma", "Durum": "Açık"}]
    risks = storage.load_table(conn, "risks", risk_def)
    ncr_def = [{"NCR No": "NCR-001", "Konu": "", "Disiplin": "", "Durum": "Açık", "Tarih": ""}]
    ncr = storage.load_table(conn, "ncr", ncr_def)

    # özet kartlar
    rk = risks.copy()
    if not rk.empty and "Olasılık (1-5)" in rk.columns:
        rk["Skor"] = (pd.to_numeric(rk["Olasılık (1-5)"], errors="coerce").fillna(0)
                      * pd.to_numeric(rk["Etki (1-5)"], errors="coerce").fillna(0))
    else:
        rk["Skor"] = []
    yuksek = int((rk["Skor"] >= 12).sum()) if len(rk) else 0
    acik_ncr = int((ncr["Durum"] != "Kapandı").sum()) if not ncr.empty and "Durum" in ncr.columns else 0
    cS = st.columns(3)
    cS[0].metric("Toplam Risk", len(rk))
    cS[1].metric("Yüksek Risk (skor ≥12)", yuksek)
    cS[2].metric("Açık NCR", acik_ncr)

    edit_rk = st.toggle("✏️ Düzenleme modu", value=False, key="rk_edit",
                        help="Açıkken risk ve NCR tablolarını düzenleyebilirsiniz.") if ADMIN else False

    st.markdown('<div class="panel-ttl">Risk Kaydı (Risk Register)</div>', unsafe_allow_html=True)
    if edit_rk:
        risks_ed = st.data_editor(risks, width="stretch", hide_index=True, num_rows="dynamic", key="risk_ed",
                                  column_config={
                                      "Olasılık (1-5)": st.column_config.NumberColumn(min_value=1, max_value=5, step=1),
                                      "Etki (1-5)": st.column_config.NumberColumn(min_value=1, max_value=5, step=1),
                                      "Durum": st.column_config.SelectboxColumn(options=["Açık", "İzleniyor", "Kapandı"])})
        if not risks_ed.equals(risks):
            storage.save_table(conn, "risks", risks_ed); st.rerun()
    else:
        rows = ""
        for _, r in rk.sort_values("Skor", ascending=False).iterrows():
            sk = r["Skor"]
            col = "#fb7185" if sk >= 12 else ("#fbbf24" if sk >= 6 else "#34d399")
            dcol = {"Açık": "#fb7185", "İzleniyor": "#fbbf24", "Kapandı": "#34d399"}.get(str(r.get("Durum", "")), "#5f7a99")
            rows += (f'<tr><td class="mx-name">{r.get("Risk","")}</td>'
                     f'<td style="text-align:center;color:#9fc3e0">{int(r.get("Olasılık (1-5)",0) or 0)}</td>'
                     f'<td style="text-align:center;color:#9fc3e0">{int(r.get("Etki (1-5)",0) or 0)}</td>'
                     f'<td style="text-align:center"><span class="mx-pill" style="background:{col}22;color:{col}">{int(sk)}</span></td>'
                     f'<td style="color:#c7e8e4;font-size:11px">{r.get("Aksiyon","")}</td>'
                     f'<td style="color:#9fc3e0;font-size:11px">{r.get("Sorumlu","")}</td>'
                     f'<td style="text-align:center;color:{dcol};font-weight:800;font-size:11px">{r.get("Durum","")}</td></tr>')
        st.markdown(f'<table class="mx"><tr><th>RİSK</th><th style="text-align:center">OLASILIK</th>'
                    f'<th style="text-align:center">ETKİ</th><th style="text-align:center">SKOR</th>'
                    f'<th>AKSİYON</th><th>SORUMLU</th><th style="text-align:center">DURUM</th></tr>{rows}</table>',
                    unsafe_allow_html=True)

    st.markdown('<div class="panel-ttl">Kalite — Uygunsuzluk (NCR) Kaydı</div>', unsafe_allow_html=True)
    if edit_rk:
        ncr_ed = st.data_editor(ncr, width="stretch", hide_index=True, num_rows="dynamic", key="ncr_ed",
                                column_config={"Durum": st.column_config.SelectboxColumn(options=["Açık", "Düzeltiliyor", "Kapandı"])})
        if not ncr_ed.equals(ncr):
            storage.save_table(conn, "ncr", ncr_ed); st.rerun()
    else:
        rows = ""
        for _, r in ncr.iterrows():
            dcol = {"Açık": "#fb7185", "Düzeltiliyor": "#fbbf24", "Kapandı": "#34d399"}.get(str(r.get("Durum", "")), "#5f7a99")
            rows += (f'<tr><td class="mx-name">{r.get("NCR No","")}</td>'
                     f'<td style="color:#c7e8e4">{r.get("Konu","")}</td>'
                     f'<td style="color:#9fc3e0;font-size:11px">{r.get("Disiplin","")}</td>'
                     f'<td style="color:#5f7a99;font-size:11px">{r.get("Tarih","")}</td>'
                     f'<td style="text-align:center;color:{dcol};font-weight:800;font-size:11px">{r.get("Durum","")}</td></tr>')
        st.markdown(f'<table class="mx"><tr><th>NCR NO</th><th>KONU</th><th>DİSİPLİN</th>'
                    f'<th>TARİH</th><th style="text-align:center">DURUM</th></tr>{rows}</table>',
                    unsafe_allow_html=True)
    if not ADMIN:
        st.caption("Görüntüleyici modu — düzenleme için yönetici girişi gerekir.")

elif page == "Baseline":
    bl = storage.load_baseline(conn)
    if bl.empty:
        st.info("Henüz baseline (referans plan) dondurulmamış. Aşağıdaki düğmeyle mevcut planı referans olarak kaydedin; "
                "sonra revizeleri bununla karşılaştırabilirsiniz.")
    else:
        ts = bl["ts"].iloc[0] if "ts" in bl.columns and len(bl) else "—"
        st.success(f"Referans plan dondurulma tarihi: **{ts}**")
    if ADMIN:
        if st.button("📌 Mevcut planı Baseline olarak dondur", type="primary"):
            storage.freeze_baseline(conn, st.session_state.df)
            st.toast("Baseline donduruldu."); st.rerun()
    if not bl.empty:
        cur = base[["id", "disc", "name", "plan", "tutar"]].merge(
            bl.rename(columns={"plan": "plan_bl", "tutar": "tutar_bl"})[["id", "plan_bl", "tutar_bl"]], on="id", how="left")
        cur["Δ Plan"] = cur["plan"] - cur["plan_bl"].fillna(cur["plan"])
        cur["Δ Bütçe"] = cur["tutar"] - cur["tutar_bl"].fillna(cur["tutar"])
        chg = cur[(cur["Δ Plan"].abs() > 1e-6) | (cur["Δ Bütçe"].abs() > 1e-6)]
        c = st.columns(3)
        c[0].metric("Baseline Bütçe", core.fmt_money(float(bl["tutar"].sum())))
        c[1].metric("Güncel Bütçe", core.fmt_money(float(base["tutar"].sum())))
        c[2].metric("Bütçe Değişimi", core.fmt_money(float(base["tutar"].sum() - bl["tutar"].sum())))
        st.markdown('<div class="panel-ttl">Baseline\'a Göre Değişen Kalemler</div>', unsafe_allow_html=True)
        if chg.empty:
            st.caption("Baseline'dan bu yana değişiklik yok.")
        else:
            st.dataframe(chg[["disc", "name", "plan_bl", "plan", "Δ Plan", "Δ Bütçe"]].rename(columns={
                "disc": "Disiplin", "name": "Poz", "plan_bl": "Plan (baseline)", "plan": "Plan (güncel)"}),
                width="stretch", hide_index=True)

elif page == "Kayıt Defteri":
    st.markdown('<div class="panel-ttl">Değişiklik Günlüğü (Audit Trail)</div>', unsafe_allow_html=True)
    cl = storage.load_changelog(conn)
    if cl.empty:
        st.caption("Henüz kayıt yok. İş Kalemleri'nde değer değiştirdikçe burada tarih/kullanıcı/eski→yeni olarak listelenir.")
    else:
        st.dataframe(cl.rename(columns={"ts": "Tarih", "usr": "Kullanıcı", "item": "Poz",
                                        "field": "Alan", "oldv": "Eski", "newv": "Yeni"}),
                     width="stretch", hide_index=True, height=520)

elif page == "Stok":
    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Malzeme Akışı — Sipariş → Sevk → Sahada → Montaj</div>', unsafe_allow_html=True)
        st.plotly_chart(charts.stock_chart(st.session_state.stock), width="stretch", config=PLOT)
    sdf = st.session_state.stock.copy()
    edited_s = st.data_editor(sdf, width="stretch", hide_index=True, num_rows="fixed",
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
    edited_h = st.data_editor(hdf, width="stretch", hide_index=True, num_rows="fixed",
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
            width="stretch", type="primary")
        st.caption("7 sayfa: Özet · İş Kalemleri · Disiplin · Grup · Geciken İşler · Stok · İSG")
    with d2:
        with st.spinner("PDF hazırlanıyor…"):
            pdf = exports.build_pdf(state)
        st.download_button("⬇️ PDF rapor indir", pdf, file_name=f"ARAKONAK_GES_{ts}.pdf",
            mime="application/pdf", width="stretch", type="primary")
        st.caption("Logolu yönetici raporu: KPI · grafikler · geciken işler")

elif page == "Veri":
    st.warning("Streamlit Cloud deposu geçici olabilir. **Kalıcı güvence için düzenli Tam Yedek (JSON) indirin** "
               "veya aşağıdan Google Sheets kalıcı senkronunu kurun.")
    b1, b2 = st.columns(2)
    with b1:
        full = json.dumps(storage.export_all(conn), ensure_ascii=False, indent=1).encode("utf-8")
        st.download_button("⬇️ TAM YEDEK (.json) indir — tüm veriler", full,
                           file_name=f"arakonak_TAMYEDEK_{datetime.now():%Y%m%d_%H%M}.json",
                           mime="application/json", width="stretch", type="primary")
        st.caption("İş kalemleri, stok, İSG, günlük kayıtlar, baseline, risk/NCR/VO/hakediş, kayıt defteri — hepsi.")
    with b2:
        csv = st.session_state.df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Sadece iş kalemleri (CSV)", csv, file_name="arakonak_iskalemleri.csv",
                           mime="text/csv", width="stretch")

    if ADMIN:
        st.divider()
        st.markdown("**Geri yükleme**")
        upj = st.file_uploader("Tam yedek (.json) geri yükle", type=["json"])
        if upj is not None:
            try:
                storage.import_all(conn, json.loads(upj.getvalue().decode("utf-8")))
                for kk in ("df", "stock", "hse"):
                    st.session_state.pop(kk, None)
                for kk in [x for x in list(st.session_state.keys()) if str(x).startswith(("ep_", "er_", "ea_"))]:
                    st.session_state.pop(kk, None)
                st.success("Tam yedek geri yüklendi."); st.rerun()
            except Exception as ex:
                st.error(f"Okunamadı: {ex}")
        up = st.file_uploader("Sadece iş kalemleri CSV geri yükle", type=["csv"])
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
                    st.session_state.df = cur.reset_index()
                    for kk in [x for x in list(st.session_state.keys()) if str(x).startswith(("ep_", "er_", "ea_"))]:
                        st.session_state.pop(kk, None)
                    persist_progress()
                    st.success("Geri yüklendi."); st.rerun()
            except Exception as ex:
                st.error(f"Okunamadı: {ex}")

    st.divider()
    with st.expander("☁️ Google Sheets ile kalıcı senkron (opsiyonel kurulum)"):
        st.markdown(
            "Streamlit Cloud verisi geçici olduğundan, kalıcılık için bir **Google servis hesabı** bağlayabilirsiniz:\n\n"
            "1. Google Cloud'da bir **servis hesabı** oluşturup JSON anahtarını indirin.\n"
            "2. Bir Google Sheet açıp bu hesabın e-postasıyla **paylaşın** (Editör).\n"
            "3. Streamlit → **Manage app → Settings → Secrets** içine anahtarı `[gcp_service_account]` başlığıyla ve "
            "`sheet_id = \"...\"` satırını ekleyin.\n\n"
            "Bağlantı kurulduğunda uygulama her kayıtta Sheet'e yazar. Anahtar yoksa uygulama SQLite + yedekle sorunsuz çalışır.")
        connected = False
        try:
            connected = "gcp_service_account" in st.secrets
        except Exception:
            connected = False
        st.caption(("🟢 Google Sheets anahtarı bulundu." if connected
                    else "⚪ Henüz Google Sheets anahtarı eklenmemiş — yerel (SQLite + yedek) modda çalışıyor."))

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
