"""
Aplikacja urodzinowa w Streamlit.

Uruchomienie:
    streamlit run app.py
"""

import base64
import json
import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# Folder z gifami BTS – wrzuć tam pliki .gif
PICTURES_DIR = Path(__file__).parent / "pictures"


def losowy_gif() -> str | None:
    """Zwraca ścieżkę do losowego gifa z folderu pictures/ lub None."""
    if not PICTURES_DIR.exists():
        return None
    gify = list(PICTURES_DIR.glob("*.gif")) + list(PICTURES_DIR.glob("*.GIF"))
    if not gify:
        return None
    return str(random.choice(gify))


def pokaz_gif_w_rogu(sciezka: str, nonce: int = 0):
    """Wyświetla gif w prawym górnym rogu jako overlay.

    `nonce` sprawia, że DOM jest unikalny przy każdym wywołaniu,
    więc animacja zawsze się odpala od nowa (nawet dla tego samego gifa).
    """
    try:
        with open(sciezka, "rb") as f:
            data = base64.b64encode(f.read()).decode()
    except OSError:
        return
    st.markdown(
        f"""
        <div id="gif-overlay-{nonce}" data-nonce="{nonce}" style="
            position: fixed;
            top: 70px;
            right: 20px;
            z-index: 9999;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
            border: 4px solid #d6336c;
            animation: gifShow-{nonce} 3.5s ease-out forwards;
        ">
            <img src="data:image/gif;base64,{data}" style="display:block; width: 220px; height: auto;">
        </div>
        <style>
        @keyframes gifShow-{nonce} {{
            0%   {{ transform: scale(0.3) rotate(-15deg); opacity: 0; }}
            10%  {{ transform: scale(1.1) rotate(5deg);  opacity: 1; }}
            20%  {{ transform: scale(1)   rotate(0deg);  opacity: 1; }}
            85%  {{ transform: scale(1)   rotate(0deg);  opacity: 1; }}
            100% {{ transform: scale(0.8) rotate(0deg);  opacity: 0; visibility: hidden; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Konfiguracja
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Wszystkiego najlepszego!", page_icon="🎂", layout="wide")

# Globalny CSS – stylizuje przyciski-karty (kontenery z kluczem zaczynającym się od "karta_")
st.markdown(
    """
    <style>
    /* Wszystkie karty */
    div[class*="st-key-karta_"] .stButton > button {
        min-height: 200px;
        border-radius: 16px;
        font-size: 18px;
        font-weight: 600;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        white-space: pre-wrap;
        line-height: 1.4;
    }
    div[class*="st-key-karta_"] .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.25);
    }

    /* Karta zakryta */
    div[class*="st-key-karta_zakryta"] .stButton > button {
        background: linear-gradient(135deg, #845ef7, #5f3dc4);
        color: white;
        border: none;
    }

    /* Karta odkryta (przycisk wyłączony, ale stylizowany na złoto) */
    div[class*="st-key-karta_odkryta"] .stButton > button:disabled {
        background: linear-gradient(135deg, #fff3bf, #ffd43b);
        color: #333;
        border: none;
        opacity: 1;
        cursor: default;
    }

    /* === Karty memory === */
    div[class*="st-key-pamkarta_"] .stButton > button {
        min-height: 110px;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        box-shadow: 0 3px 6px rgba(0,0,0,0.15);
        transition: transform 0.1s ease;
        white-space: pre-wrap;
        line-height: 1.2;
    }
    div[class*="st-key-pamkarta_"] .stButton > button:hover {
        transform: scale(1.03);
    }
    div[class*="st-key-pamkarta_zakryta"] .stButton > button {
        background: linear-gradient(135deg, #4dabf7, #1971c2);
        color: white;
        border: none;
    }
    div[class*="st-key-pamkarta_odkryta"] .stButton > button:disabled {
        background: linear-gradient(135deg, #b2f2bb, #51cf66);
        color: #1b4d22;
        border: none;
        opacity: 1;
        cursor: default;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Pula prezentów: (nazwa, emoji, wartość w diamentach)
PREZENTY = [
    ("Czekoladka", "🍫", 1),
    ("Kwiatek", "🌷", 2),
    ("Balonik", "🎈", 2),
    ("Tort", "🎂", 3),
    ("Miś", "🧸", 3),
    ("Książka", "📚", 4),
    ("Perfumy", "💐", 5),
    ("Naszyjnik", "📿", 6),
    ("Pierścionek", "💍", 8),
    ("Korona", "👑", 10),
]

ROZMIAR_TALI = 12          # używane tylko jako fallback – faktyczna talia ma tyle kart, ile prezentów
MAX_ODKRYC = 6             # ile kart można maksymalnie odkryć
BUDZET_DIAMENTOW = 5       # budżet do wyboru prezentów na końcu (w diamentach)

PREZENTY_DIR = PICTURES_DIR / "prezenty"


def _format_cena(cena: float) -> str:
    """Formatuje cenę jako liczbę bez zbędnych zer (4 -> '4', 0.5 -> '0.5')."""
    if float(cena).is_integer():
        return str(int(cena))
    return str(cena).rstrip("0").rstrip(".")


def wczytaj_prawdziwe_prezenty():
    """Czyta pliki z pictures/prezenty/ i zwraca listę (nazwa, data_url, cena_float).

    Format nazwy pliku: `slowa_oddzielone_podkresleniami_<cena>.png`,
    gdzie ostatni segment to cena w diamentach (np. `2`, `0.5`).
    """
    if not PREZENTY_DIR.exists():
        return []
    wynik = []
    pliki = sorted(
        list(PREZENTY_DIR.glob("*.png"))
        + list(PREZENTY_DIR.glob("*.jpg"))
        + list(PREZENTY_DIR.glob("*.jpeg"))
    )
    for sciezka in pliki:
        stem = sciezka.stem
        czesci = stem.split("_")
        if len(czesci) < 2:
            continue
        try:
            cena = float(czesci[-1])
        except ValueError:
            continue
        nazwa = " ".join(czesci[:-1]).strip()
        nazwa = nazwa[:1].upper() + nazwa[1:] if nazwa else stem
        try:
            with open(sciezka, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
        except OSError:
            continue
        ext = sciezka.suffix.lower().lstrip(".")
        if ext == "jpg":
            ext = "jpeg"
        data_url = f"data:image/{ext};base64,{b64}"
        wynik.append((nazwa, data_url, cena))
    return wynik


# ---------------------------------------------------------------------------
# Inicjalizacja stanu
# ---------------------------------------------------------------------------

def nowa_talia():
    """Zwraca talię zawierającą wszystkie dostępne prezenty (po jednym), w losowej kolejności."""
    pula = wczytaj_prawdziwe_prezenty()
    talia = list(pula)
    random.shuffle(talia)
    return talia


def reset_gry():
    st.session_state.ekran = "start"
    st.session_state.talia = nowa_talia()
    st.session_state.odkryte = [False] * len(st.session_state.talia)
    st.session_state.biblioteka = []           # lista odkrytych prezentów
    st.session_state.wybrane = set()           # indeksy w bibliotece wybrane na końcu
    st.session_state.ostatni_gif = None        # ścieżka do gifa pokazywanego po ostatnim odkryciu
    st.session_state.gif_nonce = 0             # licznik wymuszający świeże renderowanie gifa
    st.session_state.snake_ukonczony = False   # czy gracz wygrał wszystkie poziomy snake'a
    st.session_state.runner_ukonczony = False  # czy gracz wygrał grę biegową
    _reset_pamiec()


# ---- Stan gry pamięciowej -----------------------------------------------

PAMIEC_PARY = 8                # liczba par (czyli 16 kart, siatka 4x4)


def _reset_pamiec():
    """Resetuje stan gry pamięciowej (memory)."""
    emoji_pula = [p[1] for p in PREZENTY]
    wybor = random.sample(emoji_pula, k=min(PAMIEC_PARY, len(emoji_pula)))
    karty = wybor * 2
    random.shuffle(karty)
    st.session_state.pamiec_karty = karty
    st.session_state.pamiec_odkryte = [False] * len(karty)
    st.session_state.pamiec_wybrane = []       # bieżąco odkryte (max 2)
    st.session_state.pamiec_ruchy = 0
    st.session_state.pamiec_ukonczona = False


# Wykryj wygraną Snake'a sygnalizowaną przez JS przez query param
if st.query_params.get("snake_done") == "1":
    st.session_state.snake_ukonczony = True
    del st.query_params["snake_done"]
    st.session_state.ekran = "snake"

# Wykryj wygraną Runnera sygnalizowaną przez JS przez query param
if st.query_params.get("runner_done") == "1":
    st.session_state.runner_ukonczony = True
    del st.query_params["runner_done"]
    st.session_state.ekran = "runner"


if "ekran" not in st.session_state:
    reset_gry()


# ---------------------------------------------------------------------------
# Ekran startowy
# ---------------------------------------------------------------------------

def ekran_start():
    # Filmik tła – wstrzykiwany przez komponent JS do strony nadrzędnej
    # (st.markdown sanitizuje <video>, dlatego używamy components.html + JS).
    video_url = "./app/static/Clouds.mp4"
    components.html(
        f"""
        <script>
        (function() {{
            const doc = window.parent.document;
            // Usuń poprzednie wideo/overlay, jeśli były
            doc.querySelectorAll("#bg-video, #bg-overlay").forEach(el => el.remove());

            const v = doc.createElement("video");
            v.id = "bg-video";
            v.src = "{video_url}";
            v.autoplay = true;
            v.loop = true;
            v.muted = true;
            v.playsInline = true;
            v.setAttribute("playsinline", "");
            v.style.cssText = "position:fixed; top:0; left:0; width:100vw; height:100vh; "
                            + "object-fit:cover; z-index:-2; pointer-events:none;";
            doc.body.appendChild(v);
            // Auto-play zwykle wymaga muted – upewniamy się
            v.play().catch(() => {{}});

            const overlay = doc.createElement("div");
            overlay.id = "bg-overlay";
            overlay.style.cssText = "position:fixed; top:0; left:0; width:100vw; height:100vh; "
                                  + "background: rgba(255,255,255,0.25); z-index:-1; pointer-events:none;";
            doc.body.appendChild(overlay);

            // Tło aplikacji musi być przezroczyste, żeby video było widoczne
            const style = doc.createElement("style");
            style.id = "bg-video-style";
            style.textContent = `
                [data-testid="stAppViewContainer"], [data-testid="stApp"], [data-testid="stMain"] {{
                    background: transparent !important;
                }}
                [data-testid="stHeader"] {{ background: transparent !important; }}
            `;
            doc.head.appendChild(style);
        }})();
        </script>
        """,
        height=0,
    )

    # Lecące balony – generujemy losowe parametry
    balony_emoji = ["🎈", "🎀", "🎉", "💖", "✨", "🌸"]
    balony_html = ""
    for i in range(18):
        left = random.randint(0, 95)
        delay = round(random.uniform(0, 12), 2)
        duration = round(random.uniform(7, 14), 2)
        size = random.randint(30, 60)
        emoji = random.choice(balony_emoji)
        balony_html += (
            f'<div class="balon" style="left:{left}vw; '
            f'animation-delay:{delay}s; animation-duration:{duration}s; '
            f'font-size:{size}px;">{emoji}</div>'
        )

    st.markdown(
        f"""
        <div class="balony-warstwa">
            {balony_html}
        </div>

        <style>
        .balony-warstwa {{
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            pointer-events: none;
            overflow: hidden;
            z-index: 0;
        }}
        .balon {{
            position: absolute;
            bottom: -80px;
            animation-name: leciBalon;
            animation-timing-function: linear;
            animation-iteration-count: infinite;
            filter: drop-shadow(0 4px 6px rgba(0,0,0,0.2));
        }}
        @keyframes leciBalon {{
            0%   {{ transform: translateY(0)       translateX(0)    rotate(-5deg); opacity: 0; }}
            10%  {{ opacity: 1; }}
            50%  {{ transform: translateY(-50vh)   translateX(30px) rotate(5deg);  }}
            90%  {{ opacity: 1; }}
            100% {{ transform: translateY(-110vh)  translateX(-20px) rotate(-5deg); opacity: 0; }}
        }}
        .start-content {{
            position: relative;
            z-index: 10;
        }}
        </style>

        <div class="start-content" style='text-align:center; padding: 40px;'>
            <h1 style='font-size: 64px; color: #d6336c; text-shadow: 2px 2px 8px rgba(255,255,255,0.8);'>
                🎂 Wszystkiego najlepszego! 🎉
            </h1>
            <p style='font-size: 24px; color: #333; text-shadow: 1px 1px 4px rgba(255,255,255,0.8);'>
                Spełnienia marzeń, Dominika :) ! Kliknij <b>Graj</b>, aby odkryć swoje prezenty.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🎮 Graj", use_container_width=True, type="primary"):
            reset_gry()
            st.session_state.ekran = "gra"
            st.rerun()


# ---------------------------------------------------------------------------
# Ekran gry – odkrywanie kart
# ---------------------------------------------------------------------------

def ekran_gra():
    st.markdown("<h1 style='text-align:center;'>🃏 Odkryj swoje karty 🃏</h1>", unsafe_allow_html=True)

    # Pokaż gifa BTS w prawym górnym rogu, jeśli właśnie odkryto kartę
    if st.session_state.get("ostatni_gif"):
        pokaz_gif_w_rogu(st.session_state.ostatni_gif, st.session_state.get("gif_nonce", 0))

    odkryte_ile = sum(st.session_state.odkryte)
    pozostalo = MAX_ODKRYC - odkryte_ile

    col_info1, col_info2 = st.columns(2)
    col_info1.metric("Odkryte karty", f"{odkryte_ile} / {MAX_ODKRYC}")
    col_info2.metric("Pozostałe odkrycia", pozostalo)

    st.progress(odkryte_ile / MAX_ODKRYC)

    st.markdown("---")

    # Siatka kart – 4 kolumny
    rozmiar_tali = len(st.session_state.talia)
    kolumny_na_rzad = 4
    for rzad_start in range(0, rozmiar_tali, kolumny_na_rzad):
        cols = st.columns(kolumny_na_rzad)
        for i in range(kolumny_na_rzad):
            idx = rzad_start + i
            if idx >= rozmiar_tali:
                break
            with cols[i]:
                karta_widget(idx, pozostalo)

    st.markdown("---")

    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        moga_isc_dalej = odkryte_ile > 0
        if st.button(
            "🎁 Przejdź do wyboru prezentów",
            use_container_width=True,
            type="primary",
            disabled=not moga_isc_dalej,
        ):
            st.session_state.ekran = "wybor"
            st.rerun()
        if not moga_isc_dalej:
            st.caption("Odkryj przynajmniej jedną kartę, aby przejść dalej.")


def karta_widget(idx: int, pozostalo: int):
    nazwa, data_url, wartosc = st.session_state.talia[idx]
    odkryta = st.session_state.odkryte[idx]

    if odkryta:
        # Karta odkryta – wyświetl zdjęcie prezentu w stylizowanym kafelku
        st.markdown(
            f"""
            <div style='
                background: linear-gradient(135deg, #fff3bf, #ffd43b);
                border-radius: 16px;
                padding: 12px;
                text-align: center;
                min-height: 240px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            '>
                <img src="{data_url}" style="
                    width: 100%; height: 150px; object-fit: contain;
                    border-radius: 8px; background: white;"/>
                <div style='font-weight: bold; margin-top: 8px;'>{nazwa}</div>
                <div style='color: #d6336c; font-weight:600;'>💎 {_format_cena(wartosc)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Cała karta jako klikalny przycisk
        label = f"# 🎴\n\n**Karta #{idx + 1}**\n\nKliknij, aby odkryć"
        with st.container(key=f"karta_zakryta_{idx}"):
            if st.button(
                label,
                key=f"btn_karta_{idx}",
                use_container_width=True,
                disabled=pozostalo <= 0,
            ):
                st.session_state.odkryte[idx] = True
                st.session_state.biblioteka.append((nazwa, data_url, wartosc))
                st.session_state.ostatni_gif = losowy_gif()
                st.session_state.gif_nonce = st.session_state.get("gif_nonce", 0) + 1
                st.rerun()


# ---------------------------------------------------------------------------
# Ekran wyboru prezentów z biblioteki
# ---------------------------------------------------------------------------

def ekran_wybor():
    st.markdown("<h1 style='text-align:center;'>🎁 Wybierz swoje prezenty 🎁</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center; font-size:18px;'>"
        f"Masz <b>{BUDZET_DIAMENTOW} 💎</b> do wydania. Wybieraj mądrze!</p>",
        unsafe_allow_html=True,
    )

    prezenty = st.session_state.biblioteka
    wybrane = st.session_state.wybrane

    if not prezenty:
        st.error("Najpierw odkryj kilka kart na poprzednim ekranie.")
        if st.button("← Wróć do kart", use_container_width=True):
            st.session_state.ekran = "gra"
            st.rerun()
        return

    # Wyczyść nieprawidłowe indeksy z poprzedniego stanu
    wybrane.intersection_update(range(len(prezenty)))

    suma = sum(prezenty[i][2] for i in wybrane)
    pozostalo = BUDZET_DIAMENTOW - suma

    col1, col2, col3 = st.columns(3)
    col1.metric("Wydane", f"{_format_cena(suma)} 💎")
    col2.metric("Pozostały budżet", f"{_format_cena(pozostalo)} 💎")
    col3.metric("Wybrane prezenty", len(wybrane))

    st.markdown("---")

    kolumny_na_rzad = 4
    for rzad_start in range(0, len(prezenty), kolumny_na_rzad):
        cols = st.columns(kolumny_na_rzad)
        for i in range(kolumny_na_rzad):
            idx = rzad_start + i
            if idx >= len(prezenty):
                break
            with cols[i]:
                nazwa, data_url, wartosc = prezenty[idx]
                jest_wybrany = idx in wybrane
                stac_mnie = jest_wybrany or wartosc <= pozostalo

                kolor = "#51cf66" if jest_wybrany else ("#fff3bf" if stac_mnie else "#ffe3e3")
                st.markdown(
                    f"""
                    <div style='
                        background: {kolor};
                        border-radius: 16px;
                        padding: 12px;
                        text-align: center;
                        min-height: 240px;
                        border: {"3px solid #2f9e44" if jest_wybrany else "1px solid #ddd"};
                    '>
                        <img src="{data_url}" style="
                            width: 100%; height: 150px; object-fit: contain;
                            border-radius: 8px; background: white;"/>
                        <div style='font-weight: bold; margin-top: 8px;'>{nazwa}</div>
                        <div style='color: #d6336c; font-weight: 600;'>💎 {_format_cena(wartosc)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                etykieta = "✖ Usuń" if jest_wybrany else "➕ Wybierz"
                if st.button(
                    etykieta,
                    key=f"wybor_{idx}",
                    use_container_width=True,
                    disabled=not stac_mnie,
                ):
                    if jest_wybrany:
                        wybrane.remove(idx)
                    else:
                        wybrane.add(idx)
                    st.rerun()

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📨 Wyślij odpowiedzi", use_container_width=True, type="primary", disabled=len(wybrane) == 0):
            st.session_state.ekran = "snake"
            st.rerun()
    with col_b:
        if st.button("🔄 Zagraj jeszcze raz", use_container_width=True):
            reset_gry()
            st.rerun()


# ---------------------------------------------------------------------------
# Ekran Snake – musisz zjeść wszystkie wybrane prezenty
# ---------------------------------------------------------------------------

def ekran_snake():
    st.markdown("<h1 style='text-align:center;'>🐍 Złap swoje prezenty! 🐍</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; font-size:18px;'>"
        "3 poziomy! Steruj wężem strzałkami (lub WASD), zjedz <b>wszystkie</b> prezenty "
        "i unikaj przeciwników (owca, robur).</p>",
        unsafe_allow_html=True,
    )

    # Wybrane prezenty użytkownika – ich zdjęcia będą żądanym “jedzeniem” węża
    biblioteka = st.session_state.get("biblioteka", [])
    wybrane_idx = sorted(st.session_state.get("wybrane", set()))
    wybrane_prezenty = [biblioteka[i] for i in wybrane_idx if i < len(biblioteka)]
    if not wybrane_prezenty:
        wybrane_prezenty = biblioteka or wczytaj_prawdziwe_prezenty()
    prezenty_urls = [p[1] for p in wybrane_prezenty]
    prezenty_json = json.dumps(prezenty_urls, ensure_ascii=False)

    # Wczytaj obrazki przeciwników jako data URL (jeśli istnieją)
    def img_data_url(nazwa: str) -> str:
        sciezka = PICTURES_DIR / nazwa
        if not sciezka.exists():
            return ""
        try:
            with open(sciezka, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"data:image/jpeg;base64,{b64}"
        except OSError:
            return ""

    owca_url = img_data_url("owca.jpg")
    robur_url = img_data_url("robur.jpg")

    html = f"""
    <div style="display:flex; flex-direction:column; align-items:center; font-family:sans-serif;">
        <div style="display:flex; gap:30px; margin-bottom:10px; font-size:18px; font-weight:bold;">
            <div style="color:#5f3dc4;">Poziom: <span id="level">1</span> / 3</div>
            <div style="color:#d6336c;">Pozostało: <span id="left">0</span></div>
        </div>
        <canvas id="game" width="500" height="500"
                style="background:#f8f9fa; border:4px solid #845ef7; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.2);">
        </canvas>
        <div id="status" style="margin-top:12px; font-size:20px; font-weight:bold; min-height:30px; text-align:center;"></div>
        <div style="margin-top:10px; display:flex; gap:10px;">
            <button id="restart" style="
                padding:10px 20px; font-size:16px; cursor:pointer;
                background:#845ef7; color:white; border:none; border-radius:8px;
            ">🔄 Zacznij poziom od nowa</button>
            <button id="next" style="
                padding:10px 20px; font-size:16px; cursor:pointer;
                background:#2f9e44; color:white; border:none; border-radius:8px;
                display:none;
            ">➡ Następny poziom</button>
        </div>
    </div>

    <script>
    (function() {{
        const PREZENTY_URLS = {prezenty_json};
        const OWCA_URL = {json.dumps(owca_url)};
        const ROBUR_URL = {json.dumps(robur_url)};
        const CELL = 25;
        const COLS = 20;
        const ROWS = 20;

        const canvas = document.getElementById("game");
        const ctx = canvas.getContext("2d");
        const levelEl = document.getElementById("level");
        const leftEl = document.getElementById("left");
        const statusEl = document.getElementById("status");
        const restartBtn = document.getElementById("restart");
        const nextBtn = document.getElementById("next");

        // Wczytaj obrazki przeciwników
        const owcaImg = new Image();
        if (OWCA_URL) owcaImg.src = OWCA_URL;
        const roburImg = new Image();
        if (ROBUR_URL) roburImg.src = ROBUR_URL;

        // Wczytaj obrazki prezentów (wybranych przez użytkownika)
        const prezentImgs = PREZENTY_URLS.map(url => {{
            const img = new Image();
            img.src = url;
            return img;
        }});

        // Konfiguracja poziomów
        const LEVELS = [
            // Poziom 1 – maks. 10 prezentów, bez przeciwników
            {{ presentCount: 10, enemies: [], speed: 130 }},
            // Poziom 2 – 5 prezentów, jeden przeciwnik (owca)
            {{ presentCount: 5, enemies: [{{type: "owca", count: 1}}], speed: 120 }},
            // Poziom 3 – 5 prezentów, owca + robur
            {{ presentCount: 5, enemies: [{{type: "owca", count: 1}}, {{type: "robur", count: 1}}], speed: 110 }},
        ];

        let level = 0;             // 0,1,2 → poziom 1,2,3
        let snake, dir, nextDir, foods, enemies, gameOver, won, tickHandle, enemyTickCounter;

        function randEmptyCell(occupied) {{
            const free = [];
            for (let x = 0; x < COLS; x++) {{
                for (let y = 0; y < ROWS; y++) {{
                    if (!occupied.some(c => c.x === x && c.y === y)) {{
                        free.push({{x, y}});
                    }}
                }}
            }}
            if (free.length === 0) return null;
            return free[Math.floor(Math.random() * free.length)];
        }}

        function randDir() {{
            const dirs = [{{x:1,y:0}}, {{x:-1,y:0}}, {{x:0,y:1}}, {{x:0,y:-1}}];
            return dirs[Math.floor(Math.random()*dirs.length)];
        }}

        function initLevel() {{
            const cfg = LEVELS[level];
            snake = [{{x: 10, y: 10}}, {{x: 9, y: 10}}, {{x: 8, y: 10}}];
            dir = {{x: 1, y: 0}};
            nextDir = dir;
            gameOver = false;
            won = false;
            statusEl.textContent = "";
            nextBtn.style.display = "none";
            levelEl.textContent = (level + 1);
            enemyTickCounter = 0;

            // Prezenty – losowy wybór ze zdjęć wybranych przez użytkownika (z powtórzeniami)
            foods = [];
            const occupied = [...snake];
            for (let i = 0; i < cfg.presentCount; i++) {{
                const cell = randEmptyCell(occupied);
                if (!cell) break;
                const imgIdx = prezentImgs.length
                    ? Math.floor(Math.random() * prezentImgs.length) : 0;
                foods.push({{x: cell.x, y: cell.y, imgIdx}});
                occupied.push(cell);
            }}

            // Przeciwnicy
            enemies = [];
            for (const e of cfg.enemies) {{
                for (let i = 0; i < e.count; i++) {{
                    const cell = randEmptyCell(occupied);
                    if (!cell) break;
                    enemies.push({{x: cell.x, y: cell.y, type: e.type, dir: randDir()}});
                    occupied.push(cell);
                }}
            }}

            leftEl.textContent = foods.length;
            if (tickHandle) clearInterval(tickHandle);
            tickHandle = setInterval(tick, cfg.speed);
            draw();
        }}

        function moveEnemies() {{
            for (const en of enemies) {{
                // Z 25% szansą zmień kierunek losowo (mniej przewidywalnie)
                if (Math.random() < 0.25) en.dir = randDir();
                let nx = en.x + en.dir.x;
                let ny = en.y + en.dir.y;
                // Odbij się od ściany
                if (nx < 0 || nx >= COLS || ny < 0 || ny >= ROWS) {{
                    en.dir = randDir();
                    nx = en.x + en.dir.x;
                    ny = en.y + en.dir.y;
                    if (nx < 0 || nx >= COLS || ny < 0 || ny >= ROWS) continue;
                }}
                en.x = nx;
                en.y = ny;
            }}
        }}

        function tick() {{
            if (gameOver || won) return;
            dir = nextDir;
            const head = {{x: snake[0].x + dir.x, y: snake[0].y + dir.y}};

            // Kolizja ze ścianą / sobą
            if (head.x < 0 || head.x >= COLS || head.y < 0 || head.y >= ROWS) return endGame(false);
            if (snake.some(c => c.x === head.x && c.y === head.y)) return endGame(false);

            snake.unshift(head);

            // Zjedzony prezent?
            const foodIdx = foods.findIndex(f => f.x === head.x && f.y === head.y);
            if (foodIdx >= 0) {{
                foods.splice(foodIdx, 1);
                leftEl.textContent = foods.length;
            }} else {{
                snake.pop();
            }}

            // Ruch przeciwników – co 2. tick (wolniej niż wąż)
            enemyTickCounter++;
            if (enemyTickCounter % 2 === 0) moveEnemies();

            // Kolizja głowy z przeciwnikiem
            for (const en of enemies) {{
                if (en.x === snake[0].x && en.y === snake[0].y) return endGame(false);
            }}

            // Wygrana poziomu
            if (foods.length === 0) return endGame(true);

            draw();
        }}

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = "#f8f9fa";
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Prezenty – jako zdjęcia
            const FOOD_SIZE = CELL + 6;
            for (const f of foods) {{
                const img = prezentImgs[f.imgIdx];
                const fx = f.x * CELL + CELL/2 - FOOD_SIZE/2;
                const fy = f.y * CELL + CELL/2 - FOOD_SIZE/2;
                if (img && img.complete && img.naturalWidth > 0) {{
                    ctx.drawImage(img, fx, fy, FOOD_SIZE, FOOD_SIZE);
                }} else {{
                    // Fallback – emoji prezentu
                    ctx.font = (CELL - 2) + "px serif";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText("🎁", f.x * CELL + CELL/2, f.y * CELL + CELL/2);
                }}
            }}
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            // Przeciwnicy – rysowani lekko większe niż komórka, wycentrowani
            const ENEMY_SIZE = CELL + 14;
            for (const en of enemies) {{
                const img = en.type === "owca" ? owcaImg : roburImg;
                const px = en.x * CELL + CELL/2 - ENEMY_SIZE/2;
                const py = en.y * CELL + CELL/2 - ENEMY_SIZE/2;
                if (img.complete && img.naturalWidth > 0) {{
                    ctx.drawImage(img, px, py, ENEMY_SIZE, ENEMY_SIZE);
                }} else {{
                    // Fallback emoji
                    ctx.font = ENEMY_SIZE + "px serif";
                    ctx.fillText(en.type === "owca" ? "🐑" : "🤖", en.x * CELL + CELL/2, en.y * CELL + CELL/2);
                    ctx.font = (CELL - 2) + "px serif";
                }}
            }}

            // Wąż
            for (let i = 0; i < snake.length; i++) {{
                const c = snake[i];
                ctx.fillStyle = i === 0 ? "#5f3dc4" : "#845ef7";
                ctx.fillRect(c.x * CELL + 1, c.y * CELL + 1, CELL - 2, CELL - 2);
            }}
            // Oczy głowy
            const head = snake[0];
            ctx.fillStyle = "white";
            ctx.beginPath();
            ctx.arc(head.x * CELL + CELL/2 - 5, head.y * CELL + CELL/2 - 3, 3, 0, Math.PI*2);
            ctx.arc(head.x * CELL + CELL/2 + 5, head.y * CELL + CELL/2 - 3, 3, 0, Math.PI*2);
            ctx.fill();
        }}

        function endGame(victory) {{
            won = victory;
            gameOver = !victory;
            clearInterval(tickHandle);
            if (victory) {{
                if (level < LEVELS.length - 1) {{
                    statusEl.textContent = "🎉 Poziom " + (level+1) + " ukończony! Kliknij \\"Następny poziom\\".";
                    statusEl.style.color = "#2f9e44";
                    nextBtn.style.display = "inline-block";
                }} else {{
                    statusEl.textContent = "🏆 Brawo! Ukończyłaś wszystkie 3 poziomy! Przejdź do gry pamięciowej.";
                    statusEl.style.color = "#2f9e44";
                    // Zasygnalizuj Streamlitowi wygraną przez query param
                    try {{
                        const url = new URL(window.parent.location.href);
                        url.searchParams.set("snake_done", "1");
                        window.parent.location.replace(url.toString());
                    }} catch (e) {{}}
                }}
            }} else {{
                statusEl.textContent = "💥 Ups! Spróbuj jeszcze raz ten sam poziom.";
                statusEl.style.color = "#e03131";
            }}
        }}

        document.addEventListener("keydown", (e) => {{
            const k = e.key.toLowerCase();
            if ((k === "arrowup"    || k === "w") && dir.y !== 1)  nextDir = {{x: 0, y: -1}};
            if ((k === "arrowdown"  || k === "s") && dir.y !== -1) nextDir = {{x: 0, y: 1}};
            if ((k === "arrowleft"  || k === "a") && dir.x !== 1)  nextDir = {{x: -1, y: 0}};
            if ((k === "arrowright" || k === "d") && dir.x !== -1) nextDir = {{x: 1, y: 0}};
            if (["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"," "].includes(e.key)) e.preventDefault();
        }});

        canvas.tabIndex = 0;
        canvas.addEventListener("click", () => canvas.focus());
        canvas.focus();

        restartBtn.addEventListener("click", () => initLevel());
        nextBtn.addEventListener("click", () => {{
            if (level < LEVELS.length - 1) {{
                level++;
                initLevel();
            }}
        }});

        initLevel();
    }})();
    </script>
    """

    components.html(html, height=720)

    st.markdown("---")
    snake_ok = st.session_state.get("snake_ukonczony", False)
    if snake_ok:
        st.success("🏆 Snake ukończony! Możesz przejść dalej.")
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        if st.button(
            "🧠 Przejdź do gry pamięciowej",
            use_container_width=True,
            type="primary",
            disabled=not snake_ok,
        ):
            _reset_pamiec()
            st.session_state.ekran = "pamiec"
            st.rerun()
        if not snake_ok:
            st.caption("Najpierw wygraj wszystkie 3 poziomy Snake'a.")
    with col_a:
        if st.button("← Wróć do wyboru", use_container_width=True):
            st.session_state.ekran = "wybor"
            st.rerun()


# ---------------------------------------------------------------------------
# Ekran gry pamięciowej (memory) – dopasuj pary
# ---------------------------------------------------------------------------

def ekran_pamiec():
    st.markdown("<h1 style='text-align:center;'>🧠 Dopasuj pary 🧠</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; font-size:18px;'>"
        "Klikaj karty, aby je odkrywać. Znajdź wszystkie pary identycznych prezentów, "
        "żeby odebrać nagrodę!</p>",
        unsafe_allow_html=True,
    )

    karty = st.session_state.pamiec_karty
    odkryte = st.session_state.pamiec_odkryte
    wybrane = st.session_state.pamiec_wybrane
    ruchy = st.session_state.pamiec_ruchy
    znalezione_pary = sum(odkryte) // 2
    wszystkie_pary = len(karty) // 2

    col1, col2, col3 = st.columns(3)
    col1.metric("Ruchy", ruchy)
    col2.metric("Znalezione pary", f"{znalezione_pary} / {wszystkie_pary}")
    col3.metric("Pozostało", wszystkie_pary - znalezione_pary)
    st.progress(znalezione_pary / wszystkie_pary if wszystkie_pary else 0)

    st.markdown("---")

    # Siatka 4 kolumn
    kolumny_na_rzad = 4
    for rzad_start in range(0, len(karty), kolumny_na_rzad):
        cols = st.columns(kolumny_na_rzad)
        for i in range(kolumny_na_rzad):
            idx = rzad_start + i
            if idx >= len(karty):
                break
            with cols[i]:
                pamiec_karta_widget(idx)

    st.markdown("---")

    if st.session_state.pamiec_ukonczona:
        st.balloons()
        st.success("🎉 Brawo! Znalazłaś wszystkie pary!")

    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        if st.button(
            "�‍♀️ Przejdź do gry biegowej",
            use_container_width=True,
            type="primary",
            disabled=not st.session_state.pamiec_ukonczona,
        ):
            st.session_state.runner_ukonczony = False
            st.session_state.ekran = "runner"
            st.rerun()
        if not st.session_state.pamiec_ukonczona:
            st.caption("Znajdź wszystkie pary, aby przejść dalej.")
    with col_a:
        if st.button("🔄 Zacznij memory od nowa", use_container_width=True):
            _reset_pamiec()
            st.rerun()


def pamiec_karta_widget(idx: int):
    karty = st.session_state.pamiec_karty
    odkryte = st.session_state.pamiec_odkryte
    wybrane = st.session_state.pamiec_wybrane

    pokazana = odkryte[idx] or idx in wybrane
    emoji = karty[idx]

    if pokazana:
        label = f"# {emoji}"
        klucz = f"pamkarta_odkryta_{idx}"
    else:
        label = "# 🎴"
        klucz = f"pamkarta_zakryta_{idx}"

    with st.container(key=klucz):
        klik = st.button(
            label,
            key=f"btn_pam_{idx}",
            use_container_width=True,
            disabled=pokazana or st.session_state.pamiec_ukonczona,
        )
    if klik:
        # Jeśli wcześniej były 2 niedopasowane karty – zamknij je
        if len(wybrane) >= 2:
            st.session_state.pamiec_wybrane = []
            wybrane = st.session_state.pamiec_wybrane
        wybrane.append(idx)
        if len(wybrane) == 2:
            st.session_state.pamiec_ruchy += 1
            a, b = wybrane
            if karty[a] == karty[b]:
                odkryte[a] = True
                odkryte[b] = True
                st.session_state.pamiec_wybrane = []
                if all(odkryte):
                    st.session_state.pamiec_ukonczona = True
        st.rerun()


# ---------------------------------------------------------------------------
# Ekran Runner – blondynka skacze przez przeszkody i zbiera prezenty
# ---------------------------------------------------------------------------

def ekran_runner():
    st.markdown("<h1 style='text-align:center;'>🏃‍♀️ Bieg po prezenty! 🎁</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; font-size:18px;'>"
        "Naciśnij <b>SPACJĘ</b> lub <b>↑</b> (albo dotknij ekranu), aby skoczyć. "
        "Omijaj przeszkody i zbierz <b>15 prezentów</b>, żeby wygrać!</p>",
        unsafe_allow_html=True,
    )

    # Cel – ile prezentów trzeba zebrać
    cel = 15

    # Wczytaj obrazki postaci i przeszkody jako data URL
    def img_data_url(nazwa: str) -> str:
        sciezka = PICTURES_DIR / nazwa
        if not sciezka.exists():
            return ""
        try:
            with open(sciezka, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"data:image/jpeg;base64,{b64}"
        except OSError:
            return ""

    dominika_url = img_data_url("dominika.jpg")
    pacholek_url = img_data_url("pacholek-drogowy.jpg")

    # Wybrane prezenty użytkownika – ich zdjęcia będą zbieraną nagrodą w runnerze
    biblioteka = st.session_state.get("biblioteka", [])
    wybrane_idx = sorted(st.session_state.get("wybrane", set()))
    wybrane_prezenty = [biblioteka[i] for i in wybrane_idx if i < len(biblioteka)]
    if not wybrane_prezenty:
        wybrane_prezenty = biblioteka or wczytaj_prawdziwe_prezenty()
    prezenty_urls = [p[1] for p in wybrane_prezenty]
    prezenty_urls_json = json.dumps(prezenty_urls, ensure_ascii=False)

    html = f"""
    <div style="display:flex; flex-direction:column; align-items:center; font-family:sans-serif;">
        <div style="display:flex; gap:30px; margin-bottom:10px; font-size:18px; font-weight:bold;">
            <div style="color:#d6336c;">🎁 Zebrane: <span id="score">0</span> / {cel}</div>
            <div style="color:#5f3dc4;">❤ Życia: <span id="lives">3</span></div>
        </div>
        <canvas id="runner" width="900" height="380"
                style="background:linear-gradient(180deg, #a5d8ff 0%, #d0ebff 70%, #ffd8a8 70%, #ffd8a8 100%);
                       border:4px solid #5f3dc4; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.2);
                       max-width:100%;">
        </canvas>
        <div id="status" style="margin-top:12px; font-size:20px; font-weight:bold; min-height:30px; text-align:center;"></div>
        <button id="restart" style="
            margin-top:10px; padding:10px 20px; font-size:16px; cursor:pointer;
            background:#845ef7; color:white; border:none; border-radius:8px;
        ">🔄 Zacznij od nowa</button>
    </div>

    <script>
    (function() {{
        const canvas = document.getElementById("runner");
        const ctx = canvas.getContext("2d");
        const scoreEl = document.getElementById("score");
        const livesEl = document.getElementById("lives");
        const statusEl = document.getElementById("status");
        const restartBtn = document.getElementById("restart");

        const W = canvas.width;
        const H = canvas.height;
        const GROUND_Y = H * 0.78;
        const GRAVITY = 0.55;
        const JUMP_V = -16;
        const TARGET = {cel};

        const PRESENT_EMOJIS = ["🎁", "🎀", "💎", "🌷", "🍫", "🧸", "💍", "👑"];
        const OBSTACLE_EMOJIS = ["🌵", "🪨", "🔥"];

        const PRESENT_URLS = {prezenty_urls_json};
        const presentImgs = PRESENT_URLS.map(url => {{
            const img = new Image();
            img.src = url;
            return img;
        }});

        const DOMINIKA_URL = {json.dumps(dominika_url)};
        const PACHOLEK_URL = {json.dumps(pacholek_url)};
        const dominikaImg = new Image();
        if (DOMINIKA_URL) dominikaImg.src = DOMINIKA_URL;
        const pacholekImg = new Image();
        if (PACHOLEK_URL) pacholekImg.src = PACHOLEK_URL;

        let player, obstacles, gifts, speed, score, lives, gameOver, won, lastSpawn, frame, raf;

        function initGame() {{
            player = {{
                x: 80,
                y: GROUND_Y - 90,
                w: 70,
                h: 90,
                vy: 0,
                onGround: true,
            }};
            obstacles = [];
            gifts = [];
            speed = 8;
            score = 0;
            lives = 3;
            gameOver = false;
            won = false;
            lastSpawn = 0;
            frame = 0;
            statusEl.textContent = "";
            scoreEl.textContent = "0";
            livesEl.textContent = "3";
            cancelAnimationFrame(raf);
            loop();
        }}

        function jump() {{
            if (gameOver || won) return;
            if (player.onGround) {{
                player.vy = JUMP_V;
                player.onGround = false;
            }}
        }}

        function spawn() {{
            // Co jakiś czas dodaj przeszkodę albo prezent
            if (Math.random() < 0.55) {{
                // Przeszkoda na ziemi – pachołek drogowy
                obstacles.push({{
                    x: W + 20,
                    y: GROUND_Y - 55,
                    w: 45, h: 55,
                    emoji: OBSTACLE_EMOJIS[Math.floor(Math.random()*OBSTACLE_EMOJIS.length)]
                }});
            }} else {{
                // Prezent – czasami w powietrzu (musi skoczyć)
                const inAir = Math.random() < 0.5;
                const imgIdx = presentImgs.length
                    ? Math.floor(Math.random() * presentImgs.length) : 0;
                gifts.push({{
                    x: W + 20,
                    y: inAir ? GROUND_Y - 130 : GROUND_Y - 50,
                    w: 48, h: 48,
                    imgIdx,
                    emoji: PRESENT_EMOJIS[Math.floor(Math.random()*PRESENT_EMOJIS.length)]
                }});
            }}
        }}

        function rectsOverlap(a, b) {{
            return a.x < b.x + b.w && a.x + a.w > b.x &&
                   a.y < b.y + b.h && a.y + a.h > b.y;
        }}

        function drawPlayer() {{
            const px = player.x, py = player.y;
            // Cień
            ctx.fillStyle = "rgba(0,0,0,0.2)";
            ctx.beginPath();
            ctx.ellipse(px + player.w/2, GROUND_Y + 5, 22, 5, 0, 0, Math.PI*2);
            ctx.fill();

            if (dominikaImg.complete && dominikaImg.naturalWidth > 0) {{
                // Lekkie podskakiwanie podczas biegu (gdy na ziemi)
                const bob = player.onGround ? Math.abs(Math.sin(frame * 0.25)) * 2 : 0;
                ctx.drawImage(dominikaImg, px, py - bob, player.w, player.h);
            }} else {{
                // Fallback – prosty rysunek postaci, gdy zdjęcie jeszcze się nie wczytało
                ctx.fillStyle = "#ffd8a8";
                ctx.fillRect(px, py, player.w, player.h);
                ctx.fillStyle = "#ffe066";
                ctx.fillRect(px + 5, py, player.w - 10, 18);
            }}
        }}

        function drawGround() {{
            // Kreski na piasku
            ctx.strokeStyle = "#e8a76b";
            ctx.lineWidth = 2;
            for (let i = 0; i < 10; i++) {{
                const gx = ((frame * speed * 0.5) % 80) - 80 + i * 80;
                ctx.beginPath();
                ctx.moveTo(gx, GROUND_Y + 15);
                ctx.lineTo(gx + 30, GROUND_Y + 15);
                ctx.stroke();
            }}
        }}

        function drawClouds() {{
            ctx.fillStyle = "rgba(255,255,255,0.85)";
            for (let i = 0; i < 4; i++) {{
                const cx = ((frame * 0.5) % (W + 100) + i * 220) % (W + 100) - 50;
                const cy = 30 + (i % 2) * 30;
                ctx.beginPath();
                ctx.arc(cx,      cy, 18, 0, Math.PI*2);
                ctx.arc(cx + 18, cy - 6, 22, 0, Math.PI*2);
                ctx.arc(cx + 38, cy, 18, 0, Math.PI*2);
                ctx.fill();
            }}
        }}

        function loop() {{
            frame++;
            ctx.clearRect(0, 0, W, H);
            drawClouds();
            drawGround();

            if (!gameOver && !won) {{
                // Fizyka gracza
                player.vy += GRAVITY;
                player.y += player.vy;
                if (player.y >= GROUND_Y - player.h) {{
                    player.y = GROUND_Y - player.h;
                    player.vy = 0;
                    player.onGround = true;
                }}

                // Spawn
                lastSpawn++;
                const spawnEvery = Math.max(50, 110 - Math.floor(score * 2));
                if (lastSpawn > spawnEvery) {{
                    spawn();
                    lastSpawn = 0;
                }}

                // Ruch przeszkód
                for (const o of obstacles) o.x -= speed;
                for (const g of gifts) g.x -= speed;
                obstacles = obstacles.filter(o => o.x + o.w > -20);
                gifts = gifts.filter(g => g.x + g.w > -20);

                // Kolizje z przeszkodami
                for (let i = obstacles.length - 1; i >= 0; i--) {{
                    if (rectsOverlap(player, obstacles[i])) {{
                        obstacles.splice(i, 1);
                        lives--;
                        livesEl.textContent = lives;
                        if (lives <= 0) {{
                            gameOver = true;
                            statusEl.textContent = "💥 Koniec gry! Spróbuj jeszcze raz.";
                            statusEl.style.color = "#e03131";
                        }}
                    }}
                }}
                // Kolizje z prezentami
                for (let i = gifts.length - 1; i >= 0; i--) {{
                    if (rectsOverlap(player, gifts[i])) {{
                        gifts.splice(i, 1);
                        score++;
                        scoreEl.textContent = score;
                        if (score >= TARGET) {{
                            won = true;
                            statusEl.textContent = "🏆 Brawo! Zebrałaś wszystkie prezenty!";
                            statusEl.style.color = "#2f9e44";
                            try {{
                                const url = new URL(window.parent.location.href);
                                url.searchParams.set("runner_done", "1");
                                window.parent.location.replace(url.toString());
                            }} catch (e) {{}}
                        }}
                    }}
                }}

                // Stopniowo przyspieszaj
                speed = 8 + Math.min(6, score * 0.3);
            }}

            // Rysuj prezenty (zdjęcia wybranych) i przeszkody
            ctx.font = "32px serif";
            ctx.textAlign = "left";
            ctx.textBaseline = "top";
            for (const g of gifts) {{
                const img = presentImgs[g.imgIdx];
                if (img && img.complete && img.naturalWidth > 0) {{
                    ctx.drawImage(img, g.x, g.y, g.w, g.h);
                }} else {{
                    ctx.fillText(g.emoji, g.x, g.y);
                }}
            }}
            for (const o of obstacles) {{
                if (pacholekImg.complete && pacholekImg.naturalWidth > 0) {{
                    // Pachołek drogowy ze zdjęcia – nieco wyższy niż hitbox
                    ctx.drawImage(pacholekImg, o.x - 5, o.y - 8, o.w + 10, o.h + 8);
                }} else {{
                    ctx.fillText(o.emoji, o.x, o.y);
                }}
            }}

            drawPlayer();

            raf = requestAnimationFrame(loop);
        }}

        // Sterowanie
        document.addEventListener("keydown", (e) => {{
            if (e.key === " " || e.key === "ArrowUp" || e.key === "w" || e.key === "W") {{
                e.preventDefault();
                jump();
            }}
        }});
        canvas.addEventListener("click", jump);
        canvas.addEventListener("touchstart", (e) => {{ e.preventDefault(); jump(); }});

        restartBtn.addEventListener("click", initGame);
        initGame();
    }})();
    </script>
    """

    components.html(html, height=520)

    st.markdown("---")
    runner_ok = st.session_state.get("runner_ukonczony", False)
    if runner_ok:
        st.success("🏆 Bieg ukończony! Możesz odebrać prezenty.")
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        if st.button(
            "🎁 Odbierz prezenty",
            use_container_width=True,
            type="primary",
            disabled=not runner_ok,
        ):
            st.session_state.ekran = "podsumowanie"
            st.rerun()
        if not runner_ok:
            st.caption("Najpierw zbierz wszystkie prezenty w grze biegowej.")
    with col_a:
        if st.button("← Wróć do memory", use_container_width=True):
            st.session_state.ekran = "pamiec"
            st.rerun()


# ---------------------------------------------------------------------------
# Ekran podsumowania
# ---------------------------------------------------------------------------

def ekran_podsumowanie():
    st.markdown("<h1 style='text-align:center;'>🎉 Twoje prezenty 🎉</h1>", unsafe_allow_html=True)
    st.balloons()

    prezenty = st.session_state.biblioteka
    wybrane_set = st.session_state.wybrane
    wybrane_set.intersection_update(range(len(prezenty)))
    wybrane = sorted(wybrane_set)
    suma = sum(prezenty[i][2] for i in wybrane)

    st.markdown(
        f"<p style='text-align:center; font-size:20px;'>"
        f"Wybrałaś <b>{len(wybrane)}</b> prezentów za łącznie <b>{_format_cena(suma)} 💎</b>:</p>",
        unsafe_allow_html=True,
    )

    cols = st.columns(min(4, max(1, len(wybrane) or 1)))
    for i, idx in enumerate(wybrane):
        nazwa, data_url, wartosc = prezenty[idx]
        with cols[i % len(cols)]:
            st.markdown(
                f"""
                <div style='
                    background: linear-gradient(135deg, #ffd43b, #fab005);
                    border-radius: 16px;
                    padding: 16px;
                    text-align: center;
                    margin-bottom: 10px;
                '>
                    <img src="{data_url}" style="
                        width: 100%; height: 160px; object-fit: contain;
                        border-radius: 8px; background: white;"/>
                    <div style='font-size: 18px; font-weight: bold; margin-top: 8px;'>{nazwa}</div>
                    <div style='color: #862e9c; font-weight:600;'>💎 {_format_cena(wartosc)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # === Wyślij listę prezentów ===
    if wybrane:
        st.markdown("<h3 style='text-align:center;'>📬 Wyślij swoją listę prezentów</h3>", unsafe_allow_html=True)

        # Tekst listy do wysłania / skopiowania / pobrania
        linie = [f"- {prezenty[i][0]} (💎 {_format_cena(prezenty[i][2])})" for i in wybrane]
        tresc = (
            "Cześć!\n\n"
            "Oto moja lista wybranych prezentów urodzinowych:\n\n"
            + "\n".join(linie)
            + f"\n\nŁącznie: {_format_cena(suma)} 💎\n\n"
            "Pozdrawiam,\nDominika 🎂"
        )
        temat = "🎁 Moja lista prezentów urodzinowych"

        # Domyślny adres mailowy – użytkownik może go zmienić
        adres = st.text_input(
            "📧 Adres e-mail odbiorcy:",
            value="aleksis550@wp.pl",
            placeholder="np. aleksis550@wp.pl",
        )

        from urllib.parse import quote
        mailto = f"mailto:{quote(adres)}?subject={quote(temat)}&body={quote(tresc)}"

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(
                f"""
                <a href="{mailto}" target="_blank" style="
                    display:block; text-align:center;
                    background: linear-gradient(135deg, #4dabf7, #1971c2);
                    color: white; text-decoration: none;
                    padding: 12px; border-radius: 10px; font-weight: 600;
                ">📨 Otwórz w programie pocztowym</a>
                """,
                unsafe_allow_html=True,
            )
        with col_m2:
            st.download_button(
                "💾 Pobierz listę (.txt)",
                data=tresc.encode("utf-8"),
                file_name="lista_prezentow.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with st.expander("📄 Pokaż treść listy (do skopiowania)"):
            st.code(tresc, language="text")

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Zagraj jeszcze raz", use_container_width=True, type="primary"):
            reset_gry()
            st.rerun()


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

ekran = st.session_state.get("ekran", "start")
if ekran == "start":
    ekran_start()
elif ekran == "gra":
    ekran_gra()
elif ekran == "wybor":
    ekran_wybor()
elif ekran == "snake":
    ekran_snake()
elif ekran == "pamiec":
    ekran_pamiec()
elif ekran == "runner":
    ekran_runner()
elif ekran == "podsumowanie":
    ekran_podsumowanie()
