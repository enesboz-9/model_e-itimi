"""
MODÜL 4 — Streamlit Arayüzü
Araç Değerleme ve Piyasa Analiz Platformu
"""

import streamlit as st
import pandas as pd
import numpy as np
import pickle
import base64
import json
import requests
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="AutoValuate — Araç Değerleme",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════
# TEMA & CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

* { font-family: 'DM Sans', sans-serif; }

.stApp {
    background: #09090f;
    background-image:
        radial-gradient(ellipse 80% 60% at 50% -10%, rgba(99,102,241,.18) 0%, transparent 70%),
        radial-gradient(ellipse 60% 40% at 90% 80%, rgba(16,185,129,.10) 0%, transparent 60%);
}

/* Genel arka plan */
section[data-testid="stSidebar"] { background: #0f0f1a; }

/* Başlık */
.hero { text-align:center; padding: 3rem 1rem 2rem; }
.hero-title {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: clamp(2rem, 5vw, 3.5rem);
    letter-spacing: -1.5px;
    background: linear-gradient(135deg, #fff 30%, #818cf8 70%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.hero-sub {
    color: #6b7280;
    font-size: 1rem;
    margin-top: .6rem;
    font-weight: 300;
    letter-spacing: .5px;
}

/* Sekme çubuğu */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 14px;
    padding: 5px;
    gap: 4px;
    backdrop-filter: blur(10px);
}
.stTabs [data-baseweb="tab"] {
    color: #6b7280;
    border-radius: 10px;
    padding: 9px 22px;
    font-size: .875rem;
    font-weight: 500;
    transition: all .2s;
}
.stTabs [aria-selected="true"] {
    background: rgba(99,102,241,.2) !important;
    color: #818cf8 !important;
    border: 1px solid rgba(99,102,241,.3) !important;
}

/* Kart */
.gcard {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 16px;
    padding: 22px 24px;
    margin-bottom: 18px;
    backdrop-filter: blur(8px);
}
.gcard-title {
    font-family: 'Syne', sans-serif;
    font-size: .75rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #818cf8;
    margin-bottom: 16px;
}

/* Sonuç kutusu */
.result-hero {
    background: linear-gradient(135deg,
        rgba(99,102,241,.12) 0%,
        rgba(16,185,129,.08) 100%);
    border: 1.5px solid rgba(99,102,241,.35);
    border-radius: 20px;
    padding: 40px;
    text-align: center;
    margin: 20px 0;
    position: relative;
    overflow: hidden;
}
.result-hero::before {
    content: '';
    position: absolute;
    top: -50%;  left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at center,
        rgba(99,102,241,.05) 0%, transparent 60%);
    pointer-events: none;
}
.result-label {
    color: #9ca3af;
    font-size: .85rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.result-price {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight: 800;
    color: #fff;
    letter-spacing: -1px;
}
.result-range {
    color: #6b7280;
    font-size: .88rem;
    margin-top: 8px;
}
.verdict-uygun  { color: #34d399; font-weight: 700; font-size: 1.1rem; }
.verdict-pahali { color: #f87171; font-weight: 700; font-size: 1.1rem; }
.verdict-normal { color: #fbbf24; font-weight: 700; font-size: 1.1rem; }

/* Metrik kartları */
.mkart-row { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 18px; }
.mkart {
    flex: 1; min-width: 110px;
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 12px;
    padding: 14px;
    text-align: center;
}
.mkart-val { color: #e5e7eb; font-size: 1rem; font-weight: 600; }
.mkart-lbl { color: #6b7280; font-size: .72rem; margin-top: 4px; }

/* İlan kartları */
.ilan {
    background: rgba(255,255,255,.025);
    border: 1px solid rgba(255,255,255,.06);
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 10px;
    transition: border-color .2s;
}
.ilan:hover { border-color: rgba(99,102,241,.4); }
.ilan-uygun  { border-left: 3px solid #34d399; }
.ilan-pahali { border-left: 3px solid #f87171; }
.ilan-normal { border-left: 3px solid #fbbf24; }
.ilan-fiyat  { color: #e5e7eb; font-size: 1.3rem; font-weight: 700; }
.ilan-meta   { color: #6b7280; font-size: .8rem; margin-top: 6px; }

/* Rozet */
.badge {
    display: inline-block;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: .72rem;
    font-weight: 600;
    margin-right: 6px;
}
.b-green  { background: rgba(52,211,153,.12); color:#34d399; border:1px solid rgba(52,211,153,.3); }
.b-red    { background: rgba(248,113,113,.12); color:#f87171; border:1px solid rgba(248,113,113,.3); }
.b-yellow { background: rgba(251,191,36,.12);  color:#fbbf24; border:1px solid rgba(251,191,36,.3); }
.b-indigo { background: rgba(99,102,241,.12);  color:#818cf8; border:1px solid rgba(99,102,241,.3); }
.b-gray   { background: rgba(255,255,255,.05); color:#9ca3af; border:1px solid rgba(255,255,255,.1); }

/* Progress bar */
.gbar { height:6px; background:rgba(255,255,255,.06); border-radius:3px; overflow:hidden; margin:5px 0 12px; }
.gbar-fill { height:100%; border-radius:3px; }

/* Öneri kartı */
.oneri-card {
    background: rgba(99,102,241,.07);
    border: 1px solid rgba(99,102,241,.2);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ENCODER VERİLERİ
# ══════════════════════════════════════════════════════════════
MARKA_ENC = {"Alfa Romeo": 0, "Arora": 1, "Audi": 2, "BMW": 3, "BYD": 4, "Buick": 5, "Cadillac": 6, "Chery": 7, "Chevrolet": 8, "Chrysler": 9, "Citroen": 10, "Cupra": 11, "DS Automobiles": 12, "Dacia": 13, "Daewoo": 14, "Daihatsu": 15, "Dodge": 16, "Ferrari": 17, "Fiat": 18, "Ford": 19, "Geely": 20, "Honda": 21, "Hyundai": 22, "Ikco": 23, "Infiniti": 24, "Jaguar": 25, "Kia": 26, "Kuba": 27, "Lada": 28, "Lancia": 29, "Leapmotor": 30, "Lexus": 31, "Lincoln": 32, "Lotus": 33, "Luqi": 34, "MG": 35, "Maserati": 36, "Mazda": 37, "Mercedes - Benz": 38, "Mercury": 39, "Mini": 40, "Mitsubishi": 41, "Nissan": 42, "Opel": 43, "Peugeot": 44, "Plymouth": 45, "Pontiac": 46, "Porsche": 47, "Proton": 48, "RKS": 49, "Rainwoll": 50, "Reeder": 51, "Regal Raptor": 52, "Relive": 53, "Renault": 54, "Rover": 55, "Saab": 56, "Seat": 57, "Skoda": 58, "Smart": 59, "Subaru": 60, "Suzuki": 61, "TOGG": 62, "Tata": 63, "Tesla": 64, "Tofaş": 65, "Toyota": 66, "Vanderhall": 67, "Volkswagen": 68, "Volta": 69, "Volvo": 70, "Yuki": 71, "nan": 72}

SERI_ENC = {"1 Serisi": 0, "100 NX": 1, "100 Serisi": 2, "106": 3, "107": 4, "121": 5, "126 Bis": 6, "145": 7, "146": 8, "147": 9, "156": 10, "159": 11, "166": 12, "190": 13, "2": 14, "2 Serisi": 15, "200": 16, "200 SX": 17, "205": 18, "206": 19, "206+": 20, "207": 21, "208": 22, "214": 23, "216": 24, "218": 25, "220": 26, "230": 27, "240": 28, "25": 29, "250": 30, "260": 31, "280": 32, "3": 33, "3 Serisi": 34, "300": 35, "300 C": 36, "300 M": 37, "3000GT": 38, "301": 39, "306": 40, "307": 41, "308": 42, "309": 43, "315": 44, "323": 45, "348": 46, "350 Z": 47, "4 Serisi": 48, "400": 49, "405": 50, "406": 51, "407": 52, "414": 53, "415": 54, "416": 55, "418": 56, "420": 57, "45": 58, "5": 59, "5 Serisi": 60, "500": 61, "500 Abarth": 62, "500 Ailesi": 63, "508": 64, "560": 65, "6": 66, "6 Serisi": 67, "607": 68, "620": 69, "623 Si": 70, "626": 71, "7 Serisi": 72, "75": 73, "80 Serisi": 74, "806": 75, "807": 76, "820": 77, "850": 78, "9-3": 79, "9-5": 80, "90 Serisi": 81, "900": 82, "9000": 83, "940": 84, "960": 85, "A": 86, "A1": 87, "A2": 88, "A3": 89, "A4": 90, "A5": 91, "A6": 92, "A7": 93, "A8": 94, "AMİ": 95, "Accent": 96, "Accent Blue": 97, "Accent Era": 98, "Accord": 99, "Adam": 100, "Agila": 101, "Albea": 102, "Alhambra": 103, "Alia": 104, "Almera": 105, "Altea": 106, "Altima": 107, "Alto": 108, "Amy": 109, "Applause": 110, "Arosa": 111, "Arteon": 112, "Ascona": 113, "Astra": 114, "Astra-e": 115, "Atos": 116, "Attrage": 117, "Auris": 118, "Avenger": 119, "Avensis": 120, "Aveo": 121, "B": 122, "B-Max": 123, "BLS": 124, "BRZ": 125, "BX": 126, "Baleno": 127, "Bluebird": 128, "Bora": 129, "Born": 130, "Boxster": 131, "Brava": 132, "Bravo": 133, "C": 134, "C-Elysée": 135, "C-Max": 136, "C1": 137, "C2": 138, "C3": 139, "C3 Picasso": 140, "C30": 141, "C4": 142, "C4 Grand Picasso": 143, "C4 Picasso": 144, "C4 X": 145, "C5": 146, "C6": 147, "C70": 148, "C8": 149, "CL": 150, "CLA": 151, "CLC": 152, "CLK": 153, "CLS": 154, "CR-Z": 155, "CRX": 156, "CT": 157, "CTS": 158, "Calibra": 159, "Camaro": 160, "Camry": 161, "Capital": 162, "Carens": 163, "Carina": 164, "Carisma": 165, "Carmel": 166, "Carnival": 167, "Cayman": 168, "Ceed": 169, "Celica": 170, "Cerato": 171, "Chance": 172, "Charade": 173, "Citigo": 174, "City": 175, "Civic": 176, "Clarus": 177, "Clio": 178, "Colt": 179, "Concorde": 180, "Cooper": 181, "Cooper Clubman": 182, "Cooper S": 183, "Copen": 184, "Cordoba": 185, "Corolla": 186, "Corona": 187, "Corsa": 188, "Corsa-e": 189, "Corvette": 190, "Coupe": 191, "Cressida": 192, "Croma": 193, "Crossfire": 194, "Crown": 195, "Cruze": 196, "Cuore": 197, "DS3": 198, "DS4": 199, "DS5": 200, "DS9": 201, "Daimler": 202, "DeVille": 203, "Delta": 204, "Diamante": 205, "Dolphin": 206, "Doğan": 207, "E": 208, "EOS": 209, "EQE": 210, "ES": 211, "EV1": 212, "EV300": 213, "EZI": 214, "Echo": 215, "Egea": 216, "Elantra": 217, "Emgrand": 218, "Epica": 219, "Escort": 220, "Espace": 221, "Espero": 222, "Esprit": 223, "Evanda": 224, "Evasion": 225, "Excel": 226, "Exeo": 227, "F-Type": 228, "FC": 229, "FR-V": 230, "Fabia": 231, "Familia": 232, "Favorit": 233, "Felicia": 234, "Festiva": 235, "Fiesta": 236, "Firebird": 237, "Fluence": 238, "Focus": 239, "ForFour": 240, "ForTwo": 241, "Forman": 242, "Fusion": 243, "GS": 244, "GT": 245, "GT-R": 246, "GTV": 247, "Galant": 248, "Galaxy": 249, "Gen 2": 250, "Genesis": 251, "Getz": 252, "Ghibli": 253, "Giulia": 254, "Giulietta": 255, "Golf": 256, "GranTurismo": 257, "Granada": 258, "Grand C-Max": 259, "Grand Marquis": 260, "Grand Scenic": 261, "Grandeur": 262, "Han": 263, "Hector": 264, "ID.3": 265, "ID.7": 266, "IS": 267, "Ibiza": 268, "Idea": 269, "Ignis": 270, "Impreza": 271, "Indica": 272, "Indigo": 273, "Insignia": 274, "Integra": 275, "Ioniq 6": 276, "Jazz": 277, "Jetta": 278, "Jogger": 279, "John Cooper": 280, "Justy": 281, "K4": 282, "K5 Long": 283, "Ka": 284, "Kadett": 285, "Kalina": 286, "Kalos": 287, "Kappa": 288, "Kartal": 289, "Kimo": 290, "LHS": 291, "Lacetti": 292, "Laguna": 293, "Lancer": 294, "Lancer Evolution": 295, "Lanos": 296, "Lantis": 297, "Laser": 298, "Latitude": 299, "Laurel Altima": 300, "Le Sabre": 301, "Legacy": 302, "Leganza": 303, "Legend": 304, "Leon": 305, "Levorg": 306, "Liana": 307, "Linea": 308, "Lodgy": 309, "Logan": 310, "Lupo": 311, "M": 312, "M Serisi": 313, "M5": 314, "MG4": 315, "MG7": 316, "MPV": 317, "MT3": 318, "MX": 319, "Magentis": 320, "Manta": 321, "Manza": 322, "Marea": 323, "Marina": 324, "Mark": 325, "Maruti": 326, "Materia": 327, "Matiz": 328, "Matrix": 329, "Maxima": 330, "Megane": 331, "Megane E-Tech": 332, "Meriva": 333, "MiTo": 334, "Micra": 335, "Model 3": 336, "Model S": 337, "Model X": 338, "Model Y": 339, "Modus": 340, "Mondeo": 341, "Move": 342, "Murat": 343, "Mustang": 344, "N1": 345, "NX Coupe": 346, "Neon": 347, "New Beetle": 348, "Nexia": 349, "Niche": 350, "Note": 351, "Nova": 352, "Nubira": 353, "Octavia": 354, "Omega": 355, "One": 356, "Opirus": 357, "Optima": 358, "PT Cruiser": 359, "Palio": 360, "Panamera": 361, "Panda": 362, "Passat": 363, "Passat Alltrack": 364, "Passat Variant": 365, "Phaeton": 366, "Picanto": 367, "Polo": 368, "Prelude": 369, "Premacy": 370, "Pride": 371, "Primera": 372, "Prius": 373, "Pro Ceed": 374, "Pulsar": 375, "Punto": 376, "Q30": 377, "Q50": 378, "Q60": 379, "Quattroporte": 380, "R": 381, "R 11": 382, "R 12": 383, "R 19": 384, "R 21": 385, "R 25": 386, "R 5": 387, "R 9": 388, "R5 E-Tech": 389, "RCZ": 390, "RS": 391, "RW10": 392, "RX": 393, "Rapid": 394, "Reev Fancy": 395, "Rekord": 396, "Rezzo": 397, "Rio": 398, "Roomster": 399, "S": 400, "S-Max": 401, "S-Type": 402, "S1": 403, "S2000": 404, "S40": 405, "S60": 406, "S70": 407, "S80": 408, "S90": 409, "SL": 410, "SLK": 411, "SX4": 412, "Safrane": 413, "Saga": 414, "Samand": 415, "Samara": 416, "Sandero": 417, "Santamo": 418, "Savvy": 419, "Saxo": 420, "Scala": 421, "Scenic": 422, "Scirocco": 423, "Scorpio": 424, "Seal": 425, "Seal U": 426, "Sebring": 427, "Sedici": 428, "Sentra": 429, "Sephia": 430, "Serçe": 431, "Seville": 432, "Sharan": 433, "Shuma": 434, "Shuttle": 435, "Siena": 436, "Sierra": 437, "Sirion": 438, "Solenza": 439, "Sonata": 440, "Sovereign": 441, "Space Star": 442, "Space Wagon": 443, "Spark": 444, "Splash": 445, "Starlet": 446, "Stilo": 447, "Stratus": 448, "Stream": 449, "Streetwise": 450, "Sunny": 451, "SuperB": 452, "Swift": 453, "Symbol": 454, "T03": 455, "T10F": 456, "TT": 457, "TTS": 458, "Taliant": 459, "Talisman": 460, "Taunus": 461, "Taurus": 462, "Teana": 463, "Tempra": 464, "Thema": 465, "Tico": 466, "Tigra": 467, "Tipo": 468, "Toledo": 469, "Topolino": 470, "Touran": 471, "Town Car": 472, "Trajet": 473, "Twingo": 474, "Twizy": 475, "Ulysse": 476, "Uno": 477, "Up Club": 478, "Urban Cruiser": 479, "V40": 480, "V40 Cross Country": 481, "V50": 482, "V60": 483, "V60 Cross Country": 484, "V70": 485, "V90 Cross Country": 486, "VAZ": 487, "VW CC": 488, "Vectra": 489, "Vega": 490, "Vel Satis": 491, "Venga": 492, "Vento": 493, "Verso": 494, "Vista": 495, "Vivio": 496, "Wagon R": 497, "Waja": 498, "X-Type": 499, "XE": 500, "XF": 501, "XJ": 502, "XJR": 503, "XJS": 504, "XKR": 505, "XM": 506, "Xantia": 507, "Xsara": 508, "YRV": 509, "Yaris": 510, "Ypsilon": 511, "Z Serisi": 512, "ZOE": 513, "ZT": 514, "ZX": 515, "Zafira": 516, "e-208": 517, "e-308": 518, "e-C3": 519, "e-C4": 520, "e-C4 X": 521, "i Serisi": 522, "i10": 523, "i20": 524, "i20 Active": 525, "i20 N": 526, "i20 Troy": 527, "i30": 528, "i40": 529, "ix20": 530, "Şahin": 531, "nan": 532}

YAKIT_ENC = {"Benzin": 0, "Dizel": 1, "Elektrik": 2, "Hibrit": 3, "LPG & Benzin": 4}
VITES_ENC = {"Düz": 0, "Otomatik": 1, "Yarı Otomatik": 2}
KASA_ENC = {"Bilinmiyor": 0, "Cabrio": 1, "Coupe": 2, "Hatchback/3": 3, "Hatchback/5": 4, "MPV": 5, "Pick-up": 6, "Roadster": 7, "SUV": 8, "Sedan": 9, "Station wagon": 10}
RENK_ENC = {"Altın": 0, "Bej": 1, "Beyaz": 2, "Bordo": 3, "Diğer": 4, "Füme": 5, "Gri": 6, "Gri (Gümüş)": 7, "Gri (metalik)": 8, "Gri (titanyum)": 9, "Kahverengi": 10, "Kırmızı": 11, "Lacivert": 12, "Mavi": 13, "Mavi (metalik)": 14, "Mor": 15, "Pembe": 16, "Sarı": 17, "Siyah": 18, "Turkuaz": 19, "Turuncu": 20, "Yeşil": 21, "Yeşil (metalik)": 22, "Şampanya": 23}
DURUM_ENC = {"Bilinmiyor": 0, "Sıfır": 1, "Yurtdışından İthal Sıfır": 2, "İkinci El": 3}
CEKIS_ENC = {"Önden Çekiş": 0, "Arkadan İtiş": 1, "4WD (Sürekli)": 2, "AWD (Elektronik)": 3}

# ══════════════════════════════════════════════════════════════
# KAYNAK YÜKLEYİCİLER
# ══════════════════════════════════════════════════════════════
@st.cache_resource
def yukle_model():
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for fname in ["model.pkl", "arac_fiyat_modeli.pkl",
                  os.path.join(script_dir, "model.pkl"),
                  os.path.join(script_dir, "arac_fiyat_modeli.pkl")]:
        if os.path.exists(fname):
            try:
                with open(fname, "rb") as f: return pickle.load(f)
            except Exception: continue
    return None

@st.cache_resource
def yukle_meta():
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for fname in ["model_meta.pkl", os.path.join(script_dir, "model_meta.pkl")]:
        if os.path.exists(fname):
            try:
                with open(fname, "rb") as f: return pickle.load(f)
            except Exception: continue
    return {}

@st.cache_data(show_spinner="Veri seti yükleniyor...")
def yukle_ham():
    """
    İlan Arama ve Piyasa Analizi için ham veri yükler.
    Önce arabam_temiz.csv/arabam_features.csv'yi dener (metin sütunlar varsa).
    Yoksa ham CSV'den gerekli sütunları okur ve enc sütunlarını metin'e çevirir.
    """
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Enc CSV'den ters çevir
    # Ters mapping sözlükleri
    enc_to_marka   = {v: k for k, v in MARKA_ENC.items()}
    enc_to_yakit   = {v: k for k, v in YAKIT_ENC.items()}
    enc_to_vites   = {v: k for k, v in VITES_ENC.items()}
    enc_to_kasa    = {v: k for k, v in KASA_ENC.items()}
    enc_to_renk    = {v: k for k, v in RENK_ENC.items()}
    enc_to_durum   = {v: k for k, v in DURUM_ENC.items()}

    # enc sütunlu CSV
    enc_cols = ["marka_enc","seri_enc","arac_yasi","yil","km","fiyat",
                "yakit_tipi_enc","vites_tipi_enc","kasa_tipi_enc",
                "renk_enc","arac_durumu_enc"]
    for fname in ["arabam_temiz.csv", "arabam_features.csv",
                  os.path.join(script_dir, "arabam_temiz.csv"),
                  os.path.join(script_dir, "arabam_features.csv")]:
        if not os.path.exists(fname):
            continue
        try:
            with open(fname, encoding="utf-8-sig") as fh:
                header = fh.readline()
            mevcut = [c for c in enc_cols if c in header]
            if "marka_enc" not in mevcut or "fiyat" not in mevcut:
                continue
            df = pd.read_csv(fname, encoding="utf-8-sig", usecols=mevcut, low_memory=False)
            df = df.dropna(subset=["fiyat"])
            df["fiyat"] = pd.to_numeric(df["fiyat"], errors="coerce")
            # yil sütunu yoksa arac_yasi'ndan türet
            if "yil" not in df.columns:
                if "arac_yasi" in df.columns:
                    df["yil"] = (2026 - pd.to_numeric(df["arac_yasi"], errors="coerce")).astype("Int64")
                else:
                    df["yil"] = 2020
            else:
                df["yil"] = pd.to_numeric(df["yil"], errors="coerce").astype("Int64")
            # km sütunu yoksa yillik_km * arac_yasi'ndan tahmin et
            if "km" not in df.columns:
                if "yillik_km" in df.columns and "arac_yasi" in df.columns:
                    df["km"] = pd.to_numeric(df["yillik_km"], errors="coerce") * pd.to_numeric(df["arac_yasi"], errors="coerce")
                else:
                    df["km"] = 50000
            else:
                df["km"] = pd.to_numeric(df["km"], errors="coerce")
            # enc → metin
            df["marka"]       = df["marka_enc"].map(enc_to_marka).fillna("Bilinmiyor")
            df["yakit_tipi"]  = df["yakit_tipi_enc"].map(enc_to_yakit).fillna("Bilinmiyor") if "yakit_tipi_enc" in df.columns else "Bilinmiyor"
            df["vites_tipi"]  = df["vites_tipi_enc"].map(enc_to_vites).fillna("Bilinmiyor") if "vites_tipi_enc" in df.columns else "Bilinmiyor"
            df["kasa_tipi"]   = df["kasa_tipi_enc"].map(enc_to_kasa).fillna("Bilinmiyor")   if "kasa_tipi_enc"  in df.columns else "Bilinmiyor"
            df["renk"]        = df["renk_enc"].map(enc_to_renk).fillna("Bilinmiyor")         if "renk_enc"       in df.columns else "Bilinmiyor"
            df["arac_durumu"] = df["arac_durumu_enc"].map(enc_to_durum).fillna("Bilinmiyor") if "arac_durumu_enc" in df.columns else "Bilinmiyor"
            # Seri: enc → isim (SERI_ENC duz sozluk: {seri_adi: enc_deger})
            enc_to_seri = {v: k for k, v in SERI_ENC.items()}
            if "seri_enc" in df.columns:
                df["seri"] = df["seri_enc"].map(enc_to_seri).fillna("Diğer")
            else:
                df["seri"] = "Diğer"
            df["kimden"]      = "Sahibinden"
            df["agir_hasarli"] = "Hayır"
            df["sehir"]       = ""
            sonuc = df[df["fiyat"] > 0].copy()
            if len(sonuc) > 0:
                return sonuc
        except Exception as e:
            continue

    # Son çare: ham CSV'den oku
    for fname in ["arabam.com-otomobil-veri-seti-csv.csv",
                  os.path.join(script_dir, "arabam.com-otomobil-veri-seti-csv.csv")]:
        if not os.path.exists(fname):
            continue
        try:
            usecols = ["marka","seri","yil","km","fiyat","yakit_tipi","vites_tipi",
                       "kasa_tipi","renk","arac_durumu","kimden","agir_hasarli","sehir"]
            df = pd.read_csv(fname, encoding="utf-8-sig", usecols=usecols, low_memory=False)
            df = df.dropna(subset=["fiyat"])
            df["fiyat"] = pd.to_numeric(df["fiyat"], errors="coerce")
            df["yil"]   = pd.to_numeric(df["yil"],   errors="coerce").astype("Int64")
            df["km"]    = pd.to_numeric(df["km"],     errors="coerce")
            sonuc = df[df["fiyat"] > 0].copy()
            if len(sonuc) > 0:
                return sonuc
        except Exception:
            continue

    return None

model = yukle_model()
meta  = yukle_meta()

# ══════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════
def tl(x): return f"{x:,.0f} TL"

def fotograf_analiz(img_bytes):
    b64 = base64.standard_b64encode(img_bytes).decode()
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":300,
                  "messages":[{"role":"user","content":[
                      {"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":b64}},
                      {"type":"text","text":'Araç fotoğrafı. SADECE JSON:\n{"kasa_tipi":"Sedan|Hatchback/5|Hatchback/3|SUV|Coupe|Station wagon|MPV|Cabrio|Pick-up|Bilinmiyor","renk":"Beyaz|Siyah|Gri|Kırmızı|Mavi|Lacivert|Kahverengi|Bordo|Yeşil|Sarı|Turuncu|Mor|Bej|Şampanya|Füme|Diğer","aciklama":"kısa açıklama"}'}
                  ]}]},
            timeout=15
        )
        t = r.json()["content"][0]["text"].strip().replace("```json","").replace("```","")
        return json.loads(t)
    except Exception as e:
        return {"kasa_tipi":"Bilinmiyor","renk":"Diğer","aciklama":str(e)}

def tahmin_yap(form):
    """
    Model ile fiyat tahmini.
    Özellik listesini model.feature_names_in_'den alır — hardcode yok.
    19-feature eski model ve 25-feature yeni model ikisini de destekler.
    """
    arac_yasi = 2026 - form["yil"]
    guc_hacim = form["motor_gucu_hp"] / form["motor_hacmi_cc"] if form["motor_hacmi_cc"] > 0 else 0
    seri_enc  = SERI_ENC.get(form["seri"], 0)  # Global encoding

    def yas_seg(y):
        return 0 if y<=2 else 1 if y<=5 else 2 if y<=10 else 3 if y<=15 else 4
    def guc_seg(h):
        return 0 if h<90 else 1 if h<140 else 2 if h<220 else 3
    def hacim_seg(c):
        return 0 if c<1000 else 1 if c<1400 else 2 if c<1800 else 3 if c<2500 else 4

    # FE normalizasyon sabitleri — model_meta varsa oradan, yoksa eğitim verisi istatistikleri
    fe_sabitler = meta.get("fe_sabitler", {})
    gh_median = fe_sabitler.get("guc_hacim_median", 0.0693)
    gh_std    = fe_sabitler.get("guc_hacim_std",    0.0388)
    guc_hacim_norm = float(np.clip((guc_hacim - gh_median) / (gh_std + 1e-9), -3, 3))

    # Marka popülaritesi
    marka_pop = 0.5
    try:
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for pkl_path in ["marka_meta.pkl", os.path.join(script_dir, "marka_meta.pkl")]:
            if os.path.exists(pkl_path):
                with open(pkl_path, "rb") as fh:
                    mm = pickle.load(fh)
                pop_dict = mm.get("popularite", {})
                max_pop  = max(pop_dict.values()) if pop_dict else 1
                marka_pop = pop_dict.get(form["marka"], 0) / max_pop if max_pop > 0 else 0.5
                break
    except Exception:
        pass

    # Tüm olası feature'ları hesapla
    row = {
        # ── Temel 19 feature (her model için) ──────────────────
        "arac_yasi":          arac_yasi,
        "km":                 form["km"],
        "yillik_km":          form["km"] / max(arac_yasi, 1),
        "hasar_skoru":        form["hasar_skoru"],
        "motor_hacmi_cc":     form["motor_hacmi_cc"],
        "motor_gucu_hp":      form["motor_gucu_hp"],
        "guc_hacim_orani":    guc_hacim,
        "cekis_enc":          CEKIS_ENC.get(form["cekis"], 0),
        "kimden_galeri":      1 if form["kimden"] == "Galeriden" else 0,
        "kimden_bayi":        1 if form["kimden"] == "Yetkili Bayiden" else 0,
        "agir_hasarli_evet":  1 if form["agir_hasar"] == "Evet" else 0,
        "takasa_uygun_evet":  1 if form["takasa"] == "Evet" else 0,
        "marka_enc":          MARKA_ENC.get(form["marka"], 0),
        "seri_enc":           seri_enc,
        "yakit_tipi_enc":     YAKIT_ENC.get(form["yakit"], 0),
        "vites_tipi_enc":     VITES_ENC.get(form["vites"], 0),
        "kasa_tipi_enc":      KASA_ENC.get(form["kasa"], 0),
        "renk_enc":           RENK_ENC.get(form["renk"], 2),
        "arac_durumu_enc":    DURUM_ENC.get(form["durum"], 2),
        # ── FE feature'ları (25-feature yeni model için) ────────
        "yas_segment":        yas_seg(arac_yasi),
        "guc_hacim_norm":     guc_hacim_norm,
        "guc_segment":        guc_seg(form["motor_gucu_hp"]),
        "hacim_segment":      hacim_seg(form["motor_hacmi_cc"]),
        "marka_popularite":   marka_pop,
        "km_anomali":         0.0,
    }

    # ── Model feature listesini belirle ──────────────────────────
    # Öncelik: 1) model.feature_names_in_  2) model_meta  3) model'in XGBoost iç listesi
    if hasattr(model, "feature_names_in_"):
        ozellikler = list(model.feature_names_in_)
    elif meta.get("ozellikler"):
        ozellikler = meta["ozellikler"]
    else:
        # Eski XGBoost: booster'dan feature isimlerini al
        try:
            ozellikler = model.get_booster().feature_names
            if not ozellikler:
                raise ValueError("boş")
        except Exception:
            # Son çare: sadece temel 19 feature gönder
            ozellikler = [
                "arac_yasi","km","yillik_km","hasar_skoru","motor_hacmi_cc",
                "motor_gucu_hp","guc_hacim_orani","cekis_enc","kimden_galeri",
                "kimden_bayi","agir_hasarli_evet","takasa_uygun_evet","marka_enc",
                "seri_enc","yakit_tipi_enc","vites_tipi_enc","kasa_tipi_enc",
                "renk_enc","arac_durumu_enc",
            ]

    veri = pd.DataFrame([{k: row.get(k, 0) for k in ozellikler}])
    return float(np.expm1(model.predict(veri)[0]))

def piyasa_analiz(df_ham, marka, seri=None, yil_min=2010, yil_max=2026):
    mask = df_ham["marka"].str.lower() == marka.lower()
    if seri:
        mask &= df_ham["seri"].str.lower() == seri.lower()
    mask &= df_ham["yil"].between(yil_min, yil_max)
    d = df_ham[mask]
    if d.empty: return {}
    return {
        "adet": len(d), "min": d["fiyat"].min(), "max": d["fiyat"].max(),
        "medyan": d["fiyat"].median(), "ort": d["fiyat"].mean(),
        "q25": d["fiyat"].quantile(.25), "q75": d["fiyat"].quantile(.75),
        "yakit": d["yakit_tipi"].value_counts().to_dict() if "yakit_tipi" in d else {},
        "kasa":  d["kasa_tipi"].value_counts().to_dict()  if "kasa_tipi"  in d else {},
    }

def oneri_bul(df_ham, kasa, fiyat_ust, fiyat_alt, marka_hariç=None, n=5):
    """Aynı kasa tipinde, benzer fiyat bandında alternatif öner."""
    df_ham = df_ham.reset_index(drop=True)  # index uyumsuzluğunu önle
    mask = pd.Series([True] * len(df_ham))
    if "kasa_tipi" in df_ham.columns and kasa and kasa != "Bilinmiyor":
        mask &= df_ham["kasa_tipi"].str.lower() == kasa.lower()
    mask &= df_ham["fiyat"].between(fiyat_alt, fiyat_ust)
    if marka_hariç and "marka" in df_ham.columns:
        mask &= df_ham["marka"].str.lower() != marka_hariç.lower()
    sonuc = df_ham[mask].copy()
    if sonuc.empty: return pd.DataFrame()
    return sonuc.sort_values("fiyat").drop_duplicates(subset=["marka","seri"]).head(n)

def verdict(tahmin, medyan):
    pct = ((tahmin - medyan) / medyan) * 100 if medyan > 0 else 0
    if pct <= -10:
        return "uygun", f"Piyasadan %{abs(pct):.1f} ucuz ✓", "verdict-uygun", "b-green"
    elif pct >= 10:
        return "pahali", f"Piyasadan %{abs(pct):.1f} pahalı ✗", "verdict-pahali", "b-red"
    else:
        return "normal", f"Piyasa ortalamasına yakın (~%{abs(pct):.1f})", "verdict-normal", "b-yellow"

# ══════════════════════════════════════════════════════════════
# BAŞLIK
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
    <h1 class="hero-title">AutoValuate</h1>
    <p class="hero-sub">Yapay Zeka Destekli Araç Değerleme & Piyasa Analiz Platformu</p>
</div>
""", unsafe_allow_html=True)

if model is None:
    st.error("⚠️ model.pkl (veya arac_fiyat_modeli.pkl) bulunamadı. Önce `python3 3_model_egitim.py` çalıştır.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs([
    "🔮  Değerleme",
    "🔍  İlan Arama",
    "📊  Piyasa Analizi",
    "🤖  Model Bilgisi",
])

# ══════════════════════════════════════════════════════════════
# TAB 1 — DEĞERLEME
# ══════════════════════════════════════════════════════════════
with tab1:

    # — Fotoğraf —
    st.markdown('<div class="gcard"><div class="gcard-title">📸 Araç Fotoğrafı (İsteğe Bağlı)</div>', unsafe_allow_html=True)
    foto = st.file_uploader("Fotoğraf yükle → kasa tipi ve renk otomatik tespit edilir",
                             type=["jpg","jpeg","png"], key="foto")
    ai_kasa = ai_renk = None
    if foto:
        c1, c2 = st.columns(2)
        with c1: st.image(foto, use_container_width=True)
        with c2:
            with st.spinner("🤖 AI analiz ediyor..."):
                res = fotograf_analiz(foto.read())
                ai_kasa = res.get("kasa_tipi","Bilinmiyor")
                ai_renk = res.get("renk","Diğer")
            st.success(f"**Kasa:** {ai_kasa}  |  **Renk:** {ai_renk}")
            st.caption(res.get("aciklama",""))
            st.info("Aşağıda AI tespitlerini onaylayabilir veya değiştirebilirsin.")
    st.markdown('</div>', unsafe_allow_html=True)

    # — Form —
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="gcard"><div class="gcard-title">🚘 Araç Bilgileri</div>', unsafe_allow_html=True)
        marka = st.selectbox("Marka", sorted(MARKA_ENC), index=list(sorted(MARKA_ENC)).index("Toyota"))
        seri_listesi = sorted(SERI_ENC.get(marka, {"Diğer":0}).keys())
        seri = st.selectbox("Model / Seri", seri_listesi or ["Diğer"])
        cy, ck = st.columns(2)
        with cy: yil = st.number_input("Yıl", 1985, 2026, 2019, step=1)
        with ck: km  = st.slider("Kilometre", 0, 500_000, 85_000, step=5000)
        durum = st.selectbox("Araç Durumu", list(DURUM_ENC), index=3)
        h1, h2 = st.columns(2)
        with h1:
            kimden     = st.radio("Kimden?", ["Sahibinden","Galeriden","Yetkili Bayiden"])
            agir_hasar = st.radio("Ağır Hasarlı?", ["Hayır","Evet"])
        with h2:
            takasa      = st.radio("Takasa Uygun?", ["Hayır","Evet"])
            hasar_skoru = st.slider("Hasar Skoru", 0, 26, 0,
                                    help="0=Orijinal, 26=Maksimum hasar")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="gcard"><div class="gcard-title">⚙️ Teknik &amp; Ek Bilgiler <span style="font-size:0.72rem;font-weight:400;opacity:.6">(İsteğe Bağlı)</span></div>', unsafe_allow_html=True)
        st.caption("Boş bırakılan alanlar için model ortalama değerleri kullanır.")

        with st.expander("🔧 Motor & Performans", expanded=False):
            ch, cg = st.columns(2)
            with ch: motor_hacmi = st.number_input("Motor Hacmi (cc)", 0, 7000, 0, step=50,
                                                    help="0 = belirtilmemiş")
            with cg: motor_gucu  = st.number_input("Motor Gücü (HP)",  0, 1500, 0, step=5,
                                                    help="0 = belirtilmemiş")
            cekis = st.selectbox("Çekiş", ["Belirtilmemiş"] + list(CEKIS_ENC))

        with st.expander("🚗 Yakıt / Vites / Kasa", expanded=False):
            yakit = st.selectbox("Yakıt Tipi", ["Belirtilmemiş"] + list(YAKIT_ENC))
            vites = st.selectbox("Vites",      ["Belirtilmemiş"] + list(VITES_ENC))
            kasa_opts = ["Belirtilmemiş"] + [k for k in KASA_ENC if k != "Bilinmiyor"] + ["Bilinmiyor"]
            kasa_idx  = kasa_opts.index(ai_kasa) if ai_kasa and ai_kasa in kasa_opts else 0
            kasa = st.selectbox("Kasa Tipi" + (" 🤖" if ai_kasa else ""), kasa_opts, index=kasa_idx)

        with st.expander("🎨 Renk", expanded=False):
            renk_listesi = ["Belirtilmemiş"] + sorted(RENK_ENC)
            renk_idx = renk_listesi.index(ai_renk) if ai_renk and ai_renk in renk_listesi else 0
            renk = st.selectbox("Renk" + (" 🤖" if ai_renk else ""), renk_listesi, index=renk_idx)

        # Varsayılan değerleri belirle (belirtilmemişse medyan/ortalama kullan)
        motor_hacmi_son = motor_hacmi if motor_hacmi > 0 else 1600
        motor_gucu_son  = motor_gucu  if motor_gucu  > 0 else 110
        cekis_son       = cekis  if cekis  != "Belirtilmemiş" else "Önden Çekiş"
        yakit_son       = yakit  if yakit  != "Belirtilmemiş" else list(YAKIT_ENC)[1]
        vites_son       = vites  if vites  != "Belirtilmemiş" else list(VITES_ENC)[1]
        kasa_son        = kasa   if kasa   != "Belirtilmemiş" else "Sedan"
        renk_son        = renk   if renk   != "Belirtilmemiş" else "Beyaz"

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔮  Değerleme Yap", use_container_width=True, type="primary"):
        form = dict(
            marka=marka, seri=seri, yil=yil, km=km,
            yakit=yakit_son, vites=vites_son, kasa=kasa_son, durum=durum,
            motor_hacmi_cc=motor_hacmi_son, motor_gucu_hp=motor_gucu_son,
            cekis=cekis_son, renk=renk_son, kimden=kimden,
            agir_hasar=agir_hasar, takasa=takasa, hasar_skoru=hasar_skoru,
        )

        # Lüks/egzotik marka kontrolü
        LUKS_MARKALAR = {
            "Ferrari", "Lamborghini", "Bentley", "Rolls-Royce", "Maserati",
            "Aston Martin", "McLaren", "Bugatti", "Koenigsegg", "Pagani",
            "Maybach", "Lotus",
        }
        luks_uyari = marka in LUKS_MARKALAR

        with st.spinner("Hesaplanıyor..."):
            tahmin = tahmin_yap(form)
        alt, ust = tahmin * .90, tahmin * 1.10

        if luks_uyari:
            st.warning(
                f"⚠️ **{marka}** için tahmin güvenilirliği düşük olabilir. "
                "Eğitim verisinde bu marka için çok az ilan bulunmaktadır. "
                "Sonucu referans değil, yaklaşık bir alt/üst sınır olarak değerlendirin."
            )

        # Piyasa karşılaştırması
        df_ham = yukle_ham()
        ana = piyasa_analiz(df_ham, marka, None, yil-2, yil+2) if df_ham is not None else {}
        medyan = ana.get("medyan", tahmin)
        vrd, vrd_txt, vrd_cls, badge_cls = verdict(tahmin, medyan)

        st.markdown(f"""
        <div class="result-hero">
            <div class="result-label">TAHMİNİ PAZAR DEĞERİ</div>
            <div class="result-price">{tl(tahmin)}</div>
            <div class="result-range">Beklenen Aralık: {tl(alt)} — {tl(ust)}</div>
            <br>
            <span class="{vrd_cls}">{vrd_txt}</span>
        </div>
        <div class="mkart-row">
            <div class="mkart"><div class="mkart-val">{marka} {seri}</div><div class="mkart-lbl">Araç</div></div>
            <div class="mkart"><div class="mkart-val">{yil}</div><div class="mkart-lbl">Yıl</div></div>
            <div class="mkart"><div class="mkart-val">{km:,} km</div><div class="mkart-lbl">Kilometre</div></div>
            <div class="mkart"><div class="mkart-val">{motor_hacmi_son} cc / {motor_gucu_son} HP</div><div class="mkart-lbl">Motor</div></div>
            <div class="mkart"><div class="mkart-val">{2026-yil} yıl</div><div class="mkart-lbl">Araç Yaşı</div></div>
        </div>
        """, unsafe_allow_html=True)

        if ana:
            st.markdown(f"""
            <div class="gcard" style="margin-top:20px;">
                <div class="gcard-title">📊 Piyasa Özeti ({marka} · {yil-2}–{yil+2})</div>
                <div style="display:flex;gap:20px;flex-wrap:wrap;color:#9ca3af;font-size:.85rem;">
                    <span>Min: <b style="color:#e5e7eb">{tl(ana['min'])}</b></span>
                    <span>%25: <b style="color:#e5e7eb">{tl(ana['q25'])}</b></span>
                    <span>Medyan: <b style="color:#e5e7eb">{tl(ana['medyan'])}</b></span>
                    <span>%75: <b style="color:#e5e7eb">{tl(ana['q75'])}</b></span>
                    <span>Max: <b style="color:#e5e7eb">{tl(ana['max'])}</b></span>
                    <span>İlan: <b style="color:#e5e7eb">{ana['adet']:,}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # — Alternatif öneriler —
        if df_ham is not None:
            oneriler = oneri_bul(df_ham, kasa, tahmin * 1.15, tahmin * 0.75, marka_hariç=marka)
            if not oneriler.empty:
                st.markdown('<div class="gcard"><div class="gcard-title">💡 Benzer Araç Önerileri (Aynı Kasa, Farklı Marka)</div>', unsafe_allow_html=True)
                for _, r in oneriler.iterrows():
                    fiyat_o = r.get("fiyat", 0)
                    fark_o  = ((fiyat_o - tahmin) / tahmin * 100) if tahmin > 0 else 0
                    fark_renk = "#34d399" if fark_o < 0 else "#f87171"
                    st.markdown(f"""
                    <div class="oneri-card">
                        <b style="color:#e5e7eb">{r.get('marka','')} {r.get('seri','')}</b>
                        <span style="color:#6b7280;font-size:.82rem;margin-left:10px">{r.get('yil','')} · {int(r.get('km',0)):,} km</span>
                        <span style="float:right;color:{fark_renk};font-weight:600">{tl(fiyat_o)}</span>
                        <div style="color:#6b7280;font-size:.8rem;margin-top:4px;">
                            {r.get('yakit_tipi','')} · {r.get('vites_tipi','')} · {r.get('kasa_tipi','')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TAB 2 — İLAN ARAMA
# ══════════════════════════════════════════════════════════════
with tab2:
    df_h2 = yukle_ham()
    if df_h2 is None:
        st.error("Veri seti bulunamadı.")
    else:
        st.markdown('<div class="gcard"><div class="gcard-title">🔎 Filtreler</div>', unsafe_allow_html=True)
        markalar2 = sorted(df_h2["marka"].dropna().unique())
        cm1, cm2, cm3 = st.columns([2,2,1])
        with cm1:
            s_marka = st.selectbox("Marka", markalar2,
                                   index=list(markalar2).index("Toyota") if "Toyota" in markalar2 else 0,
                                   key="s_marka")
        with cm2:
            seriler2 = ["Tümü"] + sorted(df_h2[df_h2["marka"]==s_marka]["seri"].dropna().unique())
            s_seri = st.selectbox("Model", seriler2, key="s_seri")
            s_seri_val = None if s_seri == "Tümü" else s_seri
        with cm3:
            s_limit = st.selectbox("Göster", [25, 50, 100, 250, "Tümü"], index=1)

        cy1, cy2, ck2, cs2 = st.columns([1,1,2,2])
        with cy1: s_ymin = st.number_input("Yıl min", 1985, 2026, 2015, key="symin")
        with cy2: s_ymax = st.number_input("Yıl max", 1985, 2026, 2026, key="symax")
        with ck2: s_km   = st.slider("Max KM", 0, 500_000, 200_000, step=10_000)
        with cs2: s_sira = st.selectbox("Sırala", ["En Düşük Fiyat","En Yüksek Fiyat","En Az KM","En Yeni"])
        s_fmax = st.number_input("Max Fiyat (TL, 0 = sınırsız)", 0, 100_000_000, 0, step=100_000)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🔍  Listele", use_container_width=True, type="primary"):
            mask = df_h2["marka"].str.lower() == s_marka.lower()
            if s_seri_val: mask &= df_h2["seri"].str.lower() == s_seri_val.lower()
            mask &= df_h2["yil"].between(int(s_ymin), int(s_ymax))
            if s_km < 500_000: mask &= df_h2["km"] <= s_km
            if s_fmax > 0:     mask &= df_h2["fiyat"] <= s_fmax
            sonuc = df_h2[mask].copy()
            sira_map = {"En Düşük Fiyat":("fiyat",True),"En Yüksek Fiyat":("fiyat",False),
                        "En Az KM":("km",True),"En Yeni":("yil",False)}
            col_s, asc_s = sira_map[s_sira]
            if s_limit == "Tümü":
                sonuc = sonuc.sort_values(col_s, ascending=asc_s)
            else:
                sonuc = sonuc.sort_values(col_s, ascending=asc_s).head(int(s_limit))

            if sonuc.empty:
                st.warning("Eşleşen ilan bulunamadı.")
            else:
                ana2 = piyasa_analiz(df_h2, s_marka, s_seri_val, int(s_ymin), int(s_ymax))
                medyan2 = ana2.get("medyan", sonuc["fiyat"].median())

                if ana2:
                    st.markdown(f"""
                    <div class="gcard">
                        <div style="display:flex;gap:12px;flex-wrap:wrap;justify-content:space-around;">
                            <div style="text-align:center"><div style="color:#e5e7eb;font-size:1.2rem;font-weight:700">{ana2['adet']:,}</div><div style="color:#6b7280;font-size:.75rem">Toplam İlan</div></div>
                            <div style="text-align:center"><div style="color:#e5e7eb;font-size:1.2rem;font-weight:700">{tl(ana2['min'])}</div><div style="color:#6b7280;font-size:.75rem">En Düşük</div></div>
                            <div style="text-align:center"><div style="color:#e5e7eb;font-size:1.2rem;font-weight:700">{tl(ana2['medyan'])}</div><div style="color:#6b7280;font-size:.75rem">Medyan</div></div>
                            <div style="text-align:center"><div style="color:#e5e7eb;font-size:1.2rem;font-weight:700">{tl(ana2['ort'])}</div><div style="color:#6b7280;font-size:.75rem">Ortalama</div></div>
                            <div style="text-align:center"><div style="color:#e5e7eb;font-size:1.2rem;font-weight:700">{tl(ana2['max'])}</div><div style="color:#6b7280;font-size:.75rem">En Yüksek</div></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.caption(f"**{len(sonuc)}** sonuç gösteriliyor (toplam eşleşen: **{int(mask.sum()):,}**) · 🟢 Uygun  🟡 Ortalama  🔴 Pahalı")

                for _, row in sonuc.iterrows():
                    f_r = row.get("fiyat",0)
                    pct = ((f_r - medyan2) / medyan2 * 100) if medyan2 > 0 else 0
                    if pct <= -10:   cls, fark_html = "ilan-uygun",  f'<span style="color:#34d399;font-size:.8rem;font-weight:600">▼ %{abs(pct):.1f} ucuz</span>'
                    elif pct >= 10:  cls, fark_html = "ilan-pahali", f'<span style="color:#f87171;font-size:.8rem;font-weight:600">▲ %{abs(pct):.1f} pahalı</span>'
                    else:            cls, fark_html = "ilan-normal", f'<span style="color:#fbbf24;font-size:.8rem;font-weight:600">≈ Ortalama</span>'

                    kimden_badge = '<span class="badge b-green">Sahibinden</span>' if "Sahibinden" in str(row.get("kimden","")) else '<span class="badge b-gray">Galeriden</span>'
                    km_d = f"{int(row.get('km',0)):,}" if pd.notna(row.get("km")) else "?"

                    st.markdown(f"""
                    <div class="ilan {cls}">
                        <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                            <div>
                                <span style="color:#e5e7eb;font-weight:600">{row.get('marka','')} {row.get('seri','')}</span>
                                <span style="color:#6b7280;font-size:.85rem;margin-left:8px">{row.get('yil','')}</span>
                            </div>
                            <div style="text-align:right">
                                <div class="ilan-fiyat">{tl(f_r)}</div>
                                {fark_html}
                            </div>
                        </div>
                        <div class="ilan-meta">{kimden_badge} 🛣️ {km_d} km · ⛽ {row.get('yakit_tipi','-')} · 🔧 {row.get('vites_tipi','-')} · 🚘 {row.get('kasa_tipi','-')} · 📍 {row.get('sehir','-')}</div>
                    </div>
                    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TAB 3 — PİYASA ANALİZİ
# ══════════════════════════════════════════════════════════════
with tab3:
    df_h3 = yukle_ham()
    if df_h3 is None:
        st.error("Veri seti bulunamadı.")
    else:
        st.markdown('<div class="gcard"><div class="gcard-title">📊 Filtreler</div>', unsafe_allow_html=True)
        markalar3 = sorted(df_h3["marka"].dropna().unique())
        pa1, pa2 = st.columns(2)
        with pa1:
            marka3 = st.selectbox("Marka", markalar3,
                                   index=list(markalar3).index("Toyota") if "Toyota" in markalar3 else 0,
                                   key="a_marka")
        with pa2:
            seriler3 = ["Tümü"] + sorted(df_h3[df_h3["marka"]==marka3]["seri"].dropna().unique())
            seri3    = st.selectbox("Seri", seriler3, key="a_seri")
            seri3v   = None if seri3=="Tümü" else seri3
        ya1, ya2 = st.columns(2)
        with ya1: ymin3 = st.number_input("Yıl min", 1990, 2026, 2015, key="a_ymin")
        with ya2: ymax3 = st.number_input("Yıl max", 1990, 2026, 2026, key="a_ymax")
        st.markdown('</div>', unsafe_allow_html=True)

        ana3 = piyasa_analiz(df_h3, marka3, seri3v, int(ymin3), int(ymax3))

        if not ana3:
            st.warning("Yeterli veri yok.")
        else:
            # Özet
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin-bottom:20px;">
                <div class="mkart"><div class="mkart-val">{ana3['adet']:,}</div><div class="mkart-lbl">Toplam İlan</div></div>
                <div class="mkart"><div class="mkart-val">{tl(ana3['min'])}</div><div class="mkart-lbl">Min</div></div>
                <div class="mkart"><div class="mkart-val">{tl(ana3['q25'])}</div><div class="mkart-lbl">%25 Çeyrek</div></div>
                <div class="mkart"><div class="mkart-val">{tl(ana3['medyan'])}</div><div class="mkart-lbl">Medyan</div></div>
                <div class="mkart"><div class="mkart-val">{tl(ana3['q75'])}</div><div class="mkart-lbl">%75 Çeyrek</div></div>
                <div class="mkart"><div class="mkart-val">{tl(ana3['max'])}</div><div class="mkart-lbl">Max</div></div>
            </div>
            """, unsafe_allow_html=True)

            # Plotly: Yıl bazlı fiyat kutusu
            mask3 = df_h3["marka"].str.lower() == marka3.lower()
            if seri3v: mask3 &= df_h3["seri"].str.lower() == seri3v.lower()
            mask3 &= df_h3["yil"].between(int(ymin3), int(ymax3))
            df_plot = df_h3[mask3].copy()

            if len(df_plot) > 0:
                c_g1, c_g2 = st.columns(2)

                with c_g1:
                    # Yıl bazlı medyan bar chart
                    yil_g = df_plot.groupby("yil")["fiyat"].median().reset_index()
                    yil_g.columns = ["Yıl","Medyan Fiyat"]
                    fig1 = px.bar(
                        yil_g.sort_values("Yıl"), x="Yıl", y="Medyan Fiyat",
                        title=f"{marka3} — Yıl Bazlı Medyan Fiyat",
                        color="Medyan Fiyat",
                        color_continuous_scale=["#312e81","#6366f1","#34d399"],
                        template="plotly_dark",
                    )
                    fig1.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#9ca3af",
                        coloraxis_showscale=False,
                        margin=dict(t=40,b=20,l=10,r=10),
                    )
                    st.plotly_chart(fig1, use_container_width=True)

                with c_g2:
                    # Yakıt dağılımı pasta
                    if ana3["yakit"]:
                        yakit_df = pd.DataFrame(list(ana3["yakit"].items()), columns=["Yakıt","Adet"])
                        fig2 = px.pie(
                            yakit_df, names="Yakıt", values="Adet",
                            title="Yakıt Tipi Dağılımı",
                            color_discrete_sequence=["#6366f1","#34d399","#f59e0b","#f87171","#818cf8"],
                            template="plotly_dark",
                            hole=0.45,
                        )
                        fig2.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font_color="#9ca3af",
                            margin=dict(t=40,b=20,l=10,r=10),
                        )
                        st.plotly_chart(fig2, use_container_width=True)

                # Fiyat dağılımı histogramı
                fig3 = px.histogram(
                    df_plot, x="fiyat", nbins=50,
                    title=f"{marka3} — Fiyat Dağılımı",
                    template="plotly_dark",
                    color_discrete_sequence=["#6366f1"],
                )
                fig3.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#9ca3af",
                    margin=dict(t=40,b=20,l=10,r=10),
                )
                fig3.add_vline(x=ana3["medyan"], line_dash="dash", line_color="#34d399",
                               annotation_text="Medyan", annotation_font_color="#34d399")
                st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB 4 — MODEL BİLGİSİ
# ══════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="gcard"><div class="gcard-title">🤖 Model Performansı</div>', unsafe_allow_html=True)

    if meta.get("test_metrikleri"):
        m = meta["test_metrikleri"]
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:20px;">
            <div class="mkart"><div class="mkart-val">{m.get('mae',0):,.0f} TL</div><div class="mkart-lbl">MAE (Test)</div></div>
            <div class="mkart"><div class="mkart-val">{m.get('rmse',0):,.0f} TL</div><div class="mkart-lbl">RMSE (Test)</div></div>
            <div class="mkart"><div class="mkart-val">%{m.get('mape',0):.1f}</div><div class="mkart-lbl">MAPE (Test)</div></div>
            <div class="mkart"><div class="mkart-val">{m.get('r2',0):.4f}</div><div class="mkart-lbl">R² (Test)</div></div>
        </div>
        """, unsafe_allow_html=True)

    if meta.get("feature_imp"):
        imp = pd.Series(meta["feature_imp"]).sort_values(ascending=False).head(15)
        fig_imp = px.bar(
            imp.reset_index(), x=0, y="index",
            orientation="h",
            title="En Önemli 15 Özellik",
            template="plotly_dark",
            color=0,
            color_continuous_scale=["#312e81","#6366f1","#34d399"],
        )
        fig_imp.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#9ca3af",
            coloraxis_showscale=False,
            yaxis_title="", xaxis_title="Önem Skoru",
            margin=dict(t=40,b=20,l=10,r=10),
        )
        st.plotly_chart(fig_imp, use_container_width=True)

    if meta.get("best_params"):
        st.markdown('<div class="gcard-title" style="margin-top:16px">⚙️ Hiperparametreler</div>', unsafe_allow_html=True)
        st.json(meta["best_params"])

    st.markdown('</div>', unsafe_allow_html=True)