#!/usr/bin/env python3
"""Valeurs de référence tirées de OXYHUB_PROD_REF_MEDIA.sql (France).

On reprend le vocabulaire (type, famille, thématique, couverture),
pas le format SQL ni les contraintes MySQL — livrable = CSV.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

CSV_COLUMNS = [
    "id",
    "nom",
    "pays_code",
    "pays_nom",
    "langue",
    "type_media",
    "famille_media",
    "thematique_media",
    "couverture_geo",
    "url",
    "groupe_media",
    "ville",
    "periodicite",
    "source_liste",
    "priorite_rp",
]

TARGET_PAYS = ("BE", "CH", "PT", "ES")

TYPE_MEDIA_VALUES = {"WEB", "PRESSE", "RADIO", "TV", "AGENCES"}
COUVERTURE_VALUES = {"Nationale", "Régionale/Départementale", "Internationale"}

FAMILLE_VALUES = {
    "Médias spécialisés grand public",
    "Médias professionnels",
    "Médias régionaux (hors PQR)",
    "Radios Régionales",
    "Blogs",
    "Médias institutionnels",
    "Médias étrangers",
    "PQR/PQD (Quotidiens régionaux)",
    "Radios Nationales",
    "TV Câble/Sat",
    "Médias associatifs",
    "Radios Web/Podcasts",
    "Agences de presse",
    "Médias d'information générale (hors PQN)",
    "TV Grandes Chaînes",
    "TV Régionales",
    "Médias corporate",
    "TV Web",
    "PQN (Quotidiens nationaux)",
    "Hors famille",
    "Portails, Aggrégateurs",
    "Société de production",
}

THEMATIQUE_VALUES = {
    "Actualités-Infos Générales",
    "Lifestyle",
    "Culture/Arts, littérature et culture générale",
    "Culture/Divertissement, Cinéma, Jeux vidéos",
    "Culture/Musique",
    "Médecine",
    "Tourisme-Gastronomie",
    "Economie - Services",
    "Auto-Moto-Cyclo",
    "Social-Société",
    "Agroalimentaire-Agriculture",
    "Politique",
    "BTP - Immobilier - Architecture",
    "Sports",
    "Energie-Environnement",
    "Gestion d'entreprise - Management",
    "Banques-Finance",
    "Mode-Beauté-Bien être",
    "Communication - Médias - Internet",
    "Education-Enseignement",
    "Maison-Décoration",
    "Informatique-Télécommunications",
    "Loisirs - Hobbies",
    "Sciences & Techniques",
    "High-Tech - Electronique Grand Public",
    "Droit",
    "Industrie",
    "Transport - Logistique",
    "Divertissement TV/Radio",
}

PAYS_NOM = {
    "FR": "France",
    "BE": "Belgique",
    "CH": "Suisse",
    "PT": "Portugal",
    "ES": "Espagne",
}

AGENCY_NAMES = {
    "belga",
    "lusa",
    "efe",
    "europapress",
    "keystoneats",
    "keystone",
    "ats",
    "awpfinanznachrichten",
    "awp",
    "agencefrancepresse",
    "afp",
}

TYPE_ALIASES = {
    "web": "WEB",
    "web natif": "WEB",
    "print": "PRESSE",
    "presse": "PRESSE",
    "presse quotidienne": "PRESSE",
    "presse magazine": "PRESSE",
    "tv": "TV",
    "television": "TV",
    "télévision": "TV",
    "radio": "RADIO",
    "agences": "AGENCES",
    "agence de presse": "AGENCES",
}

THEME_ALIASES = {
    "generaliste": "Actualités-Infos Générales",
    "généraliste": "Actualités-Infos Générales",
    "actualites": "Actualités-Infos Générales",
    "informacaogeral": "Actualités-Infos Générales",
    "informacaoespecializada": "Actualités-Infos Générales",
    "regional": "Actualités-Infos Générales",
    "régional": "Actualités-Infos Générales",
    "economie": "Economie - Services",
    "économie": "Economie - Services",
    "sport": "Sports",
    "sports": "Sports",
    "tematicodesporto": "Sports",
    "tematicodesportivo": "Sports",
    "tematicocinema": "Culture/Divertissement, Cinéma, Jeux vidéos",
    "tematicocinemaseries": "Culture/Divertissement, Cinéma, Jeux vidéos",
    "tematicoentretenimento": "Culture/Divertissement, Cinéma, Jeux vidéos",
    "tematicoentretenimentolifestyle": "Lifestyle",
    "tematicoculturalsocial": "Culture/Arts, littérature et culture générale",
    "tematicoreligiao": "Social-Société",
    "tematicoinfantil": "Lifestyle",
    "tematico": "Lifestyle",
    "people": "Lifestyle",
    "doutrinaria": "Social-Société",
    "radiofonico": "Actualités-Infos Générales",
    "televisivo": "Actualités-Infos Générales",
}

THEME_KEYWORDS = (
    (re.compile(r"financ|banque|bourse|stock|bolsa", re.I), "Banques-Finance"),
    (re.compile(r"econom|écon|negocio|negócio|business|handels|bilanz|agefi", re.I), "Economie - Services"),
    (re.compile(r"sport|desport|football|futbol|futebol|olympic", re.I), "Sports"),
    (re.compile(r"auto|moto|cyclo|voiture|coche", re.I), "Auto-Moto-Cyclo"),
    (re.compile(r"saude|saúde|medic|salud|health|santé", re.I), "Médecine"),
    (re.compile(r"turismo|gastronom|vinho|vino|wine|cuisine|resto", re.I), "Tourisme-Gastronomie"),
    (re.compile(r"cinema|filme|series|série|jeux video|videojuego", re.I), "Culture/Divertissement, Cinéma, Jeux vidéos"),
    (re.compile(r"musica|musique|radio hit", re.I), "Culture/Musique"),
    (re.compile(r"cultur|arte|art\b|literat|livre|libro", re.I), "Culture/Arts, littérature et culture générale"),
    (re.compile(r"moda|mode|beaut|beauté", re.I), "Mode-Beauté-Bien être"),
    (re.compile(r"tech|digital|informati|telecom|high.?tech", re.I), "Informatique-Télécommunications"),
    (re.compile(r"enviro|energi|clima|ecolog|écologie", re.I), "Energie-Environnement"),
    (re.compile(r"educ|escol|universid|enseignement", re.I), "Education-Enseignement"),
    (re.compile(r"imobili|immobilier|architect|btp", re.I), "BTP - Immobilier - Architecture"),
    (re.compile(r"direito|droit|law|jurid", re.I), "Droit"),
    (re.compile(r"agri|agro|vinicola", re.I), "Agroalimentaire-Agriculture"),
    (re.compile(r"industr|engenh", re.I), "Industrie"),
    (re.compile(r"transport|logist", re.I), "Transport - Logistique"),
    (re.compile(r"politique|politica|política", re.I), "Politique"),
    (re.compile(r"societe|société|social", re.I), "Social-Société"),
    (re.compile(r"lifestyle|people|celebr", re.I), "Lifestyle"),
    (re.compile(r"maison|deco|décor|casa", re.I), "Maison-Décoration"),
    (re.compile(r"media|comunicação|communication", re.I), "Communication - Médias - Internet"),
)

PRO_HINT = re.compile(
    r"profissional|professionnel|b2b|industria|indústria|gestion|gestão|"
    r"trade|jornal de negocios|handels|agefi|finanz",
    re.I,
)
ASSOC_HINT = re.compile(r"associa|associatif|doutrin|paroquial|igreja|église|club", re.I)
INSTIT_HINT = re.compile(r"official|officiel|camara|câmara|ayuntamiento|commune|municipal|governo|gobierno", re.I)
BLOG_HINT = re.compile(r"\bblog\b|wordpress|blogspot|medium\.com", re.I)
PORTAL_HINT = re.compile(r"portal|aggreg|aggrég|yahoo|msn", re.I)
DAILY_HINT = re.compile(
    r"quotidien|diario|diário|tageszeitung|daily|jornal|krant|zeitung|"
    r"diária|diaria",
    re.I,
)
MAG_HINT = re.compile(r"magazine|revista|hebdo|semaine|wochen|mensuel|mensal", re.I)
CABLE_HINT = re.compile(r"cable|câble|sat|sport tv|canal\+|canal plus|movistar|disney|axn", re.I)
WEB_TV_HINT = re.compile(r"web tv|webtv|streaming|youtube|twitch", re.I)


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def media_name(nom: str) -> str:
    raw = unicodedata.normalize("NFC", (nom or "").strip())
    return re.sub(r"\s+", " ", raw)


def is_agency(rec: dict[str, Any]) -> bool:
    typ = str(rec.get("type_media") or "")
    support = str(rec.get("support") or "")
    notes = str(rec.get("notes") or "")
    if TYPE_ALIASES.get(typ.lower()) == "AGENCES":
        return True
    if fold(support) in {"nachrichtenagentur", "agence", "agencia", "agência"}:
        return True
    if "agence nationale" in notes.lower() or "entreprise noticieuse" in notes.lower():
        return True
    if "agence" in notes.lower() and "presse" in notes.lower():
        return True
    return fold(str(rec.get("nom") or "")) in AGENCY_NAMES


def map_type(rec: dict[str, Any]) -> str:
    if is_agency(rec):
        return "AGENCES"
    raw = str(rec.get("type_media") or "")
    mapped = TYPE_ALIASES.get(raw.lower()) or TYPE_ALIASES.get(fold(raw))
    if mapped in TYPE_MEDIA_VALUES:
        return mapped
    support = fold(str(rec.get("support") or ""))
    if "radio" in support or "audio" in support:
        return "RADIO"
    if support in {"tv", "video", "television"}:
        return "TV"
    if "online" in support or support == "web":
        return "WEB"
    if "papel" in support or "print" in support or "zeitung" in support:
        return "PRESSE"
    return "WEB"


def map_couverture(rec: dict[str, Any], type_media: str) -> str:
    if type_media == "AGENCES":
        # Dump : siège national = Nationale ; bureaux / fils mondiaux = Internationale.
        raw = fold(str(rec.get("couverture") or ""))
        if "internat" in raw:
            return "Internationale"
        return "Nationale"
    raw = str(rec.get("couverture") or "")
    key = fold(raw)
    if "internat" in key:
        return "Internationale"
    if any(k in key for k in ("region", "local", "depart", "canton", "provinc", "comunid")):
        return "Régionale/Départementale"
    if raw in COUVERTURE_VALUES:
        return raw
    return "Nationale"


def map_thematique(rec: dict[str, Any]) -> str:
    raw = str(rec.get("thematique") or "").strip()
    if raw in THEMATIQUE_VALUES:
        return raw
    alias = THEME_ALIASES.get(raw.lower()) or THEME_ALIASES.get(fold(raw))
    if alias:
        # Pour la presse spécialisée ERC, affiner par le nom.
        if fold(raw) == "informacaoespecializada":
            inferred = _theme_from_text(str(rec.get("nom") or ""), str(rec.get("notes") or ""))
            return inferred or alias
        return alias
    inferred = _theme_from_text(
        raw, str(rec.get("nom") or ""), str(rec.get("notes") or "")
    )
    return inferred or "Actualités-Infos Générales"


def _theme_from_text(*parts: str) -> str | None:
    blob = " ".join(parts)
    for rx, theme in THEME_KEYWORDS:
        if rx.search(blob):
            return theme
    return None


def _is_daily(rec: dict[str, Any]) -> bool:
    blob = " ".join(
        [
            str(rec.get("periodicite") or ""),
            str(rec.get("support") or ""),
            str(rec.get("type_media") or ""),
            str(rec.get("notes") or ""),
            str(rec.get("nom") or ""),
        ]
    )
    if DAILY_HINT.search(blob):
        return True
    per = fold(str(rec.get("periodicite") or ""))
    return per in {"quotidien", "diaria", "daily", "tageszeitung", "mo-sa", "24/7"}


def map_famille(rec: dict[str, Any], type_media: str, couverture: str, thematique: str) -> str:
    if type_media == "AGENCES":
        return "Agences de presse"

    blob = " ".join(
        [
            str(rec.get("nom") or ""),
            str(rec.get("notes") or ""),
            str(rec.get("thematique") or ""),
            str(rec.get("support") or ""),
            str(rec.get("url") or ""),
        ]
    )
    specialized = thematique != "Actualités-Infos Générales" or fold(
        str(rec.get("thematique") or "")
    ) in {"informacaoespecializada", "tematico"}

    if type_media == "RADIO":
        if "podcast" in fold(blob) or "web" in fold(str(rec.get("support") or "")):
            return "Radios Web/Podcasts"
        if couverture == "Régionale/Départementale":
            return "Radios Régionales"
        return "Radios Nationales"

    if type_media == "TV":
        if couverture == "Régionale/Départementale":
            return "TV Régionales"
        if WEB_TV_HINT.search(blob):
            return "TV Web"
        if CABLE_HINT.search(blob) or specialized:
            return "TV Câble/Sat"
        return "TV Grandes Chaînes"

    # PRESSE / WEB
    if ASSOC_HINT.search(blob):
        return "Médias associatifs"
    if INSTIT_HINT.search(blob):
        return "Médias institutionnels"
    if type_media == "WEB" and PORTAL_HINT.search(blob):
        return "Portails, Aggrégateurs"
    if type_media == "WEB" and BLOG_HINT.search(blob):
        return "Blogs"

    if couverture == "Régionale/Départementale":
        if type_media == "PRESSE" and _is_daily(rec):
            return "PQR/PQD (Quotidiens régionaux)"
        return "Médias régionaux (hors PQR)"

    if type_media == "PRESSE" and _is_daily(rec) and not specialized:
        return "PQN (Quotidiens nationaux)"

    if PRO_HINT.search(blob) or thematique in {
        "Economie - Services",
        "Banques-Finance",
        "Gestion d'entreprise - Management",
        "Droit",
        "Industrie",
        "Transport - Logistique",
    }:
        return "Médias professionnels"

    if specialized:
        return "Médias spécialisés grand public"

    if type_media == "WEB":
        return "Médias d'information générale (hors PQN)"
    if MAG_HINT.search(blob):
        return "Médias d'information générale (hors PQN)"
    return "Médias d'information générale (hors PQN)"


def to_row(rec: dict[str, Any], row_id: str) -> dict[str, Any]:
    type_media = map_type(rec)
    couverture = map_couverture(rec, type_media)
    thematique = map_thematique(rec)
    famille = map_famille(rec, type_media, couverture, thematique)
    if famille not in FAMILLE_VALUES:
        famille = "Hors famille"
    if thematique not in THEMATIQUE_VALUES:
        thematique = "Actualités-Infos Générales"
    cc = str(rec.get("pays_code") or "")
    return {
        "id": row_id,
        "nom": media_name(str(rec.get("nom") or "")),
        "pays_code": cc,
        "pays_nom": rec.get("pays_nom") or PAYS_NOM.get(cc, ""),
        "langue": rec.get("langue") or "",
        "type_media": type_media,
        "famille_media": famille,
        "thematique_media": thematique,
        "couverture_geo": couverture,
        "url": rec.get("url") or "",
        "groupe_media": rec.get("groupe_media") or "",
        "ville": rec.get("ville") or "",
        "periodicite": rec.get("periodicite") or "",
        "source_liste": rec.get("source_liste") or "",
        "priorite_rp": int(rec.get("priorite_rp") or 3),
    }


def build_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """CSV rows hors France, id stable MED-XX-NNNN."""
    by_cc: dict[str, list[dict[str, Any]]] = {cc: [] for cc in TARGET_PAYS}
    for rec in records:
        cc = rec.get("pays_code")
        if cc in by_cc:
            by_cc[cc].append(rec)

    out: list[dict[str, Any]] = []
    for cc in TARGET_PAYS:
        subset = sorted(
            by_cc[cc],
            key=lambda r: (
                0 if r.get("source_liste") == "SEED" else 1,
                int(r.get("priorite_rp") or 9),
                fold(str(r.get("nom") or "")),
            ),
        )
        for i, rec in enumerate(subset, start=1):
            out.append(to_row(rec, f"MED-{cc}-{i:04d}"))
    return out
