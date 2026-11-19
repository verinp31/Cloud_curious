"""Candidats, notes et profils fictifs utilisés par l'étude.

Ces vecteurs ne décrivent aucun programme publié. Ils servent à vérifier que les formules
produisent un classement, et que ce classement change quand le profil d'électeur change.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

from algorithme import (
    GRAINE,
    N_SIM_CODAGE,
    N_SIM_POIDS,
    P_BRUIT_CODAGE,
    SIGMA_POIDS,
    alerte_budget,
    citations_insuffisantes,
    contributions,
    kappa_quadratique,
    part_des_domaines,
    part_des_leviers,
    publiable,
    retrait_un_domaine,
    score_candidat,
    score_strict,
    scores_par_domaine,
    sensibilite_codage,
    sensibilite_poids,
    classer,
)
from grille import QUESTIONS, index_questions

# Questions où le pôle 4 est une dépense ou une recette publique supplémentaire.
# Liste fermée, utilisée seulement comme alerte de lecture, pas comme un budget.
QUESTIONS_DEPENSE = (
    23, 25, 28, 30, 31, 32, 33, 34, 37, 38, 43, 48, 50, 51, 53,
    55, 61, 63, 65, 66, 67, 73, 82, 84, 86, 88, 89, 97, 98, 100,
)
QUESTIONS_RECETTE = (9, 10, 11, 12, 14, 17)

CANDIDATS = (
    {"id": "ancrage", "nom": "Candidat A", "etiquette": "Ancrage"},
    {"id": "ouverture", "nom": "Candidat B", "etiquette": "Ouverture"},
    {"id": "equilibre", "nom": "Candidat C", "etiquette": "Équilibre"},
)

# Notes de 0 à 4. None = question absente du corpus fictif.
_ANCRAGE = (
    1, 2, 1, 1, 1, 1, 0, 2,
    0, 1, 0, 1, 1, 3, 3, 1, 1, 1,
    1, 0, 1, 0, 2, 1, 1, 1, 2, 2,
    2, 2, 1, 2, 2, 1, 3, 2,
    2, 2, 1, 1, 2, 1, 2, 2,
    1, 4, 1, 1, 1, 1, 2, 1, 2, 1,
    3, 1, 1, 1, 4,
    3, 1, 0, 1, 2, 4,
    4, 2, 4, 4, 4, 1, 4, 3,
    1, 0, 1, 2, 0, 1,
    0, 1, 1, 3, 4, 4, 3, 4, 1,
    4, 4, 1, 4, 2, 4, 1, 2,
    1, 2, 2, 1,
)
_OUVERTURE = (
    4, 4, 4, 4, 4, 4, 4, 4,
    3, 4, 4, 3, 3, 4, 4, 3, 4, 4,
    4, 4, 4, 4, 4, 4, 3, 4, 4, 4,
    4, 4, 4, 4, 4, 4, 3, 4,
    4, 4, 4, 4, 3, 4, 4, 3,
    4, 2, 4, 4, 4, 4, 4, 4, 4, 4,
    4, 4, 3, 4, 3,
    3, 4, 4, 4, 3, 3,
    2, 4, 1, 1, 1, 4, 1, 4,
    4, 4, 3, 4, 4, 4,
    4, 3, 4, 3, 3, 3, 4, 3, 4,
    4, 3, 4, 2, 4, 4, 4, 4,
    4, 4, 4, 4,
)
_EQUILIBRE = (
    3, 3, 2, None, 3, 2, 2, 3,
    2, 2, 2, 2, None, 3, 3, 2, 2, 2,
    2, 2, 2, 2, 3, 2, 2, 2, 3, 3,
    3, 4, 2, 3, 3, 3, 3, None,
    4, 3, 2, 2, 2, 2, 3, None,
    2, 3, 3, 3, 2, 3, 3, 2, 3, None,
    3, 2, 2, 2, 3,
    3, 2, 2, 2, 3, 3,
    3, 3, 2, 2, None, 2, 3, 3,
    2, 1, 2, 4, 1, 2,
    2, 2, None, 3, 4, 3, 3, 2, 2,
    3, 3, 2, 4, None, 3, 2, 3,
    2, 3, 3, 2,
)

_CIBLES_SERVICES = (
    4, 4, 3, 4, 4, 4, 4, 4,
    3, 4, 4, 3, 2, 4, 4, 4, 4, 4,
    4, 4, 4, 4, 4, 4, 3, 4, 4, 4,
    4, 4, 4, 4, 4, 4, 4, 4,
    4, 4, 4, 3, 3, 4, 4, 4,
    4, 3, 4, 4, 4, 4, 4, 4, 4, 4,
    4, 4, 3, 4, 4,
    4, 4, 4, 4, 4, 3,
    3, 4, 1, 1, 1, 4, 1, 4,
    3, 4, 3, 4, 3, 4,
    4, 3, 4, 3, 3, 4, 4, 3, 4,
    4, 3, 4, 3, 4, 4, 4, 4,
    4, 4, 4, 4,
)
_CIBLES_SURETE = (
    1, 2, 1, 1, 1, 2, 1, 2,
    0, 1, 0, 1, 1, 3, 4, 1, 1, 1,
    2, 1, 1, 0, 2, 1, 1, 1, 3, 2,
    2, 2, 1, 2, 2, 2, 4, 2,
    2, 2, 1, 1, 2, 1, 2, 2,
    2, 4, 1, 2, 1, 1, 2, 1, 2, 1,
    3, 1, 1, 1, 4,
    3, 1, 0, 1, 2, 4,
    4, 3, 4, 4, 4, 1, 4, 3,
    1, 0, 1, 2, 0, 1,
    0, 1, 1, 3, 4, 4, 3, 4, 1,
    4, 4, 1, 4, 2, 4, 1, 2,
    1, 2, 3, 1,
)

POIDS_SERVICES = {
    "INST": 0.6, "FISC": 1.2, "TRAV": 1.3, "SANT": 1.8, "EDUC": 1.6,
    "CLIM": 2.0, "AGRI": 1.0, "LOGT": 1.2, "SECU": 0.5, "IMMI": 0.7,
    "EURO": 0.9, "ECON": 1.0, "SOCI": 1.8,
}
POIDS_SURETE = {
    "INST": 1.0, "FISC": 1.6, "TRAV": 1.3, "SANT": 0.7, "EDUC": 0.6,
    "CLIM": 0.4, "AGRI": 0.9, "LOGT": 0.8, "SECU": 2.2, "IMMI": 2.0,
    "EURO": 1.4, "ECON": 1.2, "SOCI": 0.5,
}
POIDS_CENTRE = {code: 1.0 for code in POIDS_SERVICES}


def _cibles_a_mi_chemin():
    """Cibles construites après le codage : milieu arrondi de A et de C.

    Ce vecteur est un banc d'essai. Il violerait la règle de pré-enregistrement
    s'il était présenté comme le profil d'un électeur.
    """
    valeurs = []
    for note_a, note_c in zip(_ANCRAGE, _EQUILIBRE):
        if note_c is None:
            valeurs.append(note_a)
        else:
            valeurs.append(int(round((note_a + note_c) / 2)))
    return tuple(valeurs)


_CIBLES_SERRE = _cibles_a_mi_chemin()

PROFILS = (
    {
        "id": "services",
        "nom": "Services publics et climat",
        "court": "Services et climat",
        "cibles": _CIBLES_SERVICES,
        "poids_domaine": POIDS_SERVICES,
        "intention": (
            "Cibles proches des pôles de services publics, de redistribution et de transition "
            "climatique. Le nucléaire est visé à 3, pas à l'extrême : ce profil ne demande pas "
            "la sortie du parc. La défense est visée au maintien modernisé, pas à une baisse."
        ),
    },
    {
        "id": "surete",
        "nom": "Sûreté et pouvoir d'achat",
        "court": "Sûreté",
        "cibles": _CIBLES_SURETE,
        "poids_domaine": POIDS_SURETE,
        "intention": (
            "Cibles proches des pôles de baisse des prélèvements, de contrôle de l'immigration, "
            "de réponse pénale ferme et d'effort de défense. Le salaire minimum est visé au milieu, "
            "pas à la baisse : le pouvoir d'achat n'est pas traduit par une seule question."
        ),
    },
    {
        "id": "centre",
        "nom": "Cibles centristes équipondérées",
        "court": "Centre équipondéré",
        "cibles": (2,) * 100,
        "poids_domaine": POIDS_CENTRE,
        "intention": (
            "Chaque cible est au milieu de l'échelle, et chaque question a le même poids. "
            "Ce profil récompense les programmes qui restent au centre ou qui se taisent, "
            "parce que le code 2 sert aux deux. Ce n'est pas un profil politiquement neutre."
        ),
    },
    {
        "id": "serre",
        "nom": "Banc d'essai : cibles à mi-chemin de A et de C",
        "court": "Banc d'essai",
        "cibles": _CIBLES_SERRE,
        "poids_domaine": POIDS_CENTRE,
        "banc": True,
        "intention": (
            "Les cibles sont le milieu arrondi des notes de A et de C, calculé après le codage. "
            "Les poids sont égaux. Ce n'est pas un profil d'électeur : la méthode interdit de "
            "fabriquer les cibles une fois les notes connues. Le banc sert à voir le classement "
            "se défaire quand l'écart de tête est inférieur à un point."
        ),
    },
)


def _vecteur_en_dict(valeurs):
    if len(valeurs) != 100:
        raise ValueError(f"un vecteur doit avoir 100 valeurs, pas {len(valeurs)}")
    return {index + 1: valeur for index, valeur in enumerate(valeurs)}


def operationnalite_exemple(candidat, note):
    """Règle d'illustration seulement. Un vrai codage lit l'instrument dans le texte."""
    if note is None:
        return None
    if note == 2:
        return 0
    if candidat == "equilibre":
        return 1 if note in (0, 4) else 0
    return 2 if note in (0, 4) else 1


def notes_par_id():
    bruts = {
        "ancrage": _ANCRAGE,
        "ouverture": _OUVERTURE,
        "equilibre": _EQUILIBRE,
    }
    return {cle: _vecteur_en_dict(valeurs) for cle, valeurs in bruts.items()}


def operationnalites_par_id(notes=None):
    notes = notes_par_id() if notes is None else notes
    return {
        cle: {qid: operationnalite_exemple(cle, note) for qid, note in vecteur.items()}
        for cle, vecteur in notes.items()
    }


def profil_par_id(profil):
    cibles = _vecteur_en_dict(profil["cibles"])
    poids = {}
    for question in QUESTIONS:
        poids[question["id"]] = float(profil["poids_domaine"][question["domaine"]])
    return cibles, poids


def nom_affiche(candidat_id):
    for candidat in CANDIDATS:
        if candidat["id"] == candidat_id:
            return f"{candidat['nom']} — {candidat['etiquette']}"
    return candidat_id


def simuler_second_codage(reference, p_un_cran, p_deux_crans, graine):
    generateur = random.Random(graine)
    second = []
    for note in reference:
        tirage = generateur.random()
        if tirage < p_deux_crans:
            delta = -2 if generateur.random() < 0.5 else 2
        elif tirage < p_deux_crans + p_un_cran:
            delta = -1 if generateur.random() < 0.5 else 1
        else:
            delta = 0
        second.append(min(4, max(0, note + delta)))
    return second


def _ligne_candidat(candidat_id, notes, cibles, poids, operationnalite):
    calcul = score_candidat(notes, cibles, poids, operationnalite)
    strict = score_strict(notes, cibles, poids, operationnalite)
    return {
        "id": candidat_id,
        "nom": nom_affiche(candidat_id),
        "score": calcul["score"],
        "couverture": calcul["couverture"],
        "n_observe": calcul["n_observe"],
        "score_strict": strict["score"],
        "precision": calcul["precision"],
        "score_specifie": calcul["score_specifie"],
        "domaines": scores_par_domaine(notes, cibles, poids, operationnalite),
        "budget": alerte_budget(notes, QUESTIONS_DEPENSE, QUESTIONS_RECETTE),
    }


def evaluer_profil(profil, notes, operationnalites, avec_simulation=True):
    cibles, poids = profil_par_id(profil)
    notes_nommees = {nom_affiche(cle): vecteur for cle, vecteur in notes.items()}
    op_nommees = {nom_affiche(cle): vecteur for cle, vecteur in operationnalites.items()}
    lignes = [
        _ligne_candidat(cle, notes[cle], cibles, poids, operationnalites[cle])
        for cle in notes
    ]
    ordre = classer(lignes)
    premier = ordre[0]["nom"]
    second = ordre[1]["nom"]
    id_premier = ordre[0]["id"]
    id_second = ordre[1]["id"]
    ecarts = contributions(notes[id_premier], notes[id_second], cibles, poids)
    ecarts_tries = sorted(ecarts, key=lambda ligne: abs(ligne["contribution"]), reverse=True)
    somme = sum(ligne["contribution"] for ligne in ecarts)
    face_a_face = contributions(notes["ouverture"], notes["ancrage"], cibles, poids)
    face_a_face = sorted(face_a_face, key=lambda ligne: ligne["contribution"], reverse=True)
    retraits = retrait_un_domaine(notes_nommees, cibles, poids, op_nommees)
    domaines_qui_changent = [ligne["nom"] for ligne in retraits if ligne["premier"] != premier]
    resultat = {
        "id": profil["id"],
        "nom": profil["nom"],
        "court": profil["court"],
        "intention": profil["intention"],
        "ordre": ordre,
        "premier": premier,
        "second": second,
        "ecart_tete": ordre[0]["score"] - ordre[1]["score"],
        "contributions": ecarts_tries,
        "somme_contributions": somme,
        "face_a_face": face_a_face,
        "parts_domaines": part_des_domaines(poids),
        "parts_leviers": part_des_leviers(poids),
        "retraits": retraits,
        "domaines_qui_changent": domaines_qui_changent,
        "couverture_min": min(ligne["couverture"] for ligne in ordre),
    }
    if avec_simulation:
        frequence_poids = sensibilite_poids(
            notes_nommees, cibles, poids, operationnalite_par_candidat=op_nommees
        )
        frequence_codage = sensibilite_codage(
            notes_nommees, cibles, poids, operationnalite_par_candidat=op_nommees
        )
        resultat["stabilite_poids"] = frequence_poids[premier]
        resultat["stabilite_codage"] = frequence_codage[premier]
        resultat["frequence_poids"] = frequence_poids
        resultat["frequence_codage"] = frequence_codage
        ok, motifs = publiable(
            resultat["couverture_min"],
            resultat["stabilite_poids"],
            resultat["stabilite_codage"],
            kappa=None,
        )
        resultat["publiable"] = ok
        resultat["motifs_blocage"] = motifs
    return resultat


def demo_kappa(notes):
    reference = [notes["ancrage"][i] for i in range(1, 101)]
    acceptable = simuler_second_codage(reference, 0.28, 0.08, 7)
    refuse = simuler_second_codage(reference, 0.10, 0.55, 3)
    return {
        "acceptable": kappa_quadratique(reference, acceptable),
        "refuse": kappa_quadratique(reference, refuse),
        "parametres_acceptables": "28 % de décalages d'un cran et 8 % de décalages de deux crans",
        "parametres_refuses": "10 % de décalages d'un cran et 55 % de décalages de deux crans",
    }


def empreinte_grille():
    import hashlib
    import json
    payload = json.dumps(QUESTIONS, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def ecrire_modeles(dossier):
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    notes = notes_par_id()
    ops = operationnalites_par_id(notes)
    chemin_notes = dossier / "notes_exemple.csv"
    with chemin_notes.open("w", newline="", encoding="utf-8") as fichier:
        ecrivain = csv.DictWriter(
            fichier,
            fieldnames=["candidat", "question", "note", "operationnalite", "citation"],
        )
        ecrivain.writeheader()
        for cle, vecteur in notes.items():
            for qid in range(1, 101):
                note = vecteur[qid]
                ecrivain.writerow({
                    "candidat": cle,
                    "question": qid,
                    "note": "" if note is None else note,
                    "operationnalite": "" if ops[cle][qid] is None else ops[cle][qid],
                    "citation": "FICTIF",
                })
    chemins_profils = {}
    for profil in PROFILS:
        cibles, poids = profil_par_id(profil)
        chemin = dossier / f"profil_{profil['id']}.csv"
        with chemin.open("w", newline="", encoding="utf-8") as fichier:
            ecrivain = csv.DictWriter(fichier, fieldnames=["question", "cible", "poids"])
            ecrivain.writeheader()
            for qid in range(1, 101):
                ecrivain.writerow({
                    "question": qid,
                    "cible": cibles[qid],
                    "poids": f"{poids[qid]:.1f}",
                })
        chemins_profils[profil["id"]] = chemin
    return chemin_notes, chemins_profils


def controler_exemple(notes, evaluations, kappa):
    manquants = [qid for qid, note in notes["equilibre"].items() if note is None]
    if len(manquants) != 8:
        raise ValueError(f"le candidat C devrait laisser 8 questions vides, pas {len(manquants)}")
    for cle in ("ancrage", "ouverture"):
        if any(note is None for note in notes[cle].values()):
            raise ValueError(f"{cle} ne devrait pas avoir de question vide")
    tetes = [evaluation["premier"] for evaluation in evaluations]
    if len(set(tetes)) < 2:
        raise ValueError("l'exemple ne montre pas que le profil change la tête du classement")
    if not evaluations[0]["premier"].startswith("Candidat B"):
        raise ValueError(f"profil services, tête inattendue : {evaluations[0]['premier']}")
    if not evaluations[1]["premier"].startswith("Candidat A"):
        raise ValueError(f"profil sûreté, tête inattendue : {evaluations[1]['premier']}")
    if not evaluations[2]["premier"].startswith("Candidat C"):
        raise ValueError(f"profil centre, tête inattendue : {evaluations[2]['premier']}")
    if kappa["acceptable"]["kappa"] < 0.60:
        raise ValueError("le double codage de démonstration acceptable est sous le seuil")
    if kappa["refuse"]["kappa"] >= 0.60:
        raise ValueError("le double codage refusé devrait être sous le seuil")
    centre = evaluations[2]
    specifie = sorted(centre["ordre"], key=lambda ligne: -ligne["score_specifie"])
    if specifie[0]["id"] != "ancrage":
        raise ValueError("le score spécifié du profil centriste devrait placer A en tête")
    if centre["ordre"][0]["id"] != "equilibre":
        raise ValueError("le score de proximité du profil centriste devrait placer C en tête")
    banc = evaluations[3]
    if banc["ecart_tete"] >= 1:
        raise ValueError("le banc d'essai devrait avoir un écart de tête inférieur à un point")
    strict = sorted(banc["ordre"], key=lambda ligne: -ligne["score_strict"])
    if strict[0]["id"] == banc["ordre"][0]["id"]:
        raise ValueError("le score strict du banc d'essai devrait changer la tête du classement")
    if "stabilite_codage" in banc and banc["stabilite_codage"] >= 0.70:
        raise ValueError("le bruit de codage du banc d'essai devrait rester sous le seuil de stabilité")
    # Le fichier d'exemple ne doit pas passer pour une source.
    faux_problemes = citations_insuffisantes(notes, {cle: {i: "FICTIF" for i in range(1, 101)} for cle in notes})
    if len(faux_problemes) < 50:
        raise ValueError("le contrôle des citations n'a pas rejeté le libellé FICTIF")


def tout_calculer(avec_simulation=True):
    notes = notes_par_id()
    operationnalites = operationnalites_par_id(notes)
    evaluations = [
        evaluer_profil(profil, notes, operationnalites, avec_simulation=avec_simulation)
        for profil in PROFILS
    ]
    kappa = demo_kappa(notes)
    controler_exemple(notes, evaluations, kappa)
    return {
        "notes": notes,
        "operationnalites": operationnalites,
        "evaluations": evaluations,
        "kappa": kappa,
        "empreinte": empreinte_grille(),
        "questions": index_questions(),
        "constantes": {
            "graine": GRAINE,
            "n_poids": N_SIM_POIDS,
            "n_codage": N_SIM_CODAGE,
            "sigma": SIGMA_POIDS,
            "bruit": P_BRUIT_CODAGE,
        },
    }


if __name__ == "__main__":
    calculs = tout_calculer()
    for evaluation in calculs["evaluations"]:
        print(evaluation["nom"])
        for ligne in evaluation["ordre"]:
            print(
                f"  {ligne['nom']}: {ligne['score']:.2f} "
                f"couverture={ligne['couverture']:.2f} "
                f"strict={ligne['score_strict']:.2f} "
                f"précision={ligne['precision']:.1f} "
                f"spécifié={ligne['score_specifie']:.1f}"
            )
        print(
            f"  stabilité poids={evaluation['stabilite_poids']:.3f} "
            f"codage={evaluation['stabilite_codage']:.3f}"
        )
    print(
        "kappa acceptable",
        round(calculs["kappa"]["acceptable"]["kappa"], 3),
        "kappa refusé",
        round(calculs["kappa"]["refuse"]["kappa"], 3),
    )
