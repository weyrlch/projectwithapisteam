# badge_utils.py

# --- 1) Definição das insígnias e fórmulas de XP ---
badges = [
    {
        "name": "One-Stop Shopper",
        "G_min": 1,  "G_max": 4,
        "formula": lambda G: round(94 + 6 * G)
    },
    {
        "name": "Selected Collector",
        "G_min": 5,  "G_max": 9,
        "formula": lambda G: round(100 + 5 * G)
    },
    {
        "name": "Adept Accumulator",
        "G_min": 10, "G_max": 24,
        "formula": lambda G: round(150 + 3.31 * (G - 10))
    },
    {
        "name": "Sharp-Eyed Stockpiler",
        "G_min": 25, "G_max": 49,
        "formula": lambda G: round(150 + 2 * G)
    },
    {
        "name": "Collection Agent",
        "G_min": 50,  "G_max": 99,
        "formula": lambda G: round(250 + 1.49 * (G - 50))
    },
    {
        "name": "Power Player",
        "G_min": 100, "G_max": 249,
        "formula": lambda G: round(325 + 1.1585 * (G - 100))
    },
    {
        "name": "Game Mechanic",
        "G_min": 250, "G_max": 499,
        "formula": lambda G: 250 + G
    },
    {
        "name": "Director of Acquisitions",
        "G_min": 500,  "G_max": 999,
        "formula": lambda G: 250 + G
    },
    {
        "name": "Game Industry Guardian",
        "G_min": 1000, "G_max": 1999,
        "formula": lambda G: 250 + G
    },
    {
        "name": "Gaming God",
        "G_min": 2000, "G_max": 2999,
        "formula": lambda G: 250 + G
    },
    {
        "name": "Accrual Expert",
        "G_min": 3000, "G_max": 3999,
        "formula": lambda G: 250 + G
    },
    {
        "name": "Ambassador of Amassment",
        "G_min": 4000, "G_max": 4999,
        "formula": lambda G: 250 + G
    },
    {
        "name": "Digital Deity",
        "G_min": 5000, "G_max": 5999,
        "formula": lambda G: 250 + G
    },
    {
        "name": "Collection King",
        "G_min": 6000, "G_max": 6999,
        "formula": lambda G: 250 + G
    },
    {
        "name": "Magnate of Amassment",
        "G_min": 7000, "G_max": 7999,
        "formula": lambda G: 250 + G
    },
    {
        "name": "Stockpiler Supreme",
        "G_min": 8000, "G_max": 8999,
        "formula": lambda G: 250 + G
    },
    {
        "name": "Almighty Aggregator",
        "G_min": 9000, "G_max": 9999,
        "formula": lambda G: 250 + G
    },
    {
        "name": "Master Gatherer",
        "G_min": 10000, "G_max": 10999,
        "formula": lambda G: 250 + G
    },
    {
        "name": "Omnipotent Assemblert",
        "G_min": 11000, "G_max": 11999,
        "formula": lambda G: 250 + G
    },
    {
        "name": "Acquisition Idol",
        "G_min": 12000, "G_max": 12999,
        "formula": lambda G: 250 + G
    },
    # A partir de 13.000 jogos, nome será "Game Collector: X+"
]

# 2) Expansão de "Game Collector: 13.000+", "Game Collector: 14.000+" etc.
for start in range(13000, 28000, 1000):
    badge_name = f"Game Collector: {start:,}+"
    badges.append({
        "name": badge_name,
        "G_min": start,
        "G_max": start + 999,
        "formula": lambda G: 250 + G
    })

def badge_from_xp(xp):
    """
    Inverte XP → (nome_da_insígnia, número_de_jogos).
    Retorna (None, None) se não encontrar correspondência exata.
    """
    for badge in badges:
        for G in range(badge["G_min"], badge["G_max"] + 1):
            if badge["formula"](G) == xp:
                return badge["name"], G
    return None, None

def badge_number(G):
    """
    Retorna um valor arredondado para o número de jogos (G):
     - Valores manuais até 500:
         1-4     → 1
         5-9     → 5
         10-24   → 10
         25-49   → 25
         50-99   → 50
         100-249 → 100
         250-499 → 250
         500-999 → 500
     - A partir de 1000, arredonda para baixo em intervalos de 1000.
    """
    if G is None:
        return None
    if G < 1:
        return None
    if G < 5:
        return 1
    if G < 10:
        return 5
    if G < 25:
        return 10
    if G < 50:
        return 25
    if G < 100:
        return 50
    if G < 250:
        return 100
    if G < 500:
        return 250
    if G < 1000:
        return 500
    # A partir de 1000, arredonda para baixo a cada 1000
    return (G // 1000) * 1000


