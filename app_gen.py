import json
import random
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
GENERALT_MAPPA = BASE_DIR / "generated"


# ============================================================
# ALAPÉRTELMEZETT TEREMSZABÁLYOK
# ============================================================

ALAP_TEREM_SZABALYOK = {
    "Terem": {
        "max_parhuzamos": 2,
        "kizarolagos": [
            "kosárlabda lány",
            "kosárlabda fiú",
            "kézilabda",
        ],
        "egyutt_mehet": [
            ["torna lány", "röplabda fiú"],
            ["torna lány", "röplabda lány 1"],
            ["torna lány", "röplabda lány 2"],
            ["torna fiú", "röplabda fiú"],
            ["torna fiú", "röplabda lány 1"],
            ["torna fiú", "röplabda lány 2"],
        ],
    },
    "Kondi": {
        "max_parhuzamos": 1,
    },
    "Uszoda": {
        "max_parhuzamos": 2,
    },
    "Külső helyszín": {
        "max_parhuzamos": 99,
    },
}


# ============================================================
# JSON
# ============================================================

def json_betolt(path, alap=None):
    if not path.exists():
        return alap

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def json_ment(path, adat):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            adat,
            f,
            ensure_ascii=False,
            indent=2,
        )


def generalt_megoldasok_mentese(fix_beosztas, megoldasok):
    """
    A generált teljes beosztásokat külön JSON-fájlokba menti.

    A fájlok helye:
        generated/megoldas_01.json
        generated/megoldas_02.json
        ...

    Minden fájl a teljes heti beosztást tartalmazza:
    a kézzel rögzített fix részt + a generált részt.
    """

    GENERALT_MAPPA.mkdir(parents=True, exist_ok=True)

    # A korábbi generálás megoldásfájljait töröljük,
    # hogy ne keveredjenek az új futás eredményeivel.
    for regi_fajl in GENERALT_MAPPA.glob("megoldas_*.json"):
        regi_fajl.unlink()

    mentett_fajlok = []

    for i, generalt in enumerate(megoldasok, start=1):
        teljes = (
            [dict(sor) for sor in fix_beosztas]
            + [dict(sor) for sor in generalt]
        )

        teljes = rendezett_beosztas(teljes)

        fajl = GENERALT_MAPPA / f"megoldas_{i:02d}.json"
        json_ment(fajl, teljes)
        mentett_fajlok.append(fajl)

    return mentett_fajlok


# ============================================================
# ADATOK BETÖLTÉSE
# ============================================================

foglalkozas_adatok = json_betolt(
    FOGLALKOZASOK_FAJL,
    {"foglalkozasok": []},
)

korlat_adatok = json_betolt(
    KORLATOZASOK_FAJL,
    {
        "napok": [
            "Hétfő",
            "Kedd",
            "Szerda",
            "Csütörtök",
            "Péntek",
        ],
        "idosavok": [
            "14:30-16:00",
            "16:00-17:30",
            "17:30-19:00",
        ],
        "korlatozasok": [],
        "tanari_korlatozasok": [],
    },
)

terem_adatok = json_betolt(
    TEREM_SZABALYOK_FAJL,
    ALAP_TEREM_SZABALYOK,
)

FOGLALKOZASOK = foglalkozas_adatok.get(
    "foglalkozasok",
    [],
)

NAPOK = korlat_adatok.get(
    "napok",
    ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek"],
)

IDOSAVOK = korlat_adatok.get(
    "idosavok",
    ["14:30-16:00", "16:00-17:30", "17:30-19:00"],
)

KORLATOZASOK = korlat_adatok.get(
    "korlatozasok",
    [],
)

TANARI_KORLATOZASOK = korlat_adatok.get(
    "tanari_korlatozasok",
    [],
)

TEREM_SZABALYOK = terem_adatok

MEGLEVO_BEOSZTAS = json_betolt(
    BEOSZTAS_FAJL,
    [],
)

if MEGLEVO_BEOSZTAS is None:
    MEGLEVO_BEOSZTAS = []


# ============================================================
# SEGÉDFÜGGVÉNYEK
# ============================================================

def mezo_egyezik(szabaly_ertek, aktualis_ertek):
    return (
        szabaly_ertek == "*"
        or szabaly_ertek == aktualis_ertek
    )


