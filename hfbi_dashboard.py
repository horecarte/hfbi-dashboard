#!/usr/bin/env python3
"""HFBI Dashboard — Horecarte F&B Index
Lancia con: streamlit run hfbi_dashboard.py
"""

import sys
import sqlite3
from pathlib import Path
from collections import defaultdict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# === PASSWORD GATE ===
DASHBOARD_PASSWORD = "Horecarte2026!"

st.set_page_config(page_title="HFBI — Horecarte F&B Index", page_icon="📊", layout="wide")


def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.title("HFBI — Horecarte F&B Index")
    st.markdown("---")
    st.markdown("Dashboard riservata. Inserisci la password per accedere.")
    password = st.text_input("Password", type="password")
    if st.button("Accedi"):
        if password == DASHBOARD_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Password errata.")
    return False


if not check_password():
    st.stop()

# === APP ===
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "hfbi_index"))

from matcher import run_matching, generate_index
from paniere import PANIERE, CATEGORIE_HFBI
from panieri_settore import PANIERI_SETTORE

# Prova path deploy (data/) e path locale (scraping .../data/)
def _db_path(name, folder):
    deploy = BASE_DIR / "data" / f"{name}.db"
    local = BASE_DIR / folder / "data" / f"{name}.db"
    return str(deploy if deploy.exists() else local)

DATABASES = {
    "Sugros": _db_path("sugros", "scraping sugros"),
    "Hanos": _db_path("hanos", "scraping hanos"),
    "Teopace": _db_path("teopace", "scraping teopace"),
    "DeKlok": _db_path("deklok", "scraping deklok"),
}

SOURCE_LABELS = {
    "Sugros": "Fornitore A",
    "Hanos": "Fornitore B",
    "Teopace": "Fornitore C",
    "DeKlok": "Fornitore D",
}

COLORS = {
    "Fornitore A": "#003366",
    "Fornitore B": "#1B4F72",
    "Fornitore C": "#2E7D32",
    "Fornitore D": "#8B0000",
}


def _mask(name):
    return SOURCE_LABELS.get(name, name)


def _mask_all(matches, l1, l2, l3):
    for m in matches:
        m["source"] = _mask(m["source"])
    for level in (l1, l2, l3):
        for e in level:
            e["sources"] = {_mask(k): v for k, v in e["sources"].items()}
            e["best_source"] = _mask(e["best_source"])
    return matches, l1, l2, l3


@st.cache_data(ttl=600)
def load_all_products():
    """Carica TUTTI i prodotti grezzi da tutti i DB (non solo paniere)."""
    all_rows = []
    for source_name, db_path in DATABASES.items():
        if not Path(db_path).exists():
            continue
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM products WHERE price IS NOT NULL AND price > 0").fetchall()
        for r in rows:
            all_rows.append({
                "source": _mask(source_name),
                "code": r["code"],
                "name": r["name"],
                "brand": r["brand"] if "brand" in r.keys() else "",
                "price": r["price"],
                "category": r["category_group"] if "category_group" in r.keys() else "",
            })
        conn.close()
    return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()


@st.cache_data(ttl=600)
def load_index():
    matches = run_matching(DATABASES)
    l1, l2, l3 = generate_index(matches)
    matches, l1, l2, l3 = _mask_all(matches, l1, l2, l3)
    return matches, l1, l2, l3


# === LOAD DATA ===
matches, l1, l2, l3 = load_index()
all_products_df = load_all_products()

# === HEADER ===
st.title("HFBI — Horecarte F&B Index")
st.caption("Indice prezzi B2B normalizzato — confronto cross-grossista al kg/litro")

st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Prodotti totali", f"{len(all_products_df):,}" if not all_products_df.empty else "0")
c2.metric("Nel paniere", f"{len(matches):,}")
c3.metric("Confronti Brand", len([e for e in l1 if e["n_sources"] >= 2]))
c4.metric("Confronti Prodotto", len([e for e in l2 if e["n_sources"] >= 2]))
c5.metric("Categorie", len(l3))


