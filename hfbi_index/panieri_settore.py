"""
HFBI Panieri Settoriali — panieri specifici per tipo di attività HoReCa.

Ogni paniere è una selezione di prodotti dal paniere generale (paniere.py)
pesati per importanza nel business del cliente.

Il peso indica quanto quel prodotto incide sul costo totale del locale:
  peso 3 = prodotto core (lo comprano ogni giorno, grossi volumi)
  peso 2 = prodotto importante (settimanale, volumi medi)
  peso 1 = prodotto secondario (occasionale, piccoli volumi)
"""

# Ogni entry: (paniere_id, peso)
# paniere_id corrisponde a quelli definiti in paniere.py

PANIERI_SETTORE = {

    "Pizzeria": {
        "descrizione": "Pizzeria tradizionale / pizza al taglio",
        "prodotti_core": [
            # Ingredienti pizza
            ("FARI-001", 3),    # Farina 00
            ("FARI-002", 3),    # Semola
            ("LATT-001", 3),    # Mozzarella fior di latte
            ("LATT-002", 2),    # Mozzarella di bufala
            ("CONS-001", 3),    # Pelati
            ("CONS-002", 3),    # Passata
            ("CONS-003", 2),    # Polpa di pomodoro
            ("OLIO-001", 3),    # Olio EVO
            ("CONS-005", 2),    # Olive
            # Topping
            ("SALU-001", 2),    # Prosciutto crudo
            ("SALU-002", 2),    # Prosciutto cotto
            ("SALU-003", 1),    # Salame
            ("SALU-004", 1),    # Mortadella
            ("LATT-008", 1),    # Gorgonzola
            ("LATT-006", 2),    # Parmigiano Reggiano
            # Bevande
            ("BEVA-001", 2),    # Coca-Cola
            ("BEVA-003", 2),    # Prosecco
            ("BEVA-004", 1),    # Caffè
        ],
    },

    "Ristorante Italiano": {
        "descrizione": "Ristorante italiano tradizionale / trattoria",
        "prodotti_core": [
            # Primi
            ("PAST-001", 3),    # Spaghetti
            ("PAST-002", 3),    # Penne
            ("PAST-004", 2),    # Tagliatelle
            ("PAST-005", 1),    # Lasagna
            ("CONS-004", 3),    # Pesto
            ("CONS-001", 3),    # Pelati
            ("CONS-002", 2),    # Passata
            # Secondi / contorni
            ("OLIO-001", 3),    # Olio EVO
            ("OLIO-002", 2),    # Aceto balsamico
            # Formaggi
            ("LATT-006", 3),    # Parmigiano Reggiano
            ("LATT-007", 2),    # Grana Padano
            ("LATT-001", 2),    # Mozzarella
            ("LATT-002", 2),    # Bufala
            ("LATT-003", 1),    # Burrata
            ("LATT-004", 1),    # Ricotta
            ("LATT-008", 1),    # Gorgonzola
            ("LATT-009", 1),    # Taleggio
            # Salumi
            ("SALU-001", 2),    # Prosciutto crudo
            ("SALU-002", 1),    # Prosciutto cotto
            ("SALU-005", 2),    # Pancetta/Guanciale
            # Bevande
            ("BEVA-003", 2),    # Prosecco
            ("BEVA-004", 3),    # Caffè
            ("BEVA-001", 1),    # Coca-Cola
        ],
    },

    "Panineria / Piadineria": {
        "descrizione": "Panineria, piadineria, toast bar",
        "prodotti_core": [
            # Pane e basi
            ("PANE-001", 2),    # Base pizza / focaccia
            ("FARI-001", 1),    # Farina
            # Salumi (core business)
            ("SALU-001", 3),    # Prosciutto crudo
            ("SALU-002", 3),    # Prosciutto cotto
            ("SALU-003", 3),    # Salame
            ("SALU-004", 3),    # Mortadella
            ("SALU-005", 2),    # Pancetta
            # Formaggi
            ("LATT-001", 3),    # Mozzarella
            ("LATT-002", 2),    # Bufala
            ("LATT-005", 1),    # Mascarpone
            ("LATT-008", 1),    # Gorgonzola
            # Condimenti
            ("OLIO-001", 2),    # Olio EVO
            ("CONS-004", 2),    # Pesto
            # Bevande
            ("BEVA-001", 3),    # Coca-Cola
            ("BEVA-002", 2),    # Coca-Cola Zero
            ("BEVA-004", 2),    # Caffè
        ],
    },

    "Fast Food / Snack Bar": {
        "descrizione": "Fast food, friggitoria, snack bar, food truck",
        "prodotti_core": [
            # Bevande (alto volume)
            ("BEVA-001", 3),    # Coca-Cola
            ("BEVA-002", 3),    # Coca-Cola Zero
            # Formaggi
            ("LATT-001", 2),    # Mozzarella
            ("LATT-005", 1),    # Mascarpone
            # Salumi
            ("SALU-002", 2),    # Prosciutto cotto
            ("SALU-004", 1),    # Mortadella
            # Condimenti
            ("OLIO-001", 1),    # Olio
            ("CONS-002", 1),    # Passata
            # Pane
            ("PANE-001", 2),    # Base pizza
            ("FARI-001", 1),    # Farina
            # Caffè
            ("BEVA-004", 2),    # Caffè
        ],
    },

    "Ristorazione Collettiva": {
        "descrizione": "Mense, catering, ospedali, scuole, aziende",
        "prodotti_core": [
            # Pasta (alti volumi)
            ("PAST-001", 3),    # Spaghetti
            ("PAST-002", 3),    # Penne
            ("PAST-003", 3),    # Fusilli
            ("PAST-005", 2),    # Lasagna
            # Conserve (alti volumi)
            ("CONS-001", 3),    # Pelati
            ("CONS-002", 3),    # Passata
            ("CONS-003", 3),    # Polpa
            ("CONS-004", 2),    # Pesto
            # Formaggi
            ("LATT-006", 2),    # Parmigiano
            ("LATT-007", 3),    # Grana Padano (più economico)
            ("LATT-001", 2),    # Mozzarella
            ("LATT-004", 1),    # Ricotta
            # Olio (alti volumi)
            ("OLIO-001", 3),    # Olio EVO
            # Farina
            ("FARI-001", 2),    # Farina 00
            # Salumi
            ("SALU-002", 2),    # Prosciutto cotto
            ("SALU-004", 2),    # Mortadella
        ],
    },

    "Bar / Caffetteria": {
        "descrizione": "Bar, caffetteria, pasticceria, brunch",
        "prodotti_core": [
            # Caffè (core)
            ("BEVA-004", 3),    # Caffè
            # Latte e latticini
            ("LATT-005", 2),    # Mascarpone (tiramisù)
            ("LATT-004", 1),    # Ricotta
            # Bevande
            ("BEVA-001", 3),    # Coca-Cola
            ("BEVA-002", 2),    # Coca-Cola Zero
            ("BEVA-003", 2),    # Prosecco (aperitivo)
            # Panini bar
            ("SALU-001", 2),    # Prosciutto crudo
            ("SALU-002", 2),    # Prosciutto cotto
            ("LATT-001", 2),    # Mozzarella
            ("PANE-001", 1),    # Pane/focaccia
        ],
    },

    "Enoteca / Wine Bar": {
        "descrizione": "Enoteca, wine bar, cocktail bar con taglieri",
        "prodotti_core": [
            # Vini e spirits (core)
            ("BEVA-003", 3),    # Prosecco
            # Taglieri (core)
            ("SALU-001", 3),    # Prosciutto crudo
            ("SALU-003", 3),    # Salame
            ("SALU-005", 2),    # Pancetta/Guanciale
            ("LATT-006", 3),    # Parmigiano Reggiano
            ("LATT-007", 2),    # Grana Padano
            ("LATT-008", 2),    # Gorgonzola
            ("LATT-002", 2),    # Bufala
            ("LATT-003", 2),    # Burrata
            ("CONS-005", 2),    # Olive
            # Condimenti
            ("OLIO-001", 2),    # Olio EVO
            ("OLIO-002", 2),    # Aceto balsamico
            # Pane
            ("PANE-001", 1),    # Pane/focaccia
        ],
    },

    "Hotel / Resort": {
        "descrizione": "Hotel, B&B, resort — colazione + ristorante",
        "prodotti_core": [
            # Colazione
            ("BEVA-004", 3),    # Caffè
            ("LATT-005", 1),    # Mascarpone
            ("LATT-004", 1),    # Ricotta
            # Ristorante
            ("PAST-001", 2),    # Spaghetti
            ("PAST-002", 2),    # Penne
            ("CONS-001", 2),    # Pelati
            ("CONS-004", 1),    # Pesto
            ("OLIO-001", 2),    # Olio EVO
            ("LATT-006", 2),    # Parmigiano
            ("LATT-001", 2),    # Mozzarella
            # Bar
            ("BEVA-001", 2),    # Coca-Cola
            ("BEVA-003", 2),    # Prosecco
            # Buffet salumi/formaggi
            ("SALU-001", 2),    # Prosciutto crudo
            ("SALU-002", 2),    # Prosciutto cotto
            ("SALU-004", 1),    # Mortadella
            ("LATT-007", 1),    # Grana Padano
        ],
    },
}