def mar_beosztott_idk(beosztas):
    return {
        sor["id"]
        for sor in beosztas
        if "id" in sor
    }


def hatralevo_foglalkozasok(beosztas):
    kesz = mar_beosztott_idk(beosztas)

    return [
        foglalkozas
        for foglalkozas in FOGLALKOZASOK
        if foglalkozas["id"] not in kesz
    ]


def rendezett_beosztas(beosztas):
    sorrend_nap = {
        nap: i
        for i, nap in enumerate(NAPOK)
    }

    sorrend_idosav = {
        sav: i
        for i, sav in enumerate(IDOSAVOK)
    }

    return sorted(
        beosztas,
        key=lambda b: (
            sorrend_nap.get(b.get("nap"), 999),
            sorrend_idosav.get(b.get("idosav"), 999),
            b.get("helyszin", ""),
            b.get("tanar", ""),
            str(b.get("id", "")),
        ),
    )


# ============================================================
# TANÁR ELLENŐRZÉSE
# ============================================================

def tanar_foglalt(tanar, nap, idosav, beosztas):
    # A "Külsős" gyűjtőnév több külön embert jelenthet.
    if tanar == "Külsős":
        return False

    return any(
        sor.get("tanar") == tanar
        and sor.get("nap") == nap
        and sor.get("idosav") == idosav
        for sor in beosztas
    )


def tanar_korlatozva(tanar, nap, idosav):
    szabalyok = list(TANARI_KORLATOZASOK)

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
            nap,
        ):
            continue

        if not mezo_egyezik(
            korlat.get("idosav", "*"),
            idosav,
        ):
            continue

        return True, korlat.get(
            "ok",
            "Tanári korlátozás",
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
            nap,
        ):
            continue

        if not mezo_egyezik(
            korlat.get("idosav", "*"),
            idosav,
        ):
            continue

        return True, korlat.get(
            "ok",
            "Sportkorlátozás",
        )

    return False, ""


# ============================================================
# HELYSZÍN / TEREM
# ============================================================