# === TABS ===
tab_compare, tab_brand, tab_product, tab_category, tab_basket, tab_search = st.tabs([
    "Comparatore",
    "Confronto Brand",
    "Confronto Prodotto",
    "Indice Categoria",
    "Il Tuo Paniere",
    "Cerca Catalogo",
])


# === TAB: COMPARATORE ===
with tab_compare:
    st.subheader("Comparatore Prezzi")
    st.caption("Cerca qualsiasi prodotto e confronta i prezzi tra tutti i fornitori in tempo reale")

    if all_products_df.empty:
        st.warning("Nessun dato caricato.")
    else:
        # Barra di ricerca
        search = st.text_input(
            "Cerca prodotto (nome, brand, codice)",
            placeholder="es. mozzarella, barilla, prosecco, coca cola...",
            key="comparator_search",
        )

        if search:
            q = search.lower()
            mask = (
                all_products_df["name"].str.lower().str.contains(q, na=False)
                | all_products_df["brand"].str.lower().str.contains(q, na=False)
                | all_products_df["code"].str.lower().str.contains(q, na=False)
            )
            results = all_products_df[mask].copy()

            if results.empty:
                st.warning(f"Nessun risultato per '{search}'")
            else:
                st.markdown(f"### {len(results)} prodotti trovati per *\"{search}\"*")

                # Riepilogo per fornitore
                summary = results.groupby("source").agg(
                    prodotti=("price", "count"),
                    prezzo_min=("price", "min"),
                    prezzo_medio=("price", "mean"),
                    prezzo_max=("price", "max"),
                ).reset_index()
                summary.columns = ["Fornitore", "Prodotti", "Min", "Medio", "Max"]

                cols_summary = st.columns(len(summary))
                for i, (_, row) in enumerate(summary.iterrows()):
                    cols_summary[i].metric(
                        row["Fornitore"],
                        f"€{row['Medio']:.2f} medio",
                        f"{row['Prodotti']} prodotti",
                    )

                st.markdown("---")

                # Layout a due colonne
                col_table, col_chart = st.columns([3, 2])

                with col_table:
                    st.markdown("**Tutti i risultati (ordinati per prezzo):**")
                    display = results[["source", "name", "brand", "price", "category"]].copy()
                    display.columns = ["Fornitore", "Prodotto", "Brand", "Prezzo", "Categoria"]
                    display = display.sort_values("Prezzo")

                    st.dataframe(
                        display.head(100).style.format({"Prezzo": "€{:.2f}"}).background_gradient(
                            subset=["Prezzo"], cmap="RdYlGn_r"
                        ),
                        use_container_width=True,
                        height=500,
                    )

                with col_chart:
                    # Box plot comparativo
                    st.markdown("**Distribuzione prezzi per fornitore:**")
                    fig = px.box(
                        results, x="source", y="price", color="source",
                        color_discrete_map=COLORS,
                        points="all",
                        labels={"price": "Prezzo (EUR)", "source": ""},
                    )
                    fig.update_layout(showlegend=False, height=300)
                    st.plotly_chart(fig, use_container_width=True)

                    # Top 5 più economici
                    st.markdown("**Top 5 più economici:**")
                    cheapest = results.nsmallest(5, "price")
                    for _, r in cheapest.iterrows():
                        st.markdown(
                            f"- **€{r['price']:.2f}** — {r['brand']} {r['name'][:40]} "
                            f"*({r['source']})*"
                        )

                    # Top 5 più cari
                    st.markdown("**Top 5 più cari:**")
                    expensive = results.nlargest(5, "price")
                    for _, r in expensive.iterrows():
                        st.markdown(
                            f"- **€{r['price']:.2f}** — {r['brand']} {r['name'][:40]} "
                            f"*({r['source']})*"
                        )

                # Brand breakdown
                if len(results["brand"].dropna().unique()) > 1:
                    st.markdown("---")
                    st.markdown("### Confronto per brand")

                    brand_avg = (
                        results[results["brand"] != ""]
                        .groupby(["brand", "source"])["price"]
                        .mean()
                        .reset_index()
                    )
                    brand_avg.columns = ["Brand", "Fornitore", "Prezzo medio"]

                    # Solo brand con almeno 1 prodotto
                    top_brands = (
                        results[results["brand"] != ""]
                        .groupby("brand")
                        .size()
                        .sort_values(ascending=False)
                        .head(15)
                        .index.tolist()
                    )
                    brand_avg = brand_avg[brand_avg["Brand"].isin(top_brands)]

                    if not brand_avg.empty:
                        fig = px.bar(
                            brand_avg, x="Brand", y="Prezzo medio", color="Fornitore",
                            barmode="group",
                            color_discrete_map=COLORS,
                        )
                        fig.update_layout(height=400, xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)

        else:
            # Stato iniziale: suggerimenti
            st.markdown("#### Suggerimenti di ricerca")
            suggestions = [
                "mozzarella", "parmigiano", "spaghetti", "prosecco",
                "coca cola", "olio", "pesto", "prosciutto", "gorgonzola",
                "birra", "vino", "farina", "ricotta", "mascarpone",
            ]
            cols = st.columns(7)
            for i, s in enumerate(suggestions):
                cols[i % 7].button(s, key=f"sug_{s}", on_click=lambda x=s: st.session_state.update({"comparator_search": x}))


