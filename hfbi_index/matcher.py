"""
HFBI Matcher — Collega prodotti dei grossisti al paniere HFBI.

3 livelli di confronto:
  1. Prodotto + Brand esatto   → "Spaghetti Barilla" Sugros vs Hanos
  2. Prodotto generico          → "Spaghetti" (qualsiasi brand) per grossista
  3. Categoria                  → "Pasta secca" prezzo medio al kg per grossista
"""

import re
import sqlite3
import logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime

from paniere import PANIERE, CATEGORIE_HFBI

logger = logging.getLogger(__name__)

# === NORMALIZER ===
PATTERNS = [
    # Multi-unità: 4x500gr, 22x~350g, 18x230gr
    re.compile(r'(\d+)\s*x\s*~?(\d+[.,]?\d*)\s*(kg|gr|g|ml|cl|l|lt|ltr|liter|kilo)\b', re.I),
    # Singola unità: 500gr, ~1,3kg, ~18kg, 2.5l
    re.compile(r'~?(\d+[.,]?\d*)\s*(kg|gr|g|ml|cl|l|lt|ltr|liter|kilo)\b', re.I),
]
UNIT_TO_KG = {"kg": 1.0, "kilo": 1.0, "gr": 0.001, "g": 0.001}
UNIT_TO_L = {"l": 1.0, "lt": 1.0, "ltr": 1.0, "liter": 1.0, "cl": 0.01, "ml": 0.001}
HANOS_KG = {"kilogram": 1.0, "kg": 1.0, "gram": 0.001}
HANOS_L = {"liter": 1.0, "l": 1.0, "lt": 1.0, "centiliter": 0.01, "cl": 0.01, "milliliter": 0.001, "ml": 0.001}


def normalize_price(name, price, target_unit, content_qty=None, content_unit=None,
                    pezzi_per_cartone=None, source=None):
    """Normalizza prezzo a EUR/kg o EUR/l.

    Logica per source:
    - Hanos: prezzo al pezzo, content_qty/content_unit dall'API → diretto
    - Sugros: prezzo al pezzo, pezzi_per_cartone disponibile → prezzo = price per singolo pezzo
    - Teopace: prezzo per CARTONE intero, peso nel nome è per singolo pezzo
              → bisogna stimare pezzi_per_cartone o usare euristica
    """
    if not price or price <= 0:
        return None

    # === HANOS: dati strutturati dall'API, prezzo al pezzo ===
    if content_qty and content_unit:
        cu = content_unit.lower()
        if target_unit == "kg" and cu in HANOS_KG:
            total = content_qty * HANOS_KG[cu]
            return round(price / total, 2) if total > 0 else None
        elif target_unit == "l" and cu in HANOS_L:
            total = content_qty * HANOS_L[cu]
            return round(price / total, 2) if total > 0 else None

    # === SUGROS: prezzo al pezzo, peso nel campo 'peso' (grammi) o nel nome ===
    # Sugros vende al pezzo (€0.69 per 1 pacco di spaghetti 500g)
    if source == "Sugros":
        # Prova prima col campo peso (grammi) dal DB
        if content_qty and target_unit == "kg":
            # content_qty qui è il campo 'peso' in grammi
            kg = content_qty / 1000 if content_qty > 1 else content_qty
            if kg > 0:
                return round(price / kg, 2)
        return _parse_from_name(name, price, target_unit)

    # === TEOPACE: prezzo per CARTONE intero ===
    # "Spaghetti n12 500gr" a €39.60 = cartone di N pezzi da 500gr
    # Se il nome ha NxY (es. "4x500gr") usiamo quello
    # Altrimenti, il peso nel nome è per SINGOLO pezzo e il prezzo è per il cartone
    # → dobbiamo stimare quanti pezzi ci sono
    if source == "Teopace":
        # Prima: cerca pattern NxY nel nome (es. "4x500gr", "18x230gr")
        result = _parse_from_name(name, price, target_unit)
        if result is not None:
            # Controlla se il risultato è ragionevole (< €200/kg per food)
            if result < 200:
                return result

        # Se il prezzo al kg risulta troppo alto, probabilmente è un cartone
        # con peso singolo pezzo nel nome. Segnala come non normalizzabile
        # (meglio None che un dato sbagliato)
        return None

    # === DEFAULT: parsa dal nome ===
    return _parse_from_name(name, price, target_unit)


