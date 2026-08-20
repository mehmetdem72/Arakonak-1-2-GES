"""ARAKONAK GES — Kullanıcı girişi (uygulama seviyesi kapı).

DÜRÜST GÜVENLİK NOTU:
- Bu, PBKDF2-HMAC-SHA256 ile HASH'lenmiş parolalar + rol (admin/görüntüleyici)
  kullanan bir 'uygulama kapısı'dır. Kurumsal SSO/SAML/2FA DEĞİLDİR.
- Parola hash'leme yalnızca Python standart kütüphanesini kullanır (hashlib);
  harici paket (bcrypt vb.) GEREKTİRMEZ — böylece dağıtımda 'ModuleNotFound' olmaz.
- Parolalar kodda düz metin tutulmaz; Streamlit 'Secrets' içinde saklamanız önerilir.
  Secrets yoksa aşağıdaki VARSAYILAN hesaplar devreye girer — DAĞITIMDAN ÖNCE DEĞİŞTİRİN.
"""
from __future__ import annotations

import hashlib
import hmac
import os

import streamlit as st

_ITER = 200_000  # PBKDF2 iterasyon sayısı


def hash_password(plain: str) -> str:
    """Kendine yeten parola hash'i üretir: 'pbkdf2$<iter>$<salt_hex>$<hash_hex>'."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, _ITER)
    return f"pbkdf2${_ITER}${salt.hex()}${dk.hex()}"


def _verify(plain: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


# Varsayılan hesaplar (yalnızca Secrets tanımlı DEĞİLKEN kullanılır).
# Parolalar: admin → "arakonak2025", viewer → "viewer2025"  (LÜTFEN DEĞİŞTİRİN)
_DEFAULT_USERS = {
    "admin":  {"name": "Proje Müdürü", "role": "admin",  "hash": hash_password("arakonak2025")},
    "viewer": {"name": "İzleyici",     "role": "viewer", "hash": hash_password("viewer2025")},
}


def _users() -> dict:
    """Secrets'ta [auth.users] varsa onu, yoksa varsayılanları döndürür."""
    try:
        conf = st.secrets.get("auth", {}).get("users", None)
        if conf:
            return {u: dict(v) for u, v in conf.items()}
    except Exception:
        pass
    return _DEFAULT_USERS


def current_user():
    return st.session_state.get("auth_user")


def is_admin() -> bool:
    u = current_user()
    return bool(u and u.get("role") == "admin")


def logout():
    st.session_state.pop("auth_user", None)


def _logo_b64(black: bool = True):
    import base64
    from pathlib import Path
    here = Path(__file__).parent
    for c in (here / "assets" / "logo.svg", here / "logo.svg"):
        if c.exists():
            try:
                svg = c.read_text(encoding="utf-8")
                if black:  # NAS logosunu siyaha çevir (beyaz plaka üstünde görünür)
                    svg = svg.replace("fill:#fff", "fill:#0a0a0a").replace('fill="#fff"', 'fill="#0a0a0a"')
                return base64.b64encode(svg.encode()).decode()
            except Exception:
                return None
    return None


