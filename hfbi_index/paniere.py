"""
HFBI Paniere — Definizione del paniere prodotti standardizzato.

Ogni prodotto del paniere è un "tipo" generico (es. "Mozzarella di bufala DOP 125g")
a cui vengono matchati i prodotti specifici di ogni grossista.

Il paniere è la base dell'indice HFBI: prezzi confrontabili, normalizzati, cross-grossista.
"""

# === CATEGORIE HFBI STANDARDIZZATE ===
# Codice a 2 livelli: GRUPPO > SOTTOGRUPPO

CATEGORIE_HFBI = {
    "LATTICINI": [
        "Mozzarella",
        "Mozzarella di bufala",
        "Burrata e Stracciatella",
        "Ricotta",
        "Mascarpone",
        "Parmigiano Reggiano",
        "Grana Padano",
        "Gorgonzola",
        "Provolone",
        "Pecorino",
        "Taleggio",
        "Scamorza",
        "Caciocavallo",
        "Formaggi freschi",
        "Formaggi stagionati",
        "Latte e Panna",
        "Burro",
        "Yogurt",
    ],
    "SALUMI": [
        "Prosciutto crudo",
        "Prosciutto cotto",
        "Salame",
        "Mortadella",
        "Bresaola",
        "Pancetta",
        "Coppa",
        "Guanciale",
        "Speck",
        "'Nduja e Salsiccia",
    ],
    "PASTA": [
        "Pasta secca lunga",        # spaghetti, linguine, tagliatelle
        "Pasta secca corta",        # penne, fusilli, rigatoni
        "Pasta fresca",             # tortellini, ravioli
        "Pasta ripiena",
        "Pasta all'uovo",
        "Pasta senza glutine",
        "Gnocchi",
        "Lasagna",
    ],
    "CONSERVE E SUGHI": [
        "Pelati",
        "Polpa di pomodoro",
        "Passata di pomodoro",
        "Pomodorini",
        "Concentrato di pomodoro",
        "Sughi pronti",
        "Pesto",
        "Olive",
        "Carciofi",
        "Funghi e tartufi",
        "Tonno e conserve di pesce",
    ],
    "OLIO E CONDIMENTI": [
        "Olio extravergine di oliva",
        "Olio di oliva",
        "Olio di semi",
        "Aceto balsamico",
        "Aceto di vino",
        "Sale e Pepe",
        "Spezie e Erbe",
    ],
    "FARINA E CEREALI": [
        "Farina 00",
        "Farina di semola",
        "Farina speciale",
        "Riso",
        "Polenta",
    ],
    "PANE E PIZZA": [
        "Pane",
        "Focaccia e Piadina",
        "Pizza e basi pizza",
        "Grissini e Taralli",
    ],
    "DOLCI E DESSERT": [
        "Biscotti",
        "Cioccolato",
        "Gelato",
        "Panettone e Colomba",
        "Tiramisù e Dessert",
    ],
    "BEVANDE": [
        "Acqua minerale",
        "Bibite (Cola, Fanta, Sprite)",
        "Succhi di frutta",
        "Birra",
        "Prosecco e Spumante",
        "Vino rosso",
        "Vino bianco",
        "Vino rosé",
        "Grappa e Distillati",
        "Liquori e Amari",
        "Caffè",
        "Tè",
    ],
    "SURGELATI": [
        "Verdure surgelate",
        "Pesce surgelato",
        "Pizza surgelata",
        "Pasta surgelata",
        "Gelato",
    ],
    "CARNE E PESCE": [
        "Pollo",
        "Manzo",
        "Maiale",
        "Pesce fresco",
        "Pesce surgelato",
        "Frutti di mare",
    ],
    "ORTOFRUTTA": [
        "Verdure fresche",
        "Frutta fresca",
        "Erbe aromatiche",
        "Legumi secchi",
    ],
    "NON-FOOD": [
        "Disposables",
        "Pulizia e Detergenti",
        "Tovaglioli e Carta",
        "Attrezzatura HoReCa",
    ],
}


