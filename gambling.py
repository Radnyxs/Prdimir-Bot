""" Prdimírova hra života """

import asyncio
import os
import random
import sqlite3
import time
from collections import Counter, defaultdict

import discord
from discord.ext import commands

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gambling.db")

# ---------------------------------------------------------------- nastavení
ZISK_BEDNY = 0.9         # cena bedny = průměrná hodnota obsahu * zadaná hodnota
BEG_COOLDOWN = 30        # sekundy mezi žebráním
VEN_COOLDOWN = 60       # sekundy mezi procházkami venku
RANDE_COOLDOWN = 300    # sekundy mezi rande
PRACE_COOLDOWN = 180     # sekundy mezi pokusy o přijetí do práce
MESIC_SEKUND = 6 * 3600  # jeden "měsíc" ve hře = 6 hodin reálného času
MAX_MESICU = 3           # kolik měsíců výplaty se může nahromadit
MAX_OTEVRENI = 1000      # kolik beden najednou

# ---------------------------------------------------------------- povolené kanály
POVOLENE_KANALY = [
    1571248913955029105, # prdimírova-hra-života
    1481018427752845496, # pokec 1
    1481018108809314468, # pokec 2
    1481018152816083065, # pokec 3
    1481044760582951146, # Soukromý e-sex
]

# ---------------------------------------------------------------- rarity
RARITY = {
    "common":    {"nazev": "Common",    "sance": 60,   "emoji": "⚪", "barva": 0x9E9E9E, "ansi": "\u001b[1;37m", "poradi": 0},
    "uncommon":  {"nazev": "Uncommon",  "sance": 25,   "emoji": "🟢", "barva": 0x4CAF50, "ansi": "\u001b[1;32m", "poradi": 1},
    "rare":      {"nazev": "Rare",      "sance": 10,   "emoji": "🔵", "barva": 0x2196F3, "ansi": "\u001b[1;34m", "poradi": 2},
    "epic":      {"nazev": "Epic",      "sance": 4,    "emoji": "🟣", "barva": 0x9C27B0, "ansi": "\u001b[1;35m", "poradi": 3},
    "legendary": {"nazev": "Legendary", "sance": 0.75, "emoji": "🟡", "barva": 0xFFC107, "ansi": "\u001b[1;33m", "poradi": 4},
    "godlike":   {"nazev": "Godlike",   "sance": 0.20, "emoji": "🔴", "barva": 0xF44336, "ansi": "\u001b[1;31m", "poradi": 5},
    "voidborn":  {"nazev": "Voidborn",  "sance": 0.05, "emoji": "⚫", "barva": 0x3B0A5A, "ansi": "\u001b[1;30m", "poradi": 6},
}

# ---------------------------------------------------------------- investice (firmy a krypto)
INVESTMENTS_DATA = {
    "NEVIDIMJA": {"nazev": "NEVIDIMJÁ Corp.", "emoji": "🟩", "typ": "Firma", "base": 1500, "popis": "Výrobce grafických karet, které nikdo nevidí skladem."},
    "JABLICKO": {"nazev": "Jablíčko", "emoji": "🍎", "typ": "Firma", "base": 3200, "popis": "Prodávají předražené hliníkové cihly s rysem jablka."},
    "BITCHCOIN": {"nazev": "Bitchcoin", "emoji": "🪙", "typ": "Krypto", "base": 45000, "popis": "Digitální měna pro každého, kdo propadl hazardu."},
    "NEGEREUM": {"nazev": "Negereum", "emoji": "💠", "typ": "Krypto", "base": 12000, "popis": "Chytré smlouvy a drahé poplatky za převod."},
    "GIGACHAD": {"nazev": "GigaChad Motors", "emoji": "🚗", "typ": "Firma", "base": 8500, "popis": "Elektromobily, co občas zapomenou zatočit."},
    "MOJIDA": {"nazev": "Mojida", "emoji": "🥰", "typ": "Firma", "base": 950, "popis": "Společnost žijící z animovaných smajlíků."},
}

# ---------------------------------------------------------------- bedny a itemy
BEDNY_DATA = {
    "popelnice": {
        "nazev": "Popelnicová bedna",
        "emoji": "🗑️",
        "popis": "Co lidé vyhodili, to ty vyhrabeš.",
        "itemy": [
            ("P01", "🌂 Rozbitý deštník", "common", 30),
            ("P02", "🥫 Prázdná plechovka", "common", 35),
            ("P03", "🧦 Ponožka bez páru", "uncommon", 120),
            ("P04", "🧸 Zaprášený medvídek", "uncommon", 200),
            ("P05", "🎮 Použitá PlayStation 1", "rare", 1000),
            ("P06", "🃏 Pokémon karta (podezřele pravá)", "rare", 1500),
            ("P07", "🪎 Dědův poklad z půdy", "epic", 3500),
            ("P08", "🦷 FlyGunův zub", "epic", 5000),
            ("P09", "🎫🍫 Zlatý lístek Willyho Wonky", "legendary", 15000),
            ("P10", "🚽🪙 Zlatý záchod", "godlike", 120000),
            ("P11", "🗑️🛸 Popelnice z jiné dimenze", "voidborn", 600000),
        ],
    },
    "hospoda": {
        "nazev": "Hospodská bedna",
        "emoji": "🍺",
        "popis": "Vítej v baru U Médi! Pijeme rekreačně.",
        "itemy": [
            ("H01", "🫙 Prázdný půllitr", "common", 40),
            ("H02", "🍺 Plný půllitr", "common", 70),
            ("H03", "🍖 Utopenec", "uncommon", 130),
            ("H04", "🥃 Panák whiskey", "uncommon", 200),
            ("H05", "🐱 Hospodská kočka (plyšová)", "rare", 599),
            ("H06", "🚰 Zlatý kohoutek", "rare", 900),
            ("H07", "🪟 Stolek u okna (rezervovaný)", "epic", 4000),
            ("H08", "👗 Šaty barmanovy ex z Louis Vuitton", "epic", 6999),
            ("H09", "💶🤑 Věčný účet u barmana", "legendary", 20000),
            ("H10", "🍻👑 Zlatý půllitr šampiona", "godlike", 139999),
            ("H11", "🍺♾️ Pivo, které nikdy nedojde", "voidborn", 800000),
        ],
    },
    "vesmir": {
        "nazev": "Kosmická bedna",
        "emoji": "🚀",
        "popis": "Odpadky z celé galaxie, některé jsou ale cenné.",
        "itemy": [
            ("K01", "🪨 Kosmický šrot", "common", 250),
            ("K02", "⛽ Prázdná palivová nádrž", "common", 250),
            ("K03", "🍽️ Astronautické jídlo z tuby", "uncommon", 400),
            ("K04", "💫 Kosmická hvězda", "uncommon", 999),
            ("K05", "🏖️ Marťanský písek", "rare", 2999),
            ("K06", "🛰️ Kus satelitu", "rare", 6999),
            ("K07", "🌐 Hologram planety Země", "epic", 44999),
            ("K08", "🕳️ Mini černá díra v lahvičce", "epic", 55999),
            ("K09", "👽🛸 Mimozemská technologie", "legendary", 109999),
            ("K10", "🪐💍 Prsten planety Jupiter", "godlike", 300000),
            ("K11", "👁️🌫️ Oko Prázdnoty", "voidborn", 1500000),
        ],
    },
    "ruda": {
        "nazev": "Rudová bedna",
        "emoji": "💍",
        "popis": "Všechny vzácné rudy v jedné bedně.",
        "itemy": [
            ("R01", "🌱 Hlína ze zahrady", "common", 15),
            ("R02", "🔥 Uhlí (100kg)", "uncommon", 249),
            ("R03", "🔨 Železo (1t)", "rare", 2500),
            ("R04", "🔶 Měď (50kg) - cigánský sen", "epic", 20000),
            ("R05", "🏅 Zlato (100g)", "epic", 199999),
            ("R06", "🟩🍀 Jadeit (10g)", "legendary", 499999),
            ("R07", "💎💍 Diamant (5g)", "godlike", 2499999),
            ("R08", "🟣💥 Antimatter (1μg)", "voidborn", 29999999),
        ],
    },
    "super": {
        "nazev": "Superschopnostní bedna",
        "emoji": "💪",
        "popis": "Budeme další Avengers!!",
        "itemy": [
            ("S01", "🐇 Honze skákání", "common", 999),
            ("S02", "💪 Supersíla", "uncommon", 70000),
            ("S03", "🏃 Nadlidské reflexy", "uncommon", 70000),
            ("S04", "🧚 Létání", "rare", 200000),
            ("S05", "📖 Death Note", "epic", 500000),
            ("S06", "🕴️ Teleportace", "epic", 500000),
            ("S07", "🍀🔢 Manipulace pravděpodobností", "legendary", 2500000),
            ("S08", "💉😤 Titan sérum z AoT", "godlike", 12000000),
            ("S09", "🌊🛘🔥🌪️ Avatar", "voidborn", 50000000),
        ],
    },
}

ITEMS = {}
BEDNY = {}
for _klic, _cfg in BEDNY_DATA.items():
    _podle_rarity = defaultdict(list)
    for _kod, _nazev, _rarita, _hodnota in _cfg["itemy"]:
        assert _kod not in ITEMS, f"duplicitní kód {_kod}"
        _podle_rarity[_rarita].append(_kod)
        ITEMS[_kod] = {"kod": _kod, "nazev": _nazev, "rarita": _rarita,
                       "hodnota": _hodnota, "bedna": _klic, "sance": 0.0}
    assert set(_podle_rarity) == set(RARITY), f"bedna {_klic} nemá všechny rarity"
    _kody, _vahy = [], []
    for _rarita, _seznam in _podle_rarity.items():
        _sance = RARITY[_rarita]["sance"] / len(_seznam)
        for _kod in _seznam:
            ITEMS[_kod]["sance"] = _sance
            _kody.append(_kod)
            _vahy.append(_sance)
    _ev = sum(ITEMS[k]["hodnota"] * w / 100 for k, w in zip(_kody, _vahy))
    BEDNY[_klic] = {
        "nazev": _cfg["nazev"], "emoji": _cfg["emoji"], "popis": _cfg["popis"],
        "kody": _kody, "vahy": _vahy,
        "cena": int(round(_ev * ZISK_BEDNY / 10) * 10),
    }

# ---------------------------------------------------------------- partneři (Tinder & venku)
# pohlavi: "zena" nebo "muz"
# kde: "tinder", "venku", nebo "oboje"
# buff_typ:
#   - "plat"        -> zvýší výplatu z práce o (buff_hodnota * 100) %
#   - "sleva_bedny" -> zlevní bedny o (buff_hodnota * 100) %
#   - "kasino"      -> zvýší výhry ve slotech, blackjacku, pokeru i ruletě o (buff_hodnota * 100) %
#   - "kapesne"     -> při každém rande ti dá kapesné ve výši buff_hodnota (v Kč)
PARTNERI = {
    # --- ŽENY ---
    "magda_ucetni": {
        "jmeno": "Magdaléna (24)",
        "pohlavi": "zena",
        "kde": "tinder",
        "kategorie": "Účetní",
        "bio": "UHK\nlepší účetní jak izraelci 😁😁",
        "sance_match": 0.65,
        "narocnost": 1,
        "buff_typ": "plat",
        "buff_hodnota": 0.15,
        "buff_popis": "💵 +15 % k výplatě z práce",
    },
    "katarina_mentalistka": {
        "jmeno": "Katarína (22)",
        "pohlavi": "zena",
        "kde": "tinder",
        "kategorie": "Dealerka",
        "bio": "mentalistka, využívám to v kasinech :p",
        "sance_match": 0.45,
        "narocnost": 2,
        "buff_typ": "kasino",
        "buff_hodnota": 0.15,
        "buff_popis": "🎰 +15 % k výhrám v kasinu",
    },
    "vanessa_dedicka": {
        "jmeno": "Vanessa (21)",
        "pohlavi": "zena",
        "kde": "tinder",
        "kategorie": "Bohatá dědička",
        "bio": "Táta vlastní půlku Prahy. Kapesné pro přítele je samozřejmost.",
        "sance_match": 0.25,
        "narocnost": 3,
        "buff_typ": "kapesne",
        "buff_hodnota": 10000,
        "buff_popis": "💎 +10 000 Kč kapesné při každém rande",
    },
    "klara_knihovnice": {
        "jmeno": "Klára (25)",
        "pohlavi": "zena",
        "kde": "venku",
        "kategorie": "Sběratelka starožitností",
        "bio": "Potkal jsi ji u antikvariátu. Má kontakty na levné bedny.",
        "sance_match": 0.60,
        "narocnost": 1,
        "buff_typ": "sleva_bedny",
        "buff_hodnota": 0.15,
        "buff_popis": "📦 15% sleva na všechny bedny",
    },
    "natalie_mafianka": {
        "jmeno": "Natálie (25)",
        "pohlavi": "zena",
        "kde": "venku",
        "kategorie": "Dcera kmotra",
        "bio": "Seděla sama v zapadlém baru. Nikdo se jí neodváží odporovat, od pohledu vypadá jako alt mamina.",
        "sance_match": 0.30,
        "narocnost": 3,
        "buff_typ": "plat",
        "buff_hodnota": 0.35,
        "buff_popis": "🪎 +35 % k výplatě z práce",
    },

    # --- MUŽI ---
    "patrik_pravnik": {
        "jmeno": "Patrik (31)",
        "pohlavi": "muz",
        "kde": "tinder",
        "kategorie": "Právník",
        "bio": "Jsem nejlepší právník a konzultant v ČR.",
        "sance_match": 0.55,
        "narocnost": 2,
        "buff_typ": "plat",
        "buff_hodnota": 0.20,
        "buff_popis": "⚖️ +20 % k výplatě z práce",
    },
    "lukas_trader": {
        "jmeno": "Lukáš (26)",
        "pohlavi": "muz",
        "kde": "tinder",
        "kategorie": "Krypto barón",
        "bio": "Koupil jsem Bitchcoin v roce 2012. Ano bylo mi 12, tuff. Rád se podělím.",
        "sance_match": 0.30,
        "narocnost": 3,
        "buff_typ": "kapesne",
        "buff_hodnota": 10000,
        "buff_popis": "🪙 +10 000 Kč kapesné při každém rande",
    },
    "bartolomej_matematik": {
        "jmeno": "Bartoloměj (24)",
        "pohlavi": "muz",
        "kde": "tinder",
        "kategorie": "Počítadlo karet",
        "bio": "Znám všechny kasinové triky. Chceš pomoct - hit me up.",
        "sance_match": 0.50,
        "narocnost": 1,
        "buff_typ": "kasino",
        "buff_hodnota": 0.12,
        "buff_popis": "🃏 +12 % k výhrám v kasinu",
    },
    "ondra_skladnik": {
        "jmeno": "Ondra (28)",
        "pohlavi": "muz",
        "kde": "venku",
        "kategorie": "Šéf celního skladu",
        "bio": "Potkal jsi ho u přístavu. Umí zařídit bedny pod rukou.",
        "sance_match": 0.60,
        "narocnost": 1,
        "buff_typ": "sleva_bedny",
        "buff_hodnota": 0.15,
        "buff_popis": "📦 15% sleva na všechny bedny",
    },
    "viktor_boss": {
        "jmeno": "Viktor (34)",
        "pohlavi": "muz",
        "kde": "venku",
        "kategorie": "Majitel kasina",
        "bio": "Vystoupil z černého Mercedesu. VIP servis máš jistý.",
        "sance_match": 0.25,
        "narocnost": 3,
        "buff_typ": "kasino",
        "buff_hodnota": 0.15,
        "buff_popis": "👑 +15 % k výhrám v kasinu",
    },
}

