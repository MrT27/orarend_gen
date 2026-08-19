import streamlit as st

# =========================================================
# ALAPADATOK
# =========================================================

NAPOK = [
    "Hétfő",
    "Kedd",
    "Szerda",
    "Csütörtök",
    "Péntek"
]

IDOSAVOK = [
    "14:30-16:00",
    "16:00-17:30",
    "17:30-19:00"
]


SPORTOK = {
    "úszás": {
        "hely": "Uszoda",
        "tanarok": {
            "UT": 1,
        }
    },

    "röplabda": {
        "hely": "Terem",
        "tanarok": {
            "SZS": 1,
            "SZZS": 2,
        }
    },

    "atlétika": {
        "hely": "Terem",
        "tanarok": {
            "SZZS": 1,
        }
    },

    "torna lány": {
        "hely": "Terem",
        "tanarok": {
            "RM": 1,
        }
    },

    "kosárlabda lány": {
        "hely": "Terem",
        "tanarok": {
            "RM": 1,
        }
    },

    "kondi": {
        "hely": "Kondi",
        "tanarok": {
            "SZS": 1,
            "KK": 2,
        }
    },

    "torna fiú": {
        "hely": "Terem",
        "tanarok": {
            "KSZJ": 1,
        }
    },

    "tollaslabda": {
        "hely": "Terem",
        "tanarok": {
            "SZS": 1,
        }
    },

    "labdarúgás": {
        "hely": "Terem",
        "tanarok": {
            "UT": 1,
        }
    },

    "kosárlabda fiú": {
        "hely": "Terem",
        "tanarok": {
            "KSZJ": 1,
        }
    },

    "kézilabda": {
        "hely": "Terem",
        "tanarok": {
            "SZS": 1,
        }
    },

    "aikido": {
        "hely": "Tatami",
        "tanarok": {}
    }
}


# =========================================================
# SESSION STATE
# =========================================================

if "beosztas" not in st.session_state:
    st.session_state.beosztas = []


# =========================================================
# SEGÉDFÜGGVÉNYEK
# =========================================================

def tanar_foglalt(nap, idosav, tanar):

    for ora in st.session_state.beosztas:

        if (
            ora["nap"] == nap
            and ora["idosav"] == idosav
            and ora["tanar"] == tanar
        ):
            return True

    return False


def hely_foglalt(nap, idosav, hely):

    for ora in st.session_state.beosztas:

        if (
            ora["nap"] == nap
            and ora["idosav"] == idosav
            and ora["hely"] == hely
        ):
            return True

    return False


def alkalmak_szama(sport, tanar):

    db = 0

    for ora in st.session_state.beosztas:

        if (
            ora["sport"] == sport
            and ora["tanar"] == tanar
        ):
            db += 1

    return db


def ellenorzes(nap, idosav, sport, tanar):

    hibak = []

    hely = SPORTOK[sport]["hely"]

    # Úszás szabály
    if sport == "úszás":

        if idosav != "14:30-16:00":
            hibak.append(
                "Az úszás csak 14:30-16:00 között lehet."
            )

        if nap in ["Szerda", "Péntek"]:
            hibak.append(
                "Szerdán és pénteken nincs úszás."
            )

    # Tanár foglaltság
    if tanar_foglalt(nap, idosav, tanar):

        hibak.append(
            f"{tanar} ebben az idősávban már foglalt."
        )

    # Hely foglaltság
    if hely_foglalt(nap, idosav, hely):

        hibak.append(
            f"A(z) {hely} ebben az idősávban már foglalt."
        )

    # Tanári alkalomszám
    max_alkalom = SPORTOK[sport]["tanarok"].get(tanar)

    if max_alkalom is not None:

        jelenlegi = alkalmak_szama(
            sport,
            tanar
        )

        if jelenlegi >= max_alkalom:

            hibak.append(
                f"{tanar} a(z) {sport} foglalkozásból "
                f"maximum {max_alkalom} alkalmat vihet."
            )

    return hibak