# === PANIERE PRODOTTI TIPO ===
# Ogni entry è un prodotto "tipo" con:
# - id: identificativo univoco HFBI
# - nome: nome standardizzato
# - categoria/sottocategoria: dalla tassonomia sopra
# - unità: kg, l, pz — unità di normalizzazione
# - keywords: parole chiave per il matching automatico (case-insensitive)
# - brand_keywords: brand che identificano questo tipo (opzionale)
# - exclude: parole da escludere (evita falsi positivi)

PANIERE = [
    # === LATTICINI ===
    {
        "id": "LATT-001", "nome": "Mozzarella fior di latte",
        "categoria": "LATTICINI", "sottocategoria": "Mozzarella",
        "unita": "kg",
        "keywords": ["mozzarella", "fior di latte"],
        "exclude": ["bufala", "buffel", "vegan", "pizza", "rasp"],
    },
    {
        "id": "LATT-002", "nome": "Mozzarella di bufala DOP",
        "categoria": "LATTICINI", "sottocategoria": "Mozzarella di bufala",
        "unita": "kg",
        "keywords": ["mozzarella", "bufala"],
        "exclude": ["vegan"],
    },
    {
        "id": "LATT-003", "nome": "Burrata",
        "categoria": "LATTICINI", "sottocategoria": "Burrata e Stracciatella",
        "unita": "kg",
        "keywords": ["burrata"],
        "exclude": [],
    },
    {
        "id": "LATT-004", "nome": "Ricotta fresca",
        "categoria": "LATTICINI", "sottocategoria": "Ricotta",
        "unita": "kg",
        "keywords": ["ricotta"],
        "exclude": ["salata", "affumicata", "tortelloni", "tortellini", "ravioli", "raviolo",
                     "pasta", "saus", "pesto", "gnocchi", "lasagna", "cannelloni",
                     "confetti", "cake", "cheesecake", "torta", "mousse", "crema",
                     "perline", "emiliane", "sugo"],
    },
    {
        "id": "LATT-005", "nome": "Mascarpone",
        "categoria": "LATTICINI", "sottocategoria": "Mascarpone",
        "unita": "kg",
        "keywords": ["mascarpone"],
        "exclude": ["tiramisu", "tiramisù", "cake", "torta", "gorgonzola", "dolcetto",
                     "crema", "pasta", "sugo"],
    },
    {
        "id": "LATT-006", "nome": "Parmigiano Reggiano",
        "categoria": "LATTICINI", "sottocategoria": "Parmigiano Reggiano",
        "unita": "kg",
        "keywords": ["parmigiano reggiano"],
        "exclude": ["tortelloni", "tortellini", "ravioli", "raviolo", "pasta", "gnocchi",
                     "sugo", "pesto", "snack", "tarallini", "crema", "perline",
                     "emiliane", "scaglie", "grattugiat"],
    },
    {
        "id": "LATT-007", "nome": "Grana Padano",
        "categoria": "LATTICINI", "sottocategoria": "Grana Padano",
        "unita": "kg",
        "keywords": ["grana padano"],
        "exclude": ["tortelloni", "tortellini", "ravioli", "pasta", "sugo", "snack",
                     "grattugiat", "scaglie"],
    },
    {
        "id": "LATT-008", "nome": "Gorgonzola",
        "categoria": "LATTICINI", "sottocategoria": "Gorgonzola",
        "unita": "kg",
        "keywords": ["gorgonzola"],
        "exclude": ["saus", "pasta", "risotto", "mascarpone", "dolcetto", "sugo",
                     "tortelloni", "ravioli", "gnocchi", "margherita"],
    },
    {
        "id": "LATT-009", "nome": "Taleggio",
        "categoria": "LATTICINI", "sottocategoria": "Taleggio",
        "unita": "kg",
        "keywords": ["taleggio"],
        "exclude": [],
    },

    # === SALUMI ===
    {
        "id": "SALU-001", "nome": "Prosciutto crudo",
        "categoria": "SALUMI", "sottocategoria": "Prosciutto crudo",
        "unita": "kg",
        "keywords": ["prosciutto crudo", "prosciutto di parma", "rauwe ham"],
        "exclude": ["cotto", "pizza"],
    },
    {
        "id": "SALU-002", "nome": "Prosciutto cotto",
        "categoria": "SALUMI", "sottocategoria": "Prosciutto cotto",
        "unita": "kg",
        "keywords": ["prosciutto cotto"],
        "exclude": ["crudo"],
    },
    {
        "id": "SALU-003", "nome": "Salame italiano",
        "categoria": "SALUMI", "sottocategoria": "Salame",
        "unita": "kg",
        "keywords": ["salame", "salami"],
        "exclude": ["pizza"],
    },
    {
        "id": "SALU-004", "nome": "Mortadella Bologna",
        "categoria": "SALUMI", "sottocategoria": "Mortadella",
        "unita": "kg",
        "keywords": ["mortadella"],
        "exclude": [],
    },
    {
        "id": "SALU-005", "nome": "Pancetta",
        "categoria": "SALUMI", "sottocategoria": "Pancetta",
        "unita": "kg",
        "keywords": ["pancetta", "guanciale"],
        "exclude": ["pasta", "saus"],
    },

    # === PASTA ===
    {
        "id": "PAST-001", "nome": "Spaghetti di semola",
        "categoria": "PASTA", "sottocategoria": "Pasta secca lunga",
        "unita": "kg",
        "keywords": ["spaghetti"],
        "exclude": ["chitarra", "uovo", "glutenfree", "gluten", "volkoren", "integrale"],
    },
    {
        "id": "PAST-002", "nome": "Penne rigate di semola",
        "categoria": "PASTA", "sottocategoria": "Pasta secca corta",
        "unita": "kg",
        "keywords": ["penne"],
        "exclude": ["glutenfree", "gluten", "volkoren", "integrale", "uovo"],
    },
    {
        "id": "PAST-003", "nome": "Fusilli di semola",
        "categoria": "PASTA", "sottocategoria": "Pasta secca corta",
        "unita": "kg",
        "keywords": ["fusilli"],
        "exclude": ["glutenfree", "gluten", "volkoren", "integrale"],
    },
    {
        "id": "PAST-004", "nome": "Tagliatelle all'uovo",
        "categoria": "PASTA", "sottocategoria": "Pasta all'uovo",
        "unita": "kg",
        "keywords": ["tagliatelle"],
        "exclude": ["glutenfree", "gluten"],
    },
    {
        "id": "PAST-005", "nome": "Lasagna sfoglia",
        "categoria": "PASTA", "sottocategoria": "Lasagna",
        "unita": "kg",
        "keywords": ["lasagna", "lasagne"],
        "exclude": ["bolognese", "klaar", "ready", "maaltijd"],
    },

    # === CONSERVE ===
    {
        "id": "CONS-001", "nome": "Pomodori pelati",
        "categoria": "CONSERVE E SUGHI", "sottocategoria": "Pelati",
        "unita": "kg",
        "keywords": ["pelati", "pomodori pelati", "gepelde tomaten"],
        "exclude": [],
    },
    {
        "id": "CONS-002", "nome": "Passata di pomodoro",
        "categoria": "CONSERVE E SUGHI", "sottocategoria": "Passata di pomodoro",
        "unita": "kg",
        "keywords": ["passata"],
        "exclude": [],
    },
    {
        "id": "CONS-003", "nome": "Polpa di pomodoro",
        "categoria": "CONSERVE E SUGHI", "sottocategoria": "Polpa di pomodoro",
        "unita": "kg",
        "keywords": ["polpa", "pomodoro a pezzi", "gehakte tomaten", "tomatenblokjes"],
        "exclude": [],
    },
    {
        "id": "CONS-004", "nome": "Pesto alla genovese",
        "categoria": "CONSERVE E SUGHI", "sottocategoria": "Pesto",
        "unita": "kg",
        "keywords": ["pesto genovese", "pesto groen", "pesto basilicum"],
        "exclude": ["rosso", "rood", "cracker", "pasta pesto"],
    },
    {
        "id": "CONS-005", "nome": "Olive verdi / nere",
        "categoria": "CONSERVE E SUGHI", "sottocategoria": "Olive",
        "unita": "kg",
        "keywords": ["olive", "olijven"],
        "exclude": ["olijfolie", "olio"],
    },

    # === OLIO ===
    {
        "id": "OLIO-001", "nome": "Olio extravergine di oliva",
        "categoria": "OLIO E CONDIMENTI", "sottocategoria": "Olio extravergine di oliva",
        "unita": "l",
        "keywords": ["olio extra", "extravergine", "extra vierge", "olijfolie extra"],
        "exclude": ["tartufo", "peperoncino"],
    },
    {
        "id": "OLIO-002", "nome": "Aceto balsamico di Modena",
        "categoria": "OLIO E CONDIMENTI", "sottocategoria": "Aceto balsamico",
        "unita": "l",
        "keywords": ["balsamico", "aceto balsamico"],
        "exclude": ["creme", "crema", "glaze"],
    },

    # === FARINA ===
    {
        "id": "FARI-001", "nome": "Farina 00",
        "categoria": "FARINA E CEREALI", "sottocategoria": "Farina 00",
        "unita": "kg",
        "keywords": ["farina 00", "farina tipo 00", "meel 00"],
        "exclude": [],
    },
    {
        "id": "FARI-002", "nome": "Farina di semola rimacinata",
        "categoria": "FARINA E CEREALI", "sottocategoria": "Farina di semola",
        "unita": "kg",
        "keywords": ["semola", "semolina", "griesmeel"],
        "exclude": ["pasta", "pane"],
    },

    # === BEVANDE ===
    {
        "id": "BEVA-001", "nome": "Coca-Cola",
        "categoria": "BEVANDE", "sottocategoria": "Bibite (Cola, Fanta, Sprite)",
        "unita": "l",
        "keywords": ["coca cola", "coca-cola"],
        "exclude": ["zero", "light", "diet"],
    },
    {
        "id": "BEVA-002", "nome": "Coca-Cola Zero",
        "categoria": "BEVANDE", "sottocategoria": "Bibite (Cola, Fanta, Sprite)",
        "unita": "l",
        "keywords": ["coca cola zero", "coca-cola zero"],
        "exclude": [],
    },
    {
        "id": "BEVA-003", "nome": "Prosecco DOC",
        "categoria": "BEVANDE", "sottocategoria": "Prosecco e Spumante",
        "unita": "l",
        "keywords": ["prosecco"],
        "exclude": [],
    },
    {
        "id": "BEVA-004", "nome": "Caffè in grani",
        "categoria": "BEVANDE", "sottocategoria": "Caffè",
        "unita": "kg",
        "keywords": ["caffè", "koffie", "espresso", "caffe"],
        "brand_keywords": ["illy", "lavazza", "segafredo", "pellini"],
        "exclude": ["capsule", "pad", "dolce gusto", "nespresso", "machine", "apparaat"],
    },

    # === PANE E PIZZA ===
    {
        "id": "PANE-001", "nome": "Base pizza",
        "categoria": "PANE E PIZZA", "sottocategoria": "Pizza e basi pizza",
        "unita": "kg",
        "keywords": ["pizzabodem", "base pizza", "pizza base", "pinsa"],
        "exclude": [],
    },
]