# ---------------------------------------------------------------- práce a žebrání
PRACE = {
    "letaky": {"nazev": "🗞️ Roznašeč letáků",
               "popis": "Dobrý den, mám pro vás letáček. :-)",
               "plat": 11000, "sance": 0.90},
    "nadobi": {"nazev": "🍻 Umývač nádobí v hospodě",
               "popis": "Každý večer za odměnu posloucháš alkoholiky v krizi středního věku.",
               "plat": 16000, "sance": 0.80},
    "taxi": {"nazev": "🚕 Taxikář",
             "popis": "Tommy Angelo?",
             "plat": 36000, "sance": 0.50},
    "programator": {"nazev": "💻 Programátor",
                    "popis": "Děláš svoji práci s Claude a tváříš se, že víš, co děláš.",
                    "plat": 60000, "sance": 0.35},
    "tiktok": {"nazev": "💃 TikTok influencer",
               "popis": "Tančíš před telefonem a doufáš, že to nikdo z rodiny neuvidí.",
               "plat": 100000, "sance": 0.20},
    "poslanec": {"nazev": "😴 Poslanec",
                 "popis": "Hlavně nic nedělat a mít pěknou kancelář.",
                 "plat": 170000, "sance": 0.10},
    "fbi": {"nazev": "🤵 FBI Agent",
            "popis": "Kam tě pošle tvoje další mise?",
            "plat": 600000, "sance": 0.025},
    "onlyfans": {"nazev": "🔞 OnlyFans superstar",
                 "popis": "Bro think he Gattouz.",
                 "plat": 1400000, "sance": 0.01},
    "mafie": {"nazev": "🇮🇹 Sicilská Mafie",
              "popis": "Staneš se členem největší sicilské Mafie.",
              "plat": 2750000, "sance": 0.005}
}

ZEBRANI = [
    (0.25, ["Patrick Jane odrbal kasino v Praze a dal ti půlku výdělků.", "https://tenor.com/view/patrick-jane-simon-baker-gif-16469773169763019049"], 250000, 300000),
    (0.25, ["Na zahradu ti spadl vzácný lunární meteorit, oh no!! Jdeš ho prodat...ou jes.", "https://tenor.com/view/boom-bomb-explosion-iron-man-tony-stark-gif-15429820"], 130000, 200000),
    (0.25, ["Dostal/a jsi perník od Heisenberga a prodal/a ho.", "https://tenor.com/view/walter-white-meth-gif-26319392"], 100000, 120000),
    (0.25, ['Přišel businessman a řekl ti "Tady máš, zainvestuj to."', 'https://tenor.com/view/anonymous-foundation-make-money-foundation-gif-15622453'], 50000, 50000),
    (0.25, ["RAMky jsou v dnešní době drahý...ou co to je tam za rohem?...Nic, podívej se do kapsy. :-)", "https://tenor.com/view/el-luchito-con-la-ram-gif-15851431"], 35000, 60000),
    (0.25, ["Tvé smysly zaznamenaly rozbitý bankomat...infinite money glitch?", "https://tenor.com/view/money-money-money-gif-15228319"], 30000, 55000),
    (0.5, ["Ó hele, strom peněžník!", "https://tenor.com/view/shake-money-grows-on-tree-money-rain-level-up-mafia-boss-gif-14984899"], 15000, 20000),
    (0.5, ["Přišel skutečný MrBeast!! Co tu dělá?", "https://tenor.com/view/mr-beast-meme-little-beast-ireetable-gif-1335428652767034021"], 10000, 25000),
    (1, "NVIDIA CEO Jensen Huang ti dal nabídku, jestli bys nechtěl/a aféru.", 5000, 10000),
    (1.5, "GTA 6 vychází!! Nějakej borec ti na ní dal prachy.", 2500, 4000),
    (2, "Dnes prdění na Karlově mostě, překvapivě to fungovalo.", 500, 1500),
    (2, "Sponzorováno Izraelem. 🇮🇱", 2000, 2000),
    (2, "Z nebes na tebe spadla tisícovka, vau!", 1000, 1000),
    (2, ["Všiml si tě budget MrBeast a doufáš, že ti dá majlant.", "Paní v obleku ti řekla, ať jdeš k barberovi."], 500, 1500),
    (5, 'Příspěvek na hru "Sex with Hitler 2"', 250, 400),
    (5, "Prdnul/a sis a turista to vzal jako magický trik.", 200, 500),
    (5, "Dal/a sis 1v1 v Clash Royale proti kolemjdoucímu, výhra!!", 300, 450),
    (16, "Nějaká babička ti hodila drobné do kelímku.", 10, 50),
    (16, ['Přišlo děcko a zařvalo "SIX SEVEN".', "Borec stál před tebou 5 minut s peněženkou a počítal, aby ti dal přesně 67 Kč."], 67, 67),
    (15, "Turista tě vzal za pouličního umělce a dal ti slušné spropitné.", 50, 200),
    (10, ["Pod lavičkou jsi našel/a zapomenutou stokorunu.", "Ahoj, tady Prdimír, tady máš kilčo na štrúdl."], 100, 100),
    (5, ["Nějaký chlápek ti dal rovnou celou kapesní kasičku.", "Dostal/a jsi příspěvek na dobrý kebab."], 200, 400),
    (10, "Nikdo si tě nevšiml. Jen jedna holubice ti něco hodila na hlavu.", 0, 0),
]


# ---------------------------------------------------------------- pomocné funkce
def kc(n):
    return f"{int(n):,}".replace(",", " ") + " Kč"


def cas(sekundy):
    s = int(max(0, sekundy))
    h, zb = divmod(s, 3600)
    m, s = divmod(zb, 60)
    casti = []
    if h:
        casti.append(f"{h} h")
    if m:
        casti.append(f"{m} min")
    if s or not casti:
        casti.append(f"{s} s")
    return " ".join(casti)


def najdi_item(text):
    t = text.strip()
    if t.upper() in ITEMS:
        return t.upper()
    t = t.lower()
    for kod, it in ITEMS.items():
        if it["nazev"].lower() == t:
            return kod
    for kod, it in ITEMS.items():
        if t in it["nazev"].lower():
            return kod
    return None


def najdi_investici(text):
    t = text.strip().upper()
    if t in INVESTMENTS_DATA:
        return t
    for sym, data in INVESTMENTS_DATA.items():
        if t in data["nazev"].upper() or t == sym:
            return sym
    return None


def vygeneruj_graf(history):
    if not history:
        return "---"
    min_v = min(history)
    max_v = max(history)
    diff = max_v - min_v if max_v != min_v else 1
    blocks = ["▂", "▃", "▄", "▅", "▆", "▇", "█"]
    chart = ""
    for val in history:
        idx = int((val - min_v) / diff * (len(blocks) - 1))
        chart += blocks[max(0, min(idx, len(blocks) - 1))]
    return chart


def povolena_pohlavi(pohlavi: str, orientace: str) -> set[str]:
    p = (pohlavi or "muz").lower()
    o = (orientace or "hetero").lower()
    if o == "bi":
        return {"muz", "zena"}
    if o == "homo":
        return {"muz"} if p == "muz" else {"zena"}
    # default hetero
    return {"zena"} if p == "muz" else {"muz"}