def _parse_from_name(name, price, target_unit):
    """Estrae peso/volume dal nome e calcola prezzo normalizzato."""
    for pat in PATTERNS:
        m = pat.search(name)
        if not m:
            continue
        groups = m.groups()
        if len(groups) == 3:
            mult, val, unit = int(groups[0]), float(groups[1].replace(",", ".")), groups[2].lower()
        else:
            mult, val, unit = 1, float(groups[0].replace(",", ".")), groups[1].lower()

        if target_unit == "kg" and unit in UNIT_TO_KG:
            total = mult * val * UNIT_TO_KG[unit]
            return round(price / total, 2) if total > 0 else None
        elif target_unit == "l" and unit in UNIT_TO_L:
            total = mult * val * UNIT_TO_L[unit]
            return round(price / total, 2) if total > 0 else None
    return None


def _max_price_per_unit(categoria, unita):
    """Soglia massima ragionevole per prezzo normalizzato. Oltre = errore di normalizzazione."""
    limits = {
        "PASTA": 30,           # max €30/kg per pasta premium
        "CONSERVE E SUGHI": 80,  # max €80/kg per pesto/tartufo
        "LATTICINI": 120,      # max €120/kg per formaggi premium
        "SALUMI": 150,         # max €150/kg per bresaola/culatello
        "OLIO E CONDIMENTI": 500,  # olio e balsamico premium
        "BEVANDE": 200,        # spirits premium al litro
        "FARINA E CEREALI": 20,
        "PANE E PIZZA": 40,
        "DOLCI E DESSERT": 100,
    }
    return limits.get(categoria, 200)


def match_product(name, brand, item):
    """Verifica se un prodotto matcha un item del paniere."""
    name_lower = (name or "").lower()
    brand_lower = (brand or "").lower()
    text = name_lower + " " + brand_lower

    for kw in item["keywords"]:
        if kw.lower() not in text:
            return False

    for ex in item.get("exclude", []):
        if ex.lower() in name_lower:
            return False

    return True


def normalize_brand(brand):
    """Normalizza nome brand per matching esatto."""
    if not brand:
        return ""
    b = brand.strip().lower()
    # Rimuovi suffissi comuni
    for suffix in [" s.p.a.", " srl", " b.v.", " bv"]:
        b = b.replace(suffix, "")
    return b.strip()


def run_matching(databases):
    """Esegue matching di tutti i prodotti contro il paniere.

    Returns: lista di match con livello di aggregazione
    """
    matches = []

    for source_name, db_path in databases.items():
        if not Path(db_path).exists():
            logger.warning(f"DB non trovato: {db_path}")
            continue

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM products WHERE price IS NOT NULL AND price > 0"
        ).fetchall()

        source_matches = 0
        for row in rows:
            name = row["name"]
            try:
                brand = row["brand"] or ""
            except (IndexError, KeyError):
                brand = ""
            price = row["price"]

            content_qty = None
            content_unit = None
            pezzi_per_cartone = None
            try:
                content_qty = row["content_quantity"]
                content_unit = row["content_unit"]
            except (IndexError, KeyError):
                pass
            try:
                pezzi_per_cartone = row["pezzi_per_cartone"]
            except (IndexError, KeyError):
                pass
            # Sugros: campo 'peso' in grammi — usalo come content_qty
            if source_name == "Sugros" and not content_qty:
                try:
                    peso_val = row["peso"]
                    if peso_val:
                        content_qty = float(peso_val)
                except (IndexError, KeyError, ValueError, TypeError):
                    pass

            for item in PANIERE:
                if not match_product(name, brand, item):
                    continue

                price_norm = normalize_price(
                    name, price, item["unita"],
                    content_qty=content_qty, content_unit=content_unit,
                    pezzi_per_cartone=pezzi_per_cartone, source=source_name,
                )

                # Sanity check: scarta prezzi normalizzati assurdi
                # (probabilmente cartone non riconosciuto o match sbagliato)
                if price_norm is not None:
                    max_reasonable = _max_price_per_unit(item["categoria"], item["unita"])
                    if price_norm > max_reasonable:
                        continue

                matches.append({
                    "paniere_id": item["id"],
                    "paniere_nome": item["nome"],
                    "categoria": item["categoria"],
                    "sottocategoria": item["sottocategoria"],
                    "unita": item["unita"],
                    "source": source_name,
                    "product_code": row["code"],
                    "product_name": name,
                    "brand": brand,
                    "brand_normalized": normalize_brand(brand),
                    "price_raw": price,
                    "price_normalized": price_norm,
                })
                source_matches += 1

        conn.close()
        logger.info(f"{source_name}: {source_matches} match")

    return matches


