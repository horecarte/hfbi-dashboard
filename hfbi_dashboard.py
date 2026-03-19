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
    """Gate con password. Restituisce True se autenticato."""
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

DATABASES = {
    "Sugros": str(BASE_DIR / "data" / "sugros.db"),
    "Hanos": str(BASE_DIR / "data" / "hanos.db"),
    "Teopace": str(BASE_DIR / "data" / "teopace.db"),
}

# Nomi oscurati per il frontend — i clienti non devono sapere le fonti
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


# === DATA ===
def _mask_source(name):
    """Sostituisce il nome reale del grossista con il codice anonimo."""
    return SOURCE_LABELS.get(name, name)


def _mask_data(matches, l1, l2, l3):
    """Anonimizza tutti i nomi grossista nei dati."""
    for m in matches:
        m["source"] = _mask_source(m["source"])

    for level in (l1, l2, l3):
        for entry in level:
            entry["sources"] = {
                _mask_source(k): v for k, v in entry["sources"].items()
            }
            entry["best_source"] = _mask_source(entry["best_source"])

    return matches, l1, l2, l3


@st.cache_data(ttl=600)
def load_index():
    matches = run_matching(DATABASES)
    l1, l2, l3 = generate_index(matches)
    matches, l1, l2, l3 = _mask_data(matches, l1, l2, l3)
    return matches, l1, l2, l3


# === PAGE ===
st.title("HFBI — Horecarte F&B Index")
st.caption("Indice prezzi B2B normalizzato — confronto cross-grossista al kg/litro")

matches, l1, l2, l3 = load_index()

# === KPI ===
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Prodotti matchati", f"{len(matches):,}")
c2.metric("Confronti Brand (L1)", len([e for e in l1 if e["n_sources"] >= 2]))
c3.metric("Confronti Prodotto (L2)", len([e for e in l2 if e["n_sources"] >= 2]))
c4.metric("Categorie (L3)", len(l3))


# === TABS ===
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Confronto Brand",
    "Confronto Prodotto",
    "Indice Categoria",
    "Il Tuo Paniere",
    "Cerca",
])


# === TAB 1: LIVELLO 1 — Prodotto + Brand ===
with tab1:
    st.subheader("Stesso prodotto, stesso brand — chi costa meno?")
    st.caption("Solo prodotti presenti su 2+ grossisti, ordinati per spread (differenza %)")

    multi_l1 = [e for e in l1 if e["n_sources"] >= 2]
    multi_l1.sort(key=lambda x: x["spread_pct"], reverse=True)

    if not multi_l1:
        st.info("Nessun prodotto trovato su più grossisti.")
    else:
        # Filtro categoria
        cats = sorted(set(e["categoria"] for e in multi_l1))
        sel_cat = st.selectbox("Filtra per categoria", ["Tutte"] + cats, key="l1_cat")
        if sel_cat != "Tutte":
            multi_l1 = [e for e in multi_l1 if e["categoria"] == sel_cat]

        # Grafico
        rows = []
        for e in multi_l1:
            for src, stats in e["sources"].items():
                rows.append({
                    "Prodotto": e["nome"],
                    "Grossista": src,
                    "Prezzo/unità": stats["avg_price"],
                    "Unità": e["unita"],
                    "Spread": f"{e['spread_pct']:.0f}%",
                })
        df = pd.DataFrame(rows)

        if not df.empty:
            fig = px.bar(
                df, x="Prezzo/unità", y="Prodotto", color="Grossista",
                orientation="h", barmode="group",
                color_discrete_map=COLORS,
                labels={"Prezzo/unità": "EUR/kg o EUR/l"},
            )
            fig.update_layout(
                height=max(400, len(multi_l1) * 50),
                yaxis={"categoryorder": "total ascending"},
            )
            st.plotly_chart(fig, use_container_width=True)

        # Tabella dettaglio
        st.markdown("**Dettaglio:**")
        table_rows = []
        for e in multi_l1:
            row = {
                "Prodotto": e["nome"],
                "Categoria": e["categoria"],
                "Unità": e["unita"],
                "Spread": f"{e['spread_pct']:.0f}%",
                "Migliore": e["best_source"],
            }
            for src, stats in sorted(e["sources"].items()):
                row[src] = f"€{stats['avg_price']:.2f}"
            table_rows.append(row)

        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, height=500)