# === TAB: CONFRONTO BRAND ===
with tab_brand:
    st.subheader("Stesso prodotto, stesso brand — chi costa meno?")
    st.caption("Prodotti presenti su 2+ fornitori, ordinati per spread")

    multi_l1 = [e for e in l1 if e["n_sources"] >= 2]
    multi_l1.sort(key=lambda x: x["spread_pct"], reverse=True)

    if not multi_l1:
        st.info("Nessun prodotto trovato su più fornitori.")
    else:
        cats = sorted(set(e["categoria"] for e in multi_l1))
        sel_cat = st.selectbox("Filtra per categoria", ["Tutte"] + cats, key="l1_cat")
        if sel_cat != "Tutte":
            multi_l1 = [e for e in multi_l1 if e["categoria"] == sel_cat]

        rows = []
        for e in multi_l1:
            for src, stats in e["sources"].items():
                rows.append({
                    "Prodotto": e["nome"],
                    "Fornitore": src,
                    "Prezzo/unità": stats["avg_price"],
                })
        df = pd.DataFrame(rows)

        if not df.empty:
            fig = px.bar(
                df, x="Prezzo/unità", y="Prodotto", color="Fornitore",
                orientation="h", barmode="group",
                color_discrete_map=COLORS,
                labels={"Prezzo/unità": "EUR/kg o EUR/l"},
            )
            fig.update_layout(height=max(400, len(multi_l1) * 50), yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)

        table_rows = []
        for e in multi_l1:
            row = {"Prodotto": e["nome"], "Categoria": e["categoria"],
                   "Spread": f"{e['spread_pct']:.0f}%", "Migliore": e["best_source"]}
            for src, stats in sorted(e["sources"].items()):
                row[src] = f"€{stats['avg_price']:.2f}"
            table_rows.append(row)
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, height=500)


# === TAB: CONFRONTO PRODOTTO ===
with tab_product:
    st.subheader("Prodotto generico — prezzo medio per fornitore (tutti i brand)")

    multi_l2 = [e for e in l2 if e["n_sources"] >= 2]
    multi_l2.sort(key=lambda x: x["spread_pct"], reverse=True)

    if not multi_l2:
        st.info("Nessun prodotto su più fornitori.")
    else:
        rows = []
        for e in multi_l2:
            for src, stats in e["sources"].items():
                rows.append({
                    "Prodotto": e["nome"],
                    "Fornitore": src,
                    "Prezzo medio": stats["avg_price"],
                    "N. prodotti": stats["count"],
                    "Brand": ", ".join(stats["brands"][:3]),
                })
        df = pd.DataFrame(rows)

        fig = px.bar(
            df, x="Prezzo medio", y="Prodotto", color="Fornitore",
            orientation="h", barmode="group",
            color_discrete_map=COLORS,
            hover_data=["N. prodotti", "Brand"],
        )
        fig.update_layout(height=max(400, len(multi_l2) * 55), yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

        table_rows = []
        for e in multi_l2:
            row = {"Prodotto": e["nome"], "Categoria": e["categoria"]}
            for src, stats in sorted(e["sources"].items()):
                row[f"{src}"] = f"€{stats['avg_price']:.2f}"
                row[f"{src} brand"] = ", ".join(stats["brands"][:3])
            row["Spread"] = f"{e['spread_pct']:.0f}%"
            row["Migliore"] = e["best_source"]
            table_rows.append(row)
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, height=500)


