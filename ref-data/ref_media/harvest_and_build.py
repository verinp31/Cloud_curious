#!/usr/bin/env python3
"""Étend ref_media : Web / Print / TV / Radio × Nationale / Régionale.

Sources :
  - seed prioritaire (generate_ref_media.ROWS)
  - ERC Portugal (registres officiels 01-09-2026)
  - Swissdox (médias CH actifs)
  - catégories Wikipedia (BE / CH / PT / ES)
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from generate_ref_media import COLUMNS, ROWS as SEED_ROWS

HERE = Path(__file__).resolve().parent
HARVEST = HERE / "harvest"
OFFICIAL = HARVEST / "official"
UA = "ref-media-harvest/2.0 (OnePM; relations-presse; +https://github.com/verinp31/Cloud_curious)"

PAYS = {
    "FR": "France",
    "BE": "Belgique",
    "CH": "Suisse",
    "PT": "Portugal",
    "ES": "Espagne",
}

TYPE_MAP_SEED = {
    "Presse quotidienne": "Print",
    "Presse magazine": "Print",
    "Web natif": "Web",
    "Télévision": "TV",
    "Radio": "Radio",
    "Agence de presse": "AGENCES",
}

SKIP_TITLE_RE = re.compile(
    r"^(list of|liste des|liste de|lista de|lista das|categoría|categorie|category|"
    r"index of|portal:|template:|wikipedia:|file:|help:)",
    re.I,
)
SKIP_CAT_RE = re.compile(
    r"(journalist|journaliste|people|personnalité|personnalité|empresa de comunicación|"
    r"media compan|société de média|defunct|former|disparu|eingestellt|"
    r"extinto|extinta|desaparecid|voormalig|histórico|historico|history of|histoire de|"
    r"siglo|siècle|century|scientific|scientifique|científic|académic|academic|"
    r"historieta|comic|bande dessin|founders|fondateur|works originally|"
    r"film|cinéma|cinema|programming|émission|emission|animateur|présentateur|"
    r"presentateur|acteur|actor|original programming)",
    re.I,
)


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def slug_code(nom: str) -> str:
    raw = fold(nom).upper()[:28] or "MEDIA"
    return raw


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url or url in {"-", "--", "n/a", "NA"}:
        return ""
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url.lstrip("/")
    return url.rstrip("/")


def norm_name_key(nom: str, pays: str) -> str:
    return f"{pays}|{fold(nom)}"


def http_get(url: str, timeout: int = 40) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def http_json(url: str, timeout: int = 40) -> dict:
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def map_couverture(value: str) -> str:
    v = fold(value)
    if any(k in v for k in ("regional", "regionale", "local", "comunidad", "canton", "provinc", "comarcal", "auton")):
        return "Régionale"
    return "Nationale"


def map_type_from_text(*parts: str) -> str | None:
    blob = fold(" ".join(parts))
    if any(k in blob for k in ("radio", "audio", "fm", "dab")) and "television" not in blob:
        if "web" in blob and "radio" in blob:
            return "Radio"
        return "Radio"
    if any(k in blob for k in ("tv", "television", "televis", "fernseh")):
        return "TV"
    if any(k in blob for k in ("online", "web", "digital", "onlinemedium", "site")):
        return "Web"
    if any(k in blob for k in ("print", "papel", "journal", "zeitung", "magazine", "revista", "presse", "periodico", "jornal")):
        return "Print"
    return None


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def load_seed() -> list[dict]:
    records = []
    for raw in SEED_ROWS:
        rec = dict(zip(COLUMNS, raw))
        rec["type_media"] = TYPE_MAP_SEED.get(str(rec["type_media"]), str(rec["type_media"]))
        if rec["type_media"] not in {"Web", "Print", "TV", "Radio", "AGENCES"}:
            rec["type_media"] = "Web"
        rec["couverture"] = "Nationale" if rec["couverture"] == "Internationale" else rec["couverture"]
        rec["support"] = rec["type_media"]
        rec["source_liste"] = "SEED"
        rec["actif"] = True if rec["actif"] in {True, "true", "TRUE", 1} else False
        records.append(rec)
    return records


# ---------------------------------------------------------------------------
# ERC Portugal
# ---------------------------------------------------------------------------

def parse_erc_pp(path: Path) -> list[dict]:
    rows = list(csv.reader(path.read_text(encoding="utf-8", errors="replace").splitlines()))
    out = []
    for row in rows[2:]:
        if len(row) < 5 or not row[2].strip():
            continue
        nom = row[2].strip()
        suporte = row[3].strip()
        ambito = row[4].strip()
        thematique = row[5].strip() if len(row) > 5 else ""
        periodicite = row[6].strip() if len(row) > 6 else ""
        ville = row[10].strip() if len(row) > 10 else ""
        groupe = row[17].strip() if len(row) > 17 else ""
        url = normalize_url(row[22].strip() if len(row) > 22 else "")
        type_media = "Web" if fold(suporte) == "online" else "Print"
        out.append(
            {
                "nom": nom,
                "pays_code": "PT",
                "langue": "pt",
                "type_media": type_media,
                "support": suporte or type_media,
                "periodicite": periodicite,
                "thematique": thematique or "Généraliste",
                "couverture": map_couverture(ambito or "Nacional"),
                "groupe_media": groupe,
                "ville": ville,
                "url": url,
                "priorite_rp": 3,
                "actif": True,
                "notes": f"ERC PP {row[0].strip()} · {suporte} · {ambito}",
                "source_liste": "ERC",
            }
        )
    return out


def parse_erc_radio(path: Path) -> list[dict]:
    rows = list(csv.reader(path.read_text(encoding="utf-8", errors="replace").splitlines()))
    out = []
    for row in rows[2:]:
        if len(row) < 10:
            continue
        nom = (row[9] or row[2] or "").strip()
        if not nom:
            continue
        ville = (row[5] or "").strip()
        groupe = (row[2] or "").strip()
        # colonnes suivantes variables : tenter un site si présent
        url = ""
        for cell in row[12:]:
            if "." in cell and not cell.startswith("20") and "@" not in cell:
                if re.search(r"[a-zA-Z0-9-]+\.[a-z]{2,}", cell):
                    url = normalize_url(cell.strip())
                    break
        national = fold(nom).startswith("rtp") or fold(nom) in {
            "rfm", "radio comercial", "renascenca", "tsf", "cmradio", "radio observador"
        }
        out.append(
            {
                "nom": nom,
                "pays_code": "PT",
                "langue": "pt",
                "type_media": "Radio",
                "support": "Radio",
                "periodicite": "Continu",
                "thematique": "Généraliste",
                "couverture": "Nationale" if national else "Régionale",
                "groupe_media": groupe,
                "ville": ville,
                "url": url,
                "priorite_rp": 3,
                "actif": True,
                "notes": f"ERC OR {row[0].strip()}",
                "source_liste": "ERC",
            }
        )
    return out


def parse_erc_tv(path: Path) -> list[dict]:
    rows = list(csv.reader(path.read_text(encoding="utf-8", errors="replace").splitlines()))
    out = []
    for row in rows[2:]:
        if len(row) < 10:
            continue
        nom = (row[9] or "").strip()
        if not nom:
            continue
        ambito = row[10].strip() if len(row) > 10 else "Nacional"
        thematique = row[11].strip() if len(row) > 11 else "Généraliste"
        ville = (row[5] or "").strip()
        groupe = (row[2] or "").strip()
        out.append(
            {
                "nom": nom,
                "pays_code": "PT",
                "langue": "pt",
                "type_media": "TV",
                "support": "TV",
                "periodicite": "Continu",
                "thematique": thematique or "Généraliste",
                "couverture": map_couverture(ambito),
                "groupe_media": groupe,
                "ville": ville,
                "url": "",
                "priorite_rp": 3,
                "actif": True,
                "notes": f"ERC OT {row[0].strip()} · {ambito}",
                "source_liste": "ERC",
            }
        )
    return out


def parse_erc_web(path: Path) -> list[dict]:
    rows = list(csv.reader(path.read_text(encoding="utf-8", errors="replace").splitlines()))
    header_idx = next(
        (i for i, r in enumerate(rows) if any("Serviço de Programas" in c for c in r)),
        None,
    )
    if header_idx is None:
        return []
    out = []
    last_district = ""
    for row in rows[header_idx + 1 :]:
        if len(row) < 8:
            continue
        if row[0].strip():
            last_district = row[0].strip()
        nom = (row[1] or "").strip()
        if not nom:
            continue
        typ = (row[7] or "").strip()
        type_media = "Radio" if "radio" in fold(typ) else ("TV" if "tele" in fold(typ) else "Web")
        url = normalize_url(row[12].strip() if len(row) > 12 else "")
        groupe = row[8].strip() if len(row) > 8 else ""
        ville = row[9].strip() if len(row) > 9 else ""
        out.append(
            {
                "nom": nom,
                "pays_code": "PT",
                "langue": "pt",
                "type_media": type_media,
                "support": "Web",
                "periodicite": "Continu",
                "thematique": typ or "Généraliste",
                "couverture": "Régionale",
                "groupe_media": groupe,
                "ville": ville or last_district,
                "url": url,
                "priorite_rp": 3,
                "actif": True,
                "notes": f"ERC SPDEI {row[3].strip() if len(row) > 3 else ''} · {last_district}",
                "source_liste": "ERC",
            }
        )
    return out


def parse_erc_agencies(path: Path) -> list[dict]:
    rows = list(csv.reader(path.read_text(encoding="utf-8", errors="replace").splitlines()))
    out = []
    for row in rows:
        if len(row) < 6:
            continue
        nom = (row[5] or "").strip()
        if not nom or "LISTA" in nom or nom == "Designação":
            continue
        out.append(
            {
                "nom": nom,
                "pays_code": "PT",
                "langue": "pt",
                "type_media": "AGENCES",
                "support": "Agence",
                "periodicite": "Continu",
                "thematique": "Généraliste",
                "couverture": "Nationale",
                "groupe_media": nom,
                "ville": (row[9] or "").strip() if len(row) > 9 else "Lisbonne",
                "url": "",
                "priorite_rp": 2,
                "actif": True,
                "notes": "ERC entreprise noticieuse",
                "source_liste": "ERC",
            }
        )
    return out


def load_erc() -> list[dict]:
    files = {
        "pt_pp.csv": parse_erc_pp,
        "pt_radio.csv": parse_erc_radio,
        "pt_tv.csv": parse_erc_tv,
        "pt_web.csv": parse_erc_web,
        "pt_agences.csv": parse_erc_agencies,
    }
    records = []
    for name, parser in files.items():
        path = OFFICIAL / name
        if path.exists():
            records.extend(parser(path))
    return records


# ---------------------------------------------------------------------------
# Swissdox
# ---------------------------------------------------------------------------

SWISSDOX_TYPE = {
    "tageszeitung": "Print",
    "wochenzeitung": "Print",
    "sonntagszeitung": "Print",
    "zeitschrift": "Print",
    "onlinemedium": "Web",
    "audio": "Radio",
    "video": "TV",
    "nachrichtenagentur": "AGENCES",
}


def harvest_swissdox() -> list[dict]:
    cache = HARVEST / "swissdox.html"
    html = ""
    try:
        html = http_get("https://swissdox.ch/medienarchiv/medienliste/", timeout=90).decode("utf-8", "replace")
        cache.write_text(html, encoding="utf-8")
    except Exception as exc:
        print("  swissdox download", exc)
        if cache.exists():
            html = cache.read_text(encoding="utf-8", errors="replace")
    if not html:
        return []
    # rows are markdown-like or HTML table; parse both
    records = []
    # HTML table rows
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.I | re.S):
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.I | re.S)]
        cells = [re.sub(r"\s+", " ", c) for c in cells if c]
        if len(cells) < 8:
            continue
        nom, typ, status, lang, country = cells[0], cells[2] if len(cells) > 2 else "", "", "", ""
        # flexible: find status / lang / country by known tokens
        joined = " | ".join(cells)
        if "aktuell" not in joined.lower() and "eingestellt" not in joined.lower():
            continue
        status = "aktuell" if re.search(r"\baktuell\b", joined, re.I) else "eingestellt"
        if status != "aktuell":
            continue
        lang = "de"
        if re.search(r"\bFR\b", joined):
            lang = "fr"
        elif re.search(r"\bIT\b", joined):
            lang = "it"
        elif re.search(r"\bEN\b", joined) and "DT" not in joined:
            lang = "en"
        if not re.search(r"\bCH\b", joined):
            continue
        type_media = SWISSDOX_TYPE.get(fold(typ), map_type_from_text(typ, nom) or "Print")
        if type_media not in {"Web", "Print", "TV", "Radio", "AGENCES"}:
            type_media = "Print"
        if nom.lower() in {"titel", "title"}:
            continue
        regional = bool(
            re.search(
                r"(anzeiger|region|landbote|gazette|feuille|journal de |bote|blatt)$",
                nom,
                re.I,
            )
        ) or type_media == "Print" and not re.search(
            r"^(nzz|blick|20 min|le temps|tages-anzeiger|le matin|watson|beobachter|bilanz|handels)",
            nom,
            re.I,
        )
        records.append(
            {
                "nom": nom,
                "pays_code": "CH",
                "langue": lang,
                "type_media": type_media,
                "support": typ or type_media,
                "periodicite": cells[4] if len(cells) > 4 else "",
                "thematique": "Généraliste",
                "couverture": "Régionale" if regional and type_media in {"Print", "Web"} else "Nationale",
                "groupe_media": "",
                "ville": "",
                "url": "",
                "priorite_rp": 3,
                "actif": True,
                "notes": f"Swissdox · {typ}",
                "source_liste": "SWISSDOX",
            }
        )
    # fallback: markdown pipe tables
    if len(records) < 50:
        for line in html.splitlines():
            if line.count("|") < 8:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 8:
                continue
            nom, typ, status = cells[0], cells[2], cells[3]
            if status.lower() != "aktuell":
                continue
            country = cells[9] if len(cells) > 9 else ""
            if country != "CH":
                continue
            lang_raw = cells[8] if len(cells) > 8 else "DT"
            lang = "de"
            if "FR" in lang_raw:
                lang = "fr"
            elif "IT" in lang_raw:
                lang = "it"
            type_media = SWISSDOX_TYPE.get(fold(typ), "Print")
            if nom.lower() == "titel":
                continue
            records.append(
                {
                    "nom": nom,
                    "pays_code": "CH",
                    "langue": lang,
                    "type_media": type_media if type_media in {"Web", "Print", "TV", "Radio", "AGENCES"} else "Print",
                    "support": typ,
                    "periodicite": cells[4] if len(cells) > 4 else "",
                    "thematique": "Généraliste",
                    "couverture": "Régionale" if "online" not in fold(typ) and "nzz" not in fold(nom) else "Nationale",
                    "groupe_media": "",
                    "ville": "",
                    "url": "",
                    "priorite_rp": 3,
                    "actif": True,
                    "notes": f"Swissdox · {typ}",
                    "source_liste": "SWISSDOX",
                }
            )
    return records


# ---------------------------------------------------------------------------
# Wikipedia categories
# ---------------------------------------------------------------------------

# 5e champ = profondeur de crawl Wikipedia
WIKI_CATS = {
    "BE": [
        ("en", "Category:Newspapers published in Belgium", "Print", "Régionale", 2),
        ("en", "Category:Magazines published in Belgium", "Print", "Nationale", 1),
        ("en", "Category:Radio stations in Belgium", "Radio", "Régionale", 1),
        ("nl", "Categorie:Vlaamse televisiezender", "TV", "Nationale", 1),
        ("fr", "Catégorie:Chaîne de télévision en Belgique", "TV", "Nationale", 1),
        ("en", "Category:Belgian news websites", "Web", "Nationale", 1),
        ("fr", "Catégorie:Presse écrite belge", "Print", "Régionale", 2),
        ("fr", "Catégorie:Magazine belge", "Print", "Nationale", 1),
        ("fr", "Catégorie:Radio en Belgique", "Radio", "Régionale", 1),
        ("fr", "Catégorie:Chaîne de télévision belge", "TV", "Nationale", 1),
        ("nl", "Categorie:Belgische krant", "Print", "Régionale", 2),
        ("nl", "Categorie:Belgisch tijdschrift", "Print", "Nationale", 1),
        ("nl", "Categorie:Belgische radiozender", "Radio", "Régionale", 1),
        ("nl", "Categorie:Belgische televisiezender", "TV", "Nationale", 1),
        ("de", "Kategorie:Zeitung (Belgien)", "Print", "Régionale", 2),
    ],
    "CH": [
        ("en", "Category:Newspapers published in Switzerland", "Print", "Régionale", 2),
        ("en", "Category:Magazines published in Switzerland", "Print", "Nationale", 1),
        ("en", "Category:Radio stations in Switzerland", "Radio", "Régionale", 1),
        ("en", "Category:Television stations in Switzerland", "TV", "Nationale", 1),
        ("fr", "Catégorie:Presse écrite suisse", "Print", "Régionale", 2),
        ("fr", "Catégorie:Radio en Suisse", "Radio", "Régionale", 1),
        ("de", "Kategorie:Schweizer Zeitung", "Print", "Régionale", 2),
        ("de", "Kategorie:Hörfunksender in der Schweiz", "Radio", "Régionale", 1),
        ("de", "Kategorie:Fernsehsender (Schweiz)", "TV", "Nationale", 1),
        ("it", "Categoria:Quotidiani svizzeri", "Print", "Régionale", 2),
    ],
    "PT": [
        ("pt", "Categoria:Jornais de Portugal", "Print", "Régionale", 2),
        ("pt", "Categoria:Revistas de Portugal", "Print", "Nationale", 1),
        ("pt", "Categoria:Rádios de Portugal", "Radio", "Régionale", 1),
        ("pt", "Categoria:Canais de televisão de Portugal", "TV", "Nationale", 1),
        ("en", "Category:Newspapers published in Portugal", "Print", "Régionale", 2),
        ("en", "Category:Radio stations in Portugal", "Radio", "Régionale", 1),
        ("en", "Category:Television stations in Portugal", "TV", "Nationale", 1),
    ],
    "ES": [
        ("es", "Categoría:Periódicos de España", "Print", "Régionale", 2),
        ("es", "Categoría:Revistas de España", "Print", "Nationale", 1),
        ("es", "Categoría:Emisoras de radio de España", "Radio", "Régionale", 2),
        ("es", "Categoría:Canales de televisión de España", "TV", "Nationale", 1),
        ("es", "Categoría:Periódicos digitales de España", "Web", "Nationale", 2),
        ("es", "Categoría:Prensa digital de España", "Web", "Nationale", 1),
        ("en", "Category:Newspapers published in Spain", "Print", "Régionale", 2),
        ("en", "Category:Radio stations in Spain", "Radio", "Régionale", 1),
        ("en", "Category:Television stations in Spain", "TV", "Nationale", 1),
        ("ca", "Categoria:Diaris de Catalunya", "Print", "Régionale", 2),
        ("ca", "Categoria:Ràdios de Catalunya", "Radio", "Régionale", 1),
        ("gl", "Categoría:Xornais de Galicia", "Print", "Régionale", 2),
        ("eu", "Kategoria:Espainiako egunkariak", "Print", "Régionale", 2),
    ],
}

WIKI_LANG_DEFAULT = {
    "en": {"BE": "nl", "CH": "de", "PT": "pt", "ES": "es"},
    "fr": {"BE": "fr", "CH": "fr", "PT": "pt", "ES": "es"},
    "nl": {"BE": "nl", "CH": "de", "PT": "pt", "ES": "es"},
    "de": {"BE": "de", "CH": "de", "PT": "pt", "ES": "es"},
    "pt": {"BE": "nl", "CH": "de", "PT": "pt", "ES": "es"},
    "es": {"BE": "nl", "CH": "de", "PT": "pt", "ES": "es"},
    "ca": {"BE": "nl", "CH": "de", "PT": "pt", "ES": "ca"},
    "gl": {"BE": "nl", "CH": "de", "PT": "pt", "ES": "gl"},
    "eu": {"BE": "nl", "CH": "de", "PT": "pt", "ES": "eu"},
    "it": {"BE": "nl", "CH": "it", "PT": "pt", "ES": "es"},
}


def wiki_api(lang: str, params: dict) -> dict:
    params = dict(params)
    params.setdefault("format", "json")
    params.setdefault("formatversion", "2")
    url = f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    try:
        return http_json(url, timeout=30)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        time.sleep(0.8)
        return http_json(url, timeout=40)


def crawl_category(lang: str, title: str, type_media: str, couverture: str, pays: str, max_depth: int = 1) -> list[dict]:
    seen_cats: set[str] = set()
    records: list[dict] = []
    queue = [(title, 0)]
    while queue:
        cat, depth = queue.pop(0)
        key = f"{lang}:{cat}"
        if key in seen_cats or depth > max_depth:
            continue
        seen_cats.add(key)
        if SKIP_CAT_RE.search(cat):
            continue
        cmcontinue = None
        for _ in range(20):
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": cat,
                "cmlimit": 500,
                "cmtype": "page|subcat",
            }
            if cmcontinue:
                params["cmcontinue"] = cmcontinue
            data = wiki_api(lang, params)
            members = data.get("query", {}).get("categorymembers", [])
            for m in members:
                mtitle = m.get("title") or ""
                if m.get("ns") == 14:  # category
                    queue.append((mtitle, depth + 1))
                    continue
                if m.get("ns") not in (0, None) and m.get("ns") != 0:
                    continue
                if SKIP_TITLE_RE.search(mtitle):
                    continue
                if SKIP_CAT_RE.search(mtitle):
                    continue
                # drop parenthetical disambiguators that are not media
                clean = re.sub(r"\s*\([^)]*\)\s*$", "", mtitle).strip()
                if len(clean) < 2:
                    continue
                lang_code = WIKI_LANG_DEFAULT.get(lang, {}).get(pays, "fr")
                local_cov = couverture
                if re.search(r"local|régional|regional|comarcal|provincial|canton|autonóm", cat + " " + mtitle, re.I):
                    local_cov = "Régionale"
                records.append(
                    {
                        "nom": clean,
                        "pays_code": pays,
                        "langue": lang_code,
                        "type_media": type_media,
                        "support": type_media,
                        "periodicite": "",
                        "thematique": "Généraliste",
                        "couverture": local_cov,
                        "groupe_media": "",
                        "ville": "",
                        "url": f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(mtitle.replace(' ', '_'))}",
                        "priorite_rp": 3,
                        "actif": True,
                        "notes": f"Wikipedia {lang} · {cat}",
                        "source_liste": "WIKIPEDIA",
                    }
                )
            cmcontinue = data.get("continue", {}).get("cmcontinue")
            if not cmcontinue:
                break
            time.sleep(0.05)
        time.sleep(0.05)
    return records


def harvest_wikipedia() -> list[dict]:
    all_recs = []
    for pays, cats in WIKI_CATS.items():
        if pays == "ES":
            print("  pause anti-429 avant ES…")
            time.sleep(20)
        for lang, title, typ, cov, depth in cats:
            try:
                recs = crawl_category(lang, title, typ, cov, pays, max_depth=depth)
                recs = [r for r in recs if not SKIP_CAT_RE.search(r.get("notes", ""))]
                print(f"  wiki {pays} {lang} {title} → {len(recs)}")
                all_recs.extend(recs)
                time.sleep(0.4)
            except Exception as exc:
                print(f"  wiki FAIL {pays} {title}: {exc}")
                time.sleep(8)
                try:
                    recs = crawl_category(lang, title, typ, cov, pays, max_depth=depth)
                    recs = [r for r in recs if not SKIP_CAT_RE.search(r.get("notes", ""))]
                    print(f"  wiki RETRY {pays} {title} → {len(recs)}")
                    all_recs.extend(recs)
                except Exception as exc2:
                    print(f"  wiki FAIL2 {pays} {title}: {exc2}")
    return all_recs


# ---------------------------------------------------------------------------
# Merge + export
# ---------------------------------------------------------------------------

MEDIA_TOKEN_RE = re.compile(
    r"\b(radio|tv|t[eé]l[eé]|journal|diario|diari|gazette|news|nieuws|fm|presse|"
    r"zeitung|magazine|canal|cadena|voix|voz|echo|libre|soir|matin|web|press|"
    r"media|média|krant|blad|revue|jornal|zeit|post|herald|correo|périodique|"
    r"hebdo|quotidien|emisora|zender|sender)\b",
    re.I,
)


def looks_like_person(nom: str) -> bool:
    if MEDIA_TOKEN_RE.search(nom):
        return False
    parts = [p for p in re.split(r"[\s\-]+", nom) if p]
    if len(parts) not in (2, 3):
        return False
    articles = {"de", "du", "la", "le", "el", "los", "las", "van", "von", "der", "die", "das", "the", "het"}
    if any(p.lower() in articles for p in parts):
        return False
    alpha = [p for p in parts if p.isalpha()]
    if len(alpha) != len(parts):
        return False
    return all(p[0].isupper() and p[1:].islower() for p in alpha)


def merge(records: list[dict]) -> list[dict]:
    by_key: dict[str, dict] = {}
    source_rank = {"SEED": 0, "ERC": 1, "SWISSDOX": 2, "WIKIPEDIA": 3}

    def better(new: dict, old: dict) -> bool:
        if source_rank.get(new["source_liste"], 9) < source_rank.get(old["source_liste"], 9):
            return True
        if new.get("url") and not old.get("url"):
            return True
        if new.get("groupe_media") and not old.get("groupe_media"):
            return True
        return False

    for rec in records:
        nom = rec["nom"].strip()
        if not nom:
            continue
        if rec.get("source_liste") == "WIKIPEDIA" and looks_like_person(nom):
            continue
        key = norm_name_key(nom, rec["pays_code"])
        # also collapse ".ch / .pt online twins" of same print title
        if key in by_key:
            if better(rec, by_key[key]):
                kept = rec
                kept["priorite_rp"] = min(int(rec["priorite_rp"]), int(by_key[key]["priorite_rp"]))
                if by_key[key].get("url") and not kept.get("url"):
                    kept["url"] = by_key[key]["url"]
                by_key[key] = kept
            else:
                by_key[key]["priorite_rp"] = min(int(rec["priorite_rp"]), int(by_key[key]["priorite_rp"]))
        else:
            by_key[key] = rec

    # assign ids / codes
    counters: dict[str, int] = defaultdict(int)
    used_codes: set[str] = set()
    out = []
    # seed first so they keep human codes when possible
    ordered = sorted(
        by_key.values(),
        key=lambda r: (source_rank.get(r["source_liste"], 9), r["pays_code"], r["nom"].lower()),
    )
    for rec in ordered:
        cc = rec["pays_code"]
        counters[cc] += 1
        rec["id_media"] = f"MED-{cc}-{counters[cc]:04d}"
        rec["pays_nom"] = PAYS[cc]
        code = rec.get("code") or slug_code(rec["nom"])
        base = code
        n = 2
        while code in used_codes:
            code = f"{base}{n}"
            n += 1
        rec["code"] = code
        used_codes.add(code)
        rec["url"] = rec.get("url") or ""
        rec["groupe_media"] = rec.get("groupe_media") or ""
        rec["ville"] = rec.get("ville") or ""
        rec["periodicite"] = rec.get("periodicite") or ""
        rec["thematique"] = rec.get("thematique") or "Généraliste"
        rec["support"] = rec.get("support") or rec["type_media"]
        rec["notes"] = rec.get("notes") or ""
        rec["actif"] = bool(rec.get("actif", True))
        rec["priorite_rp"] = int(rec.get("priorite_rp") or 3)
        out.append(rec)
    return out


def write_outputs(records: list[dict]) -> None:
    # CSV
    with (HERE / "ref_media.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            row = {k: rec.get(k, "") for k in COLUMNS}
            row["actif"] = "true" if rec["actif"] else "false"
            writer.writerow(row)

    typed = []
    for rec in records:
        item = {k: rec.get(k, "") for k in COLUMNS}
        item["actif"] = bool(rec["actif"])
        item["priorite_rp"] = int(rec["priorite_rp"])
        typed.append(item)
    (HERE / "ref_media.json").write_text(json.dumps(typed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def sql_lit(value) -> str:
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if isinstance(value, int):
            return str(value)
        return "'" + str(value).replace("'", "''") + "'"

    lines = [
        "-- ref_media — Web / Print / TV / Radio × Nationale / Régionale",
        "CREATE TABLE IF NOT EXISTS ref_media (",
        "    id_media      VARCHAR(20)  PRIMARY KEY,",
        "    code          VARCHAR(40)  NOT NULL UNIQUE,",
        "    nom           VARCHAR(240) NOT NULL,",
        "    pays_code     CHAR(2)      NOT NULL,",
        "    pays_nom      VARCHAR(40)  NOT NULL,",
        "    langue        VARCHAR(8)   NOT NULL,",
        "    type_media    VARCHAR(16)  NOT NULL,",
        "    support       VARCHAR(40),",
        "    periodicite   VARCHAR(40),",
        "    thematique    VARCHAR(80),",
        "    couverture    VARCHAR(16)  NOT NULL,",
        "    groupe_media  VARCHAR(240),",
        "    ville         VARCHAR(80),",
        "    url           VARCHAR(255),",
        "    priorite_rp   SMALLINT     NOT NULL,",
        "    actif         BOOLEAN      NOT NULL DEFAULT TRUE,",
        "    notes         TEXT,",
        "    source_liste  VARCHAR(16)  NOT NULL",
        ");",
        "CREATE INDEX IF NOT EXISTS idx_ref_media_pays ON ref_media (pays_code);",
        "CREATE INDEX IF NOT EXISTS idx_ref_media_type ON ref_media (type_media);",
        "CREATE INDEX IF NOT EXISTS idx_ref_media_couv ON ref_media (couverture);",
        "DELETE FROM ref_media;",
        "INSERT INTO ref_media (" + ", ".join(COLUMNS) + ") VALUES",
    ]
    values = []
    for rec in records:
        vals = []
        for col in COLUMNS:
            v = rec.get(col, "")
            if col == "actif":
                vals.append(sql_lit(bool(rec["actif"])))
            elif col == "priorite_rp":
                vals.append(sql_lit(int(rec["priorite_rp"])))
            else:
                vals.append(sql_lit(v if v is not None else ""))
        values.append("    (" + ", ".join(vals) + ")")
    lines.append(",\n".join(values) + ";\n")
    (HERE / "ref_media.sql").write_text("\n".join(lines), encoding="utf-8")

    # Catalogue = synthèse, pas 5000 lignes
    by = defaultdict(list)
    for rec in records:
        by[(rec["pays_nom"], rec["type_media"], rec["couverture"])].append(rec)
    md = [
        "# Catalogue médias — `ref_media` (étendu)",
        "",
        "Catégories alignées sur la base France : **Web / Print / TV / Radio**, puis **Nationale / Régionale**.",
        "",
        f"**{len(records)} médias** au total.",
        "",
        "## Volumes",
        "",
        "| Pays | Web | Print | TV | Radio | Nationale | Régionale | Total |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cc, nom in PAYS.items():
        subset = [r for r in records if r["pays_code"] == cc]
        if not subset:
            continue
        md.append(
            "| {nom} | {web} | {prt} | {tv} | {rd} | {nat} | {reg} | {tot} |".format(
                nom=nom,
                web=sum(r["type_media"] == "Web" for r in subset),
                prt=sum(r["type_media"] == "Print" for r in subset),
                tv=sum(r["type_media"] == "TV" for r in subset),
                rd=sum(r["type_media"] == "Radio" for r in subset),
                nat=sum(r["couverture"] == "Nationale" for r in subset),
                reg=sum(r["couverture"] == "Régionale" for r in subset),
                tot=len(subset),
            )
        )
    md += ["", "## Titres prioritaires (seed RP)", ""]
    for rec in records:
        if rec["source_liste"] == "SEED" and rec["pays_code"] != "FR":
            md.append(
                f"- **{rec['nom']}** ({rec['pays_nom']}, {rec['type_media']}, {rec['couverture']}) — {rec.get('url','')}"
            )
    md += ["", "## Détail par pays × type × couverture", ""]
    for pays_nom in PAYS.values():
        keys = [k for k in by if k[0] == pays_nom]
        if not keys:
            continue
        md.append(f"### {pays_nom}")
        md.append("")
        for key in sorted(keys):
            recs = by[key]
            md.append(f"**{key[1]} · {key[2]}** — {len(recs)} titres")
            preview = ", ".join(r["nom"] for r in recs[:12])
            more = f" … +{len(recs)-12}" if len(recs) > 12 else ""
            md.append(f"{preview}{more}")
            md.append("")
    (HERE / "CATALOGUE.md").write_text("\n".join(md), encoding="utf-8")


def copy_erc_if_needed() -> None:
    OFFICIAL.mkdir(parents=True, exist_ok=True)
    mapping = {
        "pt_pp.csv": "1zniO1wn8CGV3VeVKD_ne0mFQYXtLt6uUBta7tWkQ4XM.csv",
        "pt_radio.csv": "1eHZiZ1wAsfJu3opwaCHq9w7gQC7s_xCWrLiMwai9Hjk.csv",
        "pt_tv.csv": "1tJ7-at4tfwQwbtlktp4VFtTISmHWb3rB6MDoSoWEV8s.csv",
        "pt_web.csv": "1P8Swh29QmkepztYfPhWyVlghmz4uHzOmToSWOflORZA.csv",
        "pt_agences.csv": "1nMCthu8JeVVXHOBOG-Pn6flAsiNjclMbFm6fkZxUI3k.csv",
    }
    src_dir = Path("/tmp/media-harvest/erc")
    for dest, src_name in mapping.items():
        src = src_dir / src_name
        dst = OFFICIAL / dest
        if src.exists() and not dst.exists():
            dst.write_bytes(src.read_bytes())


def main() -> None:
    copy_erc_if_needed()
    print("seed…")
    records = load_seed()
    print("  ", len(records))
    print("ERC…")
    erc = load_erc()
    print("  ", len(erc))
    records.extend(erc)
    print("Swissdox…")
    try:
        swiss = harvest_swissdox()
        print("  ", len(swiss))
        records.extend(swiss)
    except Exception as exc:
        print("  FAIL", exc)
    print("Wikipedia…")
    wiki = harvest_wikipedia()
    print("  ", len(wiki))
    records.extend(wiki)
    print("merge…")
    merged = merge(records)
    print("  ", len(merged), Counter(r["pays_code"] for r in merged))
    print("  types", Counter(r["type_media"] for r in merged))
    write_outputs(merged)
    print("écrit", HERE)
    from build_oxyhub import main as oxyhub_main

    print("oxyhub…")
    oxyhub_main()


if __name__ == "__main__":
    main()
