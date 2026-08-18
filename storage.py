"""ARAKONAK GES — Kalıcı veri katmanı (SQLite).

DÜRÜST NOT: Streamlit Community Cloud dosya sistemi 'geçici'dir; uygulama uykuya
dalıp yeniden başladığında SQLite dosyası SIFIRLANABİLİR. Bu yüzden:
  1) SQLite oturumlar/sekmeler arası akıcı kalıcılık sağlar (yerelde tam kalıcı),
  2) 'Veri' sekmesindeki Excel/CSV dışa-içe aktarma GERÇEK yedeğinizdir,
  3) Kalıcı bulut için harici DB (Postgres/Supabase) bağlanabilir (README'ye bakın).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

import core

DB_DIR = Path("data")
DB_PATH = DB_DIR / "arakonak.db"


def get_conn(path: str | Path = DB_PATH) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS progress(
        id TEXT PRIMARY KEY, grp TEXT, disc TEXT, name TEXT, unit TEXT,
        qty REAL, up REAL, plan REAL, real REAL, ac REAL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS stock(
        id TEXT PRIMARY KEY, name TEXT, unit TEXT, ordered REAL, delivered REAL,
        onsite REAL, installed REAL, remaining REAL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS hse(
        id TEXT PRIMARY KEY, label TEXT, value REAL, unit TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS snapshots(
        ts TEXT, scope TEXT DEFAULT 'ALL', pv_pct REAL, ev_pct REAL, ac_usd REAL, bac REAL, note TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS baseline(
        id TEXT PRIMARY KEY, plan REAL, tutar REAL, ts TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS changelog(
        ts TEXT, usr TEXT, item TEXT, field TEXT, oldv TEXT, newv TEXT)""")
    # eski tablolara 'scope' sütunu ekle (geçiş)
    try:
        cols = [r[1] for r in cur.execute("PRAGMA table_info(snapshots)").fetchall()]
        if "scope" not in cols:
            cur.execute("ALTER TABLE snapshots ADD COLUMN scope TEXT DEFAULT 'ALL'")
    except Exception:
        pass
    conn.commit()
    if cur.execute("SELECT COUNT(*) FROM progress").fetchone()[0] == 0:
        seed_all(conn)


def seed_all(conn: sqlite3.Connection) -> None:
    from seed_data import SEED_STOCK, SEED_HSE
    df = core.seed_df()
    df.to_sql("progress", conn, if_exists="replace", index=False)
    pd.DataFrame(SEED_STOCK).to_sql("stock", conn, if_exists="replace", index=False)
    pd.DataFrame(SEED_HSE).to_sql("hse", conn, if_exists="replace", index=False)
    conn.execute("DELETE FROM snapshots")
    _ensure_setting(conn, "proj_name", "ARAKONAK GES")
    _ensure_setting(conn, "proj_loc", "Muş / Bulanık")
    _ensure_setting(conn, "start", (pd.Timestamp.today().normalize() - pd.Timedelta(days=60)).strftime("%Y-%m-%d"))
    _ensure_setting(conn, "end", (pd.Timestamp.today().normalize() + pd.Timedelta(days=300)).strftime("%Y-%m-%d"))
    conn.commit()


def _ensure_setting(conn, k, v):
    if conn.execute("SELECT 1 FROM settings WHERE k=?", (k,)).fetchone() is None:
        conn.execute("INSERT INTO settings(k,v) VALUES(?,?)", (k, json.dumps(v)))


