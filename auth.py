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

    logo = _logo_b64(black=True)
    logo_html = (f'<img src="data:image/svg+xml;base64,{logo}" '
                 f'style="height:60px;display:block"/>'
                 if logo else '<div style="font-size:44px">⚡</div>')

    st.markdown(f"""
    <style>
      section[data-testid="stSidebar"]{{display:none;}}
      /* ★ Şifre göster/gizle butonunu gizle — 'visibility' yazısı sorununun kesin çözümü */
      [data-testid="stTextInputRevealButton"]{{display:none !important;}}
      [data-testid="stAppViewContainer"]{{
        background:
          radial-gradient(1100px 700px at 12% -5%, #0e7d8c 0%, transparent 52%),
          radial-gradient(900px 640px at 100% 12%, rgba(45,212,191,.35), transparent 55%),
          radial-gradient(1150px 780px at 60% 120%, rgba(34,211,238,.28), transparent 60%),
          linear-gradient(150deg,#04222b 0%, #06414f 45%, #0a6b76 100%);
        background-size:200% 200%; animation:bgshift 16s ease infinite;
      }}
      @keyframes bgshift{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}
      [data-testid="stAppViewContainer"]::before{{
        content:"";position:fixed;inset:0;pointer-events:none;opacity:.5;
        background-image:linear-gradient(rgba(255,255,255,.055) 1px,transparent 1px),
                         linear-gradient(90deg,rgba(255,255,255,.055) 1px,transparent 1px);
        background-size:44px 44px;
        -webkit-mask-image:radial-gradient(circle at 50% 40%,#000,transparent 75%);
                mask-image:radial-gradient(circle at 50% 40%,#000,transparent 75%);
      }}
      .block-container{{padding-top:8vh;max-width:520px;}}
      [data-testid="stForm"]{{
        background:linear-gradient(160deg,rgba(255,255,255,.16),rgba(255,255,255,.06));
        border:1px solid rgba(255,255,255,.26);border-radius:26px;padding:34px 34px 28px;
        box-shadow:0 30px 70px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.28);
        backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
      }}
      .login-brand{{text-align:center;margin-bottom:6px;}}
      .login-plate{{display:inline-flex;align-items:center;justify-content:center;
        background:#ffffff;border:1px solid rgba(255,255,255,.7);border-radius:22px;padding:16px 26px;
        box-shadow:0 14px 30px rgba(0,0,0,.28);}}
      .login-title{{font-family:'Inter',sans-serif;font-size:30px;font-weight:900;letter-spacing:.4px;margin:18px 0 2px;
        background:linear-gradient(90deg,#ffffff,#a7f3e8);-webkit-background-clip:text;background-clip:text;color:transparent;}}
      .login-sub{{font-family:'Inter',sans-serif;color:#c3ece9;font-weight:600;font-size:13px;margin-bottom:6px;}}
      .login-chips{{display:flex;gap:7px;justify-content:center;flex-wrap:wrap;margin:12px 0 20px;}}
      .login-chip{{font-family:'Inter',sans-serif;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.24);
        color:#e6fbf8;padding:4px 11px;border-radius:999px;font-size:11px;font-weight:700;}}
      [data-testid="stForm"] label{{color:#dff6f3 !important;font-weight:700 !important;font-size:12.5px !important;}}
      [data-testid="stForm"] input{{
        background:rgba(255,255,255,.96) !important;border-radius:12px !important;
        border:1px solid rgba(255,255,255,.55) !important;color:#0b2a33 !important;font-weight:600 !important;}}
      [data-testid="stForm"] div[data-baseweb="input"]{{border-radius:12px !important;background:transparent !important;
        border-color:transparent !important;}}
      [data-testid="stForm"] div[data-baseweb="base-input"]{{background:transparent !important;}}
      [data-testid="stForm"] .stFormSubmitButton button{{
        width:100%;background:linear-gradient(120deg,#14b8a6,#0ea5c4 55%,#22d3ee) !important;color:#04222b !important;
        border:none !important;border-radius:13px !important;padding:11px 0 !important;font-weight:900 !important;
        font-size:15px !important;letter-spacing:.4px;box-shadow:0 14px 28px rgba(20,184,166,.5) !important;
        transition:transform .15s, box-shadow .15s;}}
      [data-testid="stForm"] .stFormSubmitButton button:hover{{
        transform:translateY(-2px);box-shadow:0 20px 38px rgba(20,184,166,.62) !important;}}
      .login-foot{{text-align:center;color:#a7d9d5;font-size:11px;margin-top:14px;font-family:'Inter',sans-serif;}}
    </style>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        st.markdown(f"""
        <div class="login-brand">
          <div class="login-plate">{logo_html}</div>
          <div class="login-title">ARAKONAK GES</div>
          <div class="login-sub">Proje Kontrol Panosu · Güvenli Giriş</div>
          <div class="login-chips">
            <span class="login-chip">⚡ 88,14 MWp DC</span>
            <span class="login-chip">📍 Muş / Bulanık</span>
            <span class="login-chip">🔒 Yetkili Erişim</span>
          </div>
        </div>""", unsafe_allow_html=True)
        usr = st.text_input("Kullanıcı adı", autocomplete="username", placeholder="kullanıcı adınız")
        pw = st.text_input("Parola", type="password", autocomplete="current-password", placeholder="parolanız")
        ok = st.form_submit_button("Giriş Yap  →", use_container_width=True)
        st.markdown('<div class="login-foot">Test: admin / arakonak2025 · viewer / viewer2025 — '
                    'dağıtımdan önce Secrets ile değiştirin.</div>', unsafe_allow_html=True)

    if ok:
        rec = _users().get(usr.strip())
        if rec and _verify(pw, rec.get("hash", "")):
            st.session_state.auth_user = {
                "username": usr.strip(),
                "name": rec.get("name", usr.strip()),
                "role": rec.get("role", "viewer"),
            }
            st.rerun()
        else:
            st.error("Kullanıcı adı veya parola hatalı.")
    return False