# ---------------------------------------------------------------- databáze
class Databaze:
    """SQLite. Všechny operace jsou synchronní a bez `await` uvnitř."""

    def __init__(self, cesta):
        self.con = sqlite3.connect(cesta)
        self.con.row_factory = sqlite3.Row
        self.con.executescript("""
            CREATE TABLE IF NOT EXISTS players (
                user_id     INTEGER PRIMARY KEY,
                balance     INTEGER NOT NULL DEFAULT 0,
                job_id      TEXT,
                last_beg    REAL NOT NULL DEFAULT 0,
                last_pay    REAL NOT NULL DEFAULT 0,
                last_apply  REAL NOT NULL DEFAULT 0,
                pohlavi     TEXT NOT NULL DEFAULT 'muz',
                orientace   TEXT NOT NULL DEFAULT 'hetero',
                partner_id  TEXT,
                spokojenost INTEGER NOT NULL DEFAULT 100,
                last_rande  REAL NOT NULL DEFAULT 0,
                last_venku  REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS inventory (
                user_id   INTEGER NOT NULL,
                item_code TEXT NOT NULL,
                count     INTEGER NOT NULL,
                PRIMARY KEY (user_id, item_code)
            );
            CREATE TABLE IF NOT EXISTS market (
                symbol TEXT PRIMARY KEY,
                price REAL NOT NULL,
                history TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS portfolio (
                user_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                shares REAL NOT NULL,
                invested_czk REAL NOT NULL,
                PRIMARY KEY (user_id, symbol)
            );
        """)
        self.con.commit()
        self._migruj_players()
        self._init_market()

    def _migruj_players(self):
        """Bezpečně doplní nové sloupce do již existující databáze."""
        existujici = {r["name"] for r in self.con.execute("PRAGMA table_info(players)").fetchall()}
        nove_sloupce = {
            "pohlavi": "TEXT NOT NULL DEFAULT 'muz'",
            "orientace": "TEXT NOT NULL DEFAULT 'hetero'",
            "partner_id": "TEXT",
            "spokojenost": "INTEGER NOT NULL DEFAULT 100",
            "last_rande": "REAL NOT NULL DEFAULT 0",
            "last_venku": "REAL NOT NULL DEFAULT 0",
        }
        for col, definition in nove_sloupce.items():
            if col not in existujici:
                self.con.execute(f"ALTER TABLE players ADD COLUMN {col} {definition}")
        self.con.commit()

    def _init_market(self):
        rows = self.con.execute("SELECT symbol FROM market").fetchall()
        existing = {r["symbol"] for r in rows}
        for sym, data in INVESTMENTS_DATA.items():
            if sym not in existing:
                p = float(data["base"])
                hist = [str(int(p * random.uniform(0.85, 1.15))) for _ in range(6)]
                hist.append(str(int(p)))
                self.con.execute("INSERT OR REPLACE INTO market (symbol, price, history) VALUES (?, ?, ?)",
                                 (sym, p, ",".join(hist)))
        self.con.commit()

    def get_market_asset(self, symbol):
        r = self.con.execute("SELECT price, history FROM market WHERE symbol = ?", (symbol,)).fetchone()
        if not r:
            return None
        return r["price"], [float(x) for x in r["history"].split(",")]

    def update_market_asset(self, symbol):
        price, hist = self.get_market_asset(symbol)
        if not price:
            return None, None
        change_pct = random.uniform(-0.12, 0.15)
        new_price = max(10, round(price * (1 + change_pct), 2))
        hist.pop(0)
        hist.append(new_price)
        hist_str = ",".join(str(int(x)) for x in hist)
        self.con.execute("UPDATE market SET price = ?, history = ? WHERE symbol = ?", (new_price, hist_str, symbol))
        self.con.commit()
        return new_price, hist

    def get_all_market(self):
        rows = self.con.execute("SELECT symbol, price, history FROM market").fetchall()
        result = {}
        for r in rows:
            sym = r["symbol"]
            price = r["price"]
            hist = [float(x) for x in r["history"].split(",")]
            if random.random() < 0.4:
                price, hist = self.update_market_asset(sym)
            result[sym] = {"price": price, "history": hist}
        return result

    # --- hráč
    def hrac(self, uid):
        self.con.execute("INSERT OR IGNORE INTO players (user_id) VALUES (?)", (uid,))
        self.con.commit()
        return self.con.execute("SELECT * FROM players WHERE user_id=?", (uid,)).fetchone()

    def nastav(self, uid, **pole):
        sloupce = ", ".join(f"{k}=?" for k in pole)
        self.con.execute(f"UPDATE players SET {sloupce} WHERE user_id=?", (*pole.values(), uid))
        self.con.commit()

    def pricti(self, uid, castka):
        self.hrac(uid)
        self.con.execute("UPDATE players SET balance = balance + ? WHERE user_id=?", (int(castka), uid))
        self.con.commit()

    # --- inventář
    def pocet(self, uid, kod):
        r = self.con.execute("SELECT count FROM inventory WHERE user_id=? AND item_code=?",
                             (uid, kod)).fetchone()
        return r["count"] if r else 0

    def inventar(self, uid):
        rows = self.con.execute(
            "SELECT item_code, count FROM inventory WHERE user_id=? AND count>0", (uid,)).fetchall()
        return {r["item_code"]: r["count"] for r in rows}

    def _pridej_item(self, uid, kod, n):
        self.con.execute(
            "INSERT INTO inventory (user_id, item_code, count) VALUES (?,?,?) "
            "ON CONFLICT(user_id, item_code) DO UPDATE SET count = count + excluded.count",
            (uid, kod, n))

    def _odeber_item(self, uid, kod, n):
        self.con.execute("UPDATE inventory SET count = count - ? WHERE user_id=? AND item_code=?",
                         (n, uid, kod))
        self.con.execute("DELETE FROM inventory WHERE user_id=? AND item_code=? AND count<=0",
                         (uid, kod))

    def majitele(self, kod):
        r = self.con.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(count),0) AS k FROM inventory "
            "WHERE item_code=? AND count>0", (kod,)).fetchone()
        return r["n"], r["k"]

    # --- transakce beden
    def koupit_bedny(self, uid, cena, kody):
        zustatek = self.hrac(uid)["balance"]
        if zustatek < cena:
            return None
        self.con.execute("UPDATE players SET balance = balance - ? WHERE user_id=?", (cena, uid))
        for kod in kody:
            self._pridej_item(uid, kod, 1)
        self.con.commit()
        return zustatek - cena

    def prodat_botovi(self, uid, kod, kolik, castka):
        self.hrac(uid)
        if self.pocet(uid, kod) < kolik:
            return False
        self._odeber_item(uid, kod, kolik)
        self.con.execute("UPDATE players SET balance = balance + ? WHERE user_id=?", (castka, uid))
        self.con.commit()
        return True

    def vymena(self, a, a_kod, b, b_kod):
        if self.pocet(a, a_kod) < 1 or self.pocet(b, b_kod) < 1:
            return False
        self._odeber_item(a, a_kod, 1)
        self._odeber_item(b, b_kod, 1)
        self._pridej_item(a, b_kod, 1)
        self._pridej_item(b, a_kod, 1)
        self.con.commit()
        return True

    def prodej_hraci(self, prodavajici, kupujici, kod, cena):
        self.hrac(prodavajici)
        zustatek = self.hrac(kupujici)["balance"]
        if self.pocet(prodavajici, kod) < 1:
            return "item"
        if zustatek < cena:
            return "penize"
        self._odeber_item(prodavajici, kod, 1)
        self._pridej_item(kupujici, kod, 1)
        self.con.execute("UPDATE players SET balance = balance - ? WHERE user_id=?", (cena, kupujici))
        self.con.execute("UPDATE players SET balance = balance + ? WHERE user_id=?", (cena, prodavajici))
        self.con.commit()
        return "ok"

    # --- žebříčky
    def vsichni(self):
        hraci = {r["user_id"]: r["balance"]
                 for r in self.con.execute("SELECT user_id, balance FROM players")}
        inv = defaultdict(dict)
        for r in self.con.execute("SELECT user_id, item_code, count FROM inventory WHERE count>0"):
            inv[r["user_id"]][r["item_code"]] = r["count"]
        return hraci, inv


