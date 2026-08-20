"""ARAKONAK GES — Çekirdek hesap motoru.

Bu modül Streamlit'ten BAĞIMSIZDIR (import etmez), böylece ayrı test edilebilir.
İçerik: satır zenginleştirme, EVM (Kazanılmış Değer) metrikleri, disiplin/grup
kırılımları, geciken iş tespiti ve S-eğrisi (baseline + snapshot) hesapları.
"""
from __future__ import annotations

import math
import pandas as pd

from seed_data import SEED_ROWS

GROUPS = ["GES-1 EPC", "GES-2 EPC", "ORTAK EPC"]
GROUP_SHORT = {"GES-1 EPC": "GES-1", "GES-2 EPC": "GES-2", "ORTAK EPC": "ORTAK"}
SCOPE_MAP = {"Tümü": "ALL", "GES-1": "GES-1 EPC", "GES-2": "GES-2 EPC", "ORTAK": "ORTAK EPC"}

COLS = ["id", "grp", "disc", "name", "unit", "qty", "up", "plan", "real"]


# ────────────────────────────── VERİ ──────────────────────────────
def seed_df() -> pd.DataFrame:
    """Tohum veriden temiz çalışma tablosu üretir. 'ac' (fiili maliyet) = 0 başlar."""
    df = pd.DataFrame(SEED_ROWS)[COLS].copy()
    for c in ("qty", "up", "plan", "real"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df["ac"] = 0.0  # fiili maliyet ($) — kullanıcı girer; girilmezse maliyet EVM'i 'veri yok'
    return df


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Her satır için türetilmiş sütunları hesaplar."""
    df = df.copy()
    if "ac" not in df.columns:
        df["ac"] = 0.0
    df["tutar"] = df["qty"] * df["up"]              # BAC (poz bütçesi)
    df["planW"] = df["tutar"] * df["plan"] / 100.0  # PV — Planlanan Değer
    df["realW"] = df["tutar"] * df["real"] / 100.0  # EV — Kazanılmış Değer
    df["comp"] = df["realW"]
    df["kalan"] = df["tutar"] - df["comp"]
    df["sapma"] = df["real"] - df["plan"]           # ilerleme sapması (puan)

    def durum(r):
        if r["real"] >= 100: return "TAMAMLANDI"
        if r["real"] <= 0:   return "BAŞLAMADI"
        if r["real"] < r["plan"] - 1e-9: return "GERİDE"
        return "DEVAM"

    df["durum"] = df.apply(durum, axis=1)
    return df


def scope_df(df: pd.DataFrame, scope: str) -> pd.DataFrame:
    return df if scope == "ALL" else df[df["grp"] == scope]


# ────────────────────────────── EVM ──────────────────────────────
def kpis(df: pd.DataFrame) -> dict:
    """Snapshot EVM metrikleri. Maliyet metrikleri yalnızca AC girilmişse üretilir."""
    bac   = float(df["tutar"].sum())
    ev    = float(df["realW"].sum())
    pv    = float(df["planW"].sum())
    ac    = float(df.get("ac", pd.Series(dtype=float)).sum())

    ilerleme = (ev / bac * 100) if bac else 0.0
    planPct  = (pv / bac * 100) if bac else 0.0
    sv  = ev - pv
    spi = (ev / pv) if pv else None

    has_cost = ac > 0
    cv   = (ev - ac) if has_cost else None
    cpi  = (ev / ac) if has_cost else None
    eac  = (bac / cpi) if (has_cost and cpi) else None
    etc  = (eac - ac) if (eac is not None) else None
    vac  = (bac - eac) if (eac is not None) else None
    tcpi = ((bac - ev) / (bac - ac)) if (has_cost and (bac - ac) != 0) else None

    return {
        "budget": bac, "comp": ev, "kalan": bac - ev,
        "ilerleme": ilerleme, "planPct": planPct,
        "PV": pv, "EV": ev, "AC": ac, "BAC": bac,
        "SV": sv, "SPI": spi, "spi": spi,           # 'spi' geriye dönük uyum
        "CV": cv, "CPI": cpi, "EAC": eac, "ETC": etc, "VAC": vac, "TCPI": tcpi,
        "has_cost": has_cost,
    }


def status_counts(df: pd.DataFrame):
    vc = df["durum"].value_counts().to_dict()
    return [(s, int(vc.get(s, 0))) for s in ["TAMAMLANDI", "DEVAM", "GERİDE", "BAŞLAMADI"]]


def disc_agg(df_all: pd.DataFrame, scope: str) -> pd.DataFrame:
    scoped = scope_df(df_all, scope)
    g = scoped.groupby("disc").agg(
        budget=("tutar", "sum"), comp=("comp", "sum"),
        planW=("planW", "sum"), realW=("realW", "sum"), ac=("ac", "sum"),
    ).reset_index()
    g = g[g["budget"] > 0].copy()
    g["planPct"] = g["planW"] / g["budget"] * 100
    g["realPct"] = g["realW"] / g["budget"] * 100
    g["compPct"] = g["comp"] / g["budget"] * 100
    g["sapma"]   = g["realPct"] - g["planPct"]

    bg = df_all.groupby(["disc", "grp"]).agg(b=("tutar", "sum"), c=("comp", "sum")).reset_index()
    breakdown = {}
    for disc in g["disc"]:
        parts, sub = [], bg[bg["disc"] == disc]
        for grp in GROUPS:
            row = sub[sub["grp"] == grp]
            if not row.empty and row["b"].iloc[0] > 0:
                parts.append(f"{GROUP_SHORT[grp]}: %{row['c'].iloc[0]/row['b'].iloc[0]*100:.0f}")
        breakdown[disc] = "   •   ".join(parts)
    g["breakdown"] = g["disc"].map(breakdown)
    return g.sort_values("budget", ascending=False)


def group_agg(df_all: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for grp in GROUPS:
        sub = df_all[df_all["grp"] == grp]
        b = float(sub["tutar"].sum())
        if b <= 0:
            continue
        rows.append({
            "grp": grp, "short": GROUP_SHORT[grp], "budget": b,
            "planPct": sub["planW"].sum() / b * 100,
            "realPct": sub["realW"].sum() / b * 100,
            "comp": float(sub["comp"].sum()), "kalan": b - float(sub["comp"].sum()),
        })
    return pd.DataFrame(rows)


def delayed_items(df: pd.DataFrame, top: int = 15) -> pd.DataFrame:
    """Geride kalan kalemleri, bütçeye göre ağırlıklı 'risk' skoruyla sıralar."""
    d = df[df["durum"] == "GERİDE"].copy()
    if d.empty:
        return d
    d["gecikme"] = (d["plan"] - d["real"]).clip(lower=0)          # puan
    d["riskUSD"] = d["tutar"] * d["gecikme"] / 100.0              # $ cinsinden etki
    return d.sort_values("riskUSD", ascending=False).head(top)


# ─────────────────────── S-EĞRİSİ (baseline + snapshot) ───────────────────────
def s_curve_baseline(bac: float, start, end, n: int = 24):
    """Proje başlangıç–bitişi arasında standart 'S' (kümülatif) baseline üretir.

    NOT: Bu MODELLENMİŞ bir baseline'dır (poz-poz zaman planı verisi olmadığından).
    Gerçek plan eğrisi için 'anlık görüntü' (snapshot) mekanizması kullanılır.
    """
    if not start or not end or end <= start:
        return pd.DataFrame(columns=["date", "planUSD", "planPct"])
    total_days = (end - start).days or 1
    xs = [start + pd.Timedelta(days=round(total_days * i / (n - 1))) for i in range(n)]
    out = []
    for dt in xs:
        t = ((dt - start).days) / total_days
        # yumuşak S: smootherstep
        s = 0 if t <= 0 else (1 if t >= 1 else t * t * t * (t * (t * 6 - 15) + 10))
        out.append({"date": pd.Timestamp(dt), "planUSD": bac * s, "planPct": s * 100})
    return pd.DataFrame(out)


def s_curve_from_snapshots(snaps: pd.DataFrame) -> pd.DataFrame:
    """Kaydedilmiş anlık görüntülerden gerçek PV/EV eğrisini kurar.

    snaps sütunları: ts (tarih), pv_pct, ev_pct, ac_usd, bac
    """
    if snaps is None or snaps.empty:
        return pd.DataFrame(columns=["date", "pvPct", "evPct", "acPct"])
    s = snaps.copy()
    s["date"] = pd.to_datetime(s["ts"]).dt.normalize()
    s = s.sort_values("date").groupby("date", as_index=False).last()
    s["pvPct"] = s["pv_pct"]
    s["evPct"] = s["ev_pct"]
    s["acPct"] = (s["ac_usd"] / s["bac"] * 100).where(s["bac"] > 0, 0)
    return s[["date", "pvPct", "evPct", "acPct"]]


# ────────────────────────────── BİÇİM ──────────────────────────────
def fmt_money(v) -> str:
    v = round(v or 0)
    if abs(v) >= 1e6: return f"${v/1e6:.2f}M"
    if abs(v) >= 1e3: return f"${v/1e3:.0f}K"
    return f"${v:.0f}"


def fmt_full(v) -> str:
    return f"${(v or 0):,.0f}".replace(",", ".")


def per_scope_kpis(base: pd.DataFrame) -> dict:
    """Her kapsam (ALL/GES-1/GES-2/ORTAK) için günlük kayıt metrikleri."""
    out = {}
    for label, scope in SCOPE_MAP.items():
        s = scope_df(base, scope)
        b = float(s["tutar"].sum())
        out[scope] = {
            "pv": (float(s["planW"].sum()) / b * 100) if b else 0.0,
            "ev": (float(s["realW"].sum()) / b * 100) if b else 0.0,
            "ac": float(s.get("ac", pd.Series(dtype=float)).sum()),
            "bac": b,
        }
    return out


def narrative(k: dict, scope_label: str = "Proje") -> str:
    """Otomatik yönetici özeti cümlesi."""
    ev, pl = k["ilerleme"], k["planPct"]
    diff = ev - pl
    yon = "planında" if abs(diff) < 0.5 else (f"{abs(diff):.0f} puan önde" if diff > 0 else f"{abs(diff):.0f} puan geride")
    spi_txt = "—" if k["SPI"] is None else f"{k['SPI']:.2f}"
    s = (f"{scope_label} <b>%{ev:.1f}</b> ilerlemede; plana göre <b>{yon}</b> (SPI {spi_txt}). ")
    if k["has_cost"] and k["CPI"]:
        cpi = k["CPI"]
        s += ("Maliyet performansı " + ("hedefin üzerinde" if cpi >= 1 else "hedefin altında")
              + f" (CPI {cpi:.2f}); tahmini toplam maliyet <b>{fmt_money(k['EAC'])}</b>. ")
    else:
        s += "Maliyet metrikleri için fiili maliyet (AC) girilmeli. "
    return s


def alerts(df: pd.DataFrame, k: dict) -> list:
    """Eşik uyarıları — (seviye, mesaj)."""
    out = []
    if k["SPI"] is not None and k["SPI"] < 0.9:
        out.append(("risk", f"Zaman performansı düşük: SPI {k['SPI']:.2f} (<0.90) — proje planın gerisinde."))
    if k["has_cost"] and k["CPI"] is not None and k["CPI"] < 0.9:
        out.append(("risk", f"Maliyet performansı düşük: CPI {k['CPI']:.2f} (<0.90) — bütçe aşımı riski."))
    d = df.copy()
    d["planW"] = d["tutar"] * d["plan"] / 100
    d["realW"] = d["tutar"] * d["real"] / 100
    geride = d[(d["real"] < d["plan"] - 10)]
    if len(geride) > 0:
        tut = fmt_money(float((geride["tutar"]).sum()))
        out.append(("izle", f"{len(geride)} iş kalemi planının 10+ puan gerisinde (toplam {tut})."))
    if k["has_cost"] and k["EAC"] and k["EAC"] > k["BAC"] * 1.05:
        out.append(("risk", f"Öngörülen maliyet bütçeyi aşıyor: EAC {fmt_money(k['EAC'])} > BAC {fmt_money(k['BAC'])}."))
    if not out:
        out.append(("iyi", "Kritik eşik ihlali yok. Proje kontrol altında."))
    return out


def spi_cpi_series(snaps: pd.DataFrame) -> pd.DataFrame:
    """Günlük snapshot'lardan SPI ve CPI zaman serisi."""
    if snaps is None or snaps.empty:
        return pd.DataFrame(columns=["date", "SPI", "CPI"])
    s = snaps.copy()
    s["date"] = pd.to_datetime(s["ts"]).dt.normalize()
    s = s.sort_values("ts").groupby("date").last().reset_index()
    s["SPI"] = (s["ev_pct"] / s["pv_pct"]).where(s["pv_pct"] > 0)
    ev_usd = s["ev_pct"] / 100 * s["bac"]
    s["CPI"] = (ev_usd / s["ac_usd"]).where(s["ac_usd"] > 0)
    return s[["date", "SPI", "CPI"]]


def cashflow_series(baseline_df: pd.DataFrame, snaps: pd.DataFrame) -> pd.DataFrame:
    """Aylık planlanan (baseline'dan) vs fiili (AC) harcama."""
    if baseline_df is None or baseline_df.empty:
        return pd.DataFrame(columns=["month", "plan", "actual"])
    b = baseline_df.copy()
    b["month"] = b["date"].dt.strftime("%Y-%m")
    b = b.groupby("month", sort=True).last().reset_index()
    b["plan"] = b["planUSD"].diff().fillna(b["planUSD"]).clip(lower=0)
    out = b[["month", "plan"]].copy()
    out["actual"] = 0.0
    if snaps is not None and not snaps.empty:
        s = snaps.copy()
        s["month"] = pd.to_datetime(s["ts"]).dt.strftime("%Y-%m")
        s = s.sort_values("ts").groupby("month").last().reset_index()
        s["actual"] = s["ac_usd"].diff().fillna(s["ac_usd"]).clip(lower=0)
        out = out.merge(s[["month", "actual"]], on="month", how="left", suffixes=("", "_a"))
        out["actual"] = out["actual_a"].fillna(0.0) if "actual_a" in out else 0.0
        out = out[["month", "plan", "actual"]]
    return out


def month_rows(start, end) -> list:
    """Proje başlangıç–bitiş arası aylık satır iskeleti (manuel plan programı için)."""
    if not start or not end or end <= start:
        start = pd.Timestamp.today().normalize().replace(day=1)
        end = start + pd.Timedelta(days=330)
    months = pd.period_range(pd.Timestamp(start), pd.Timestamp(end), freq="M")
    return [{"Ay": str(m), "Plan %": None, "Gerçek %": None} for m in months]


def manual_curve(planline_df: pd.DataFrame, bac: float):
    """Elle girilen aylık Plan/Gerçek %'den S-eğrisi baseline + snapshot üretir.

    Dönüş: (baseline_df[date,planUSD,planPct], snaps_df[date,pvPct,evPct,acPct])
    Girilmemiş (boş) hücreler atlanır; hiç veri yoksa boş döner (model'e düşülür).
    """
    empty_b = pd.DataFrame(columns=["date", "planUSD", "planPct"])
    empty_s = pd.DataFrame(columns=["date", "pvPct", "evPct", "acPct"])
    if planline_df is None or planline_df.empty or "Ay" not in planline_df.columns:
        return empty_b, empty_s
    d = planline_df.copy()
    d["date"] = pd.to_datetime(d["Ay"].astype(str) + "-01", errors="coerce")
    d = d.dropna(subset=["date"]).sort_values("date")
    pl = pd.to_numeric(d.get("Plan %"), errors="coerce")
    rl = pd.to_numeric(d.get("Gerçek %"), errors="coerce")
    base = d[pl.notna()]
    baseline = pd.DataFrame({"date": base["date"], "planPct": pl[pl.notna()].clip(0, 100)})
    baseline["planUSD"] = baseline["planPct"] / 100 * bac
    mask = pl.notna() | rl.notna()
    snaps = pd.DataFrame({
        "date": d["date"][mask],
        "pvPct": pl[mask].ffill().fillna(0).clip(0, 100),
        "evPct": rl[mask].ffill().fillna(0).clip(0, 100),
        "acPct": 0.0,
    })
    if baseline.empty and snaps.empty:
        return empty_b, empty_s
    return baseline[["date", "planUSD", "planPct"]], snaps
