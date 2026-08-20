import json
from pathlib import Path
import streamlit as st

# ============================================================
# FÁJLOK
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

FOGLALKOZASOK_FAJL = BASE_DIR / "foglalkozasok.json"
KORLATOZASOK_FAJL = BASE_DIR / "korlatozasok.json"
TEREM_SZABALYOK_FAJL = BASE_DIR / "terem_szabalyok.json"
BEOSZTAS_FAJL = BASE_DIR / "beosztas.json"


# ============================================================
# ALAPÉRTELMEZETT TEREMSZABÁLYOK
# Ha nincs terem_szabalyok.json, ezekkel is el tud indulni.
# ============================================================

ALAP_TEREM_SZABALYOK = {
    "Terem": {
        "max_parhuzamos": 2,
        "kizarolagos": [
            "kosárlabda lány",
            "kosárlabda fiú",
            "kézilabda"
        ],
        "egyutt_mehet": [
            ["torna lány", "röplabda fiú"],
            ["torna lány", "röplabda lány 1"],
            ["torna lány", "röplabda lány 2"],
            ["torna fiú", "röplabda fiú"],
            ["torna fiú", "röplabda lány 1"],
            ["torna fiú", "röplabda lány 2"]
        ]
    },
    "Kondi": {
        "max_parhuzamos": 1
    },
    "Uszoda": {
        "max_parhuzamos": 2
    },
    "Külső helyszín": {
        "max_parhuzamos": 99
    }
}


# ============================================================
# JSON SEGÉDFÜGGVÉNYEK
# ============================================================

