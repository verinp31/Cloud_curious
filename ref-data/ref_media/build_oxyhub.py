#!/usr/bin/env python3
"""Écrit ref_media.csv (BE/CH/PT/ES) à partir du harvest existant.

Pas de SQL. Vocabulaire type/famille/thématique/couverture calé sur
OXYHUB_PROD_REF_MEDIA.sql.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from oxyhub_map import (
    COUVERTURE_VALUES,
    CSV_COLUMNS,
    FAMILLE_VALUES,
    PAYS_NOM,
    THEMATIQUE_VALUES,
    TYPE_MEDIA_VALUES,
    build_rows,
)

HERE = Path(__file__).resolve().parent


def write_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_catalogue(rows: list[dict], path: Path) -> None:
    md = [
        "# Catalogue médias BE / CH / PT / ES",
        "",
        "CSV : `ref_media.csv`. Valeurs de type / famille / thématique / couverture "
        "reprises de la base France (`OXYHUB_PROD_REF_MEDIA.sql`).",
        "",
        f"**{len(rows)} médias** (France exclue).",
        "",
        "## Volumes",
        "",
        "| Pays | WEB | PRESSE | TV | RADIO | AGENCES | Nationale | Rég./Dépt. | Internat. | Total |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cc, nom in PAYS_NOM.items():
        if cc == "FR":
            continue
        subset = [r for r in rows if r["pays_code"] == cc]
        if not subset:
            continue
        md.append(
            "| {nom} | {web} | {pr} | {tv} | {rd} | {ag} | {nat} | {reg} | {inter} | {tot} |".format(
                nom=nom,
                web=sum(r["type_media"] == "WEB" for r in subset),
                pr=sum(r["type_media"] == "PRESSE" for r in subset),
                tv=sum(r["type_media"] == "TV" for r in subset),
                rd=sum(r["type_media"] == "RADIO" for r in subset),
                ag=sum(r["type_media"] == "AGENCES" for r in subset),
                nat=sum(r["couverture_geo"] == "Nationale" for r in subset),
                reg=sum(r["couverture_geo"] == "Régionale/Départementale" for r in subset),
                inter=sum(r["couverture_geo"] == "Internationale" for r in subset),
                tot=len(subset),
            )
        )

    md += ["", "## Titres seed (priorité RP)", ""]
    for rec in rows:
        if rec["source_liste"] == "SEED":
            md.append(
                f"- **{rec['nom']}** ({rec['pays_nom']}, {rec['type_media']}, "
                f"{rec['famille_media']}, {rec['couverture_geo']}) — {rec.get('url','')}"
            )

    by = defaultdict(list)
    for rec in rows:
        by[(rec["pays_nom"], rec["type_media"], rec["couverture_geo"])].append(rec)

    md += ["", "## Détail par pays × type × couverture", ""]
    for pays_nom in ("Belgique", "Suisse", "Portugal", "Espagne"):
        keys = [k for k in by if k[0] == pays_nom]
        if not keys:
            continue
        md.append(f"### {pays_nom}")
        md.append("")
        for key in sorted(keys):
            recs = by[key]
            md.append(f"**{key[1]} · {key[2]}** — {len(recs)} titres")
            preview = ", ".join(r["nom"] for r in recs[:10])
            more = f" … +{len(recs)-10}" if len(recs) > 10 else ""
            md.append(f"{preview}{more}")
            md.append("")
    path.write_text("\n".join(md), encoding="utf-8")


def validate(rows: list[dict]) -> list[str]:
    errors = []
    seen = set()
    for rec in rows:
        i = rec["id"]
        if i in seen:
            errors.append(f"id dupliqué {i}")
        seen.add(i)
        if rec["pays_code"] not in {"BE", "CH", "PT", "ES"}:
            errors.append(f"pays {rec['pays_code']} ({i})")
        if rec["type_media"] not in TYPE_MEDIA_VALUES:
            errors.append(f"type {rec['type_media']} ({rec['nom']})")
        if rec["famille_media"] not in FAMILLE_VALUES:
            errors.append(f"famille {rec['famille_media']} ({rec['nom']})")
        if rec["thematique_media"] not in THEMATIQUE_VALUES:
            errors.append(f"thématique {rec['thematique_media']} ({rec['nom']})")
        if rec["couverture_geo"] not in COUVERTURE_VALUES:
            errors.append(f"couverture {rec['couverture_geo']} ({rec['nom']})")
        if not rec["nom"]:
            errors.append(f"nom vide {i}")
    return errors


def main() -> int:
    src = HERE / "ref_media.json"
    records = json.loads(src.read_text(encoding="utf-8"))
    rows = build_rows(records)
    errors = validate(rows)
    if errors:
        print("VALIDATION FAIL", len(errors))
        for err in errors[:30]:
            print(" ", err)
        return 1

    write_csv(rows, HERE / "ref_media.csv")
    write_catalogue(rows, HERE / "CATALOGUE.md")

    print("ok", len(rows))
    print("pays", Counter(r["pays_code"] for r in rows))
    print("types", Counter(r["type_media"] for r in rows))
    print("couv", Counter(r["couverture_geo"] for r in rows))
    print("famille", Counter(r["famille_media"] for r in rows).most_common(8))
    print("écrit", HERE / "ref_media.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