# === TAB: INDICE CATEGORIA ===
with tab_category:
    st.subheader("Indice per categoria — prezzo medio al kg")

    if not l3:
        st.info("Nessun dato.")
    else:
        col_chart, col_table = st.columns([2, 1])

        with col_chart:
            rows = []
            for e in l3:
                for src, stats in e["sources"].items():
                    rows.append({
                        "Categoria": e["nome"],
                        "Fornitore": src,
                        "Prezzo medio (€/kg)": stats["avg_price"],
                        "Prodotti": stats["count"],
                    })
            df = pd.DataFrame(rows)
            fig = px.bar(df, x="Categoria", y="Prezzo medio (€/kg)", color="Fornitore",
                        barmode="group", color_discrete_map=COLORS, hover_data=["Prodotti"])
            fig.update_layout(height=500, xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            table_rows = []
            for e in sorted(l3, key=lambda x: x["nome"]):
                row = {"Categoria": e["nome"]}
                for src, stats in sorted(e["sources"].items()):
                    row[src] = f"€{stats['avg_price']:.2f}"
                if e["n_sources"] >= 2:
                    row["Spread"] = f"{e['spread_pct']:.0f}%"
                table_rows.append(row)
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, height=400)

        if len(l3) >= 3:
            st.subheader("Radar — profilo prezzo per fornitore")
            all_src = set()
            for e in l3:
                all_src.update(e["sources"].keys())
            fig = go.Figure()
            cats_r = [e["nome"] for e in l3]
            for src in sorted(all_src):
                vals = [e["sources"].get(src, {}).get("avg_price", 0) for e in l3]
                fig.add_trace(go.Scatterpolar(r=vals, theta=cats_r, fill='toself',
                             name=src, line_color=COLORS.get(src, "#999")))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True)), height=500)
            st.plotly_chart(fig, use_container_width=True)