def json_betolt(path, alap=None):
    if not path.exists():
        return alap

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def json_ment(path, adat):
    with path.open("w", encoding="utf-8") as f:
        json.dump(
            adat,
            f,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# ADATOK BETÖLTÉSE
# ============================================================

foglalkozas_adatok = json_betolt(
    FOGLALKOZASOK_FAJL,
    {"foglalkozasok": []}
)

korlat_adatok = json_betolt(
    KORLATOZASOK_FAJL,
    {
        "napok": [
            "Hétfő",
            "Kedd",
            "Szerda",
            "Csütörtök",
            "Péntek"
        ],
        "idosavok": [
            "14:30-16:00",
            "16:00-17:30",
            "17:30-19:00"
        ],
        "korlatozasok": [],
        "tanari_korlatozasok": []
    }
)

terem_adatok = json_betolt(
    TEREM_SZABALYOK_FAJL,
    ALAP_TEREM_SZABALYOK
)

FOGLALKOZASOK = foglalkozas_adatok.get(
    "foglalkozasok",
    []
)

NAPOK = korlat_adatok.get(
    "napok",
    ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek"]
)

IDOSAVOK = korlat_adatok.get(
    "idosavok",
    ["14:30-16:00", "16:00-17:30", "17:30-19:00"]
)

KORLATOZASOK = korlat_adatok.get(
    "korlatozasok",
    []
)

TANARI_KORLATOZASOK = korlat_adatok.get(
    "tanari_korlatozasok",
    []
)

TEREM_SZABALYOK = terem_adatok


# ============================================================
# SESSION STATE / BEOSZTÁS
# ============================================================

if "beosztas" not in st.session_state:
    st.session_state.beosztas = json_betolt(
        BEOSZTAS_FAJL,
        []
    )

if st.session_state.beosztas is None:
    st.session_state.beosztas = []


def beosztas_mentese():
    json_ment(
        BEOSZTAS_FAJL,
        st.session_state.beosztas
    )


# ============================================================
# ÁLTALÁNOS SEGÉDFÜGGVÉNYEK
# ============================================================

def mezo_egyezik(szabaly_ertek, aktualis_ertek):
    return (
        szabaly_ertek == "*"
        or szabaly_ertek == aktualis_ertek
    )


def mar_beosztott_idk():
    return {
        sor["id"]
        for sor in st.session_state.beosztas
        if "id" in sor
    }


def hatralevo_foglalkozasok():
    kesz = mar_beosztott_idk()

    return [
        foglalkozas
        for foglalkozas in FOGLALKOZASOK
        if foglalkozas["id"] not in kesz
    ]


def foglalkozas_cimke(foglalkozas):
    return (
        f"{foglalkozas['id']} | "
        f"{foglalkozas['tanar']} | "
        f"{foglalkozas['sport']} | "
        f"{foglalkozas['helyszin']}"
    )


def osszes_tanar():
    tanarok = {
        f["tanar"]
        for f in FOGLALKOZASOK
        if f.get("tanar") and f.get("tanar") != "Külsős"
    }

    return sorted(tanarok)


def osszes_helyszin():
    helyszinek = {
        f["helyszin"]
        for f in FOGLALKOZASOK
        if f.get("helyszin")
    }

    sorrend = [
        "Uszoda",
        "Terem",
        "Kondi",
        "Tatami",
        "Külső helyszín"
    ]

    eredmeny = [
        h
        for h in sorrend
        if h in helyszinek
    ]

    eredmeny.extend(
        sorted(
            helyszinek - set(eredmeny)
        )
    )

    return eredmeny


# ============================================================
# TANÁR ELLENŐRZÉSE
# ============================================================

def tanar_foglalt(tanar, nap, idosav):
    # A "Külsős" gyűjtőnév több külön külsős embert is jelenthet,
    # ezért ezt nem kezeljük egyetlen konkrét tanárként.
    if tanar == "Külsős":
        return False

    return any(
        sor.get("tanar") == tanar
        and sor.get("nap") == nap
        and sor.get("idosav") == idosav
        for sor in st.session_state.beosztas
    )


def tanar_korlatozva(tanar, nap, idosav):
    # Támogatjuk a külön tanari_korlatozasok listát...
    szabalyok = list(TANARI_KORLATOZASOK)

    # ...és azt is, ha valaki a közös korlátozások közé
    # "tipus": "tanar" formában írta be.
    szabalyok.extend(
        [
            k
            for k in KORLATOZASOK
            if k.get("tipus") == "tanar"
        ]
    )

    for korlat in szabalyok:
        if korlat.get("tanar") != tanar:
            continue

        if not mezo_egyezik(
            korlat.get("nap", "*"),
            nap
        ):
            continue

        if not mezo_egyezik(
            korlat.get("idosav", "*"),
            idosav
        ):
            continue

        return True, korlat.get(
            "ok",
            "Tanári korlátozás"
        )

    return False, ""


# ============================================================
# SPORTKORLÁTOZÁS
# ============================================================

def sport_korlatozva(sport, nap, idosav):
    for korlat in KORLATOZASOK:
        if korlat.get("tipus") != "sport":
            continue

        if korlat.get("sport") != sport:
            continue

        if not mezo_egyezik(
            korlat.get("nap", "*"),
            nap
        ):
            continue

        if not mezo_egyezik(
            korlat.get("idosav", "*"),
            idosav
        ):
            continue

        return True, korlat.get(
            "ok",
            "Sportkorlátozás"
        )

    return False, ""


# ============================================================
# HELYSZÍN / TEREM TERHELHETŐSÉG
# ============================================================

def helyszinen_beosztva(nap, idosav, helyszin):
    return [
        sor
        for sor in st.session_state.beosztas
        if sor.get("nap") == nap
        and sor.get("idosav") == idosav
        and sor.get("helyszin") == helyszin
    ]


def par_engedelyezett(sport1, sport2, egyutt_mehet):
    for par in egyutt_mehet:
        if len(par) != 2:
            continue

        if (
            (par[0] == sport1 and par[1] == sport2)
            or
            (par[0] == sport2 and par[1] == sport1)
        ):
            return True

    return False


def helyszin_engedelyezett(foglalkozas, nap, idosav):
    helyszin = foglalkozas["helyszin"]
    sport = foglalkozas["sport"]

    # Külsős edzések nem terhelik az iskola termeit.
    if foglalkozas.get("kulso", False):
        return True, ""

    bent = helyszinen_beosztva(
        nap,
        idosav,
        helyszin
    )

    szabaly = TEREM_SZABALYOK.get(
        helyszin,
        {"max_parhuzamos": 1}
    )

    max_parhuzamos = szabaly.get(
        "max_parhuzamos",
        1
    )

    # Kapacitás
    if len(bent) >= max_parhuzamos:
        return (
            False,
            f"A(z) {helyszin} elérte a "
            f"{max_parhuzamos} párhuzamos foglalkozásos kapacitását."
        )

    # Ha nincs még bent senki, mehet.
    if not bent:
        return True, ""

    # Kizárólagos sportok
    kizarolagos = szabaly.get(
        "kizarolagos",
        []
    )

    if sport in kizarolagos:
        return (
            False,
            f"A(z) {sport} egyedül használhatja a(z) {helyszin} helyszínt."
        )

    for bent_sor in bent:
        if bent_sor.get("sport") in kizarolagos:
            return (
                False,
                f"A(z) {helyszin} helyszínt már kizárólagosan használja: "
                f"{bent_sor.get('sport')}."
            )

    # Ha van megadva együtt-mehet lista, akkor a már bent lévő
    # minden foglalkozással kompatibilisnek kell lennie.
    egyutt_mehet = szabaly.get(
        "egyutt_mehet",
        []
    )

    if egyutt_mehet:
        for bent_sor in bent:
            bent_sport = bent_sor.get("sport")

            if not par_engedelyezett(
                sport,
                bent_sport,
                egyutt_mehet
            ):
                return (
                    False,
                    f"A(z) {sport} és {bent_sport} "
                    f"nem használhatja együtt a(z) {helyszin} helyszínt."
                )

    return True, ""


# ============================================================
# TELJES IDŐPONT-ELLENŐRZÉS
# ============================================================

def idopont_ervenyes(foglalkozas, nap, idosav):
    hibak = []

    sport = foglalkozas["sport"]
    tanar = foglalkozas["tanar"]

    tiltott, ok = sport_korlatozva(
        sport,
        nap,
        idosav
    )

    if tiltott:
        hibak.append(ok)

    tiltott, ok = tanar_korlatozva(
        tanar,
        nap,
        idosav
    )

    if tiltott:
        hibak.append(ok)

    if tanar_foglalt(
        tanar,
        nap,
        idosav
    ):
        hibak.append(
            f"{tanar} ebben az idősávban már foglalt."
        )

    hely_ok, hely_hiba = helyszin_engedelyezett(
        foglalkozas,
        nap,
        idosav
    )

    if not hely_ok:
        hibak.append(hely_hiba)

    return (
        len(hibak) == 0,
        hibak
    )


def ervenyes_idosavok(foglalkozas, nap):
    eredmeny = []

    for idosav in IDOSAVOK:
        jo, _ = idopont_ervenyes(
            foglalkozas,
            nap,
            idosav
        )

        if jo:
            eredmeny.append(idosav)

    return eredmeny


def ervenyes_napok(foglalkozas):
    eredmeny = []

    for nap in NAPOK:
        if ervenyes_idosavok(
            foglalkozas,
            nap
        ):
            eredmeny.append(nap)

    return eredmeny


# ============================================================
# TERHELTSÉGI TÁBLÁK
# ============================================================

def tanar_terheles_tabla(nap):
    tabla = []

    for tanar in osszes_tanar():
        sor = {
            "Tanár": tanar
        }

        for idosav in IDOSAVOK:
            talalatok = [
                b
                for b in st.session_state.beosztas
                if b.get("nap") == nap
                and b.get("idosav") == idosav
                and b.get("tanar") == tanar
            ]

            if not talalatok:
                korlatozott, _ = tanar_korlatozva(
                    tanar,
                    nap,
                    idosav
                )

                sor[idosav] = (
                    "TILTOTT"
                    if korlatozott
                    else "SZABAD"
                )
            else:
                sor[idosav] = " | ".join(
                    f"{b['sport']} / {b['helyszin']}"
                    for b in talalatok
                )

        tabla.append(sor)

    return tabla


def terem_terheles_tabla(nap):
    tabla = []

    for helyszin in osszes_helyszin():
        sor = {
            "Helyszín": helyszin
        }

        szabaly = TEREM_SZABALYOK.get(
            helyszin,
            {"max_parhuzamos": 1}
        )

        max_parhuzamos = szabaly.get(
            "max_parhuzamos",
            1
        )

        for idosav in IDOSAVOK:
            talalatok = helyszinen_beosztva(
                nap,
                idosav,
                helyszin
            )

            if not talalatok:
                sor[idosav] = (
                    f"SZABAD (0/{max_parhuzamos})"
                )
            else:
                tartalom = " | ".join(
                    f"{b['sport']} / {b['tanar']}"
                    for b in talalatok
                )

                sor[idosav] = (
                    f"{tartalom} "
                    f"({len(talalatok)}/{max_parhuzamos})"
                )

        tabla.append(sor)

    return tabla


# ============================================================
# STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Délutáni testnevelés",
    layout="wide"
)