# === TAB 2: LIVELLO 2 — Prodotto generico ===
with tab2:
    st.subheader("Prodotto generico — prezzo medio per grossista (tutti i brand)")
    st.caption("Quanto costa in media la mozzarella, gli spaghetti, il parmigiano... per grossista?")

    multi_l2 = [e for e in l2 if e["n_sources"] >= 2]
    multi_l2.sort(key=lambda x: x["spread_pct"], reverse=True)

    if not multi_l2:
        st.info("Nessun prodotto su più grossisti.")
    else:
        # Grafico principale
        rows = []
        for e in multi_l2:
            for src, stats in e["sources"].items():
                rows.append({
                    "Prodotto": e["nome"],
                    "Grossista": src,
                    "Prezzo medio": stats["avg_price"],
                    "Unità": e["unita"],
                    "N. prodotti": stats["count"],
                    "Brand": ", ".join(stats["brands"][:3]),
                })
        df = pd.DataFrame(rows)

        fig = px.bar(
            df, x="Prezzo medio", y="Prodotto", color="Grossista",
            orientation="h", barmode="group",
            color_discrete_map=COLORS,
            hover_data=["N. prodotti", "Brand"],
        )
        fig.update_layout(
            height=max(400, len(multi_l2) * 55),
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tabella con dettaglio brand
        st.markdown("**Dettaglio con brand disponibili:**")
        table_rows = []
        for e in multi_l2:
            row = {"Prodotto": e["nome"], "Categoria": e["categoria"]}
            for src, stats in sorted(e["sources"].items()):
                brands = ", ".join(stats["brands"][:4])
                row[f"{src} (€/{e['unita']})"] = f"€{stats['avg_price']:.2f}"
                row[f"{src} brand"] = brands
            row["Spread"] = f"{e['spread_pct']:.0f}%"
            row["Migliore"] = e["best_source"]
            table_rows.append(row)
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, height=500)


# === TAB 3: LIVELLO 3 — Categoria ===
with tab3:
    st.subheader("Indice per categoria — prezzo medio al kg per grossista")
    st.caption("Vista macro: quale grossista è più caro su ogni categoria?")

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
                        "Grossista": src,
                        "Prezzo medio (€/kg)": stats["avg_price"],
                        "N. prodotti": stats["count"],
                    })
            df = pd.DataFrame(rows)

            fig = px.bar(
                df, x="Categoria", y="Prezzo medio (€/kg)", color="Grossista",
                barmode="group",
                color_discrete_map=COLORS,
                hover_data=["N. prodotti"],
            )
            fig.update_layout(height=500, xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.markdown("**Riepilogo:**")
            table_rows = []
            for e in sorted(l3, key=lambda x: x["nome"]):
                row = {"Categoria": e["nome"]}
                for src, stats in sorted(e["sources"].items()):
                    row[src] = f"€{stats['avg_price']:.2f}/kg ({stats['count']})"
                if e["n_sources"] >= 2:
                    row["Spread"] = f"{e['spread_pct']:.0f}%"
                    row["Migliore"] = e["best_source"]
                table_rows.append(row)
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, height=400)

        # Radar chart
        if len(l3) >= 3:
            st.subheader("Radar — profilo prezzo per grossista")
            all_sources = set()
            for e in l3:
                all_sources.update(e["sources"].keys())

            fig = go.Figure()
            categories_radar = [e["nome"] for e in l3]
            for src in sorted(all_sources):
                values = []
                for e in l3:
                    if src in e["sources"]:
                        values.append(e["sources"][src]["avg_price"])
                    else:
                        values.append(0)
                fig.add_trace(go.Scatterpolar(
                    r=values, theta=categories_radar, fill='toself',
                    name=src, line_color=COLORS.get(src, "#999"),
                ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                height=500,
            )
            st.plotly_chart(fig, use_container_width=True)


# === TAB 4: PANIERE SETTORIALE ===
with tab4:
    st.subheader("Il Tuo Paniere — costo ingredienti per tipo di attività")
    st.caption("Seleziona il tuo tipo di locale e vedi quanto costeranno i tuoi ingredienti da ogni fornitore")

    settore = st.selectbox(
        "Tipo di attività",
        list(PANIERI_SETTORE.keys()),
    )

    info = PANIERI_SETTORE[settore]
    st.markdown(f"*{info['descrizione']}*")

    # Mappa paniere_id → dati dall'indice L2
    l2_map = {e["paniere_id"]: e for e in l2}

    # Costruisci tabella
    rows = []
    all_sources_set = set()
    for pid, peso in info["prodotti_core"]:
        if pid not in l2_map:
            continue
        entry = l2_map[pid]
        all_sources_set.update(entry["sources"].keys())

        row = {
            "Prodotto": entry["nome"],
            "Categoria": entry["categoria"],
            "Importanza": "●●●" if peso == 3 else ("●●" if peso == 2 else "●"),
            "Peso": peso,
        }
        for src, stats in entry["sources"].items():
            row[src] = stats["avg_price"]

        if entry["n_sources"] >= 2:
            row["Migliore"] = entry["best_source"]
            row["Spread"] = f"{entry['spread_pct']:.0f}%"
        rows.append(row)

    if not rows:
        st.warning("Non ci sono ancora abbastanza dati per questo paniere.")
    else:
        df_pan = pd.DataFrame(rows)

        # Ordina per importanza
        df_pan = df_pan.sort_values("Peso", ascending=False)

        # Tabella prezzi
        st.markdown("### Prezzi al kg/litro per fornitore")
        sources_list = sorted(all_sources_set)
        format_dict = {src: "€{:.2f}" for src in sources_list}
        display_cols = ["Importanza", "Prodotto", "Categoria"] + sources_list
        if "Migliore" in df_pan.columns:
            display_cols += ["Migliore", "Spread"]
        available = [c for c in display_cols if c in df_pan.columns]
        st.dataframe(
            df_pan[available].style.format(format_dict, na_rep="—"),
            use_container_width=True,
            height=500,
        )

        # Costo paniere totale (somma pesata)
        st.markdown("### Costo totale paniere (somma pesata)")
        st.caption("Il peso (1-3) simula i volumi di acquisto: peso 3 = prodotto ad alto volume")

        totals = {}
        for src in sources_list:
            total = 0
            count = 0
            for _, r in df_pan.iterrows():
                if src in r and pd.notna(r[src]):
                    total += r[src] * r["Peso"]
                    count += 1
            if count > 0:
                totals[src] = round(total, 2)

        if totals:
            col_totals = st.columns(len(totals))
            sorted_totals = sorted(totals.items(), key=lambda x: x[1])
            best_total = sorted_totals[0][1]

            for i, (src, total) in enumerate(sorted_totals):
                diff = round((total - best_total) / best_total * 100, 1) if best_total > 0 else 0
                label = f"+{diff}%" if diff > 0 else "Migliore"
                col_totals[i].metric(src, f"€{total:.2f}", delta=label,
                                     delta_color="inverse" if diff > 0 else "normal")

            # Grafico confronto
            fig = px.bar(
                x=list(totals.keys()), y=list(totals.values()),
                color=list(totals.keys()),
                color_discrete_map=COLORS,
                labels={"x": "Fornitore", "y": "Costo paniere pesato (EUR)"},
                title=f"Costo paniere {settore}",
            )
            fig.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig, use_container_width=True)

        # Consigli di risparmio
        st.markdown("### Opportunità di risparmio")
        savings = []
        for _, r in df_pan.iterrows():
            prices = {src: r[src] for src in sources_list if src in r and pd.notna(r[src])}
            if len(prices) >= 2:
                best = min(prices, key=prices.get)
                worst = max(prices, key=prices.get)
                diff_pct = round((prices[worst] - prices[best]) / prices[best] * 100, 1)
                if diff_pct > 10:
                    savings.append({
                        "Prodotto": r["Prodotto"],
                        "Fornitore caro": worst,
                        "Prezzo caro": f"€{prices[worst]:.2f}/kg",
                        "Fornitore economico": best,
                        "Prezzo economico": f"€{prices[best]:.2f}/kg",
                        "Risparmio": f"{diff_pct:.0f}%",
                        "_diff": diff_pct,
                    })

        if savings:
            savings.sort(key=lambda x: x["_diff"], reverse=True)
            for s in savings[:10]:
                st.markdown(
                    f"- **{s['Prodotto']}**: {s['Fornitore caro']} a {s['Prezzo caro']} "
                    f"→ passa a {s['Fornitore economico']} a {s['Prezzo economico']} "
                    f"(**-{s['Risparmio']}**)"
                )
        else:
            st.info("Non ci sono differenze significative (>10%) tra fornitori per questo paniere.")


