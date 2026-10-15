"""Demo foods (values per 100 g). Approximate, rounded reference values for demonstration
only; replace with a licensed data source before relying on them.

Tuple: (slug, name, kcal, protein, carbs, fat).
"""

DEMO_FOODS: list[tuple[str, str, float, float, float, float]] = [
    ("chicken-breast-raw", "Piept de pui (crud)", 120, 22.5, 0, 2.6),
    ("egg-whole", "Ou întreg", 143, 12.6, 0.7, 9.5),
    ("rice-white-cooked", "Orez alb (fiert)", 130, 2.7, 28.2, 0.3),
    ("oats-rolled", "Fulgi de ovăz", 379, 13.2, 67.7, 6.5),
    ("banana", "Banană", 89, 1.1, 22.8, 0.3),
    ("apple", "Măr", 52, 0.3, 13.8, 0.2),
    ("greek-yogurt-2", "Iaurt grecesc 2%", 73, 9.9, 3.9, 2.0),
    ("cottage-cheese", "Brânză de vaci", 98, 11.1, 3.4, 4.3),
    ("salmon-raw", "Somon (crud)", 208, 20.0, 0, 13.0),
    ("potato-boiled", "Cartof (fiert)", 87, 1.9, 20.1, 0.1),
    ("bread-wholegrain", "Pâine integrală", 247, 13.0, 41.0, 3.4),
    ("milk-1-5", "Lapte 1,5%", 47, 3.4, 4.9, 1.5),
    ("olive-oil", "Ulei de măsline", 884, 0, 0, 100.0),
    ("almonds", "Migdale", 579, 21.2, 21.6, 49.9),
    ("broccoli", "Broccoli", 34, 2.8, 6.6, 0.4),
    ("tomato", "Roșii", 18, 0.9, 3.9, 0.2),
    ("kidney-beans-cooked", "Fasole roșie (fiartă)", 127, 8.7, 22.8, 0.5),
    ("pasta-cooked", "Paste (fierte)", 158, 5.8, 30.9, 0.9),
    ("tuna-in-water", "Ton în apă (conservă)", 116, 25.5, 0, 0.8),
    ("peanut-butter", "Unt de arahide", 588, 25.0, 20.0, 50.0),
]