# ── Progress ──
def load_progress(conn) -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM progress", conn)
    if "ac" not in df.columns:
        df["ac"] = 0.0
    for c in ("qty", "up", "plan", "real", "ac"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df


def save_progress(conn, df: pd.DataFrame) -> None:
    cols = ["id", "grp", "disc", "name", "unit", "qty", "up", "plan", "real", "ac"]
    df[cols].to_sql("progress", conn, if_exists="replace", index=False)
    conn.commit()


# ── Stock / HSE ──
def load_stock(conn) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM stock", conn)


def save_stock(conn, df: pd.DataFrame) -> None:
    df.to_sql("stock", conn, if_exists="replace", index=False); conn.commit()


def load_hse(conn) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM hse", conn)


def save_hse(conn, df: pd.DataFrame) -> None:
    df.to_sql("hse", conn, if_exists="replace", index=False); conn.commit()


# ── Settings ──
def get_setting(conn, k, default=None):
    row = conn.execute("SELECT v FROM settings WHERE k=?", (k,)).fetchone()
    return json.loads(row[0]) if row else default


def set_setting(conn, k, v):
    conn.execute("INSERT INTO settings(k,v) VALUES(?,?) "
                 "ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, json.dumps(v)))
    conn.commit()


# ── Snapshots ──
def add_snapshot(conn, pv_pct, ev_pct, ac_usd, bac, note="", scope="ALL"):
    conn.execute("INSERT INTO snapshots(ts,scope,pv_pct,ev_pct,ac_usd,bac,note) VALUES(?,?,?,?,?,?,?)",
                 (pd.Timestamp.today().strftime("%Y-%m-%d %H:%M"), scope, float(pv_pct), float(ev_pct),
                  float(ac_usd), float(bac), note))
    conn.commit()


def record_daily(conn, per_scope: dict, note="günlük"):
    """Bugünün tarihine, her kapsam için tek satır olacak şekilde ilerlemeyi yazar (upsert).

    per_scope: {scope_key: {'pv':.., 'ev':.., 'ac':.., 'bac':..}, ...}
    Böylece her gün girilen değerler S-eğrisinde günlük nokta olur.
    """
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    now = pd.Timestamp.today().strftime("%Y-%m-%d %H:%M")
    cur = conn.cursor()
    for scope, m in per_scope.items():
        cur.execute("DELETE FROM snapshots WHERE substr(ts,1,10)=? AND scope=?", (today, scope))
        cur.execute("INSERT INTO snapshots(ts,scope,pv_pct,ev_pct,ac_usd,bac,note) VALUES(?,?,?,?,?,?,?)",
                    (now, scope, float(m["pv"]), float(m["ev"]), float(m["ac"]), float(m["bac"]), note))
    conn.commit()


def load_snapshots(conn, scope=None) -> pd.DataFrame:
    if scope is None:
        return pd.read_sql("SELECT * FROM snapshots ORDER BY ts", conn)
    return pd.read_sql("SELECT * FROM snapshots WHERE scope=? ORDER BY ts", conn, params=(scope,))


def clear_snapshots(conn):
    conn.execute("DELETE FROM snapshots"); conn.commit()


def reset_all(conn):
    seed_all(conn)


# ── Baseline (plan dondurma) ──
def freeze_baseline(conn, df: pd.DataFrame):
    d = df.copy()
    d["tutar"] = d["qty"] * d["up"]
    d["ts"] = pd.Timestamp.today().strftime("%Y-%m-%d %H:%M")
    d[["id", "plan", "tutar", "ts"]].to_sql("baseline", conn, if_exists="replace", index=False)
    conn.commit()


def load_baseline(conn) -> pd.DataFrame:
    try:
        return pd.read_sql("SELECT * FROM baseline", conn)
    except Exception:
        return pd.DataFrame(columns=["id", "plan", "tutar", "ts"])


# ── Değişiklik günlüğü (audit) ──
def log_change(conn, usr, item, field, oldv, newv):
    conn.execute("INSERT INTO changelog(ts,usr,item,field,oldv,newv) VALUES(?,?,?,?,?,?)",
                 (pd.Timestamp.today().strftime("%Y-%m-%d %H:%M"), str(usr), str(item),
                  str(field), str(oldv), str(newv)))
    conn.commit()


def load_changelog(conn, limit=500) -> pd.DataFrame:
    try:
        return pd.read_sql(f"SELECT * FROM changelog ORDER BY ts DESC LIMIT {int(limit)}", conn)
    except Exception:
        return pd.DataFrame(columns=["ts", "usr", "item", "field", "oldv", "newv"])


# ── Genel tablo (risk / ncr / vo / hakediş) ──
def load_table(conn, name, default_rows=None) -> pd.DataFrame:
    try:
        df = pd.read_sql(f"SELECT * FROM {name}", conn)
        if len(df) == 0 and default_rows:
            df = pd.DataFrame(default_rows); df.to_sql(name, conn, if_exists="replace", index=False)
        return df
    except Exception:
        df = pd.DataFrame(default_rows or [])
        if len(df):
            df.to_sql(name, conn, if_exists="replace", index=False)
        return df


def save_table(conn, name, df: pd.DataFrame):
    df.to_sql(name, conn, if_exists="replace", index=False); conn.commit()


# ── Tam yedek (JSON) ──
def export_all(conn) -> dict:
    out = {}
    for t in ("progress", "stock", "hse", "snapshots", "baseline", "changelog",
              "risks", "ncr", "vo", "payments"):
        try:
            out[t] = pd.read_sql(f"SELECT * FROM {t}", conn).to_dict(orient="records")
        except Exception:
            out[t] = []
    try:
        out["settings"] = dict(conn.execute("SELECT k,v FROM settings").fetchall())
    except Exception:
        out["settings"] = {}
    out["_meta"] = {"app": "ARAKONAK GES v5", "exported": pd.Timestamp.today().strftime("%Y-%m-%d %H:%M")}
    return out


def import_all(conn, data: dict):
    for t in ("progress", "stock", "hse", "snapshots", "baseline", "changelog",
              "risks", "ncr", "vo", "payments"):
        if t in data and isinstance(data[t], list) and len(data[t]) > 0:
            df = pd.DataFrame(data[t])
            if not df.empty and len(df.columns) > 0:
                df.to_sql(t, conn, if_exists="replace", index=False)
    if "settings" in data and isinstance(data["settings"], dict):
        for k, v in data["settings"].items():
            conn.execute("INSERT INTO settings(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, v))
    conn.commit()