# === TAB 5: CERCA ===
with tab5:
    st.subheader("Cerca nel paniere HFBI")

    query = st.text_input("Cerca prodotto (es. mozzarella, spaghetti, prosecco)")

    if query:
        q = query.lower()
        results = [m for m in matches if q in m["product_name"].lower()
                   or q in m["brand"].lower()
                   or q in m["paniere_nome"].lower()]

        if not results:
            st.warning(f"Nessun risultato per '{query}'")
        else:
            st.markdown(f"**{len(results)} prodotti trovati**")

            df = pd.DataFrame(results)
            display_cols = ["source", "paniere_nome", "product_name", "brand",
                           "price_raw", "price_normalized", "unita"]
            available = [c for c in display_cols if c in df.columns]
            df_display = df[available].copy()
            df_display.columns = ["Grossista", "Tipo paniere", "Nome prodotto", "Brand",
                                  "Prezzo", "Prezzo/unità", "Unità"][:len(available)]
            df_display = df_display.sort_values("Prezzo/unità", na_position="last")

            st.dataframe(
                df_display.head(50).style.format({
                    "Prezzo": "€{:.2f}",
                    "Prezzo/unità": "€{:.2f}",
                }, na_rep="—"),
                use_container_width=True,
                height=500,
            )

            # Box plot per grossista
            df_with_norm = df.dropna(subset=["price_normalized"])
            if not df_with_norm.empty:
                fig = px.box(
                    df_with_norm, x="source", y="price_normalized",
                    color="source", color_discrete_map=COLORS,
                    points="all",
                    labels={"price_normalized": f"Prezzo normalizzato", "source": "Grossista"},
                    title=f"Distribuzione prezzo: {query}",
                )
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)


# === FOOTER ===
st.markdown("---")
st.caption(
    f"HFBI Dashboard — {len(matches)} prodotti matchati al paniere, "
    f"{len([e for e in l2 if e['n_sources'] >= 2])} confronti cross-grossista — "
    f"Horecarte B.V."
)