st.title(
    "Délutáni testnevelés – félautomata beosztó"
)

if not TEREM_SZABALYOK_FAJL.exists():
    st.info(
        "Nincs terem_szabalyok.json fájl, ezért az app "
        "az alapértelmezett teremszabályokat használja."
    )


# ============================================================
# ÖSSZESÍTŐ
# ============================================================

hatralevo = hatralevo_foglalkozasok()

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "Összes foglalkozás",
        len(FOGLALKOZASOK)
    )

with c2:
    st.metric(
        "Beosztva",
        len(st.session_state.beosztas)
    )

with c3:
    st.metric(
        "Hátralévő",
        len(hatralevo)
    )


# ============================================================
# ÚJ BEOSZTÁS
# ============================================================

st.divider()
st.header("Foglalkozás beosztása")

if not hatralevo:
    st.success(
        "Minden foglalkozás be van osztva."
    )

else:
    foglalkozas = st.selectbox(
        "Beosztandó foglalkozás",
        hatralevo,
        format_func=foglalkozas_cimke
    )

    nap_lista = ervenyes_napok(
        foglalkozas
    )

    if not nap_lista:
        st.error(
            "Ehhez a foglalkozáshoz jelenleg nincs egyetlen "
            "érvényes időpont sem."
        )
    else:
        nap = st.selectbox(
            "Nap",
            nap_lista
        )

        idosav_lista = ervenyes_idosavok(
            foglalkozas,
            nap
        )

        if not idosav_lista:
            st.error(
                "A kiválasztott napon nincs érvényes idősáv."
            )
        else:
            idosav = st.selectbox(
                "Idősáv",
                idosav_lista
            )

            st.write(
                f"**Tanár:** {foglalkozas['tanar']}  \n"
                f"**Sport:** {foglalkozas['sport']}  \n"
                f"**Helyszín:** {foglalkozas['helyszin']}"
            )

            if st.button(
                "Beosztás",
                type="primary"
            ):
                jo, hibak = idopont_ervenyes(
                    foglalkozas,
                    nap,
                    idosav
                )

                if not jo:
                    for hiba in hibak:
                        st.error(hiba)
                else:
                    uj_sor = dict(
                        foglalkozas
                    )

                    uj_sor["nap"] = nap
                    uj_sor["idosav"] = idosav

                    st.session_state.beosztas.append(
                        uj_sor
                    )

                    beosztas_mentese()

                    st.rerun()