# ---------------------------------------------------------------- UI: Obchod a Inventář
class ObchodView(discord.ui.View):
    """Tlačítka Přijmout / Odmítnout. Klikat smí jen ten, komu je nabídka určena."""

    def __init__(self, target_id, provest):
        super().__init__(timeout=60)
        self.target_id = target_id
        self.provest = provest
        self.hotovo = False
        self.message = None

    async def interaction_check(self, interaction):
        if interaction.user.id != self.target_id:
            await interaction.response.send_message("Tahle nabídka není pro tebe.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Přijmout", style=discord.ButtonStyle.success, emoji="✅")
    async def prijmout(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.hotovo:
            return
        self.hotovo = True
        self.stop()
        ok, text = self.provest()
        for c in self.children:
            c.disabled = True
        embed = discord.Embed(description=text, color=0x4CAF50 if ok else 0xF44336)
        await interaction.response.edit_message(content=None, embed=embed, view=self)

    @discord.ui.button(label="Odmítnout", style=discord.ButtonStyle.danger, emoji="✖️")
    async def odmitnout(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.hotovo:
            return
        self.hotovo = True
        self.stop()
        for c in self.children:
            c.disabled = True
        embed = discord.Embed(description="❌ Nabídka byla odmítnuta.", color=0xF44336)
        await interaction.response.edit_message(content=None, embed=embed, view=self)

    async def on_timeout(self):
        if self.hotovo or self.message is None:
            return
        for c in self.children:
            c.disabled = True
        try:
            await self.message.edit(content=None, view=self,
                                    embed=discord.Embed(description="⌛ Nabídka vypršela.",
                                                        color=0x757575))
        except discord.HTTPException:
            pass


class InventarSelect(discord.ui.Select):
    def __init__(self, cog, kody):
        moznosti = []
        for kod in kody[:25]:
            it = ITEMS[kod]
            r = RARITY[it["rarita"]]
            moznosti.append(discord.SelectOption(
                label=it["nazev"][:100], value=kod,
                description=f"{r['nazev']} • {kc(it['hodnota'])} • {kod}"[:100],
                emoji=r["emoji"]))
        super().__init__(placeholder="Vyber item a zjisti, kolik lidí ho vlastní…",
                         options=moznosti)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.cog.item_embed(self.values[0]),
                                                ephemeral=True)


# ---------------------------------------------------------------- UI: Seznamka (Tinder & Venku)
class TinderView(discord.ui.View):
    def __init__(self, cog, user_id, kandidati, je_venku=False):
        super().__init__(timeout=90)
        self.cog = cog
        self.user_id = user_id
        self.kandidati = list(kandidati)
        random.shuffle(self.kandidati)
        self.idx = 0
        self.je_venku = je_venku
        self.hotovo = False
        self.message = None

    def aktualni_klic(self):
        return self.kandidati[self.idx % len(self.kandidati)]

    def render_embed(self):
        klic = self.aktualni_klic()
        pt = PARTNERI[klic]
        p = self.cog.db.hrac(self.user_id)

        # Bonus k šanci na match podle bohatství a práce
        bonus_sance = 0.0
        if p["balance"] >= 500000:
            bonus_sance += 0.15
        elif p["balance"] >= 100000:
            bonus_sance += 0.08
        if p["job_id"] in ("mafie", "onlyfans", "fbi", "poslanec"):
            bonus_sance += 0.10

        efektivni_sance = min(0.95, pt["sance_match"] + bonus_sance)
        hvezdy = "⭐" * pt["narocnost"]

        titul = "🚶 Náhodné setkání venku!" if self.je_venku else "🔥 PrdTinder"
        barva = 0x2ECC71 if self.je_venku else 0xE91E63

        e = discord.Embed(
            title=f"{titul} — {pt['jmeno']}",
            description=f"*{pt['bio']}*",
            color=barva,
        )
        e.add_field(name="Povolání", value=pt["kategorie"], inline=True)
        e.add_field(name="Náročnost", value=hvezdy, inline=True)
        e.add_field(name="Šance na úspěch", value=f"{int(efektivni_sance * 100)} %", inline=True)
        e.add_field(name="✨ Pasivní schopnost", value=pt["buff_popis"], inline=False)
        e.set_footer(text="Klikni na ❤️ pro oslovení / swipe doprava, nebo ❌ pro odmítnutí.")
        return e

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Tohle není tvoje rande!", ephemeral=True)
            return False
        return True

    def _disable_all(self):
        for c in self.children:
            c.disabled = True

    @discord.ui.button(label="Oslovit", style=discord.ButtonStyle.success, emoji="❤️")
    async def like(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.hotovo:
            return
        klic = self.aktualni_klic()
        pt = PARTNERI[klic]
        p = self.cog.db.hrac(self.user_id)

        if p["partner_id"]:
            self.hotovo = True
            self._disable_all()
            self.stop()
            await interaction.response.edit_message(
                embed=discord.Embed(description="❌ Už někoho máš! Nejdřív se rozejdi přes `prd rozchod`.", color=0xF44336),
                view=self
            )
            return

        bonus_sance = 0.0
        if p["balance"] >= 500000:
            bonus_sance += 0.15
        elif p["balance"] >= 100000:
            bonus_sance += 0.08
        if p["job_id"] in ("mafie", "onlyfans", "fbi", "poslanec"):
            bonus_sance += 0.10

        efektivni_sance = min(0.95, pt["sance_match"] + bonus_sance)

        if random.random() < efektivni_sance:
            self.hotovo = True
            self._disable_all()
            self.stop()
            self.cog.db.nastav(
                self.user_id,
                partner_id=klic,
                spokojenost=100,
                last_rande=time.time()
            )
            e = discord.Embed(
                title="💘 IT'S A MATCH! Máte vztah!",
                description=(
                    f"Gratulujeme! **{pt['jmeno']}** s tebou začíná chodit!\n\n"
                    f"**Aktivní bonus:** {pt['buff_popis']}\n"
                    "Nezapomeň chodit na rande (`prd rande`) nebo dávat dárky (`prd darek <item>`)!"
                ),
                color=0xE91E63,
            )
            await interaction.response.edit_message(embed=e, view=self)
        else:
            if self.je_venku:
                self.hotovo = True
                self._disable_all()
                self.stop()
                e = discord.Embed(
                    title="💔 Košem na ulici!",
                    description=f"**{pt['jmeno']}** se na tebe podíval/a, zasmál/a se a odešel/a pryč.",
                    color=0x757575,
                )
                await interaction.response.edit_message(embed=e, view=self)
            else:
                self.idx += 1
                e = self.render_embed()
                e.set_author(name=f"💔 {pt['jmeno']} nedal/a match. Další profil:")
                await interaction.response.edit_message(embed=e, view=self)

    @discord.ui.button(label="Odmítnout", style=discord.ButtonStyle.secondary, emoji="❌")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.hotovo:
            return
        if self.je_venku:
            self.hotovo = True
            self._disable_all()
            self.stop()
            await interaction.response.edit_message(
                embed=discord.Embed(description="🚶 Šel jsi dál a nechal to být.", color=0x757575),
                view=self
            )
        else:
            self.idx += 1
            await interaction.response.edit_message(embed=self.render_embed(), view=self)

    async def on_timeout(self):
        if self.hotovo or self.message is None:
            return
        self.hotovo = True
        self._disable_all()
        try:
            await self.message.edit(
                embed=discord.Embed(description="⌛ Seznamka se zavřela kvůli neaktivitě.", color=0x757575),
                view=self
            )
        except discord.HTTPException:
            pass


# ---------------------------------------------------------------- Kasino UI
SUITS = ["♠️", "♥️", "♦️", "♣️"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALS = {r: i + 2 for i, r in enumerate(RANKS)}


def vytvor_balicek():
    deck = [(r, s) for r in RANKS for s in SUITS]
    random.shuffle(deck)
    return deck


def format_karty(hand, skryta=False):
    if skryta and len(hand) >= 2:
        return f"`{hand[0][0]}{hand[0][1]}`, `❓`"
    return ", ".join(f"`{r}{s}`" for r, s in hand)


class BlackjackView(discord.ui.View):
    def __init__(self, cog, ctx, bet, deck, player_hand, dealer_hand):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.bet = bet
        self.deck = deck
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.hotovo = False
        self.message = None

    @staticmethod
    def skore(hand):
        total = 0
        aces = 0
        for rank, _ in hand:
            if rank in ("J", "Q", "K"):
                total += 10
            elif rank == "A":
                aces += 1
                total += 11
            else:
                total += int(rank)
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def _disable_all(self):
        for child in self.children:
            child.disabled = True

    @discord.ui.button(label="Hit (Vzít kartu)", style=discord.ButtonStyle.primary, emoji="🃏")
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Tahle hra není pro tebe!", ephemeral=True)
            return
        if self.hotovo:
            return

        self.player_hand.append(self.deck.pop())
        p_score = self.skore(self.player_hand)

        if p_score > 21:
            self.hotovo = True
            self._disable_all()
            self.stop()
            e = discord.Embed(
                title="🃏 Blackjack – Prohra!",
                description=f"Přestřelil jsi s **{p_score}** body!\nZtratil jsi **{kc(self.bet)}**.",
                color=0xF44336,
            )
            e.add_field(name=f"Tvoje karty ({p_score})", value=format_karty(self.player_hand), inline=True)
            e.add_field(name=f"Dealer ({self.skore(self.dealer_hand)})", value=format_karty(self.dealer_hand), inline=True)
            e.set_footer(text=f"Zůstatek: {kc(self.cog.db.hrac(self.ctx.author.id)['balance'])}")
            await interaction.response.edit_message(embed=e, view=self)
        elif p_score == 21:
            await self._vyhodnotit_stand(interaction)
        else:
            e = discord.Embed(
                title="🃏 Blackjack",
                description=f"Sázka: **{kc(self.bet)}**\nTvoje skóre: **{p_score}**",
                color=0x3498DB,
            )
            e.add_field(name="Tvoje karty", value=format_karty(self.player_hand), inline=True)
            e.add_field(name="Dealer ukazuje", value=format_karty(self.dealer_hand, skryta=True), inline=True)
            await interaction.response.edit_message(embed=e, view=self)

    @discord.ui.button(label="Stand (Stát)", style=discord.ButtonStyle.success, emoji="🛑")
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Tahle hra není pro tebe!", ephemeral=True)
            return
        if self.hotovo:
            return
        await self._vyhodnotit_stand(interaction)

    async def _vyhodnotit_stand(self, interaction: discord.Interaction):
        self.hotovo = True
        self._disable_all()
        self.stop()

        p_score = self.skore(self.player_hand)
        d_score = self.skore(self.dealer_hand)

        while d_score < 17:
            self.dealer_hand.append(self.deck.pop())
            d_score = self.skore(self.dealer_hand)

        if d_score > 21 or p_score > d_score:
            bonus = self.cog.ziskej_buff(self.ctx.author.id, "kasino")
            vynos = int(self.bet * 2 * (1 + bonus))
            self.cog.db.pricti(self.ctx.author.id, vynos)
            extra = f" *(+{int(bonus * 100)}% bonus od partnera)*" if bonus > 0 else ""
            e = discord.Embed(
                title="🃏 Blackjack – Výhra! 👑",
                description=f"Vyhráváš **{kc(vynos)}**{extra}! ({p_score} vs {d_score})",
                color=0x2ECC71,
            )
        elif p_score < d_score:
            e = discord.Embed(
                title="🃏 Blackjack – Prohra!",
                description=f"Dealer vyhrál ({d_score} vs {p_score}). Ztratil jsi **{kc(self.bet)}**.",
                color=0xF44336,
            )
        else:
            self.cog.db.pricti(self.ctx.author.id, self.bet)
            e = discord.Embed(
                title="🃏 Blackjack – Remíza",
                description=f"Remíza ({p_score} : {d_score}). Sázka **{kc(self.bet)}** se ti vrátila.",
                color=0xF1C40F,
            )

        e.add_field(name=f"Tvoje karty ({p_score})", value=format_karty(self.player_hand), inline=True)
        e.add_field(name=f"Dealer ({d_score})", value=format_karty(self.dealer_hand), inline=True)
        e.set_footer(text=f"Zůstatek: {kc(self.cog.db.hrac(self.ctx.author.id)['balance'])}")
        await interaction.response.edit_message(embed=e, view=self)

    async def on_timeout(self):
        if self.hotovo or self.message is None:
            return
        self.hotovo = True
        self._disable_all()
        try:
            e = discord.Embed(
                title="🃏 Blackjack – Čas vypršel",
                description=f"Nestihl jsi odehrát tah včas. Sázka **{kc(self.bet)}** propadla.",
                color=0x757575,
            )
            await self.message.edit(embed=e, view=self)
        except discord.HTTPException:
            pass


class PokerView(discord.ui.View):
    """5-Card Draw Video Poker – hráč si vybere karty k podržení a zbytek vymění."""

    def __init__(self, cog, ctx, bet, deck, hand):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.bet = bet
        self.deck = deck
        self.hand = hand
        self.held = [False] * 5
        self.hotovo = False
        self.message = None
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        for i, (r, s) in enumerate(self.hand):
            btn = discord.ui.Button(
                label=f"{r}{s}" + (" (DRŽÍM)" if self.held[i] else ""),
                style=discord.ButtonStyle.success if self.held[i] else discord.ButtonStyle.secondary,
                row=0,
            )
            btn.callback = self._make_toggle(i)
            self.add_item(btn)

        draw_btn = discord.ui.Button(label="Vyměnit ostatní & Vyhodnotit", style=discord.ButtonStyle.primary, emoji="🎲", row=1)
        draw_btn.callback = self._draw_callback
        self.add_item(draw_btn)

    def _make_toggle(self, idx):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx.author.id:
                await interaction.response.send_message("Tahle hra není pro tebe!", ephemeral=True)
                return
            if self.hotovo:
                return
            self.held[idx] = not self.held[idx]
            self._build_buttons()
            await interaction.response.edit_message(embed=self.render_embed(), view=self)
        return callback

    def render_embed(self):
        karty_txt = "   ".join(
            f"**[`{r}{s}`]**" if self.held[i] else f"`{r}{s}`"
            for i, (r, s) in enumerate(self.hand)
        )
        e = discord.Embed(
            title="♠️ Video Poker (5-Card Draw)",
            description=(
                f"Sázka: **{kc(self.bet)}**\n\n"
                f"{karty_txt}\n\n"
                "Klikni na karty, které si chceš **nechat**, a pak stiskni **Vyměnit ostatní**."
            ),
            color=0x9B59B6,
        )
        e.set_footer(text="Výplaty: Pár J+ (1×) • Dva páry (2×) • Trojice (3×) • Postupka (4×) • Barva (6×) • Full House (9×) • Čtveřice (25×) • Straight Flush (50×) • Royal Flush (250×)")
        return e

    @staticmethod
    def vyhodnot_ruku(hand):
        vals = sorted([RANK_VALS[r] for r, _ in hand])
        suits = [s for _, s in hand]
        counts = Counter(vals)
        freq = sorted(counts.values(), reverse=True)

        is_flush = len(set(suits)) == 1
        is_straight = (vals == list(range(vals[0], vals[0] + 5))) or (vals == [2, 3, 4, 5, 14])

        if is_flush and vals == [10, 11, 12, 13, 14]:
            return "👑 ROYAL FLUSH!", 250
        if is_flush and is_straight:
            return "🔥 STRAIGHT FLUSH!", 50
        if freq == [4, 1]:
            return "💎 Čtveřice (Four of a Kind)!", 25
        if freq == [3, 2]:
            return "🏠 Full House!", 9
        if is_flush:
            return "🎨 Barva (Flush)!", 6
        if is_straight:
            return "📈 Postupka (Straight)!", 4
        if freq == [3, 1, 1]:
            return "🎯 Trojice (Three of a Kind)!", 3
        if freq == [2, 2, 1]:
            return "✌️ Dva páry (Two Pair)!", 2
        if freq == [2, 1, 1, 1]:
            pair_val = [v for v, c in counts.items() if c == 2][0]
            if pair_val >= 11:
                return "🃏 Vysoký pár (Jacks or Better)!", 1
        return "❌ Nic nepadlo", 0

    async def _draw_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Tahle hra není pro tebe!", ephemeral=True)
            return
        if self.hotovo:
            return

        self.hotovo = True
        self.stop()

        for i in range(5):
            if not self.held[i]:
                self.hand[i] = self.deck.pop()

        for child in self.children:
            child.disabled = True

        nazev_kombinace, nasobek = self.vyhodnot_ruku(self.hand)
        bonus = self.cog.ziskej_buff(self.ctx.author.id, "kasino")
        vyhra = int(self.bet * nasobek * (1 + bonus))

        if vyhra > 0:
            self.cog.db.pricti(self.ctx.author.id, vyhra)
            barva = 0x2ECC71
            extra = f" *(+{int(bonus * 100)}% bonus od partnera)*" if bonus > 0 else ""
            popis = f"{format_karty(self.hand)}\n\n**{nazev_kombinace}**\nVyhráváš **{kc(vyhra)}** (`{nasobek}×`){extra}!"
        else:
            barva = 0xF44336
            popis = f"{format_karty(self.hand)}\n\n{nazev_kombinace}. Ztratil jsi sázku **{kc(self.bet)}**."

        e = discord.Embed(title="♠️ Výsledek Video Pokeru", description=popis, color=barva)
        e.set_footer(text=f"Zůstatek: {kc(self.cog.db.hrac(self.ctx.author.id)['balance'])}")
        await interaction.response.edit_message(embed=e, view=self)

    async def on_timeout(self):
        if self.hotovo or self.message is None:
            return
        self.hotovo = True
        for child in self.children:
            child.disabled = True
        try:
            e = discord.Embed(
                title="♠️ Poker – Čas vypršel",
                description=f"Nestihl jsi vyměnit karty. Sázka **{kc(self.bet)}** propadla.",
                color=0x757575,
            )
            await self.message.edit(embed=e, view=self)
        except discord.HTTPException:
            pass


# ---------------------------------------------------------------- cog
class Hazard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Databaze(DB_PATH)

    async def cog_check(self, ctx):
        if ctx.channel.id not in POVOLENE_KANALY:
            kanaly = ", ".join(f"<#{cid}>" for cid in POVOLENE_KANALY)
            await ctx.send(f"❌ Gambling je povolen pouze v kanálech: {kanaly}")
            return False
        return True

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Chybí argument `{error.param.name}`.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Špatný argument (číslo, uživatel nebo kód itemu).")

    async def jmeno(self, uid):
        u = self.bot.get_user(uid)
        if u is None:
            try:
                u = await self.bot.fetch_user(uid)
            except discord.HTTPException:
                return f"Neznámý ({uid})"
        return u.display_name

    def majetek(self, uid, balance, inv):
        return balance + sum(ITEMS[k]["hodnota"] * c for k, c in inv.items() if k in ITEMS)

    def aktivni_partner(self, uid):
        """Vrátí (klic, dict_partnera) nebo (None, None)."""
        p = self.db.hrac(uid)
        pid = p["partner_id"]
        if not pid or pid not in PARTNERI:
            return None, None
        return pid, PARTNERI[pid]

    def ziskej_buff(self, uid, typ):
        """Vrátí hodnotu pasivního bonusu daného typu od aktivního partnera (jinak 0)."""
        _, pt = self.aktivni_partner(uid)
        if pt and pt["buff_typ"] == typ:
            return pt["buff_hodnota"]
        return 0

    def item_embed(self, kod):
        it = ITEMS[kod]
        r = RARITY[it["rarita"]]
        n, k = self.db.majitele(kod)
        bedna = BEDNY[it["bedna"]]
        e = discord.Embed(title=f"{r['emoji']} {it['nazev']}", color=r["barva"])
        e.add_field(name="Rarita", value=r["nazev"])
        e.add_field(name="Hodnota", value=kc(it["hodnota"]))
        e.add_field(name="Kód", value=f"`{kod}`")
        e.add_field(name="Bedna", value=f"{bedna['emoji']} {bedna['nazev']}")
        e.add_field(name="Šance na drop", value=f"{it['sance']:.3f} %")
        if n == 0:
            majitele = "Nikdo, tenhle item zatím nepadl."
        else:
            majitele = f"**{n}** hráčů vlastní tento item (celkem {k} ks)"
        e.add_field(name="👥 Majitelé", value=majitele, inline=False)
        return e

    # ---------------------------------------------------------- vztahy a seznamka
    @commands.command(name="pohlavi", aliases=["gender"])
    async def pohlavi(self, ctx, volba: str = None):
        if not volba or volba.lower() not in ("muz", "muž", "zena", "žena"):
            await ctx.send("❌ Použití: `prd pohlavi muz` nebo `prd pohlavi zena`")
            return
        v = "muz" if volba.lower() in ("muz", "muž") else "zena"
        self.db.hrac(ctx.author.id)
        self.db.nastav(ctx.author.id, pohlavi=v)
        nazev = "Muž ♂️" if v == "muz" else "Žena ♀️"
        await ctx.send(f"✅ Pohlaví nastaveno na: **{nazev}**")

    @commands.command(name="orientace", aliases=["sexualita"])
    async def orientace(self, ctx, volba: str = None):
        mapa = {
            "hetero": "hetero", "heterosexual": "hetero", "heterosexuál": "hetero",
            "bi": "bi", "bisexual": "bi", "bisexuál": "bi",
            "homo": "homo", "homosexual": "homo", "homosexuál": "homo",
        }
        if not volba or volba.lower() not in mapa:
            await ctx.send("❌ Použití: `prd orientace hetero`, `prd orientace bi` nebo `prd orientace homo`")
            return
        v = mapa[volba.lower()]
        self.db.hrac(ctx.author.id)
        self.db.nastav(ctx.author.id, orientace=v)
        nazvy = {"hetero": "Heterosexuál", "bi": "Bisexuál", "homo": "Homosexuál"}
        await ctx.send(f"✅ Orientace nastavena na: **{nazvy[v]}**")

    @commands.command(name="tinder", aliases=["seznamka", "swipe"])
    async def tinder(self, ctx):
        p = self.db.hrac(ctx.author.id)
        _, pt = self.aktivni_partner(ctx.author.id)
        if pt:
            await ctx.send(f"❌ Už chodíš s **{pt['jmeno']}**! Nejdřív se rozejdi příkazem `prd rozchod`.")
            return

        cilova_pohlavi = povolena_pohlavi(p["pohlavi"], p["orientace"])
        kandidati = [
            k for k, v in PARTNERI.items()
            if v["pohlavi"] in cilova_pohlavi and v["kde"] in ("tinder", "oboje")
        ]
        if not kandidati:
            await ctx.send("❌ Na Tinderu momentálně nikdo odpovídající tvým preferencím není.")
            return

        view = TinderView(self, ctx.author.id, kandidati, je_venku=False)
        view.message = await ctx.send(embed=view.render_embed(), view=view)

    @commands.command(name="ven", aliases=["prochazka", "venku"])
    async def ven(self, ctx):
        p = self.db.hrac(ctx.author.id)
        zbyva = VEN_COOLDOWN - (time.time() - p["last_venku"])
        if zbyva > 0:
            await ctx.send(f"⏳ Z procházky ses vrátil/a teprve před chvílí. Zkus to za {cas(zbyva)}.")
            return

        self.db.nastav(ctx.author.id, last_venku=time.time())
        _, aktivni_pt = self.aktivni_partner(ctx.author.id)

        # 50 % šance potkat někoho venku (pokud je hráč nezadaný)
        if not aktivni_pt and random.random() < 0.50:
            cilova_pohlavi = povolena_pohlavi(p["pohlavi"], p["orientace"])
            kandidati = [
                k for k, v in PARTNERI.items()
                if v["pohlavi"] in cilova_pohlavi and v["kde"] in ("venku", "oboje")
            ]
            if kandidati:
                vybrany = random.choice(kandidati)
                view = TinderView(self, ctx.author.id, [vybrany], je_venku=True)
                view.message = await ctx.send(embed=view.render_embed(), view=view)
                return

        udalosti = [
            ("Pomohl/a jsi slečně s těžkými taškami, dobrý skutek!!", 100),
            ("Prošel/a ses po parku a našel/a na zemi drobné.", 150),
            ("Vrazil/a jsi do pouličního kouzelníka, dal ti stovku za asistenci.", 100),
            ("Prošel/a ses kolem kasina, ale nikdo zajímavý nešel kolem.", 0),
            ("Našel/a jsi ztracenou dvoustovku u zastávky tramvaje.", 200),
        ]
        popis, penize = random.choice(udalosti)
        if penize > 0:
            self.db.pricti(ctx.author.id, penize)
            await ctx.send(f"🚶 {popis}\n**+{kc(penize)}**")
        else:
            await ctx.send(f"🚶 {popis}")

    @commands.command(name="rande", aliases=["date"])
    async def rande(self, ctx):
        p = self.db.hrac(ctx.author.id)
        pid, pt = self.aktivni_partner(ctx.author.id)
        if not pt:
            await ctx.send("❌ Jsi nezadaný/á! Najdi si někoho přes `prd tinder` nebo na procházce `prd ven`.")
            return

        zbyva = RANDE_COOLDOWN - (time.time() - p["last_rande"])
        if zbyva > 0:
            await ctx.send(f"⏳ Na rande jste byli nedávno. Další rande za {cas(zbyva)}.")
            return

        cena_rande = 1500 * pt["narocnost"]
        if p["balance"] < cena_rande:
            await ctx.send(f"❌ Na rande s **{pt['jmeno']}** potřebuješ **{kc(cena_rande)}**, ale máš jen {kc(p['balance'])}.")
            return

        self.db.pricti(ctx.author.id, -cena_rande)
        self.db.nastav(ctx.author.id, last_rande=time.time())

        extra_text = ""
        if pt["buff_typ"] == "kapesne":
            kapesne = int(pt["buff_hodnota"])
            self.db.pricti(ctx.author.id, kapesne)
            extra_text = f"\n💎 **{pt['jmeno']}** ti navíc dal/a kapesné **+{kc(kapesne)}**!"

        await ctx.send(
            f"🥂 Vzal/a jsi **{pt['jmeno']}** na rande za **{kc(cena_rande)}**!\n"
        )

    @commands.command(name="darek", aliases=["gift"])
    async def darek(self, ctx, *, item_text: str = None):
        if not item_text:
            await ctx.send("❌ Zadej kód nebo název itemu z inventáře! Např. `prd darek H05`")
            return
        _, pt = self.aktivni_partner(ctx.author.id)
        if not pt:
            await ctx.send("❌ Nemáš komu dát dárek, jsi nezadaný/á.")
            return

        kod = najdi_item(item_text)
        if not kod or self.db.pocet(ctx.author.id, kod) < 1:
            await ctx.send("❌ Takový item v inventáři nemáš.")
            return

        it = ITEMS[kod]
        self.db._odeber_item(ctx.author.id, kod, 1)
        self.db.con.commit()

        # Přírůstek spokojenosti podle hodnoty darovaného itemu
        if it["hodnota"] >= 5000:
            plus = 50
        elif it["hodnota"] >= 500:
            plus = 25
        elif it["hodnota"] >= 100:
            plus = 12
        else:
            plus = 5

        self.db.nastav(ctx.author.id, last_rande=time.time())
        await ctx.send(
            f"🎁 Daroval/a jsi **{it['nazev']}** partnerovi **{pt['jmeno']}**!\n"
        )

    @commands.command(name="rozchod", aliases=["breakup"])
    async def rozchod(self, ctx):
        _, pt = self.aktivni_partner(ctx.author.id)
        if not pt:
            await ctx.send("❌ Už teď jsi nezadaný/á.")
            return
        self.db.nastav(ctx.author.id, partner_id=None, spokojenost=100)
        await ctx.send(f"💔 Rozešel/a ses s **{pt['jmeno']}**. Jsi opět nezadaný/á.")

    @commands.command(name="vztah", aliases=["partner", "relationship", "ztah"])
    async def vztah(self, ctx, kdo: discord.User = None):
        kdo = kdo or ctx.author
        p = self.db.hrac(kdo.id)
        _, pt = self.aktivni_partner(kdo.id)

        if not pt:
            e = discord.Embed(
                title=f"💔 {kdo.display_name} je nezadaný/á",
                description="Najdi si někoho přes `prd tinder` nebo na procházce `prd ven`.",
                color=0x9E9E9E,
            )
            await ctx.send(embed=e)
            return

        kde_mapa = {"tinder": "🔥 PrdTinder", "venku": "🚶 Potkán/a venku", "oboje": "🔥🚶 Tinder i venku"}
        cena_rande = 1500 * pt["narocnost"]

        e = discord.Embed(
            title=f"❤️ {kdo.display_name} je ve vztahu s {pt['jmeno']}",
            description=f"*{pt['bio']}*",
            color=0xE91E63,
        )
        e.add_field(name="Povolání", value=pt["kategorie"], inline=True)
        e.add_field(name="Náročnost", value="⭐" * pt["narocnost"], inline=True)
        e.add_field(name="Seznámení", value=kde_mapa.get(pt["kde"], pt["kde"]), inline=True)
        e.add_field(name="✨ Pasivní schopnost", value=pt["buff_popis"], inline=False)
        e.add_field(name="Cena rande", value=kc(cena_rande), inline=True)

        zbyva = RANDE_COOLDOWN - (time.time() - p["last_rande"])
        if zbyva > 0:
            rande_txt = f"⏳ za {cas(zbyva)}"
        else:
            rande_txt = "✅ můžete hned (`prd rande`)"
        e.add_field(name="Další rande", value=rande_txt, inline=True)
        await ctx.send(embed=e)

    # ---------------------------------------------------------- peníze
    @commands.command(name="balance", aliases=["bal", "penize", "zustatek", "profil"])
    async def balance(self, ctx, kdo: discord.User = None):
        kdo = kdo or ctx.author
        p = self.db.hrac(kdo.id)
        inv = self.db.inventar(kdo.id)
        job = PRACE.get(p["job_id"]) if p["job_id"] else None
        _, pt = self.aktivni_partner(kdo.id)

        pohlavi_txt = "Muž ♂️" if p["pohlavi"] == "muz" else "Žena ♀️"
        orientace_mapa = {"hetero": "Hetero", "bi": "Bi", "homo": "Homo"}
        orientace_txt = orientace_mapa.get(p["orientace"], "Hetero")

        e = discord.Embed(title=f"💰 {kdo.display_name}", color=0x4CAF50)
        e.add_field(name="Zůstatek", value=kc(p["balance"]))
        e.add_field(name="Celkový majetek", value=kc(self.majetek(kdo.id, p["balance"], inv)))
        e.add_field(name="Profil", value=f"{pohlavi_txt} • {orientace_txt}", inline=True)
        e.add_field(name="Práce", value=job["nazev"] if job else "nezaměstnaný", inline=True)

        if pt:
            vztah_txt = f"❤️ **{pt['jmeno']}**\n*{pt['buff_popis']}*"
        else:
            vztah_txt = "Nezadaný/á (`prd tinder` nebo `prd ven`)"
        e.add_field(name="Vztah", value=vztah_txt, inline=False)
        await ctx.send(embed=e)

    @commands.command(name="zebrat", aliases=["beg"])
    async def zebrat(self, ctx):
        p = self.db.hrac(ctx.author.id)
        zbyva = BEG_COOLDOWN - (time.time() - p["last_beg"])
        if zbyva > 0:
            await ctx.send(f"⏳ Chvíli se projdi, ať nejsi nápadný/á. Zkus to za {cas(zbyva)}.")
            return
        _, text, lo, hi = random.choices(ZEBRANI, weights=[z[0] for z in ZEBRANI])[0]
        castka = random.randint(lo, hi) if hi != 0 else 0
        self.db.nastav(ctx.author.id, last_beg=time.time())

        # Oprava pro hlášky se seznamem [text, gif_url] vs náhodný výběr z více textů
        gif_url = None
        if isinstance(text, list):
            if len(text) == 2 and text[1].startswith("http"):
                zprava_txt, gif_url = text[0], text[1]
            else:
                zprava_txt = random.choice(text)
        else:
            zprava_txt = text

        if castka > 0:
            self.db.pricti(ctx.author.id, castka)
            await ctx.send(f"🪙 {zprava_txt}\n**+{kc(castka)}**")
        elif castka < 0:
            self.db.pricti(ctx.author.id, castka)
            await ctx.send(f"🪙 {zprava_txt}\n**{kc(castka)}**")
        else:
            await ctx.send(f"🪙 {zprava_txt}")

        if gif_url:
            await ctx.send(gif_url)

        # Malá 10% šance při žebrání na ulici potkat partnera z ulice
        _, aktivni_pt = self.aktivni_partner(ctx.author.id)
        if not aktivni_pt and random.random() < 0.10:
            cilova_pohlavi = povolena_pohlavi(p["pohlavi"], p["orientace"])
            kandidati = [
                k for k, v in PARTNERI.items()
                if v["pohlavi"] in cilova_pohlavi and v["kde"] in ("venku", "oboje")
            ]
            if kandidati:
                vybrany = random.choice(kandidati)
                view = TinderView(self, ctx.author.id, [vybrany], je_venku=True)
                view.message = await ctx.send(embed=view.render_embed(), view=view)

    @commands.command(name="prace", aliases=["job", "jobs"])
    async def prace(self, ctx, id_prace: str = None):
        p = self.db.hrac(ctx.author.id)
        if id_prace is None:
            e = discord.Embed(title="💼 Nabídka práce",
                              description=(f"Jeden „měsíc“ trvá {cas(MESIC_SEKUND)} reálného času. "
                                           "Výplatu vybereš příkazem `prd vyplata`.\n"
                                           "Přihlásit se můžeš: `prd prace <id>`"),
                              color=0x2196F3)
            for klic, j in PRACE.items():
                e.add_field(
                    name=f"{j['nazev']} (`{klic}`)",
                    value=f"{j['popis']}\n💵 {kc(j['plat'])} / měsíc • šance přijetí {float(j['sance'] * 100)} %",
                    inline=False)
            await ctx.send(embed=e)
            return

        klic = id_prace.lower()
        if klic not in PRACE:
            await ctx.send("❌ Takovou práci nenabízíme. Seznam: `prd prace`")
            return
        if p["job_id"]:
            await ctx.send("❌ Už máš práci. Nejdřív dej výpověď: `prd vypoved`")
            return
        zbyva = PRACE_COOLDOWN - (time.time() - p["last_apply"])
        if zbyva > 0:
            await ctx.send(f"⏳ Na další pohovor můžeš za {cas(zbyva)}.")
            return

        j = PRACE[klic]
        self.db.nastav(ctx.author.id, last_apply=time.time())
        if random.random() < j["sance"]:
            self.db.nastav(ctx.author.id, job_id=klic, last_pay=time.time())
            await ctx.send(f"🎉 Vzali tě! Jsi nový/á **{j['nazev']}**. "
                           f"Plat {kc(j['plat'])} za měsíc, výplata přes `prd vyplata`.")
        else:
            await ctx.send(f"📄 Na pozici **{j['nazev']}** tě nevzali. Zkus to znovu za {cas(PRACE_COOLDOWN)}.")

    def _vybrat_vyplatu(self, uid, p):
        job = PRACE.get(p["job_id"]) if p["job_id"] else None
        if not job:
            return 0, 0, 0
        mesice = min(int((time.time() - p["last_pay"]) // MESIC_SEKUND), MAX_MESICU)
        if mesice < 1:
            return 0, 0, 0
        bonus = self.ziskej_buff(uid, "plat")
        castka = int(job["plat"] * mesice * (1 + bonus))
        self.db.pricti(uid, castka)
        self.db.nastav(uid, last_pay=time.time())
        return mesice, castka, bonus

    @commands.command(name="vyplata", aliases=["plat", "salary"])
    async def vyplata(self, ctx):
        p = self.db.hrac(ctx.author.id)
        if not p["job_id"] or p["job_id"] not in PRACE:
            await ctx.send("❌ Nemáš práci. Podívej se na `prd prace`.")
            return
        mesice, castka, bonus = self._vybrat_vyplatu(ctx.author.id, p)
        if mesice < 1:
            zbyva = MESIC_SEKUND - (time.time() - p["last_pay"])
            await ctx.send(f"⏳ Šéf ti zatím nic nevyplatil. Další výplata za {cas(zbyva)}.")
            return
        extra = f" *(včetně +{int(bonus * 100)}% bonusu od partnera)*" if bonus > 0 else ""
        await ctx.send(f"💵 Výplata za {mesice}× měsíc: **+{kc(castka)}**{extra}")

    @commands.command(name="vypoved", aliases=["quit"])
    async def vypoved(self, ctx):
        p = self.db.hrac(ctx.author.id)
        if not p["job_id"]:
            await ctx.send("❌ Nemáš z čeho dávat výpověď.")
            return
        mesice, castka, _ = self._vybrat_vyplatu(ctx.author.id, p)
        self.db.nastav(ctx.author.id, job_id=None)
        extra = f" Dostal/a jsi ještě poslední výplatu **{kc(castka)}**." if castka else ""
        await ctx.send(f"📦 Dal/a jsi výpověď.{extra}")

    @commands.command(name="poslat", aliases=["pay", "darovat", "give", "prevod"])
    async def poslat(self, ctx, komu: discord.User, castka: int):
        if komu.id == ctx.author.id:
            await ctx.send("❌ Nemůžeš poslat peníze sám/a sobě.")
            return
        if komu.bot:
            await ctx.send("❌ Botovi peníze posílat nemůžeš.")
            return
        if castka <= 0:
            await ctx.send("❌ Částka musí být větší než 0 Kč.")
            return

        p = self.db.hrac(ctx.author.id)
        if p["balance"] < castka:
            await ctx.send(f"❌ Nemáš dost peněz! Tvůj zůstatek je jen {kc(p['balance'])}.")
            return

        self.db.pricti(ctx.author.id, -castka)
        self.db.pricti(komu.id, castka)
        await ctx.send(f"💸 {ctx.author.mention} poslal/a **{kc(castka)}** hráči {komu.mention}!")

    # ---------------------------------------------------------- kasino hry
    @commands.command(name="sloty", aliases=["slot", "automaty", "slots"])
    async def sloty(self, ctx, castka: int = None):
        if not castka or castka <= 0:
            await ctx.send("❌ Zadej platnou sázku! Např. `prd sloty 1000`")
            return

        p = self.db.hrac(ctx.author.id)
        if p["balance"] < castka:
            await ctx.send(f"❌ Na to nemáš dost peněz! Máš jen {kc(p['balance'])}.")
            return

        self.db.pricti(ctx.author.id, -castka)

        symboly = ["🍒", "🍋", "🍉", "⭐", "🔔", "💎", "7️⃣"]
        msg = await ctx.send(embed=discord.Embed(
            title="🎰 Kasino – Sloty",
            description="Točí se válce...\n\n🔄 | 🔄 | 🔄",
            color=0xF1C40F,
        ))

        for _ in range(3):
            await asyncio.sleep(0.75)
            f_res = [random.choice(symboly) for _ in range(3)]
            await msg.edit(embed=discord.Embed(
                title="🎰 Kasino – Sloty",
                description=f"Točí se válce...\n\n{f_res[0]} | {f_res[1]} | {f_res[2]}",
                color=0xF1C40F,
            ))

        await asyncio.sleep(0.75)
        vysledek = [random.choice(symboly) for _ in range(3)]
        bonus = self.ziskej_buff(ctx.author.id, "kasino")

        vyhra = 0
        if vysledek[0] == vysledek[1] == vysledek[2]:
            if vysledek[0] == "7️⃣":
                vyhra = int(castka * 30 * (1 + bonus))
                zprava = f"🌟 **JACKPOT 7️⃣7️⃣7️⃣!** **+{kc(vyhra)}**!"
            elif vysledek[0] == "💎":
                vyhra = int(castka * 15 * (1 + bonus))
                zprava = f"💎 **DIAMANTOVÁ VÝHRA!** **+{kc(vyhra)}**!"
            else:
                vyhra = int(castka * 5 * (1 + bonus))
                zprava = f"🎉 **Tři stejné symboly!** **+{kc(vyhra)}**!"
        elif vysledek[0] == vysledek[1] or vysledek[1] == vysledek[2] or vysledek[0] == vysledek[2]:
            vyhra = int(castka * 1.5 * (1 + bonus))
            zprava = f"✨ **Dva stejné symboly!** **+{kc(vyhra)}**!"
        else:
            zprava = f"💸 Bohužel, nic to nehodilo. **-{kc(castka)}**."

        if vyhra > 0:
            if bonus > 0:
                zprava += f" *(+{int(bonus * 100)}% bonus od partnera)*"
            self.db.pricti(ctx.author.id, vyhra)
            barva = 0x2ECC71
        else:
            barva = 0xF44336

        e = discord.Embed(
            title="🎰 Výsledek automatu",
            description=f"**{vysledek[0]} | {vysledek[1]} | {vysledek[2]}**\n\n{zprava}",
            color=barva,
        )
        e.set_footer(text=f"Zůstatek: {kc(self.db.hrac(ctx.author.id)['balance'])}")
        await msg.edit(embed=e)

    @commands.command(name="blackjack", aliases=["bj"])
    async def blackjack(self, ctx, castka: int = None):
        if not castka or castka <= 0:
            await ctx.send("❌ Zadej sázku! Např. `prd blackjack 2000`")
            return

        p = self.db.hrac(ctx.author.id)
        if p["balance"] < castka:
            await ctx.send(f"❌ Nemáš dost peněz! Máš jen {kc(p['balance'])}.")
            return

        self.db.pricti(ctx.author.id, -castka)

        deck = vytvor_balicek()
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        p_score = BlackjackView.skore(player_hand)
        if p_score == 21:
            bonus = self.ziskej_buff(ctx.author.id, "kasino")
            vyhra = int(castka * 2.5 * (1 + bonus))
            self.db.pricti(ctx.author.id, vyhra)
            extra = f" *(+{int(bonus * 100)}% bonus od partnera)*" if bonus > 0 else ""
            e = discord.Embed(
                title="🃏 NATURAL BLACKJACK! 👑",
                description=f"Rovných **21** hned z ruky! Vyhráváš **{kc(vyhra)}** (`2.5×`){extra}!",
                color=0x2ECC71,
            )
            e.add_field(name="Tvoje karty (21)", value=format_karty(player_hand), inline=True)
            e.add_field(name=f"Dealer ({BlackjackView.skore(dealer_hand)})", value=format_karty(dealer_hand), inline=True)
            e.set_footer(text=f"Zůstatek: {kc(self.db.hrac(ctx.author.id)['balance'])}")
            await ctx.send(embed=e)
            return

        view = BlackjackView(self, ctx, castka, deck, player_hand, dealer_hand)
        e = discord.Embed(
            title="🃏 Blackjack",
            description=f"Sázka: **{kc(castka)}**\nTvoje skóre: **{p_score}**",
            color=0x3498DB,
        )
        e.add_field(name="Tvoje karty", value=format_karty(player_hand), inline=True)
        e.add_field(name="Dealer ukazuje", value=format_karty(dealer_hand, skryta=True), inline=True)
        view.message = await ctx.send(embed=e, view=view)

    @commands.command(name="poker", aliases=["videopoker"])
    async def poker(self, ctx, castka: int = None):
        if not castka or castka <= 0:
            await ctx.send("❌ Zadej sázku! Např. `prd poker 1500`")
            return

        p = self.db.hrac(ctx.author.id)
        if p["balance"] < castka:
            await ctx.send(f"❌ Nemáš dost peněz! Máš jen {kc(p['balance'])}.")
            return

        self.db.pricti(ctx.author.id, -castka)

        deck = vytvor_balicek()
        hand = [deck.pop() for _ in range(5)]
        view = PokerView(self, ctx, castka, deck, hand)
        view.message = await ctx.send(embed=view.render_embed(), view=view)

    @commands.command(name="ruleta", aliases=["roulette"])
    async def ruleta(self, ctx, volba: str = None, castka: int = None):
        if not volba or not castka or castka <= 0:
            await ctx.send(
                "❌ Použití: `prd ruleta <volba> <sázka>`\n"
                "Volby: `cervena` (2×), `cerna` (2×), `zelena` / `0` (14×), nebo číslo `0–36` (36×)"
            )
            return

        v = volba.lower().strip()
        cervena_cisla = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

        typ = None
        cislo_tip = None
        if v in ("cervena", "červená", "red", "r"):
            typ = "cervena"
        elif v in ("cerna", "černá", "black", "b"):
            typ = "cerna"
        elif v in ("zelena", "zelená", "green", "g"):
            typ = "zelena"
        elif v.isdigit() and 0 <= int(v) <= 36:
            typ = "cislo"
            cislo_tip = int(v)
        else:
            await ctx.send("❌ Neplatná volba! Zadej `cervena`, `cerna`, `zelena` nebo číslo `0–36`.")
            return

        p = self.db.hrac(ctx.author.id)
        if p["balance"] < castka:
            await ctx.send(f"❌ Nemáš dost peněz! Máš jen {kc(p['balance'])}.")
            return

        self.db.pricti(ctx.author.id, -castka)

        msg = await ctx.send(embed=discord.Embed(
            title="🎡 Ruleta",
            description="Kulička se roztáčí po kole...",
            color=0xF1C40F,
        ))
        await asyncio.sleep(1.5)

        padlo = random.randint(0, 36)
        if padlo == 0:
            padla_barva = "zelena"
            barva_txt = "🟢 Zelená (0)"
        elif padlo in cervena_cisla:
            padla_barva = "cervena"
            barva_txt = f"🔴 Červená ({padlo})"
        else:
            padla_barva = "cerna"
            barva_txt = f"⚫ Černá ({padlo})"

        bonus = self.ziskej_buff(ctx.author.id, "kasino")
        vyhra = 0
        if typ == "cislo" and padlo == cislo_tip:
            vyhra = int(castka * 36 * (1 + bonus))
        elif typ == "zelena" and padla_barva == "zelena":
            vyhra = int(castka * 14 * (1 + bonus))
        elif typ in ("cervena", "cerna") and padla_barva == typ:
            vyhra = int(castka * 2 * (1 + bonus))

        if vyhra > 0:
            self.db.pricti(ctx.author.id, vyhra)
            extra = f" *(+{int(bonus * 100)}% bonus od partnera)*" if bonus > 0 else ""
            e = discord.Embed(
                title="🎡 Ruleta – Výhra!",
                description=f"Kulička zastavila na: **{barva_txt}**\n\n🎉 Vyhráváš **{kc(vyhra)}**{extra}!",
                color=0x2ECC71,
            )
        else:
            e = discord.Embed(
                title="🎡 Ruleta – Prohra",
                description=f"Kulička zastavila na: **{barva_txt}**\n\n💸 Ztratil jsi sázku **{kc(castka)}**.",
                color=0xF44336,
            )
        e.set_footer(text=f"Zůstatek: {kc(self.db.hrac(ctx.author.id)['balance'])}")
        await msg.edit(embed=e)

    # ---------------------------------------------------------- investice / trh
    @commands.command(name="trh", aliases=["market", "investice"])
    async def trh(self, ctx):
        market_data = self.db.get_all_market()
        e = discord.Embed(title="📈 Burza fiktivních firem a krypta",
                          description="Podívej se na přehled trhu. Detail zjistíš příkazem:\n`prd investinfo <symbol>`",
                          color=0x00FFCC)

        sorted_market = sorted(market_data.items(), key=lambda x: x[1]["price"], reverse=True)
        for sym, dat in sorted_market:
            meta = INVESTMENTS_DATA[sym]
            hist = dat["history"]
            cena = dat["price"]
            predchozi = hist[-2] if len(hist) >= 2 else cena
            zmena = ((cena - predchozi) / predchozi) * 100
            sipka = "🟢 📈" if zmena >= 0 else "🔴 📉"

            e.add_field(
                name=f"{meta['emoji']} {meta['nazev']} (`{sym}`)",
                value=f"💵 **{kc(cena)}** | Změna: `{zmena:+.1f}%` {sipka}\n*{meta['popis']}*",
                inline=False
            )
        e.set_footer(text="Investuj pomocí: prd invest <symbol> <částka>")
        await ctx.send(embed=e)

    @commands.command(name="investinfo", aliases=["stock", "iinfo"])
    async def investinfo(self, ctx, symbol: str = None):
        if not symbol:
            await ctx.send("❌ Zadej symbol firmy nebo krypta (např. `prd investinfo NEVIDIMJÁ`).")
            return
        sym = najdi_investici(symbol)
        if not sym:
            await ctx.send("❌ Takovou investici neznám. Napiš `prd trh` pro seznam.")
            return

        meta = INVESTMENTS_DATA[sym]
        price, hist = self.db.get_market_asset(sym)

        new_price, new_hist = self.db.update_market_asset(sym)
        graf = vygeneruj_graf(new_hist)

        predchozi = new_hist[-2] if len(new_hist) >= 2 else new_price
        zmena = ((new_price - predchozi) / predchozi) * 100

        if zmena > 5:
            doporuceni = "🔥 **Cena silně roste!** Jedem bombyyyyyy!"
        elif zmena < -5:
            doporuceni = "📉 **Cena padá!** Trochu v pici společnost teď lowk."
        else:
            doporuceni = "⚖️ **Stabilní vývoj.** Trh vyčkává na další pohyby."

        e = discord.Embed(title=f"{meta['emoji']} {meta['nazev']} (`{sym}`)",
                          description=f"{meta['popis']}\n\n**Aktuální cena:** {kc(new_price)} (`{zmena:+.1f}%`)",
                          color=0x3498DB)
        e.add_field(name="📊 Historický graf", value=f"```text\n{graf}\n```", inline=False)
        e.add_field(name="💡 Analýza a doporučení", value=doporuceni, inline=False)
        e.set_footer(text=f"Pro investování použij: prd invest {sym} <částka>")
        await ctx.send(embed=e)

    @commands.command(name="invest")
    async def invest(self, ctx, symbol: str = None, castka: int = None):
        if not symbol or castka is None:
            await ctx.send("❌ Použití příkazu: `prd invest <symbol> <částka>`\nNapříklad: `prd invest NEVIDIMJA 5000`")
            return
        if castka <= 0:
            await ctx.send("❌ Částka musí být větší než 0.")
            return

        sym = najdi_investici(symbol)
        if not sym:
            await ctx.send("❌ Taková investice neexistuje. Seznam najdeš pod `prd trh`.")
            return

        p = self.db.hrac(ctx.author.id)
        if p["balance"] < castka:
            await ctx.send(f"❌ Na to nemáš peníze! Máš jen {kc(p['balance'])}, potřebuješ {kc(castka)}.")
            return

        price, _ = self.db.get_market_asset(sym)
        shares_bought = castka / price

        self.db.pricti(ctx.author.id, -castka)

        row = self.db.con.execute("SELECT shares, invested_czk FROM portfolio WHERE user_id = ? AND symbol = ?",
                                  (ctx.author.id, sym)).fetchone()
        if row:
            new_shares = row["shares"] + shares_bought
            new_invested = row["invested_czk"] + castka
            self.db.con.execute("UPDATE portfolio SET shares = ?, invested_czk = ? WHERE user_id = ? AND symbol = ?",
                              (new_shares, new_invested, ctx.author.id, sym))
        else:
            self.db.con.execute("INSERT INTO portfolio (user_id, symbol, shares, invested_czk) VALUES (?, ?, ?, ?)",
                              (ctx.author.id, sym, shares_bought, castka))
        self.db.con.commit()

        meta = INVESTMENTS_DATA[sym]
        await ctx.send(f"✅ Úspěšně jsi investoval **{kc(castka)}** do **{meta['nazev']}** (`{sym}`)!\nZískal jsi `{shares_bought:.4f}` podílů/akcií při ceně {kc(price)}.")

    @commands.command(name="cheat", aliases=["givemoney", "addmoney"])
    async def cheat(self, ctx, castka: int, uzivatel: discord.User = None):
        MOJE_DISCORD_ID = 449847721386573825

        if ctx.author.id != MOJE_DISCORD_ID:
            await ctx.send("❌ Ty nejsi tvůrce! Zloději jeden.")
            return

        kdo = uzivatel or ctx.author
        if castka <= 0:
            await ctx.send("❌ Částka musí být větší než 0.")
            return

        self.db.pricti(kdo.id, castka)
        await ctx.send(f"🪄 Admin čarování: Přičteno **{kc(castka)}** hráči {kdo.mention}!")

    @commands.command(name="portfolio", aliases=["mojeinvestice", "pf"])
    async def portfolio(self, ctx, kdo: discord.User = None):
        kdo = kdo or ctx.author
        rows = self.db.con.execute("SELECT symbol, shares, invested_czk FROM portfolio WHERE user_id = ?",
                                   (kdo.id,)).fetchall()
        if not rows:
            await ctx.send(f"🎒 {kdo.display_name} zatím nemá žádné investice. Zkus `prd invest <symbol> <částka>`!")
            return

        market_data = self.db.get_all_market()
        e = discord.Embed(title=f"📊 Investiční portfolio: {kdo.display_name}", color=0xF1C40F)

        celkem_investovano = 0
        celkem_aktualne = 0

        for r in rows:
            sym = r["symbol"]
            shares = r["shares"]
            invested = r["invested_czk"]
            meta = INVESTMENTS_DATA[sym]
            current_price = market_data[sym]["price"]
            hodnota = shares * current_price
            zisk = hodnota - invested
            zisk_pct = (zisk / invested * 100) if invested > 0 else 0

            celkem_investovano += invested
            celkem_aktualne += hodnota

            barva_zisku = "🟢 +" if zisk >= 0 else "🔴 "
            e.add_field(
                name=f"{meta['emoji']} {meta['nazev']} (`{sym}`)",
                value=f"Počet podílů: `{shares:.4f}`\nVloženo: {kc(invested)} | Hodnota: **{kc(hodnota)}**\nVýsledek: {barva_zisku}{kc(zisk)} (`{zisk_pct:+.1f}%`)",
                inline=False
            )

        celkovy_zisk = celkem_aktualne - celkem_investovano
        celkovy_zisk_pct = (celkovy_zisk / celkem_investovano * 100) if celkem_investovano > 0 else 0

        e.add_field(
            name="💰 Celkový souhrn",
            value=f"Celkem vloženo: {kc(celkem_investovano)}\nAktuální hodnota: **{kc(celkem_aktualne)}**\nCelkový zisk/ztráta: {barva_zisku if celkovy_zisk>=0 else '🔴 '}{kc(celkovy_zisk)} (`{celkovy_zisk_pct:+.1f}%`)",
            inline=False
        )
        e.set_footer(text="Prodej své investice pomocí: prd prodatinvestici <symbol>")
        await ctx.send(embed=e)

    @commands.command(name="prodatinvestici", aliases=["sellinvest", "vybratinvestici", "prodatinv", "sellinv"])
    async def prodatinvestici(self, ctx, symbol: str = None):
        if not symbol:
            await ctx.send("❌ Zadej symbol investice, kterou chceš prodat (např. `prd prodatinvestici NEVIDIMJA`).")
            return
        sym = najdi_investici(symbol)
        if not sym:
            await ctx.send("❌ Neznámý symbol. Seznam svých investic najdeš v `prd portfolio`.")
            return

        row = self.db.con.execute("SELECT shares, invested_czk FROM portfolio WHERE user_id = ? AND symbol = ?",
                                  (ctx.author.id, sym)).fetchone()
        if not row or row["shares"] <= 0:
            await ctx.send(f"❌ Žádné podíly v `{sym}` nevlastníš.")
            return

        shares = row["shares"]
        price, _ = self.db.get_market_asset(sym)
        vyplata = shares * price

        self.db.con.execute("DELETE FROM portfolio WHERE user_id = ? AND symbol = ?", (ctx.author.id, sym))
        self.db.con.commit()
        self.db.pricti(ctx.author.id, vyplata)

        meta = INVESTMENTS_DATA[sym]
        zisk = vyplata - row["invested_czk"]
        await ctx.send(f"💸 Prodal jsi všechny své podíly v **{meta['nazev']}** za **{kc(vyplata)}**! Čistý zisk/ztráta: {kc(zisk)}.")

    # ---------------------------------------------------------- bedny
    @commands.command(name="bedny", aliases=["cases"])
    async def bedny(self, ctx):
        sleva = self.ziskej_buff(ctx.author.id, "sleva_bedny")
        popis_extra = f"\n✨ *Máš aktivní slevu {int(sleva * 100)} % na bedny od partnera!*" if sleva > 0 else ""
        e = discord.Embed(title="📦 Bedny",
                          description=f"Otevři příkazem `prd otevrit <bedna> [kolik]`{popis_extra}",
                          color=0xFF9800)
        for klic, b in BEDNY.items():
            cena = int(b["cena"] * (1 - sleva))
            e.add_field(name=f"{b['emoji']} {b['nazev']} (`{klic}`)",
                        value=f"{b['popis']}\n💰 Cena: **{kc(cena)}**", inline=False)

        ansi_barvy = {
            "common":    "\u001b[0;37m",
            "uncommon":  "\u001b[0;32m",
            "rare":      "\u001b[0;34m",
            "epic":      "\u001b[0;35m",
            "legendary": "\u001b[0;33m",
            "godlike":   "\u001b[0;31m",
            "voidborn":  "\u001b[1;30m",
        }

        radky = []
        for klic, r in RARITY.items():
            barva = ansi_barvy.get(klic, "")
            radky.append(f"{barva}{r['nazev']}: {r['sance']} %\u001b[0m")

        sance = "```ansi\n" + "\n".join(radky) + "\n```"
        e.add_field(name="Šance na rarity", value=sance, inline=False)
        await ctx.send(embed=e)

    @commands.command(name="otevrit", aliases=["case", "oc"])
    async def otevrit(self, ctx, bedna: str = None, kolik: int = 1):
        if bedna is None or bedna.lower() not in BEDNY:
            await ctx.send("❌ Neznámá bedna. Seznam najdeš v `prd bedny`.")
            return
        if not 1 <= kolik <= MAX_OTEVRENI:
            await ctx.send(f"❌ Najednou můžeš otevřít 1 až {MAX_OTEVRENI} beden.")
            return

        b = BEDNY[bedna.lower()]
        sleva = self.ziskej_buff(ctx.author.id, "sleva_bedny")
        cena = int(b["cena"] * (1 - sleva)) * kolik
        vypadle = random.choices(b["kody"], weights=b["vahy"], k=kolik)
        zustatek = self.db.koupit_bedny(ctx.author.id, cena, vypadle)
        if zustatek is None:
            ma = self.db.hrac(ctx.author.id)["balance"]
            await ctx.send(f"❌ Na to nemáš. Potřebuješ {kc(cena)}, máš {kc(ma)}.")
            return

        if kolik == 1:
            msg = await ctx.send(embed=discord.Embed(
                title=f"{b['emoji']} Otevírám {b['nazev']}…", color=0x2B2D31))
            for _ in range(3):
                await asyncio.sleep(1)
                falesny = ITEMS[random.choice(b["kody"])]
                r = RARITY[falesny["rarita"]]
                await msg.edit(embed=discord.Embed(
                    title=f"🎰 {r['emoji']} {falesny['nazev']}", color=r["barva"]))
            await asyncio.sleep(1)

            kod = vypadle[0]
            it = ITEMS[kod]
            r = RARITY[it["rarita"]]
            n, k = self.db.majitele(kod)

            popis = (
                f"```ansi\n"
                f"{r['ansi']}{it['nazev']}\u001b[0m\n"
                f"\u001b[0;37m{r['nazev']} • hodnota {kc(it['hodnota'])}\u001b[0m\n"
                f"```"
            )

            e = discord.Embed(
                title=f"{b['emoji']} Výsledek otevírání",
                description=popis,
                color=r["barva"]
            )
            if n == 1:
                e.add_field(name="👥 Majitelé", value="Jsi jediný hráč, který tento item vlastní! 👑")
            else:
                e.add_field(name="👥 Majitelé", value=f"**{n}** hráčů vlastní tento item (celkem {k} ks)")
            e.set_footer(text=f"Kód {kod} • zůstatek {kc(zustatek)}")
            await msg.edit(embed=e)
            return

        pocty = Counter(vypadle)
        poradi = sorted(pocty.items(),
                        key=lambda x: (-RARITY[ITEMS[x[0]]["rarita"]]["poradi"], -ITEMS[x[0]]["hodnota"]))
        radky = []
        for kod, pocet in poradi:
            it = ITEMS[kod]
            r = RARITY[it["rarita"]]
            n, _ = self.db.majitele(kod)
            radky.append(f"{r['emoji']} **{it['nazev']}** ×{pocet} • {kc(it['hodnota'])} • 👥 {n}")
        hodnota = sum(ITEMS[k]["hodnota"] for k in vypadle)
        nejlepsi = max(vypadle, key=lambda k: (RARITY[ITEMS[k]["rarita"]]["poradi"], ITEMS[k]["hodnota"]))
        e = discord.Embed(title=f"{b['emoji']} {kolik}× {b['nazev']}",
                          description="\n".join(radky),
                          color=RARITY[ITEMS[nejlepsi]["rarita"]]["barva"])
        e.add_field(name="Utraceno", value=kc(cena))
        e.add_field(name="Hodnota výhry", value=kc(hodnota))
        e.set_footer(text=f"Zůstatek {kc(zustatek)}")
        await ctx.send(embed=e)

    # ---------------------------------------------------------- inventář a itemy
    @commands.command(name="inventar", aliases=["inv", "inventory"])
    async def inventar(self, ctx, kdo: discord.User = None):
        kdo = kdo or ctx.author
        inv = {k: c for k, c in self.db.inventar(kdo.id).items() if k in ITEMS}
        if not inv:
            await ctx.send(f"🎒 {kdo.display_name} nemá žádné itemy.")
            return
        kody = sorted(inv, key=lambda k: (-RARITY[ITEMS[k]["rarita"]]["poradi"], -ITEMS[k]["hodnota"]))
        radky = []
        for kod in kody[:25]:
            it = ITEMS[kod]
            r = RARITY[it["rarita"]]
            radky.append(f"{r['emoji']} **{it['nazev']}** ×{inv[kod]} • `{kod}` • {kc(it['hodnota'])}")
        if len(kody) > 25:
            radky.append(f"…a dalších {len(kody) - 25} druhů")
        hodnota = sum(ITEMS[k]["hodnota"] * c for k, c in inv.items())
        e = discord.Embed(title=f"🎒 Inventář: {kdo.display_name}",
                          description="\n".join(radky), color=0x607D8B)
        e.set_footer(text=f"Hodnota itemů: {kc(hodnota)}")
        view = discord.ui.View(timeout=180)
        view.add_item(InventarSelect(self, kody))
        await ctx.send(embed=e, view=view)

    @commands.command(name="item")
    async def item(self, ctx, *, hledani: str):
        kod = najdi_item(hledani)
        if not kod:
            await ctx.send("❌ Takový item neznám. Zkus jeho kód (např. `P07`) nebo část názvu.")
            return
        await ctx.send(embed=self.item_embed(kod))

    @commands.command(name="prodat", aliases=["sell"])
    async def prodat(self, ctx, kod: str, kolik: int = 1):
        kod = najdi_item(kod)
        if not kod:
            await ctx.send("❌ Takový item neznám.")
            return
        if kolik < 1:
            await ctx.send("❌ Počet musí být aspoň 1.")
            return
        castka = ITEMS[kod]["hodnota"] * kolik
        if not self.db.prodat_botovi(ctx.author.id, kod, kolik, castka):
            await ctx.send("❌ Tolik kusů nemáš.")
            return
        await ctx.send(f"💸 Prodal jsi {kolik}× **{ITEMS[kod]['nazev']}** za **{kc(castka)}**.")

    # ---------------------------------------------------------- obchodování
    @commands.command(name="trade", aliases=["vymena"])
    async def trade(self, ctx, komu: discord.User, muj_item: str, jejich_item: str):
        muj, jejich = najdi_item(muj_item), najdi_item(jejich_item)
        if komu.id == ctx.author.id or komu.bot:
            await ctx.send("❌ S tímhle si vyměňovat nemůžeš.")
            return
        if not muj or not jejich:
            await ctx.send("❌ Neznámý item. Použij kódy z inventáře.")
            return
        if muj == jejich:
            await ctx.send("❌ Výměna stejného itemu nemá smysl.")
            return
        if self.db.pocet(ctx.author.id, muj) < 1:
            await ctx.send("❌ Tenhle item nemáš.")
            return
        if self.db.pocet(komu.id, jejich) < 1:
            await ctx.send(f"❌ {komu.display_name} tenhle item nemá.")
            return

        a, b = ITEMS[muj], ITEMS[jejich]

        def provest():
            if self.db.vymena(ctx.author.id, muj, komu.id, jejich):
                return True, (f"✅ Výměna proběhla: {ctx.author.mention} dostal **{b['nazev']}**, "
                              f"{komu.mention} dostal **{a['nazev']}**.")
            return False, "❌ Výměna selhala, někdo z vás už ten item nemá."

        e = discord.Embed(title="🔁 Nabídka výměny", color=0x03A9F4,
                          description=(f"{ctx.author.mention} nabízí {RARITY[a['rarita']]['emoji']} "
                                       f"**{a['nazev']}** za {RARITY[b['rarita']]['emoji']} "
                                       f"**{b['nazev']}** od {komu.mention}."))
        view = ObchodView(komu.id, provest)
        view.message = await ctx.send(content=komu.mention, embed=e, view=view)

    @commands.command(name="nabidka", aliases=["offer"])
    async def nabidka(self, ctx, komu: discord.User, item: str, cena: int):
        kod = najdi_item(item)
        if komu.id == ctx.author.id or komu.bot:
            await ctx.send("❌ Tomuhle prodávat nemůžeš.")
            return
        if not kod:
            await ctx.send("❌ Neznámý item. Použij kód z inventáře.")
            return
        if not 0 <= cena <= 10**12:
            await ctx.send("❌ Cena musí být od 0 do 1 000 000 000 000 Kč.")
            return
        if self.db.pocet(ctx.author.id, kod) < 1:
            await ctx.send("❌ Tenhle item nemáš.")
            return

        it = ITEMS[kod]

        def provest():
            vysledek = self.db.prodej_hraci(ctx.author.id, komu.id, kod, cena)
            if vysledek == "ok":
                return True, (f"✅ {komu.mention} koupil **{it['nazev']}** od {ctx.author.mention} "
                              f"za **{kc(cena)}**.")
            if vysledek == "penize":
                return False, "❌ Kupující nemá dost peněz."
            return False, "❌ Prodávající už ten item nemá."

        e = discord.Embed(title="🏷️ Nabídka prodeje", color=0x03A9F4,
                          description=(f"{ctx.author.mention} prodává {RARITY[it['rarita']]['emoji']} "
                                       f"**{it['nazev']}** za **{kc(cena)}** hráči {komu.mention}.\n"
                                       f"(Hodnota itemu: {kc(it['hodnota'])})"))
        view = ObchodView(komu.id, provest)
        view.message = await ctx.send(content=komu.mention, embed=e, view=view)

    # ---------------------------------------------------------- žebříčky
    @commands.command(name="top", aliases=["leaderboard", "lb"])
    async def top(self, ctx, typ: str = "majetek"):
        typ = typ.lower()
        hraci, inv = self.db.vsichni()
        ids = set(hraci) | set(inv)
        medaile = ["🥇", "🥈", "🥉"]

        if typ in ("majetek", "penize", "money", "bohatstvi"):
            zebr = sorted(((self.majetek(u, hraci.get(u, 0), inv.get(u, {})), u) for u in ids),
                          reverse=True)[:10]
            radky = []
            for i, (castka, uid) in enumerate(zebr):
                znacka = medaile[i] if i < 3 else f"**{i + 1}.**"
                radky.append(f"{znacka} {await self.jmeno(uid)}: **{kc(castka)}**")
            e = discord.Embed(title="🏆 Největší majetek",
                              description="\n".join(radky) or "Zatím nikdo nic nemá.",
                              color=0xFFC107)
            e.set_footer(text="Zůstatek + hodnota všech itemů")
            await ctx.send(embed=e)
            return

        if typ in ("rarita", "item", "vzacnost", "rare"):
            vlastnici = Counter(k for items in inv.values() for k in items if k in ITEMS)
            zebr = []
            for uid, items in inv.items():
                platne = [k for k in items if k in ITEMS]
                if not platne:
                    continue
                nej = max(platne, key=lambda k: (RARITY[ITEMS[k]["rarita"]]["poradi"], ITEMS[k]["hodnota"]))
                zebr.append((-RARITY[ITEMS[nej]["rarita"]]["poradi"], -ITEMS[nej]["hodnota"],
                             vlastnici[nej], uid, nej))
            zebr.sort()
            radky = []
            for i, (_, _, pocet_majitelu, uid, kod) in enumerate(zebr[:10]):
                it = ITEMS[kod]
                r = RARITY[it["rarita"]]
                znacka = medaile[i] if i < 3 else f"**{i + 1}.**"
                radky.append(f"{znacka} {await self.jmeno(uid)}: {r['emoji']} **{it['nazev']}** "
                             f"({r['nazev']}) • 👥 {pocet_majitelu}")
            e = discord.Embed(title="💎 Nejvzácnější itemy",
                              description="\n".join(radky) or "Zatím nikdo nemá žádný item.",
                              color=0x9C27B0)
            e.set_footer(text="Řazeno podle rarity, hodnoty a nejmenšího počtu majitelů")
            await ctx.send(embed=e)
            return

        await ctx.send("❌ Použij `prd top majetek` nebo `prd top rarita`.")

    @commands.command(name="gambling", aliases=["hazard", "ghelp", "ekonomika"])
    async def gambling_help(self, ctx):
        e = discord.Embed(
            title="🎰 Nápověda: Hazard & ekonomika",
            description="Vydělávej prachy, otevírej bedny, sbírej vzácné itemy, investuj, randi a obchoduj.\nPrefix pro všechny příkazy je **`prd`**.",
            color=0xFFC107
        )

        e.add_field(
            name="💰 Peníze a práce",
            value=(
                "`prd balance [@uživatel]` – Tvůj zůstatek, vztah a celkový majetek\n"
                "`prd zebrat` – Vyžebráš drobné (cooldown 30 s)\n"
                "`prd prace [id]` – Zobrazí nabídku prací nebo tě přihlásí\n"
                "`prd vyplata` – Vybere nahromaděnou výplatu (1 měsíc = 6 h)\n"
                "`prd vypoved` – Ukončí aktuální práci\n"
                "`prd poslat [@uživatel] [částka]` – Pošleš uživateli danou částku"
            ),
            inline=False
        )

        e.add_field(
            name="💘 Vztahy a seznamka",
            value=(
                "`prd pohlavi <muz/zena>` – Nastaví tvé pohlaví\n"
                "`prd orientace <hetero/bi/homo>` – Nastaví koho hledáš\n"
                "`prd tinder` – Swipování na randící appce\n"
                "`prd ven` – Procházka venku (šance potkat někoho na ulici)\n"
                "`prd vztah [@uživatel]` – Ukáže partnera, jeho pasivní schopnost a stav rande\n"
                "`prd rande` – Pozve partnera na rande a zvedne spokojenost\n"
                "`prd darek <item>` – Daruje partnerovi item z inventáře\n"
                "`prd rozchod` – Ukončí aktuální vztah"
            ),
            inline=False
        )

        e.add_field(
            name="🎲 Kasino hry",
            value=(
                "`prd sloty <sázka>` – Roztočí výherní automaty s animací\n"
                "`prd blackjack <sázka>` – Interaktivní blackjack s tlačítky\n"
                "`prd poker <sázka>` – Video poker (5-Card Draw) s výměnou karet\n"
                "`prd ruleta <volba> <sázka>` – Ruleta (`cervena`, `cerna`, `zelena`, `0–36`)"
            ),
            inline=False
        )

        e.add_field(
            name="📈 Investice a burza",
            value=(
                "`prd trh` – Přehled dostupných fiktivních firem a krypta\n"
                "`prd investinfo <symbol>` – Graf a detailní analýza vybrané investice\n"
                "`prd invest <symbol> <částka>` – Koupí podíly v dané firmě/kryptu\n"
                "`prd portfolio` – Zobrazí tvé aktivní investice a zisk\n"
                "`prd prodatinvestici <symbol>` – Odprodej investic zpět na hotovost"
            ),
            inline=False
        )

        e.add_field(
            name="📦 Bedny a drop",
            value=(
                "`prd bedny` – Seznam dostupných beden, cen a šancí na drop\n"
                "`prd otevrit <bedna> [počet]` – Otevře 1 až 1000 beden najednou"
            ),
            inline=False
        )

        e.add_field(
            name="🎒 Inventář a obchod",
            value=(
                "`prd inventar [@uživatel]` – Ukáže tvé itemy a jejich hodnotu\n"
                "`prd item <kód/název>` – Detail itemu a počet majitelů na serveru\n"
                "`prd prodat <kód/název> [počet]` – Prodá item botovi za základní cenu\n"
                "`prd trade <@uživatel> <tvůj_item> <jejich_item>` – Výměna 1 za 1\n"
                "`prd nabidka <@uživatel> <item> <cena>` – Prodej item jinému hráči"
            ),
            inline=False
        )

        e.add_field(
            name="🏆 Žebříčky",
            value=(
                "`prd top majetek` – Top 10 nejbohatších hráčů\n"
                "`prd top rarita` – Top 10 hráčů s nejvzácnějšími itemy"
            ),
            inline=False
        )

        e.set_footer(text="Tip: Místo celého názvu itemu stačí psát jeho kód nebo symbol (např. NEVIDIMJA).")
        await ctx.send(embed=e)


async def setup(bot):
    await bot.add_cog(Hazard(bot))