def helyszinen_beosztva(nap, idosav, helyszin, beosztas):
    return [
        sor
        for sor in beosztas
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


def helyszin_engedelyezett(
    foglalkozas,
    nap,
    idosav,
    beosztas,
):
    helyszin = foglalkozas["helyszin"]
    sport = foglalkozas["sport"]

    # Külsős edzés nem terheli az iskola termeit.
    if foglalkozas.get("kulso", False):
        return True, ""

    bent = helyszinen_beosztva(
        nap,
        idosav,
        helyszin,
        beosztas,
    )

    szabaly = TEREM_SZABALYOK.get(
        helyszin,
        {"max_parhuzamos": 1},
    )

    max_parhuzamos = szabaly.get(
        "max_parhuzamos",
        1,
    )

    if len(bent) >= max_parhuzamos:
        return (
            False,
            f"A(z) {helyszin} elérte a "
            f"{max_parhuzamos} párhuzamos foglalkozásos kapacitását.",
        )

    if not bent:
        return True, ""

    kizarolagos = szabaly.get(
        "kizarolagos",
        [],
    )

    if sport in kizarolagos:
        return (
            False,
            f"A(z) {sport} egyedül használhatja a(z) {helyszin} helyszínt.",
        )

    for bent_sor in bent:
        if bent_sor.get("sport") in kizarolagos:
            return (
                False,
                f"A(z) {helyszin} helyszínt már kizárólagosan használja: "
                f"{bent_sor.get('sport')}.",
            )

    egyutt_mehet = szabaly.get(
        "egyutt_mehet",
        [],
    )

    if egyutt_mehet:
        for bent_sor in bent:
            bent_sport = bent_sor.get("sport")

            if not par_engedelyezett(
                sport,
                bent_sport,
                egyutt_mehet,
            ):
                return (
                    False,
                    f"A(z) {sport} és {bent_sport} "
                    f"nem használhatja együtt a(z) {helyszin} helyszínt.",
                )

    return True, ""


# ============================================================
# TELJES IDŐPONT-ELLENŐRZÉS
# ============================================================

def idopont_ervenyes(
    foglalkozas,
    nap,
    idosav,
    beosztas,
):
    hibak = []

    sport = foglalkozas["sport"]
    tanar = foglalkozas["tanar"]

    tiltott, ok = sport_korlatozva(
        sport,
        nap,
        idosav,
    )

    if tiltott:
        hibak.append(ok)

    tiltott, ok = tanar_korlatozva(
        tanar,
        nap,
        idosav,
    )

    if tiltott:
        hibak.append(ok)

    if tanar_foglalt(
        tanar,
        nap,
        idosav,
        beosztas,
    ):
        hibak.append(
            f"{tanar} ebben az idősávban már foglalt."
        )

    hely_ok, hely_hiba = helyszin_engedelyezett(
        foglalkozas,
        nap,
        idosav,
        beosztas,
    )

    if not hely_ok:
        hibak.append(hely_hiba)

    return len(hibak) == 0, hibak


def lehetseges_idopontok(
    foglalkozas,
    beosztas,
):
    lehetosegek = []

    for nap in NAPOK:
        for idosav in IDOSAVOK:
            jo, _ = idopont_ervenyes(
                foglalkozas,
                nap,
                idosav,
                beosztas,
            )

            if jo:
                lehetosegek.append(
                    (nap, idosav)
                )

    return lehetosegek


# ============================================================
# MEGLÉVŐ BEOSZTÁS ELLENŐRZÉSE
# ============================================================

def meglevo_beosztas_ellenorzese(beosztas):
    hibak = []
    ideiglenes = []
    latott_idk = set()

    for sor in rendezett_beosztas(beosztas):
        sor_id = sor.get("id")

        if sor_id in latott_idk:
            hibak.append(
                f"Duplikált foglalkozás-azonosító a meglévő beosztásban: {sor_id}"
            )
            continue

        latott_idk.add(sor_id)

        if not sor.get("nap") or not sor.get("idosav"):
            hibak.append(
                f"A(z) {sor_id} bejegyzésből hiányzik a nap vagy az idősáv."
            )
            continue

        jo, okok = idopont_ervenyes(
            sor,
            sor["nap"],
            sor["idosav"],
            ideiglenes,
        )

        if not jo:
            hibak.append(
                f"{sor_id} | {sor.get('tanar')} | {sor.get('sport')} | "
                f"{sor.get('nap')} {sor.get('idosav')}: "
                + "; ".join(okok)
            )

        ideiglenes.append(dict(sor))

    return hibak


# ============================================================
# BACKTRACKING GENERÁTOR
# ============================================================

def megoldasok_keresese(
    fix_beosztas,
    hatralevo,
    max_megoldas=5,
    max_lepes=100000,
    veletlen_seed=42,
):
    """
    Több teljes beosztást keres.

    Fontos:
    - a fix_beosztas elemeihez nem nyúl;
    - semmilyen fájlt nem ír;
    - MRV heurisztikát használ:
      mindig azt a hátralévő foglalkozást választja,
      amelynek az adott pillanatban a legkevesebb
      szabályos időpontja van.
    """

    rng = random.Random(veletlen_seed)

    megoldasok = []
    lepesek = 0
    leallt_limit_miatt = False

    munkabeosztas = [
        dict(sor)
        for sor in fix_beosztas
    ]

    def keres(maradek):
        nonlocal lepesek
        nonlocal leallt_limit_miatt

        if len(megoldasok) >= max_megoldas:
            return

        if lepesek >= max_lepes:
            leallt_limit_miatt = True
            return

        lepesek += 1

        if not maradek:
            generalt = munkabeosztas[
                len(fix_beosztas):
            ]

            megoldasok.append(
                [
                    dict(sor)
                    for sor in generalt
                ]
            )
            return

        # MRV: a legszűkebb foglalkozással kezdünk.
        jeloltek = []

        for foglalkozas in maradek:
            lehetosegek = lehetseges_idopontok(
                foglalkozas,
                munkabeosztas,
            )

            if not lehetosegek:
                return

            rng.shuffle(lehetosegek)

            jeloltek.append(
                (
                    len(lehetosegek),
                    rng.random(),
                    foglalkozas,
                    lehetosegek,
                )
            )

        jeloltek.sort(
            key=lambda x: (x[0], x[1])
        )

        _, _, kivalasztott, lehetosegek = jeloltek[0]

        kovetkezo_maradek = [
            f
            for f in maradek
            if f["id"] != kivalasztott["id"]
        ]

        for nap, idosav in lehetosegek:
            uj_sor = dict(
                kivalasztott
            )
            uj_sor["nap"] = nap
            uj_sor["idosav"] = idosav

            munkabeosztas.append(
                uj_sor
            )

            keres(
                kovetkezo_maradek
            )

            munkabeosztas.pop()

            if len(megoldasok) >= max_megoldas:
                return

            if leallt_limit_miatt:
                return

    keres(
        [
            dict(f)
            for f in hatralevo
        ]
    )

    return {
        "megoldasok": megoldasok,
        "lepesek": lepesek,
        "limit_elert": leallt_limit_miatt,
    }


# ============================================================
# DIAGNOSZTIKA
# ============================================================

def kezdeti_lehetosegek_tabla(
    hatralevo,
    fix_beosztas,
):
    tabla = []

    for foglalkozas in hatralevo:
        lehetosegek = lehetseges_idopontok(
            foglalkozas,
            fix_beosztas,
        )

        tabla.append(
            {
                "id": foglalkozas.get("id"),
                "tanar": foglalkozas.get("tanar"),
                "sport": foglalkozas.get("sport"),
                "helyszin": foglalkozas.get("helyszin"),
                "szabad_idopontok": len(lehetosegek),
                "idopontok": ", ".join(
                    f"{nap} {idosav}"
                    for nap, idosav in lehetosegek
                ),
            }
        )

    return sorted(
        tabla,
        key=lambda sor: (
            sor["szabad_idopontok"],
            str(sor["id"]),
        ),
    )


# ============================================================
# STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Délutáni testnevelés – generátor",
    layout="wide",
)