# ============================================================
# MÉG BEOSZTANDÓ FOGLALKOZÁSOK
# ============================================================

st.divider()
st.header("Még beosztandó foglalkozások")

hatralevo = hatralevo_foglalkozasok()

if not hatralevo:
    st.success("Nincs hátralévő foglalkozás.")
else:
    st.dataframe(
        hatralevo,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# AKTUÁLIS BEOSZTÁS
# ============================================================

st.divider()
st.header("Aktuális beosztás")

if not st.session_state.beosztas:
    st.info("Még nincs beosztott foglalkozás.")
else:
    sorrend_nap = {
        nap: i
        for i, nap in enumerate(NAPOK)
    }

    sorrend_idosav = {
        sav: i
        for i, sav in enumerate(IDOSAVOK)
    }

    rendezett = sorted(
        st.session_state.beosztas,
        key=lambda b: (
            sorrend_nap.get(
                b.get("nap"),
                999
            ),
            sorrend_idosav.get(
                b.get("idosav"),
                999
            ),
            b.get("helyszin", ""),
            b.get("tanar", "")
        )
    )

    st.dataframe(
        rendezett,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TANÁRTERHELTSÉG - EGY TANÁR TELJES HETE
# ============================================================

def egy_tanar_terheles_tabla(tanar):

    tabla = []

    for nap in NAPOK:

        sor = {
            "Nap": nap
        }

        for idosav in IDOSAVOK:

            talalatok = [
                b
                for b in st.session_state.beosztas
                if b.get("nap") == nap
                and b.get("idosav") == idosav
                and b.get("tanar") == tanar
            ]

            if talalatok:

                tartalom = []

                for ora in talalatok:

                    szoveg = (
                        f"{ora['sport']} / "
                        f"{ora['helyszin']}"
                    )

                    if ora.get("csoport"):
                        szoveg += (
                            f" / {ora['csoport']}"
                        )

                    tartalom.append(
                        szoveg
                    )

                sor[idosav] = " | ".join(tartalom)

            else:

                korlatozott, _ = tanar_korlatozva(
                    tanar,
                    nap,
                    idosav
                )

                if korlatozott:
                    sor[idosav] = "NEM ÉR RÁ"
                else:
                    sor[idosav] = "SZABAD"

        tabla.append(sor)

    return tabla


st.divider()
st.header("Tanárterheltség")

tanarok = osszes_tanar()

kivalasztott_tanar = st.selectbox(
    "Tanár",
    tanarok,
    key="tanar_valaszto"
)

st.dataframe(
    egy_tanar_terheles_tabla(
        kivalasztott_tanar
    ),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# TEREMTERHELTSÉG - EGY HELYSZÍN TELJES HETE
# ============================================================

def egy_helyszin_terheles_tabla(helyszin):

    tabla = []

    szabaly = TEREM_SZABALYOK.get(
        helyszin,
        {"max_parhuzamos": 1}
    )

    max_parhuzamos = szabaly.get(
        "max_parhuzamos",
        1
    )

    kizarolagos = szabaly.get(
        "kizarolagos",
        []
    )

    for nap in NAPOK:

        sor = {
            "Nap": nap
        }

        for idosav in IDOSAVOK:

            talalatok = helyszinen_beosztva(
                nap,
                idosav,
                helyszin
            )

            if not talalatok:

                sor[idosav] = (
                    f"SZABAD (0/{max_parhuzamos})"
                )

            else:

                tartalom = []

                for ora in talalatok:

                    szoveg = (
                        f"{ora['sport']} / "
                        f"{ora['tanar']}"
                    )

                    if ora.get("csoport"):
                        szoveg += (
                            f" / {ora['csoport']}"
                        )

                    tartalom.append(
                        szoveg
                    )

                van_kizarolagos = any(
                    ora["sport"] in kizarolagos
                    for ora in talalatok
                )

                if van_kizarolagos:
                    allapot = "KIZÁRÓLAGOS"
                else:
                    allapot = (
                        f"{len(talalatok)}/{max_parhuzamos}"
                    )

                sor[idosav] = (
                    " | ".join(tartalom)
                    + f" [{allapot}]"
                )

        tabla.append(sor)

    return tabla


st.divider()

st.header("Teremterheltség")

helyszinek = osszes_helyszin()

kivalasztott_helyszin = st.selectbox(
    "Helyszín",
    helyszinek,
    key="terem_helyszin"
)

st.dataframe(
    egy_helyszin_terheles_tabla(
        kivalasztott_helyszin
    ),
    use_container_width=True,
    hide_index=True
)

# ============================================================
# TÖRLÉS
# ============================================================

st.divider()
st.header("Beosztás módosítása")

if not st.session_state.beosztas:
    st.info("Nincs törölhető bejegyzés.")
else:
    torlendo = st.selectbox(
        "Törlendő bejegyzés",
        st.session_state.beosztas,
        format_func=lambda b: (
            f"{b.get('id')} | "
            f"{b.get('nap')} | "
            f"{b.get('idosav')} | "
            f"{b.get('tanar')} | "
            f"{b.get('sport')} | "
            f"{b.get('helyszin')}"
        )
    )

    if st.button("Kijelölt bejegyzés törlése"):
        torlendo_id = torlendo.get("id")

        st.session_state.beosztas = [
            b
            for b in st.session_state.beosztas
            if b.get("id") != torlendo_id
        ]

        beosztas_mentese()
        st.rerun()


# ============================================================
# TELJES TÖRLÉS
# ============================================================

if st.session_state.beosztas:
    if st.button(
        "TELJES BEOSZTÁS TÖRLÉSE"
    ):
        st.session_state.beosztas = []
        beosztas_mentese()
        st.rerun()
