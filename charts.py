"""ARAKONAK GES — Plotly grafik kütüphanesi (kurumsal tema)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

import core

# ── Tema paleti (set_theme ile değişir) ──
C_OK = "#22d3ee"; C_OK_D = "#0891b2"; C_REM = "#fb7185"
C_PLAN = "#8b5cf6"; C_PLAN_D = "#7c3aed"; C_AMB = "#fbbf24"; C_PUR = "#a78bfa"
C_INK = "#e5edf7"; C_INK2 = "#a7bad4"; C_GRID = "rgba(255,255,255,.07)"
C_HOVER = "#0f1a2e"; C_TRACK = "rgba(255,255,255,.08)"; C_TICK = "#8fa3bd"
FONT = "Inter, 'Segoe UI', system-ui, sans-serif"


def set_theme(name="dark"):
    """Tüm grafik renklerini 'dark' veya 'light' temaya göre ayarlar."""
    global C_OK, C_OK_D, C_REM, C_PLAN, C_PLAN_D, C_AMB, C_PUR
    global C_INK, C_INK2, C_GRID, C_HOVER, C_TRACK, C_TICK
    if name == "light":
        C_OK, C_OK_D = "#0d9488", "#0a7268"
        C_REM, C_PLAN, C_PLAN_D = "#e11d48", "#6366f1", "#4f46e5"
        C_AMB, C_PUR = "#d97706", "#0891b2"
        C_INK, C_INK2 = "#0f2b3a", "#37525c"
        C_GRID = "rgba(15,43,58,.08)"; C_HOVER = "#0f2b3a"
        C_TRACK = "#eef2f6"; C_TICK = "#7a86b8"
    else:
        C_OK, C_OK_D = "#22d3ee", "#0891b2"
        C_REM, C_PLAN, C_PLAN_D = "#fb7185", "#a78bfa", "#7c3aed"
        C_AMB, C_PUR = "#fbbf24", "#67e8f9"
        C_INK, C_INK2 = "#dbeafe", "#9fc3e0"
        C_GRID = "rgba(34,211,238,.08)"; C_HOVER = "#0a1422"
        C_TRACK = "rgba(34,211,238,.10)"; C_TICK = "#5f7a99"


def _style(fig, height, corner=6, legend=True):
    fig.update_layout(
        height=height, margin=dict(l=8, r=14, t=30, b=8),
        font=dict(family=FONT, size=12, color=C_INK2),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=legend,
        legend=dict(orientation="h", y=1.17, x=0, xanchor="left",
                    font=dict(size=11, color=C_INK2), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=C_HOVER, font=dict(family=FONT, color="white", size=12),
                        bordercolor="rgba(255,255,255,.15)"), bargap=0.30)
    try: fig.update_layout(barcornerradius=corner)
    except Exception: pass
    fig.update_xaxes(showgrid=True, gridcolor=C_GRID, zeroline=False,
                     tickfont=dict(color=C_TICK, size=10), title=None)
    fig.update_yaxes(showgrid=False, zeroline=False,
                     tickfont=dict(color=C_INK2, size=10.5), title=None)
    return fig


def gauge(pct, plan_pct):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=round(pct, 1),
        number={"suffix": "%", "font": {"size": 38, "family": FONT, "color": C_INK}},
        delta={"reference": round(plan_pct, 1), "suffix": "%",
               "increasing": {"color": C_OK_D}, "decreasing": {"color": C_REM}, "font": {"size": 13}},
        gauge={"axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#334155",
                        "tickfont": {"size": 9, "color": "#8fa3bd"}},
               "bar": {"color": C_OK, "thickness": 0.30},
               "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
               "steps": [{"range": [0, 100], "color": C_TRACK}],
               "threshold": {"line": {"color": C_PLAN, "width": 3}, "thickness": 0.82,
                             "value": round(plan_pct, 1)}}))
    fig.update_layout(height=210, margin=dict(l=16, r=16, t=8, b=4),
                      font=dict(family=FONT), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def s_curve(baseline: pd.DataFrame, snaps: pd.DataFrame, today_pv, today_ev, today_ac=None):
    """Modellenmiş plan baseline + snapshot bazlı gerçek PV/EV/AC eğrisi + bugünkü nokta."""
    fig = go.Figure()
    if baseline is not None and not baseline.empty:
        fig.add_scatter(x=baseline["date"], y=baseline["planPct"], name="Plan Baseline (model)",
                        mode="lines", line=dict(color=C_PLAN, width=2.5, dash="dot"),
                        hovertemplate="%{x|%d.%m.%Y}<br>Plan %{y:.1f}%<extra></extra>")
    if snaps is not None and not snaps.empty:
        fig.add_scatter(x=snaps["date"], y=snaps["evPct"], name="Gerçek (EV)",
                        mode="lines+markers", line=dict(color=C_OK, width=3),
                        marker=dict(size=7), hovertemplate="%{x|%d.%m.%Y}<br>EV %{y:.1f}%<extra></extra>")
        fig.add_scatter(x=snaps["date"], y=snaps["pvPct"], name="Plan (girilen)",
                        mode="lines+markers", line=dict(color=C_PLAN_D, width=1.5, dash="dash"),
                        marker=dict(size=5), hovertemplate="%{x|%d.%m.%Y}<br>PV %{y:.1f}%<extra></extra>")
        if (snaps["acPct"] > 0).any():
            fig.add_scatter(x=snaps["date"], y=snaps["acPct"], name="Maliyet (AC)",
                            mode="lines+markers", line=dict(color=C_AMB, width=1.5),
                            marker=dict(size=5), hovertemplate="%{x|%d.%m.%Y}<br>AC %{y:.1f}%<extra></extra>")
    # bugünkü canlı nokta
    now = pd.Timestamp.today().normalize()
    fig.add_scatter(x=[now], y=[today_ev], name="Bugün (EV)", mode="markers",
                    marker=dict(size=13, color=C_OK, line=dict(color="white", width=2)),
                    hovertemplate="Bugün<br>EV %{y:.1f}%<extra></extra>")
    _style(fig, 360)
    fig.update_yaxes(range=[0, 105], ticksuffix="%", showgrid=True, gridcolor=C_GRID)
    return fig


def budget_by_disc(g: pd.DataFrame, scope: str):
    top = g.sort_values("budget", ascending=False).head(9).iloc[::-1]
    labels = [d if len(d) <= 24 else d[:22] + "…" for d in top["disc"]]
    comp = top["comp"].round().tolist()
    kalan = (top["budget"] - top["comp"]).round().tolist()
    pct = top["compPct"].tolist()
    text = [f"%{p:.0f}" if p >= 7 else "" for p in pct]
    if scope == "ALL":
        hover = [f"<b>{d}</b><br>Tamamlanan: {core.fmt_money(c)}  (%{p:.1f})<br>"
                 f"<span style='color:#9fb0e8'>{bd}</span>"
                 for d, c, p, bd in zip(top["disc"], comp, pct, top["breakdown"])]
    else:
        hover = [f"<b>{d}</b><br>Tamamlanan: {core.fmt_money(c)}  (%{p:.1f})"
                 for d, c, p in zip(top["disc"], comp, pct)]
    fig = go.Figure()
    fig.add_bar(y=labels, x=comp, orientation="h", name="Tamamlanan", marker=dict(color=C_OK),
                text=text, textposition="inside", insidetextanchor="middle",
                textfont=dict(color="white", size=12, family=FONT), hovertext=hover, hoverinfo="text")
    fig.add_bar(y=labels, x=kalan, orientation="h", name="Kalan",
                marker=dict(color="rgba(251,111,132,0.14)", line=dict(color="rgba(251,111,132,0.40)", width=1)),
                hovertext=[f"Kalan: {core.fmt_money(k)}" for k in kalan], hoverinfo="text")
    fig.update_layout(barmode="stack"); _style(fig, 400, corner=5)
    fig.update_xaxes(tickprefix="$", tickformat=".2s")
    return fig


def plan_vs_real(g: pd.DataFrame):
    d = g.sort_values(["realPct", "planPct"], ascending=True)
    labels = [x if len(x) <= 26 else x[:24] + "…" for x in d["disc"]]
    real_colors = [C_REM if r < p else C_OK for r, p in zip(d["realPct"], d["planPct"])]
    fig = go.Figure()
    fig.add_bar(y=labels, x=d["planPct"].round(1), orientation="h", name="Plan",
                marker=dict(color="rgba(14,116,144,.30)", line=dict(color=C_PLAN, width=1)))
    fig.add_bar(y=labels, x=d["realPct"].round(1), orientation="h", name="Gerçek",
                marker=dict(color=real_colors), text=[f"%{v:.0f}" for v in d["realPct"]],
                textposition="outside", textfont=dict(size=10, color=C_INK2, family=FONT), cliponaxis=False)
    fig.update_layout(barmode="group"); _style(fig, max(360, len(labels) * 30), corner=4)
    fig.update_xaxes(range=[0, 112], ticksuffix="%")
    return fig


def group_progress(gag: pd.DataFrame):
    if gag.empty:
        return _style(go.Figure(), 320)
    names = gag["short"].tolist()
    plan = gag["planPct"].round(1).tolist(); real = gag["realPct"].round(1).tolist()
    fig = go.Figure()
    fig.add_bar(x=names, y=plan, name="Plan",
                marker=dict(color="rgba(14,116,144,.30)", line=dict(color=C_PLAN, width=1)),
                text=[f"%{v:.1f}" for v in plan], textposition="outside",
                textfont=dict(color=C_PUR, family=FONT, size=11), cliponaxis=False)
    fig.add_bar(x=names, y=real, name="Gerçek", marker=dict(color=C_OK),
                text=[f"%{v:.1f}" for v in real], textposition="outside",
                textfont=dict(color=C_OK_D, family=FONT, size=11), cliponaxis=False)
    fig.update_layout(barmode="group"); _style(fig, 330, corner=6)
    fig.update_yaxes(range=[0, 112], ticksuffix="%", showgrid=True, gridcolor=C_GRID)
    fig.update_xaxes(tickfont=dict(color=C_INK2, size=12, family=FONT))
    return fig


def budget_treemap(df_all: pd.DataFrame):
    """Grup → Disiplin bütçe kırılımı (treemap), renk = ilerleme %."""
    d = df_all.copy()
    d["tutar"] = d["qty"] * d["up"]; d["comp"] = d["tutar"] * d["real"] / 100
    rows = d.groupby(["grp", "disc"]).agg(b=("tutar", "sum"), c=("comp", "sum")).reset_index()
    rows = rows[rows["b"] > 0]
    ids, labels, parents, values, colors = [], [], [], [], []
    for grp in core.GROUPS:
        sub = rows[rows["grp"] == grp]
        if sub.empty: continue
        gid = core.GROUP_SHORT[grp]
        ids.append(gid); labels.append(gid); parents.append(""); values.append(float(sub["b"].sum()))
        colors.append(float(sub["c"].sum() / sub["b"].sum() * 100) if sub["b"].sum() else 0)
        for _, r in sub.iterrows():
            nid = f"{gid}/{r['disc']}"
            ids.append(nid); labels.append(r["disc"]); parents.append(gid)
            values.append(float(r["b"])); colors.append(float(r["c"] / r["b"] * 100) if r["b"] else 0)
    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, branchvalues="total",
        marker=dict(colors=colors, colorscale=[[0, "#4c1d24"], [0.5, "#164e63"], [1, "#155e63"]],
                    cmin=0, cmax=100, line=dict(color="white", width=1)),
        textinfo="label+value+percent parent", tiling=dict(pad=2),
        hovertemplate="<b>%{label}</b><br>Bütçe: %{value:$,.0f}<br>İlerleme: %{color:.0f}%<extra></extra>"))
    fig.update_layout(height=430, margin=dict(l=4, r=4, t=8, b=4), font=dict(family=FONT),
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


def evm_waterfall(k: dict):
    """BAC → Kazanılan (EV) → Kalan görselleştirmesi."""
    fig = go.Figure(go.Waterfall(
        orientation="v", measure=["absolute", "relative", "total"],
        x=["Toplam Bütçe (BAC)", "Kazanılan (EV)", "Kalan İş"],
        y=[k["BAC"], -k["EV"], 0],
        text=[core.fmt_money(k["BAC"]), core.fmt_money(k["EV"]), core.fmt_money(k["kalan"])],
        textposition="outside", textfont=dict(family=FONT, size=12, color=C_INK),
        connector={"line": {"color": "rgba(15,21,53,.2)"}},
        increasing={"marker": {"color": C_OK}}, decreasing={"marker": {"color": C_OK}},
        totals={"marker": {"color": "rgba(251,111,132,0.26)", "line": {"color": C_REM, "width": 1}}}))
    _style(fig, 340, legend=False)
    fig.update_yaxes(tickprefix="$", tickformat=".2s")
    return fig


def pareto_remaining(df: pd.DataFrame, topn: int = 12):
    """Kalan işi en büyük olan disiplinler — Pareto (bar + kümülatif %)."""
    d = df.copy(); d["tutar"] = d["qty"] * d["up"]; d["comp"] = d["tutar"] * d["real"] / 100
    d["kalan"] = d["tutar"] - d["comp"]
    g = d.groupby("disc")["kalan"].sum().sort_values(ascending=False)
    g = g[g > 0].head(topn)
    if g.empty: return _style(go.Figure(), 320)
    total = g.sum(); cum = g.cumsum() / total * 100
    labels = [x if len(x) <= 18 else x[:16] + "…" for x in g.index]
    fig = go.Figure()
    fig.add_bar(x=labels, y=g.values, name="Kalan iş", marker=dict(color=C_PLAN),
                hovertext=[core.fmt_money(v) for v in g.values], hoverinfo="text+x")
    fig.add_scatter(x=labels, y=cum.values, name="Kümülatif %", yaxis="y2", mode="lines+markers",
                    line=dict(color=C_AMB, width=2.5), marker=dict(size=6))
    fig.update_layout(yaxis2=dict(overlaying="y", side="right", range=[0, 105],
                                  ticksuffix="%", showgrid=False, tickfont=dict(color=C_AMB, size=10)))
    _style(fig, 340)
    fig.update_yaxes(tickprefix="$", tickformat=".2s")
    fig.update_xaxes(tickangle=-35)
    return fig


def stock_chart(sdf: pd.DataFrame):
    """Stok akışı: Sipariş / Sevk / Sahada / Montajlı (yatay bar)."""
    d = sdf.copy().sort_values("ordered", ascending=True)
    labels = [x if len(x) <= 30 else x[:28] + "…" for x in d["name"]]
    fig = go.Figure()
    fig.add_bar(y=labels, x=d["installed"], orientation="h", name="Montajlı", marker=dict(color=C_OK))
    fig.add_bar(y=labels, x=(d["onsite"] - d["installed"]).clip(lower=0), orientation="h",
                name="Sahada (montaj bekleyen)", marker=dict(color=C_PLAN))
    fig.add_bar(y=labels, x=(d["delivered"] - d["onsite"]).clip(lower=0), orientation="h",
                name="Yolda/Depoda", marker=dict(color=C_AMB))
    fig.add_bar(y=labels, x=(d["ordered"] - d["delivered"]).clip(lower=0), orientation="h",
                name="Üretimde/Bekliyor",
                marker=dict(color="rgba(148,163,184,.25)", line=dict(color="#94a3b8", width=1)))
    fig.update_layout(barmode="stack"); _style(fig, max(300, len(labels) * 44), corner=4)
    return fig


def progress_donut(pct, plan_pct=None):
    """Açık kurumsal halka gösterge — Genel İlerleme."""
    pct = max(0, min(100, pct))
    fig = go.Figure(go.Pie(
        values=[pct, 100 - pct], hole=0.72, sort=False, direction="clockwise", rotation=0,
        marker=dict(colors=[C_OK, C_TRACK], line=dict(color="rgba(0,0,0,0)", width=0)),
        textinfo="none", hoverinfo="skip"))
    ann = [dict(text=f"<b>%{pct:.0f}</b>", x=0.5, y=0.52, font=dict(size=30, color=C_OK, family=FONT), showarrow=False),
           dict(text="EV / BAC", x=0.5, y=0.36, font=dict(size=11, color="#8aa", family=FONT), showarrow=False)]
    if plan_pct is not None:
        ann.append(dict(text=f"plan %{plan_pct:.0f}", x=0.5, y=0.20,
                        font=dict(size=10, color=C_PLAN, family=FONT), showarrow=False))
    fig.update_layout(annotations=ann, height=210, margin=dict(l=6, r=6, t=6, b=6),
                      showlegend=False, paper_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT))
    return fig


def monthly_combo(baseline, snaps):
    """Aylık plan vs gerçek + kümülatif çizgi (baseline'dan türetilmiş, snapshot varsa gerçek)."""
    if baseline is None or baseline.empty:
        return _style(go.Figure(), 300)
    b = baseline.copy()
    b["month"] = b["date"].dt.strftime("%b %y")
    # aylık kümülatif plan yüzdesi -> aylık artış
    b = b.groupby("month", sort=False).last().reset_index()
    b["plan_inc"] = b["planPct"].diff().fillna(b["planPct"]).clip(lower=0)
    fig = go.Figure()
    fig.add_bar(x=b["month"], y=b["plan_inc"], name="Aylık plan (Δ%)",
                marker=dict(color="rgba(99,102,241,.28)", line=dict(color=C_PLAN, width=1)))
    if snaps is not None and not snaps.empty:
        s = snaps.copy(); s["month"] = s["date"].dt.strftime("%b %y")
        fig.add_scatter(x=s["month"], y=s["evPct"], name="Gerçek kümülatif",
                        mode="lines+markers", line=dict(color=C_OK, width=3), marker=dict(size=7), yaxis="y2")
    fig.add_scatter(x=b["month"], y=b["planPct"], name="Plan kümülatif",
                    mode="lines", line=dict(color=C_PLAN, width=2, dash="dot"), yaxis="y2")
    fig.update_layout(yaxis2=dict(overlaying="y", side="right", range=[0, 105], ticksuffix="%",
                                  showgrid=False, tickfont=dict(color=C_INK2, size=10)))
    _style(fig, 300)
    fig.update_yaxes(ticksuffix="%", showgrid=True, gridcolor=C_GRID)
    return fig


def group_gauges(gag: pd.DataFrame):
    """Grup başına yarım-daire performans göstergeleri (tek figürde)."""
    if gag.empty:
        return _style(go.Figure(), 220)
    cols = ["#22d3ee", "#34d399", "#a78bfa"]  # camgobegi / zumrut / mor
    n = len(gag)
    fig = go.Figure()
    for i, (_, r) in enumerate(gag.iterrows()):
        fig.add_trace(go.Indicator(
            mode="gauge+number", value=round(r["realPct"], 0),
            number={"suffix": "%", "font": {"size": 26, "color": cols[i % 3], "family": FONT}},
            title={"text": f"<span style='color:#a7bad4;font-size:12px'>{r['short']}</span>"},
            domain={"row": 0, "column": i},
            gauge={"axis": {"range": [0, 100], "visible": False},
                   "bar": {"color": cols[i % 3], "thickness": 0.42},
                   "bgcolor": C_TRACK, "borderwidth": 0,
                   "threshold": {"line": {"color": "#fbbf24", "width": 3}, "thickness": 0.85,
                                 "value": round(r["planPct"], 0)}}))
    fig.update_layout(grid={"rows": 1, "columns": n, "pattern": "independent"},
                      height=220, margin=dict(l=16, r=16, t=30, b=6),
                      paper_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT))
    return fig