st.title(
    "Délutáni testnevelés – lehetséges beosztások generálása"
)

st.caption(
    "Ez az alkalmazás csak olvassa a meglévő JSON-fájlokat. "
    "A beosztas.json fájlt nem módosítja."
)

hatralevo = hatralevo_foglalkozasok(
    MEGLEVO_BEOSZTAS
)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "Összes foglalkozás",
        len(FOGLALKOZASOK),
    )

with c2:
    st.metric(
        "Fixen beosztva",
        len(MEGLEVO_BEOSZTAS),
    )

with c3:
    st.metric(
        "Generálandó",
        len(hatralevo),
    )


# ============================================================
# FIX BEOSZTÁS
# ============================================================

st.divider()
st.header("Meglévő kézi beosztás – fix")

if MEGLEVO_BEOSZTAS:
    st.dataframe(
        rendezett_beosztas(
            MEGLEVO_BEOSZTAS
        ),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info(
        "A beosztas.json jelenleg üres."
    )


# ============================================================
# FIX BEOSZTÁS VALIDÁLÁSA
# ============================================================

fix_hibak = meglevo_beosztas_ellenorzese(
    MEGLEVO_BEOSZTAS
)

if fix_hibak:
    st.error(
        "A meglévő kézi beosztás a jelenlegi szabályok szerint "
        "ütközést tartalmaz. A generálást ezért letiltottam."
    )

    with st.expander(
        "Ütközések megtekintése",
        expanded=True,
    ):
        for hiba in fix_hibak:
            st.write(
                f"- {hiba}"
            )


# ============================================================
# HÁTRALÉVŐ FOGLALKOZÁSOK
# ============================================================

st.divider()
st.header("Még beosztandó foglalkozások")

if not hatralevo:
    st.success(
        "Nincs generálandó foglalkozás."
    )
else:
    st.dataframe(
        hatralevo,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# KEZDETI LEHETŐSÉGEK
# ============================================================

if hatralevo:
    with st.expander(
        "Kezdeti mozgástér megtekintése"
    ):
        st.caption(
            "Ez azt mutatja, hogy csak a jelenlegi fix beosztás "
            "mellett hány szabályos időpontja van egy foglalkozásnak."
        )

        st.dataframe(
            kezdeti_lehetosegek_tabla(
                hatralevo,
                MEGLEVO_BEOSZTAS,
            ),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# GENERÁLÁS
# ============================================================

st.divider()
st.header("Megoldások keresése")

bal, kozep, jobb = st.columns(3)

with bal:
    keresett_db = st.number_input(
        "Keresendő megoldások száma",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
    )

with kozep:
    max_lepes = st.number_input(
        "Maximális keresési lépésszám",
        min_value=1000,
        max_value=2000000,
        value=100000,
        step=10000,
    )

with jobb:
    seed = st.number_input(
        "Variációs seed",
        min_value=0,
        max_value=1000000,
        value=42,
        step=1,
        help=(
            "Más seed más sorrendben próbálja a szabályos lehetőségeket, "
            "így más megoldásokat találhat."
        ),
    )

generalas_tilva = (
    bool(fix_hibak)
    or not hatralevo
)

if st.button(
    "Lehetséges beosztások keresése",
    type="primary",
    disabled=generalas_tilva,
):
    with st.spinner(
        "Megoldások keresése..."
    ):
        eredmeny = megoldasok_keresese(
            fix_beosztas=MEGLEVO_BEOSZTAS,
            hatralevo=hatralevo,
            max_megoldas=int(keresett_db),
            max_lepes=int(max_lepes),
            veletlen_seed=int(seed),
        )

    st.session_state["generator_eredmeny"] = eredmeny
    st.session_state["generator_seed"] = int(seed)

    if eredmeny["megoldasok"]:
        mentett_fajlok = generalt_megoldasok_mentese(
            MEGLEVO_BEOSZTAS,
            eredmeny["megoldasok"],
        )

        st.session_state["generator_mentett_fajlok"] = [
            str(fajl.relative_to(BASE_DIR))
            for fajl in mentett_fajlok
        ]
    else:
        st.session_state["generator_mentett_fajlok"] = []


# ============================================================
# EREDMÉNYEK
# ============================================================

eredmeny = st.session_state.get(
    "generator_eredmeny"
)

if eredmeny is not None:
    st.divider()
    st.header("Talált megoldások")

    megoldasok = eredmeny["megoldasok"]

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Talált teljes megoldás",
            len(megoldasok),
        )

    with c2:
        st.metric(
            "Keresési lépések",
            eredmeny["lepesek"],
        )

    with c3:
        st.metric(
            "Keresési limit",
            (
                "elérve"
                if eredmeny["limit_elert"]
                else "nem érte el"
            ),
        )

    if not megoldasok:
        st.warning(
            "Nem találtam teljes beosztást a megadott keresési kereten belül."
        )

        if eredmeny["limit_elert"]:
            st.info(
                "Ez még nem bizonyítja, hogy nincs megoldás. "
                "Próbálhatsz nagyobb lépésszámot vagy másik seedet."
            )
        else:
            st.info(
                "A kereső a vizsgált térben nem talált teljes folytatást. "
                "Érdemes megnézni a fenti 'Kezdeti mozgástér' táblát."
            )

    else:
        st.success(
            f"{len(megoldasok)} teljes, szabályos folytatást találtam."
        )

        mentett_fajlok = st.session_state.get(
            "generator_mentett_fajlok",
            [],
        )

        if mentett_fajlok:
            st.info(
                "A megoldások JSON-fájlokként elmentve a "
                f"`{GENERALT_MAPPA.name}/` mappába: "
                + ", ".join(
                    f"`{Path(fajl).name}`"
                    for fajl in mentett_fajlok
                )
            )

        for i, generalt in enumerate(
            megoldasok,
            start=1,
        ):
            teljes = (
                [
                    dict(sor)
                    for sor in MEGLEVO_BEOSZTAS
                ]
                + [
                    dict(sor)
                    for sor in generalt
                ]
            )

            with st.expander(
                f"{i}. megoldás",
                expanded=(i == 1),
            ):
                st.subheader(
                    "Generált foglalkozások"
                )

                st.dataframe(
                    rendezett_beosztas(
                        generalt
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                st.subheader(
                    "Teljes heti beosztás előnézete"
                )

                st.dataframe(
                    rendezett_beosztas(
                        teljes
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

st.divider()
st.caption(
    "A generált változatok a generated/ mappába kerülnek JSON-fájlokként. "
    "A beosztas.json fájlt az alkalmazás továbbra sem módosítja."
)