# === TAB: PANIERE SETTORIALE ===
with tab_basket:
    st.subheader("Il Tuo Paniere — costo ingredienti per tipo di attività")
    settore = st.selectbox("Tipo di attività", list(PANIERI_SETTORE.keys()))
    info = PANIERI_SETTORE[settore]
    st.markdown(f"*{info['descrizione']}*")

    l2_map = {e["paniere_id"]: e for e in l2}
    rows = []
    all_src_set = set()
    for pid, peso in info["prodotti_core"]:
        if pid not in l2_map:
            continue
        entry = l2_map[pid]
        all_src_set.update(entry["sources"].keys())
        row = {"Prodotto": entry["nome"], "Categoria": entry["categoria"],
               "Importanza": "●●●" if peso == 3 else ("●●" if peso == 2 else "●"), "Peso": peso}
        for src, stats in entry["sources"].items():
            row[src] = stats["avg_price"]
        if entry["n_sources"] >= 2:
            row["Migliore"] = entry["best_source"]
            row["Spread"] = f"{entry['spread_pct']:.0f}%"
        rows.append(row)

    if not rows:
        st.warning("Dati insufficienti per questo paniere.")
    else:
        df_pan = pd.DataFrame(rows).sort_values("Peso", ascending=False)
        src_list = sorted(all_src_set)

        st.markdown("### Prezzi al kg/litro per fornitore")
        fmt = {s: "€{:.2f}" for s in src_list}
        dcols = ["Importanza", "Prodotto", "Categoria"] + src_list
        if "Migliore" in df_pan.columns:
            dcols += ["Migliore", "Spread"]
        avail = [c for c in dcols if c in df_pan.columns]
        st.dataframe(df_pan[avail].style.format(fmt, na_rep="—"), use_container_width=True, height=500)

        st.markdown("### Costo totale paniere")
        totals = {}
        for src in src_list:
            t = sum(r[src] * r["Peso"] for _, r in df_pan.iterrows() if src in r and pd.notna(r[src]))
            if t > 0:
                totals[src] = round(t, 2)

        if totals:
            cols = st.columns(len(totals))
            best = min(totals.values())
            for i, (src, tot) in enumerate(sorted(totals.items(), key=lambda x: x[1])):
                diff = round((tot - best) / best * 100, 1) if best > 0 else 0
                cols[i].metric(src, f"€{tot:.2f}", delta=f"+{diff}%" if diff > 0 else "Migliore",
                              delta_color="inverse" if diff > 0 else "normal")

            fig = px.bar(x=list(totals.keys()), y=list(totals.values()),
                        color=list(totals.keys()), color_discrete_map=COLORS,
                        labels={"x": "Fornitore", "y": "Costo paniere (EUR)"},
                        title=f"Costo paniere {settore}")
            fig.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Opportunità di risparmio")
        savings = []
        for _, r in df_pan.iterrows():
            prices = {s: r[s] for s in src_list if s in r and pd.notna(r[s])}
            if len(prices) >= 2:
                best_s = min(prices, key=prices.get)
                worst_s = max(prices, key=prices.get)
                diff = round((prices[worst_s] - prices[best_s]) / prices[best_s] * 100, 1)
                if diff > 10:
                    savings.append((r["Prodotto"], worst_s, prices[worst_s], best_s, prices[best_s], diff))
        savings.sort(key=lambda x: x[5], reverse=True)
        for prod, w, wp, b, bp, d in savings[:10]:
            st.markdown(f"- **{prod}**: {w} €{wp:.2f} → {b} €{bp:.2f} (**-{d:.0f}%**)")
        if not savings:
            st.info("Nessuna differenza significativa (>10%).")


# === TAB: CERCA CATALOGO ===
with tab_search:
    st.subheader("Cerca nel catalogo completo")
    st.caption("Cerca tra tutti i 25.000+ prodotti di tutti i fornitori")

    if all_products_df.empty:
        st.warning("Nessun dato.")
    else:
        col_q, col_src = st.columns([3, 1])
        with col_q:
            q = st.text_input("Cerca per nome, brand o codice", key="search_catalog")
        with col_src:
            sources = ["Tutti"] + sorted(all_products_df["source"].unique().tolist())
            src_filter = st.selectbox("Fornitore", sources, key="search_src")

        if q:
            ql = q.lower()
            mask = (
                all_products_df["name"].str.lower().str.contains(ql, na=False)
                | all_products_df["brand"].str.lower().str.contains(ql, na=False)
                | all_products_df["code"].str.lower().str.contains(ql, na=False)
            )
            res = all_products_df[mask]
            if src_filter != "Tutti":
                res = res[res["source"] == src_filter]

            st.markdown(f"**{len(res)} risultati**")
            display = res[["source", "code", "name", "brand", "price", "category"]].copy()
            display.columns = ["Fornitore", "Codice", "Prodotto", "Brand", "Prezzo", "Categoria"]
            st.dataframe(
                display.sort_values("Prezzo").head(200).style.format({"Prezzo": "€{:.2f}"}),
                use_container_width=True, height=600,
            )


# === FOOTER ===
st.markdown("---")
st.caption(
    f"HFBI — {len(all_products_df):,} prodotti, "
    f"{len(matches)} nel paniere, "
    f"{len([e for e in l2 if e['n_sources'] >= 2])} confronti cross-fornitore — "
    f"Horecarte B.V."
)