def heatmap_disc_group(df_all: pd.DataFrame, top: int = 8):
    """Disiplin × Grup ilerleme ısı haritası (renk = gerçekleşme %)."""
    d = df_all.copy()
    d["tutar"] = d["qty"] * d["up"]; d["comp"] = d["tutar"] * d["real"] / 100
    piv = d.groupby(["disc", "grp"]).agg(b=("tutar", "sum"), c=("comp", "sum")).reset_index()
    piv["pct"] = (piv["c"] / piv["b"] * 100).where(piv["b"] > 0)
    # en büyük bütçeli disiplinler
    order = d.groupby("disc")["tutar"].sum().sort_values(ascending=False).head(top).index.tolist()
    groups = core.GROUPS
    z, text = [], []
    for disc in order:
        row, trow = [], []
        for grp in groups:
            sub = piv[(piv["disc"] == disc) & (piv["grp"] == grp)]
            if not sub.empty and pd.notna(sub["pct"].iloc[0]):
                v = float(sub["pct"].iloc[0]); row.append(v); trow.append(f"%{v:.0f}")
            else:
                row.append(None); trow.append("")
        z.append(row); text.append(trow)
    labels = [core.GROUP_SHORT[g] for g in groups]
    disc_lbl = [d if len(d) <= 16 else d[:14] + "…" for d in order]
    fig = go.Figure(go.Heatmap(
        z=z, x=labels, y=disc_lbl, text=text, texttemplate="%{text}",
        textfont=dict(family=FONT, size=11, color="#0b1220"),
        colorscale=[[0, "#fb7185"], [0.5, "#0e7490"], [1, "#2dd4bf"]], zmin=0, zmax=100,
        xgap=5, ygap=5, showscale=False, hoverongaps=False,
        hovertemplate="<b>%{y}</b> · %{x}<br>İlerleme %{z:.0f}%<extra></extra>"))
    fig.update_layout(height=300, margin=dict(l=6, r=6, t=8, b=6),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family=FONT),
                      yaxis=dict(autorange="reversed", tickfont=dict(color="#c7d6ea", size=10.5)),
                      xaxis=dict(side="top", tickfont=dict(color="#a7bad4", size=11)))
    return fig
