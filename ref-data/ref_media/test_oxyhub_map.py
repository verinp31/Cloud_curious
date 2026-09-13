#!/usr/bin/env python3
"""Contrats de mapping — sans réseau."""

from __future__ import annotations

import unittest

from oxyhub_map import (
    COUVERTURE_VALUES,
    FAMILLE_VALUES,
    THEMATIQUE_VALUES,
    TYPE_MEDIA_VALUES,
    is_agency,
    map_couverture,
    map_famille,
    map_thematique,
    map_type,
    media_name,
    to_row,
)


def rec(**kwargs):
    base = {
        "nom": "Le Soir",
        "pays_code": "BE",
        "pays_nom": "Belgique",
        "langue": "fr",
        "type_media": "Print",
        "support": "Print",
        "thematique": "Généraliste",
        "couverture": "Nationale",
        "periodicite": "Quotidien",
        "notes": "",
        "url": "https://www.lesoir.be",
        "groupe_media": "Groupe Rossel",
        "ville": "Bruxelles",
        "source_liste": "SEED",
        "priorite_rp": 1,
    }
    base.update(kwargs)
    return base


class MapTests(unittest.TestCase):
    def test_name_keeps_case(self):
        self.assertEqual(media_name("Le Soir"), "Le Soir")
        self.assertEqual(media_name("  El País  "), "El País")

    def test_types(self):
        self.assertEqual(map_type(rec(type_media="Web")), "WEB")
        self.assertEqual(map_type(rec(type_media="Print")), "PRESSE")
        self.assertEqual(map_type(rec(type_media="TV")), "TV")
        self.assertEqual(map_type(rec(type_media="Radio")), "RADIO")
        self.assertEqual(map_type(rec(type_media="Agence de presse", nom="Belga")), "AGENCES")
        self.assertEqual(map_type(rec(nom="Lusa", notes="ERC entreprise noticieuse")), "AGENCES")
        self.assertEqual(map_type(rec(support="Nachrichtenagentur", type_media="Web")), "AGENCES")

    def test_agency_seed_names(self):
        for nom in ("Belga", "EFE", "Keystone-ATS", "Europa Press", "AFP"):
            self.assertTrue(is_agency(rec(nom=nom, type_media="Web")), nom)

    def test_couverture(self):
        self.assertEqual(map_couverture(rec(couverture="Nationale"), "PRESSE"), "Nationale")
        self.assertEqual(
            map_couverture(rec(couverture="Régionale"), "PRESSE"),
            "Régionale/Départementale",
        )
        self.assertEqual(map_couverture(rec(couverture="Nationale"), "AGENCES"), "Nationale")

    def test_famille(self):
        self.assertEqual(
            map_famille(rec(), "PRESSE", "Nationale", "Actualités-Infos Générales"),
            "PQN (Quotidiens nationaux)",
        )
        self.assertEqual(
            map_famille(
                rec(periodicite="Diária"),
                "PRESSE",
                "Régionale/Départementale",
                "Actualités-Infos Générales",
            ),
            "PQR/PQD (Quotidiens régionaux)",
        )
        self.assertEqual(
            map_famille(rec(), "AGENCES", "Nationale", "Actualités-Infos Générales"),
            "Agences de presse",
        )

    def test_thematique(self):
        self.assertEqual(map_thematique(rec(thematique="Généraliste")), "Actualités-Infos Générales")
        self.assertEqual(map_thematique(rec(thematique="Économie")), "Economie - Services")
        self.assertEqual(
            map_thematique(rec(thematique="Informação Especializada", nom="Revista de Medicina")),
            "Médecine",
        )

    def test_csv_row(self):
        row = to_row(rec(), "MED-BE-0001")
        self.assertEqual(row["id"], "MED-BE-0001")
        self.assertEqual(row["nom"], "Le Soir")
        self.assertEqual(row["type_media"], "PRESSE")
        self.assertEqual(row["pays_code"], "BE")
        self.assertTrue(row["url"].startswith("https://"))
        self.assertIn(row["type_media"], TYPE_MEDIA_VALUES)
        self.assertIn(row["famille_media"], FAMILLE_VALUES)
        self.assertIn(row["thematique_media"], THEMATIQUE_VALUES)
        self.assertIn(row["couverture_geo"], COUVERTURE_VALUES)


if __name__ == "__main__":
    unittest.main()