def generate_index(matches):
    """Genera l'indice HFBI a 3 livelli.

    Livello 1: Prodotto + Brand (es. Spaghetti Barilla → prezzo per grossista)
    Livello 2: Prodotto generico (es. Spaghetti → prezzo medio per grossista)
    Livello 3: Categoria (es. Pasta secca → prezzo medio per grossista)
    """

    # === LIVELLO 1: Prodotto + Brand ===
    level1 = defaultdict(lambda: defaultdict(list))
    for m in matches:
        if m["price_normalized"] is None or not m["brand_normalized"]:
            continue
        key = (m["paniere_id"], m["brand_normalized"])
        level1[key][m["source"]].append(m)

    index_l1 = []
    for (pid, brand), sources_data in level1.items():
        item = next(i for i in PANIERE if i["id"] == pid)
        brand_display = next(
            m["brand"] for src in sources_data.values() for m in src
        )

        entry = _build_entry(
            pid=pid,
            nome=f"{item['nome']} — {brand_display}",
            categoria=item["categoria"],
            sottocategoria=item["sottocategoria"],
            unita=item["unita"],
            sources_data=sources_data,
            livello=1,
        )
        if entry:
            index_l1.append(entry)

    # === LIVELLO 2: Prodotto generico (tutti i brand) ===
    level2 = defaultdict(lambda: defaultdict(list))
    for m in matches:
        if m["price_normalized"] is None:
            continue
        level2[m["paniere_id"]][m["source"]].append(m)

    index_l2 = []
    for pid, sources_data in level2.items():
        item = next(i for i in PANIERE if i["id"] == pid)
        entry = _build_entry(
            pid=pid,
            nome=item["nome"],
            categoria=item["categoria"],
            sottocategoria=item["sottocategoria"],
            unita=item["unita"],
            sources_data=sources_data,
            livello=2,
        )
        if entry:
            index_l2.append(entry)

    # === LIVELLO 3: Categoria ===
    level3 = defaultdict(lambda: defaultdict(list))
    for m in matches:
        if m["price_normalized"] is None:
            continue
        level3[m["categoria"]][m["source"]].append(m)

    index_l3 = []
    for cat, sources_data in level3.items():
        entry = _build_entry(
            pid=f"CAT-{cat}",
            nome=cat,
            categoria=cat,
            sottocategoria="(tutte)",
            unita="kg",  # media
            sources_data=sources_data,
            livello=3,
        )
        if entry:
            index_l3.append(entry)

    return index_l1, index_l2, index_l3


