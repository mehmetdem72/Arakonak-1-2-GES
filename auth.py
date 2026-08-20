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

    logo = _logo_b64(black=False)
    logo_html = (f'<img src="data:image/svg+xml;base64,{logo}" style="height:38px;display:block"/>'
                 if logo else '<div style="font-size:30px;color:#fff">\u26a1</div>')

    st.markdown(f"""
    <style>
      section[data-testid="stSidebar"]{{display:none;}}
      header[data-testid="stHeader"]{{display:none;}}
      [data-testid="stTextInputRevealButton"]{{display:none !important;}}
      [data-testid="stAppViewContainer"]{{
        background:radial-gradient(1100px 720px at 15% -8%, #0e7d8c, transparent 52%),
                   radial-gradient(900px 640px at 100% 10%, rgba(45,212,191,.30), transparent 55%),
                   linear-gradient(150deg,#04222b,#063540 46%,#0a5560);}}
      .block-container{{padding-top:3.5vh !important;padding-bottom:2vh !important;max-width:560px !important;}}
      .lg-card{{background:linear-gradient(160deg,rgba(255,255,255,.13),rgba(255,255,255,.045));
        border:1px solid rgba(255,255,255,.22);border-radius:24px;padding:34px 38px 30px;
        box-shadow:0 30px 70px rgba(0,0,0,.42);}}
      .lg-head{{text-align:center;margin-bottom:20px;}}
      .lg-lp{{display:inline-block;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);
        border-radius:15px;padding:12px 16px;}}
      .lg-firm{{color:#eafffb;font-weight:800;font-size:14px;letter-spacing:1.5px;margin-top:12px;}}
      .lg-firm small{{display:block;color:#8fd6cf;font-weight:600;font-size:10px;letter-spacing:2px;margin-top:3px;}}
      .lg-title{{color:#fff;font-size:24px;font-weight:900;margin-top:16px;letter-spacing:-.3px;}}
      .lg-sub{{color:#bfeee9;font-size:12.5px;margin-top:4px;}}
      .lg-chips{{text-align:center;margin:14px 0 6px;}}
      .lg-chip{{display:inline-block;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);
        color:#eafffb;font-size:10.5px;font-weight:700;padding:4px 10px;border-radius:999px;margin:0 3px;}}
      [data-testid="stForm"]{{border:none !important;background:transparent !important;padding:0 !important;}}
      [data-testid="stForm"] label{{color:#dff6f3 !important;font-weight:600 !important;font-size:12.5px !important;}}
      [data-testid="stForm"] input{{background:rgba(255,255,255,.96) !important;border:1px solid rgba(255,255,255,.5) !important;
        border-radius:11px !important;color:#0b2a33 !important;font-weight:600 !important;height:46px;}}
      [data-testid="stForm"] div[data-baseweb="input"],
      [data-testid="stForm"] div[data-baseweb="base-input"]{{background:transparent !important;border:none !important;}}
      [data-testid="stForm"] .stFormSubmitButton button{{width:100%;height:48px;border-radius:12px;margin-top:6px;
        background:linear-gradient(120deg,#0e7d8c,#14b8a6 55%,#22d3ee) !important;color:#04222b !important;
        border:none !important;font-weight:800 !important;font-size:15px !important;
        box-shadow:0 14px 30px rgba(20,184,166,.4) !important;transition:transform .15s,box-shadow .15s;}}
      [data-testid="stForm"] .stFormSubmitButton button:hover{{transform:translateY(-2px);
        box-shadow:0 20px 40px rgba(20,184,166,.55) !important;}}
      .lg-foot{{text-align:center;color:#9fd9d3;font-size:10.5px;margin-top:16px;}}
      [data-testid="stAlert"]{{background:rgba(251,113,133,.15) !important;
        border:1px solid rgba(251,113,133,.45) !important;border-radius:11px !important;margin-top:14px;}}
      [data-testid="stAlert"] *{{color:#fff0f2 !important;}}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="lg-card">
      <div class="lg-head">
        <span class="lg-lp">{logo_html}</span>
        <div class="lg-firm">NAS ENERJİ A.Ş.<small>EPC · PROJE KONTROL</small></div>
        <div class="lg-title">ARAKONAK GES</div>
        <div class="lg-sub">Proje Kontrol Panosu · Güvenli Giriş</div>
        <div class="lg-chips">
          <span class="lg-chip">\u26a1 88,14 MWp</span>
          <span class="lg-chip">\U0001F4CD Muş</span>
          <span class="lg-chip">\U0001F512 Yetkili Erişim</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        usr = st.text_input("Kullanıcı adı", autocomplete="username", placeholder="kullanıcı adınızı girin")
        pw = st.text_input("Parola", type="password", autocomplete="current-password", placeholder="parolanız")
        ok = st.form_submit_button("Giriş Yap  →", width="stretch")

    st.markdown('<div class="lg-foot">© 2026 NAS ENERJİ A.Ş. · Muş / Bulanık · '
                'Erişim yalnızca yetkili proje personeline açıktır.</div>', unsafe_allow_html=True)

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