def login_gate() -> bool:
    """True → giriş yapılmış. False → giriş formu gösterildi, akış durdurulmalı."""
    if current_user():
        return True

    logo = _logo_b64(black=False)  # koyu panelde beyaz logo
    logo_html = (f'<img src="data:image/svg+xml;base64,{logo}" style="height:34px;display:block"/>'
                 if logo else '<div style="font-size:30px;color:#fff">⚡</div>')

    def _panels():
        out = ""
        for r in range(3):
            y = 130 + r * 46; sc = 1 + r * 0.34; off = r * 30
            for i in range(7):
                x = -40 + i * 118 * sc - off
                out += (f'<polygon points="{x:.0f},{y:.0f} {x+92*sc:.0f},{y:.0f} '
                        f'{x+110*sc:.0f},{y+34:.0f} {x+18*sc:.0f},{y+34:.0f}" '
                        f'fill="rgba(20,120,130,.18)" stroke="rgba(45,212,191,.5)" '
                        f'stroke-width="1" opacity="{.8-r*.12:.2f}"/>')
        return out

    st.markdown(f"""
    <style>
      section[data-testid="stSidebar"]{{display:none;}}
      [data-testid="stTextInputRevealButton"]{{display:none !important;}}
      header[data-testid="stHeader"]{{display:none;}}
      [data-testid="stAppViewContainer"]{{background:#0a141d;}}
      .block-container{{padding:0 !important;max-width:100% !important;}}
      [data-testid="stAppViewContainer"] .main .block-container{{padding-top:0 !important;}}

      /* SOL MARKA PANELİ */
      .lg-left{{position:relative;overflow:hidden;min-height:92vh;border-radius:0 26px 26px 0;
        background:linear-gradient(155deg,#04222b 0%,#063540 48%,#0a5560 100%);
        padding:46px 44px;display:flex;flex-direction:column;justify-content:space-between;}}
      .lg-grain{{position:absolute;inset:0;opacity:.5;
        background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),
        linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);background-size:40px 40px;
        -webkit-mask-image:radial-gradient(circle at 35% 25%,#000,transparent 78%);}}
      .lg-brand{{position:relative;z-index:3;}}
      .lg-lp{{display:inline-block;vertical-align:middle;background:rgba(255,255,255,.10);
        border:1px solid rgba(255,255,255,.16);border-radius:13px;padding:11px 14px;}}
      .lg-nm{{display:inline-block;vertical-align:middle;margin-left:15px;color:#eafffb;
        font-weight:800;font-size:17px;letter-spacing:.5px;}}
      .lg-nm small{{display:block;color:#8fd6cf;font-weight:600;font-size:10.5px;letter-spacing:2px;margin-top:2px;}}
      .lg-hero{{position:relative;z-index:3;}}
      .lg-hero h1{{color:#fff;font-size:31px;font-weight:900;line-height:1.18;letter-spacing:-.5px;margin:0;}}
      .lg-hero h1 span{{background:linear-gradient(90deg,#2dd4bf,#22d3ee);-webkit-background-clip:text;
        background-clip:text;color:transparent;}}
      .lg-hero p{{color:#bfeee9;font-size:13.5px;line-height:1.7;margin-top:14px;max-width:400px;}}
      .lg-stats{{position:relative;z-index:3;margin-top:22px;}}
      .lg-stat{{display:inline-block;vertical-align:top;margin-right:32px;}}
      .lg-stat .v{{color:#fff;font-size:21px;font-weight:900;}}
      .lg-stat .l{{color:#8fd6cf;font-size:10.5px;font-weight:600;margin-top:2px;}}
      .lg-foot{{position:relative;z-index:3;color:#7fb8b2;font-size:11px;
        border-top:1px solid rgba(255,255,255,.1);padding-top:14px;}}

      /* SAĞ FORM */
      .lg-formwrap{{padding:8vh 8% 4vh;}}
      .lg-secure{{display:inline-block;color:#2dd4bf;font-size:11px;font-weight:700;
        background:rgba(45,212,191,.1);border:1px solid rgba(45,212,191,.25);
        padding:5px 12px;border-radius:999px;margin-bottom:18px;}}
      .lg-wel{{color:#e6f4f4;font-size:26px;font-weight:800;letter-spacing:-.3px;}}
      .lg-wsub{{color:#7fb0b3;font-size:13.5px;margin:6px 0 26px;}}
      [data-testid="stForm"]{{border:none !important;background:transparent !important;padding:0 !important;}}
      [data-testid="stForm"] label{{color:#8fb3b8 !important;font-weight:600 !important;
        font-size:12px !important;letter-spacing:.3px;text-transform:uppercase;}}
      [data-testid="stForm"] input{{background:#0c1d29 !important;border:1px solid #1c3a44 !important;
        border-radius:11px !important;color:#e6f4f4 !important;font-weight:500 !important;height:48px;}}
      [data-testid="stForm"] div[data-baseweb="input"]{{background:transparent !important;border:none !important;}}
      [data-testid="stForm"] div[data-baseweb="base-input"]{{background:transparent !important;}}
      [data-testid="stForm"] .stFormSubmitButton button{{width:100%;height:50px;border-radius:12px;
        background:linear-gradient(120deg,#0e7d8c,#14b8a6 55%,#22d3ee) !important;color:#04222b !important;
        border:none !important;font-weight:800 !important;font-size:15px !important;
        box-shadow:0 14px 30px rgba(20,184,166,.32) !important;transition:transform .15s,box-shadow .15s;}}
      [data-testid="stForm"] .stFormSubmitButton button:hover{{transform:translateY(-2px);
        box-shadow:0 20px 38px rgba(20,184,166,.45) !important;}}
      .lg-hint{{text-align:center;color:#5f7a7f;font-size:11.5px;margin-top:20px;}}
      [data-testid="stAlert"]{{background:rgba(251,113,133,.12) !important;border:1px solid rgba(251,113,133,.4) !important;
        border-radius:11px !important;color:#fecdd3 !important;}}
      [data-testid="stAlert"] *{{color:#fecdd3 !important;}}
    </style>
    """, unsafe_allow_html=True)

    L, R = st.columns([1, 1], gap="large")
    with L:
        st.markdown(f"""
        <div class="lg-left">
          <div class="lg-grain"></div>
          <svg style="position:absolute;left:0;right:0;bottom:-10px;width:100%;height:260px"
               viewBox="0 0 560 260" preserveAspectRatio="none">
            <circle cx="450" cy="55" r="50" fill="#14b8a6" opacity=".18"/>
            <circle cx="450" cy="55" r="30" fill="#2dd4bf" opacity=".28"/>
            {_panels()}
          </svg>
          <div class="lg-brand"><span class="lg-lp">{logo_html}</span>
            <span class="lg-nm">NAS ENERJİ A.Ş.<small>EPC · PROJE KONTROL</small></span></div>
          <div class="lg-hero"><h1>Güneşten<br><span>veriye, kontrole.</span></h1>
            <p>ARAKONAK GES 88,14 MWp güneş santralinin ilerleme, bütçe ve
               performansını tek panelden yönetin.</p>
            <div class="lg-stats">
              <div class="lg-stat"><div class="v">88,14</div><div class="l">MWp DC</div></div>
              <div class="lg-stat"><div class="v">$14.43M</div><div class="l">EPC BÜTÇE</div></div>
              <div class="lg-stat"><div class="v">197</div><div class="l">İŞ KALEMİ</div></div>
            </div>
          </div>
          <div class="lg-foot">© 2026 NAS ENERJİ A.Ş. · Muş / Bulanık · Tüm hakları saklıdır.</div>
        </div>""", unsafe_allow_html=True)
    with R:
        st.markdown('<div class="lg-formwrap">', unsafe_allow_html=True)
        st.markdown('<div class="lg-secure">🔒 GÜVENLİ ERİŞİM</div>'
                    '<div class="lg-wel">Oturum Aç</div>'
                    '<div class="lg-wsub">ARAKONAK GES proje kontrol panosuna hoş geldiniz.</div>',
                    unsafe_allow_html=True)
        with st.form("login_form"):
            usr = st.text_input("Kullanıcı adı", autocomplete="username", placeholder="kullanıcı adınızı girin")
            pw = st.text_input("Parola", type="password", autocomplete="current-password", placeholder="parolanız")
            ok = st.form_submit_button("Giriş Yap  →", width="stretch")
        st.markdown('<div class="lg-hint">Erişim yalnızca yetkili proje personeline açıktır.</div>',
                    unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if ok:
            rec = _users().get(usr.strip())
            if rec and _verify(pw, rec.get("hash", "")):
                st.session_state.auth_user = {
                    "username": usr.strip(),
                    "name": rec.get("name", usr.strip()),
                    "role": rec.get("role", "viewer"),
                }
                st.rerun()
            elif not usr.strip() or not pw:
                st.warning("Lütfen kullanıcı adı ve parolayı girin.")
            elif not rec:
                st.error("❌ Böyle bir kullanıcı bulunamadı.")
            else:
                st.error("❌ Hatalı şifre girdiniz. Lütfen tekrar deneyin.")
    return False