def _build_entry(pid, nome, categoria, sottocategoria, unita, sources_data, livello):
    """Costruisce una entry dell'indice da dati raggruppati per source."""
    sources_stats = {}
    all_prices = []

    for source, products in sources_data.items():
        prices = [p["price_normalized"] for p in products if p["price_normalized"]]
        if not prices:
            continue
        avg_p = sum(prices) / len(prices)
        sources_stats[source] = {
            "avg_price": round(avg_p, 2),
            "min": round(min(prices), 2),
            "max": round(max(prices), 2),
            "count": len(prices),
            "brands": list(set(p["brand"] for p in products if p["brand"])),
        }
        all_prices.extend(prices)

    if not all_prices:
        return None

    avg_all = round(sum(all_prices) / len(all_prices), 2)
    best_source = min(sources_stats, key=lambda s: sources_stats[s]["avg_price"])
    best_price = sources_stats[best_source]["avg_price"]
    worst_price = max(s["avg_price"] for s in sources_stats.values())
    spread = round((worst_price - best_price) / best_price * 100, 1) if best_price > 0 else 0

    return {
        "livello": livello,
        "paniere_id": pid,
        "nome": nome,
        "categoria": categoria,
        "sottocategoria": sottocategoria,
        "unita": unita,
        "sources": sources_stats,
        "avg_all": avg_all,
        "best_source": best_source,
        "best_price": best_price,
        "spread_pct": spread,
        "n_sources": len(sources_stats),
    }


# === MAIN ===
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    BASE = Path(__file__).parent.parent
    DATABASES = {
        "Sugros": str(BASE / "scraping sugros" / "data" / "sugros.db"),
        "Hanos": str(BASE / "scraping hanos" / "data" / "hanos.db"),
        "Teopace": str(BASE / "scraping teopace" / "data" / "teopace.db"),
    }

    matches = run_matching(DATABASES)
    print(f"\nTotale match: {len(matches)}")
    print(f"  con prezzo normalizzato: {sum(1 for m in matches if m['price_normalized'])}")

    l1, l2, l3 = generate_index(matches)

    # === LIVELLO 1: Prodotto + Brand ===
    print(f"\n{'=' * 80}")
    print(f"LIVELLO 1 — PRODOTTO + BRAND (confronto diretto)")
    print(f"{'=' * 80}")

    multi_source_l1 = [e for e in l1 if e["n_sources"] >= 2]
    multi_source_l1.sort(key=lambda x: x["spread_pct"], reverse=True)

    for entry in multi_source_l1[:20]:
        u = entry["unita"]
        print(f"\n  {entry['nome']}")
        for src, stats in sorted(entry["sources"].items(), key=lambda x: x[1]["avg_price"]):
            print(f"    {src:12} €{stats['avg_price']:>7.2f}/{u}  ({stats['count']} prodotti)")
        print(f"    {'SPREAD':12} {entry['spread_pct']:>7.1f}%   | Migliore: {entry['best_source']}")

    # === LIVELLO 2: Prodotto generico ===
    print(f"\n{'=' * 80}")
    print(f"LIVELLO 2 — PRODOTTO GENERICO (tutti i brand)")
    print(f"{'=' * 80}")

    for entry in sorted(l2, key=lambda x: (x["categoria"], x["nome"])):
        u = entry["unita"]
        multi = " ***" if entry["n_sources"] >= 2 else ""
        print(f"\n  {entry['nome']:35} [{entry['categoria']}]{multi}")
        for src, stats in sorted(entry["sources"].items(), key=lambda x: x[1]["avg_price"]):
            brands = ", ".join(stats["brands"][:3])
            more = f" +{len(stats['brands'])-3}" if len(stats["brands"]) > 3 else ""
            print(f"    {src:12} €{stats['avg_price']:>7.2f}/{u}  "
                  f"({stats['count']} prodotti: {brands}{more})")
        if entry["n_sources"] >= 2:
            print(f"    {'SPREAD':12} {entry['spread_pct']:>7.1f}%")

    # === LIVELLO 3: Categoria ===
    print(f"\n{'=' * 80}")
    print(f"LIVELLO 3 — CATEGORIA (prezzo medio)")
    print(f"{'=' * 80}")

    for entry in sorted(l3, key=lambda x: x["nome"]):
        print(f"\n  {entry['nome']}")
        for src, stats in sorted(entry["sources"].items(), key=lambda x: x[1]["avg_price"]):
            print(f"    {src:12} €{stats['avg_price']:>7.2f}/kg  ({stats['count']} prodotti)")
        if entry["n_sources"] >= 2:
            print(f"    {'SPREAD':12} {entry['spread_pct']:>7.1f}%")