# =========================================================
# FELÜLET
# =========================================================

st.set_page_config(
    page_title="Délutáni testnevelés",
    layout="wide"
)

st.title("Délutáni testnevelés beosztó")

st.caption(
    "Félautomatikus beosztás tanár- és teremütközés ellenőrzéssel"
)


# =========================================================
# ÚJ FOGLALKOZÁS
# =========================================================

st.subheader("Új foglalkozás")

col1, col2, col3 = st.columns(3)

with col1:
    nap = st.selectbox(
        "Nap",
        NAPOK
    )

with col2:
    idosav = st.selectbox(
        "Idősáv",
        IDOSAVOK
    )

with col3:
    sport = st.selectbox(
        "Sport",
        list(SPORTOK.keys())
    )


hely = SPORTOK[sport]["hely"]

tanar_lista = list(
    SPORTOK[sport]["tanarok"].keys()
)

if not tanar_lista:
    tanar_lista = ["Nincs megadva"]

col4, col5 = st.columns(2)

with col4:

    tanar = st.selectbox(
        "Tanár",
        tanar_lista
    )

with col5:

    st.text_input(
        "Helyszín",
        value=hely,
        disabled=True
    )


# =========================================================
# ELLENŐRZÉS
# =========================================================

if tanar != "Nincs megadva":

    hibak = ellenorzes(
        nap,
        idosav,
        sport,
        tanar
    )

else:

    hibak = [
        "Ehhez a sporthoz még nincs tanár megadva."
    ]


if hibak:

    for hiba in hibak:
        st.warning(hiba)

else:

    st.success(
        "Ez a foglalkozás jelenleg beilleszthető."
    )


# =========================================================
# HOZZÁADÁS
# =========================================================

if st.button(
    "Foglalkozás hozzáadása",
    type="primary"
):

    if hibak:

        st.error(
            "A foglalkozás nem adható hozzá, "
            "mert valamelyik szabály sérül."
        )

    else:

        st.session_state.beosztas.append(
            {
                "nap": nap,
                "idosav": idosav,
                "sport": sport,
                "tanar": tanar,
                "hely": hely
            }
        )

        st.success(
            "Foglalkozás hozzáadva."
        )

        st.rerun()


# =========================================================
# BEOSZTÁS MEGJELENÍTÉSE
# =========================================================

st.divider()

st.subheader("Aktuális beosztás")


for nap_nev in NAPOK:

    st.markdown(
        f"### {nap_nev}"
    )

    cols = st.columns(3)

    for i, idosav_nev in enumerate(IDOSAVOK):

        with cols[i]:

            st.markdown(
                f"**{idosav_nev}**"
            )

            talalatok = [
                ora
                for ora in st.session_state.beosztas
                if (
                    ora["nap"] == nap_nev
                    and ora["idosav"] == idosav_nev
                )
            ]

            if not talalatok:

                st.caption(
                    "Szabad"
                )

            else:

                for ora in talalatok:

                    st.write(
                        f"{ora['sport']}"
                    )

                    st.caption(
                        f"{ora['tanar']} • {ora['hely']}"
                    )


# =========================================================
# TÖRLÉS
# =========================================================

st.divider()

st.subheader("Bejegyzések törlése")

for index, ora in enumerate(
    st.session_state.beosztas
):

    col_a, col_b = st.columns(
        [5, 1]
    )

    with col_a:

        st.write(
            f"{ora['nap']} | "
            f"{ora['idosav']} | "
            f"{ora['sport']} | "
            f"{ora['tanar']} | "
            f"{ora['hely']}"
        )

    with col_b:

        if st.button(
            "Törlés",
            key=f"torles_{index}"
        ):

            st.session_state.beosztas.pop(
                index
            )

            st.rerun()


# =========================================================
# TELJES TÖRLÉS
# =========================================================

if st.button(
    "Teljes beosztás törlése"
):

    st.session_state.beosztas = []

    st.rerun()
