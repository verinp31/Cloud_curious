"""Algorithme de comparaison de programmes présidentiels.

La note x situe un programme entre le pôle 0 et le pôle 4 d'une question.
La cible t situe la préférence déclarée de l'électeur sur la même échelle.
Le poids w dit l'importance de la question. Le score est la moyenne pondérée
des proximités, ramenée entre 0 et 100.

Lorsque toutes les cibles valent 4, la proximité d'une note x est x/4, et le
score redevient la moyenne pondérée classique des notes. Les cibles autres
que 4 servent à ne pas faire passer un pôle politique pour une évidence.

Dépendances : bibliothèque standard uniquement.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from collections import Counter
from pathlib import Path

from grille import QUESTIONS, index_questions, par_domaine

NOTE_MIN = 0
NOTE_MAX = 4
ECART_MAX = NOTE_MAX - NOTE_MIN

# Conventions de publication de cette étude. Ce sont des seuils déclarés, pas des lois.
SEUIL_KAPPA = 0.60
SEUIL_STABILITE = 0.70
SEUIL_COUVERTURE = 0.80
SIGMA_POIDS = 0.25
N_SIM_POIDS = 4000
P_BRUIT_CODAGE = 0.15
N_SIM_CODAGE = 2000
GRAINE = 20261119

# Une citation qui porte ce libellé n'est pas une source.
CITATIONS_REFUSEES = {"", "fictif"}


class ErreurMethode(ValueError):
    pass


def _verifier_echelle(valeur, nom):
    if isinstance(valeur, bool) or not isinstance(valeur, int):
        raise ErreurMethode(f"{nom} doit être un entier entre {NOTE_MIN} et {NOTE_MAX}")
    if valeur < NOTE_MIN or valeur > NOTE_MAX:
        raise ErreurMethode(f"{nom} hors échelle : {valeur}")


def proximite(note, cible):
    """1 quand la note est sur la cible, 0 quand elle est à l'autre bout de l'échelle."""
    _verifier_echelle(note, "note")
    _verifier_echelle(cible, "cible")
    return 1.0 - abs(note - cible) / ECART_MAX


def facteur_precision(operationnalite):
    """0,5 pour un choix sans instrument, 1 pour un choix pleinement spécifié.

    operationnalite vaut 0, 1 ou 2. Le facteur vaut 0,5 + operationnalite/4.
    """
    if operationnalite not in (0, 1, 2):
        raise ErreurMethode(f"opérationnalité hors échelle : {operationnalite}")
    return 0.5 + operationnalite / 4.0


def _poids_utiles(poids):
    if not poids:
        raise ErreurMethode("aucun poids")
    total = 0.0
    for cle, valeur in poids.items():
        if valeur < 0:
            raise ErreurMethode(f"poids négatif pour la question {cle}")
        total += valeur
    if total <= 0:
        raise ErreurMethode("la somme des poids est nulle")
    return total


def score_candidat(notes, cibles, poids, operationnalite=None, imputation=None):
    """Calcule le score d'un candidat.

    notes : question -> note 0..4, ou None si la question est hors corpus.
    cibles, poids : question -> valeur, pour le même ensemble de questions.
    operationnalite : question -> 0, 1 ou 2, facultatif.
    imputation : None pour écarter les questions absentes et renormaliser ;
    "proximite_nulle" pour les compter comme une proximité de 0.

    Le code 2 (silence ou milieu explicite) est une note observée, pas une absence.
    """
    if imputation not in (None, "proximite_nulle"):
        raise ErreurMethode(f"imputation inconnue : {imputation}")
    questions = set(cibles) | set(poids)
    if set(notes) != set(cibles) or set(notes) != set(poids):
        raise ErreurMethode("notes, cibles et poids ne portent pas sur les mêmes questions")
    if operationnalite is not None and set(operationnalite) != set(notes):
        raise ErreurMethode("l'opérationnalité ne porte pas sur les mêmes questions")
    for qid, cible in cibles.items():
        _verifier_echelle(cible, f"cible {qid}")
    total_poids = _poids_utiles(poids)

    somme = 0.0
    somme_specifiee = 0.0
    somme_precision = 0.0
    poids_observe = 0.0
    poids_precision = 0.0
    n_observe = 0
    peut_specifier = operationnalite is not None

    for qid in questions:
        w = poids[qid]
        if w == 0:
            continue
        note = notes[qid]
        if note is None and imputation is None:
            continue
        if note is None:
            pi = 0.0
            facteur = None
        else:
            pi = proximite(note, cibles[qid])
            if peut_specifier and operationnalite[qid] is None:
                raise ErreurMethode(f"opérationnalité absente pour la question observée {qid}")
            facteur = facteur_precision(operationnalite[qid]) if peut_specifier else None
        somme += w * pi
        poids_observe += w
        n_observe += 1
        if facteur is not None:
            somme_specifiee += w * pi * facteur
            # La précision se mesure sur les questions où le programme a pris parti.
            if note is not None and note != 2:
                somme_precision += w * (operationnalite[qid] / 2.0)
                poids_precision += w

    if n_observe == 0 or poids_observe == 0:
        return {
            "score": None,
            "score_strict": None,
            "score_specifie": None,
            "precision": None,
            "couverture": 0.0,
            "poids_observe": 0.0,
            "poids_total": total_poids,
            "n_observe": 0,
        }

    couverture = poids_observe / total_poids
    score = 100.0 * somme / poids_observe
    resultat = {
        "score": score,
        "score_specifie": (100.0 * somme_specifiee / poids_observe) if peut_specifier else None,
        "precision": (100.0 * somme_precision / poids_precision) if poids_precision else None,
        "couverture": couverture,
        "poids_observe": poids_observe,
        "poids_total": total_poids,
        "n_observe": n_observe,
    }
    return resultat


def score_strict(notes, cibles, poids, operationnalite=None):
    """Même formule, en imputant une proximité nulle aux questions absentes."""
    return score_candidat(
        notes, cibles, poids, operationnalite=operationnalite, imputation="proximite_nulle"
    )


def scores_par_domaine(notes, cibles, poids, operationnalite=None):
    sorties = []
    for groupe in par_domaine():
        ids = [q["id"] for q in groupe["questions"]]
        partiel_notes = {i: notes[i] for i in ids}
        partiel_cibles = {i: cibles[i] for i in ids}
        partiel_poids = {i: poids[i] for i in ids}
        partiel_op = None if operationnalite is None else {i: operationnalite[i] for i in ids}
        ligne = score_candidat(partiel_notes, partiel_cibles, partiel_poids, partiel_op)
        ligne["code"] = groupe["code"]
        ligne["nom"] = groupe["nom"]
        sorties.append(ligne)
    return sorties


def classer(resultats):
    """resultats : liste de dicts possédant nom, score, couverture. Ordre décroissant."""

    def cle(ligne):
        score = ligne["score"]
        if score is None:
            return (1, 0.0, ligne["nom"])
        return (0, -score, -ligne.get("couverture", 0.0), ligne["nom"])

    return sorted(resultats, key=cle)


def contributions(notes_a, notes_b, cibles, poids):
    """Écart de proximité pondérée, question par question.

    La somme des contributions, multipliée par 100 et divisée par la somme des poids
    des questions observées chez les deux, égale l'écart des scores calculés sur
    cette intersection. Si les couvertures diffèrent, ce n'est pas l'écart des scores
    renormalisés sur des ensembles différents.
    """
    if set(notes_a) != set(notes_b) or set(notes_a) != set(cibles) or set(notes_a) != set(poids):
        raise ErreurMethode("contributions : ensembles de questions différents")
    lignes = []
    for qid in sorted(notes_a):
        if notes_a[qid] is None or notes_b[qid] is None:
            continue
        if poids[qid] == 0:
            continue
        pi_a = proximite(notes_a[qid], cibles[qid])
        pi_b = proximite(notes_b[qid], cibles[qid])
        lignes.append({
            "question": qid,
            "poids": poids[qid],
            "proximite_a": pi_a,
            "proximite_b": pi_b,
            "contribution": poids[qid] * (pi_a - pi_b),
        })
    return lignes


def retrait_un_domaine(notes_par_candidat, cibles, poids, operationnalite_par_candidat=None):
    """Recalcule le classement en annulant, tour à tour, le poids de chaque domaine."""
    sorties = []
    for groupe in par_domaine():
        ids = {q["id"] for q in groupe["questions"]}
        poids_reduit = {i: (0.0 if i in ids else w) for i, w in poids.items()}
        if sum(poids_reduit.values()) <= 0:
            continue
        lignes = []
        for nom, notes in notes_par_candidat.items():
            op = None if operationnalite_par_candidat is None else operationnalite_par_candidat[nom]
            calcul = score_candidat(notes, cibles, poids_reduit, op)
            lignes.append({"nom": nom, "score": calcul["score"], "couverture": calcul["couverture"]})
        ordre = classer(lignes)
        sorties.append({
            "code": groupe["code"],
            "nom": groupe["nom"],
            "premier": ordre[0]["nom"],
            "score": ordre[0]["score"],
        })
    return sorties


def _scores_simules(notes_par_candidat, cibles, poids, operationnalite_par_candidat=None):
    lignes = []
    for nom, notes in notes_par_candidat.items():
        op = None if operationnalite_par_candidat is None else operationnalite_par_candidat[nom]
        calcul = score_candidat(notes, cibles, poids, op)
        lignes.append({"nom": nom, "score": calcul["score"], "couverture": calcul["couverture"]})
    return classer(lignes)


def sensibilite_poids(notes_par_candidat, cibles, poids, n=N_SIM_POIDS, sigma=SIGMA_POIDS,
                      graine=GRAINE, operationnalite_par_candidat=None):
    """Multiplie chaque poids par exp(sigma × loi normale), puis renormalise par la formule.

    Les poids nuls le restent. Retourne la fréquence à laquelle chaque candidat est seul en tête.
    """
    rng = random.Random(graine)
    victoires = Counter()
    egalites = 0
    for _ in range(n):
        perturbe = {}
        for qid, w in poids.items():
            if w <= 0:
                perturbe[qid] = 0.0
            else:
                perturbe[qid] = w * math.exp(sigma * rng.gauss(0.0, 1.0))
        ordre = _scores_simules(
            notes_par_candidat, cibles, perturbe, operationnalite_par_candidat
        )
        if ordre[0]["score"] is None:
            continue
        if len(ordre) > 1 and abs(ordre[0]["score"] - ordre[1]["score"]) < 1e-9:
            egalites += 1
            continue
        victoires[ordre[0]["nom"]] += 1
    frequences = {nom: victoires[nom] / n for nom in notes_par_candidat}
    frequences["_egalites"] = egalites / n
    return frequences


def sensibilite_codage(notes_par_candidat, cibles, poids, n=N_SIM_CODAGE, probabilite=P_BRUIT_CODAGE,
                       graine=GRAINE + 1, operationnalite_par_candidat=None):
    """Décale, avec une probabilité donnée, chaque note observée de +1 ou de -1, dans les bornes.

    Ce bruit figure un désaccord de codage d'un cran. Il ne remplace pas l'arbitrage des écarts
    de deux crans ou plus, qui doit avoir lieu avant de figer la matrice.
    """
    rng = random.Random(graine)
    victoires = Counter()
    egalites = 0
    questions = list(next(iter(notes_par_candidat.values())).keys())
    for _ in range(n):
        notes_bruitees = {}
        for nom, notes in notes_par_candidat.items():
            bruit = {}
            for qid in questions:
                note = notes[qid]
                if note is None or rng.random() >= probabilite:
                    bruit[qid] = note
                else:
                    decalage = -1 if rng.random() < 0.5 else 1
                    bruit[qid] = min(NOTE_MAX, max(NOTE_MIN, note + decalage))
            notes_bruitees[nom] = bruit
        ordre = _scores_simules(
            notes_bruitees, cibles, poids, operationnalite_par_candidat
        )
        if ordre[0]["score"] is None:
            continue
        if len(ordre) > 1 and abs(ordre[0]["score"] - ordre[1]["score"]) < 1e-9:
            egalites += 1
            continue
        victoires[ordre[0]["nom"]] += 1
    frequences = {nom: victoires[nom] / n for nom in notes_par_candidat}
    frequences["_egalites"] = egalites / n
    return frequences


def kappa_quadratique(codage_a, codage_b):
    """Kappa de Cohen, pondéré par le carré de l'écart, sur l'échelle 0..4.

    Les paires dont l'un des codes est absent sont écartées.
    """
    paires = [(a, b) for a, b in zip(codage_a, codage_b) if a is not None and b is not None]
    if len(paires) < 2:
        raise ErreurMethode("pas assez de paires pour un kappa")
    k = NOTE_MAX - NOTE_MIN + 1
    observe = [[0.0 for _ in range(k)] for _ in range(k)]
    for a, b in paires:
        _verifier_echelle(a, "code A")
        _verifier_echelle(b, "code B")
        observe[a][b] += 1.0
    n = float(len(paires))
    marges_a = [sum(observe[i][j] for j in range(k)) for i in range(k)]
    marges_b = [sum(observe[i][j] for i in range(k)) for j in range(k)]
    numerateur = 0.0
    denominateur = 0.0
    accord = 0.0
    for i in range(k):
        for j in range(k):
            poids_ecart = ((i - j) ** 2) / (ECART_MAX ** 2)
            attendu = marges_a[i] * marges_b[j] / n
            numerateur += poids_ecart * observe[i][j]
            denominateur += poids_ecart * attendu
        accord += observe[i][i]
    if denominateur == 0:
        kappa = 1.0
    else:
        kappa = 1.0 - numerateur / denominateur
    return {
        "kappa": kappa,
        "n": int(n),
        "accord_brut": accord / n,
    }


def publiable(couverture_min, stabilite_poids, stabilite_codage, kappa):
    """Un classement ne s'expose que si les quatre conditions de la méthode sont tenues."""
    motifs = []
    if couverture_min is None or couverture_min < SEUIL_COUVERTURE:
        motifs.append("couverture")
    if stabilite_poids is None or stabilite_poids < SEUIL_STABILITE:
        motifs.append("stabilite_poids")
    if stabilite_codage is None or stabilite_codage < SEUIL_STABILITE:
        motifs.append("stabilite_codage")
    if kappa is None or kappa < SEUIL_KAPPA:
        motifs.append("kappa")
    return (len(motifs) == 0, motifs)


def alerte_budget(notes, questions_depense, questions_recette):
    """Écart moyen de position entre des questions de dépense et des questions de recette.

    Ce n'est pas un chiffrage budgétaire. Un écart positif veut dire que le programme
    se place plus haut sur les pôles de dépense retenus que sur les pôles de recette retenus.
    """

    def moyenne(ids):
        valeurs = [notes[i] for i in ids if notes[i] is not None]
        if not valeurs:
            return None
        return sum(valeurs) / len(valeurs)

    dep = moyenne(questions_depense)
    rec = moyenne(questions_recette)
    if dep is None or rec is None:
        return None
    return {"depense": dep, "recette": rec, "ecart": dep - rec}


def part_des_leviers(poids, questions=None):
    questions = QUESTIONS if questions is None else questions
    sommes = {}
    total = 0.0
    for q in questions:
        w = poids[q["id"]]
        sommes[q["levier"]] = sommes.get(q["levier"], 0.0) + w
        total += w
    if total <= 0:
        raise ErreurMethode("poids nuls")
    return {levier: valeur / total for levier, valeur in sommes.items()}


def part_des_domaines(poids):
    parts = []
    total = sum(poids.values())
    for groupe in par_domaine():
        somme = sum(poids[q["id"]] for q in groupe["questions"])
        parts.append({
            "code": groupe["code"],
            "nom": groupe["nom"],
            "questions": len(groupe["questions"]),
            "part": somme / total,
        })
    return parts


# --- Fichiers et ligne de commande ---


def lire_notes(chemin):
    """CSV : candidat, question, note, citation, operationnalite (facultative)."""
    notes = {}
    citations = {}
    operationnalite = {}
    a_operationnalite = False
    with Path(chemin).open(newline="", encoding="utf-8") as fichier:
        lecteur = csv.DictReader(fichier)
        colonnes = set(lecteur.fieldnames or [])
        requises = {"candidat", "question", "note"}
        if not requises <= colonnes:
            raise ErreurMethode(f"colonnes manquantes dans {chemin} : {requises - colonnes}")
        a_operationnalite = "operationnalite" in colonnes
        for ligne in lecteur:
            nom = ligne["candidat"].strip()
            qid = int(ligne["question"])
            brut = ligne["note"].strip()
            note = None if brut == "" else int(brut)
            if note is not None:
                _verifier_echelle(note, f"note {nom} {qid}")
            notes.setdefault(nom, {})[qid] = note
            citations.setdefault(nom, {})[qid] = (ligne.get("citation") or "").strip()
            if a_operationnalite:
                brut_op = (ligne.get("operationnalite") or "").strip()
                if note is None:
                    op = None
                elif brut_op == "":
                    raise ErreurMethode(f"opérationnalité manquante : {nom} question {qid}")
                else:
                    op = int(brut_op)
                    if op not in (0, 1, 2):
                        raise ErreurMethode(f"opérationnalité hors échelle : {nom} {qid}")
                operationnalite.setdefault(nom, {})[qid] = op
    return notes, citations, (operationnalite if a_operationnalite else None)


def lire_profil(chemin):
    """CSV : question, cible, poids."""
    cibles = {}
    poids = {}
    with Path(chemin).open(newline="", encoding="utf-8") as fichier:
        lecteur = csv.DictReader(fichier)
        colonnes = set(lecteur.fieldnames or [])
        if not {"question", "cible", "poids"} <= colonnes:
            raise ErreurMethode(f"colonnes manquantes dans {chemin}")
        for ligne in lecteur:
            qid = int(ligne["question"])
            cible = int(ligne["cible"])
            _verifier_echelle(cible, f"cible {qid}")
            cibles[qid] = cible
            poids[qid] = float(ligne["poids"].replace(",", "."))
    return cibles, poids


def citations_insuffisantes(notes, citations):
    """Une note autre que 2 doit renvoyer à un passage. Le silence (2) doit être tracé aussi,
    mais le contrôle bloque d'abord les prises de position sans source, et refuse le mot FICTIF.
    """
    problemes = []
    for nom, vecteur in notes.items():
        for qid, note in vecteur.items():
            if note is None or note == 2:
                continue
            source = citations.get(nom, {}).get(qid, "").strip()
            if source.casefold() in CITATIONS_REFUSEES:
                problemes.append(f"{nom} question {qid}")
    return problemes


def ecrire_resultats(chemin, lignes):
    with Path(chemin).open("w", newline="", encoding="utf-8") as fichier:
        colonnes = ["candidat", "score", "couverture", "score_strict", "precision", "score_specifie"]
        ecrivain = csv.DictWriter(fichier, fieldnames=colonnes)
        ecrivain.writeheader()
        for ligne in lignes:
            ecrivain.writerow({cle: ligne.get(cle, "") for cle in colonnes})


def commander_scorer(args):
    notes, citations, operationnalite = lire_notes(args.notes)
    cibles, poids = lire_profil(args.profil)
    attendus = {q["id"] for q in QUESTIONS}
    if set(cibles) != attendus:
        raise ErreurMethode("le profil ne couvre pas exactement les questions 1 à 100")
    for nom, vecteur in notes.items():
        if set(vecteur) != attendus:
            raise ErreurMethode(f"{nom} ne couvre pas exactement les questions 1 à 100")
    if args.exiger_citations:
        problemes = citations_insuffisantes(notes, citations)
        if problemes:
            raise ErreurMethode(
                "citations manquantes ou fictives pour : " + ", ".join(problemes[:12])
            )
    lignes = []
    for nom in sorted(notes):
        op = None if operationnalite is None else operationnalite[nom]
        calcul = score_candidat(notes[nom], cibles, poids, op)
        strict = score_strict(notes[nom], cibles, poids, op)
        lignes.append({
            "nom": nom,
            "candidat": nom,
            "score": calcul["score"],
            "couverture": calcul["couverture"],
            "score_strict": strict["score"],
            "precision": calcul["precision"],
            "score_specifie": calcul["score_specifie"],
        })
    lignes = classer(lignes)
    for ligne in lignes:
        print(
            f"{ligne['candidat']}\tscore={_fmt(ligne['score'])}\t"
            f"couverture={_fmt(ligne['couverture'])}\tstrict={_fmt(ligne['score_strict'])}"
        )
    if args.sortie:
        ecrire_resultats(
            args.sortie,
            [
                {
                    "candidat": ligne["candidat"],
                    "score": _fmt(ligne["score"]),
                    "couverture": _fmt(ligne["couverture"]),
                    "score_strict": _fmt(ligne["score_strict"]),
                    "precision": _fmt(ligne["precision"]),
                    "score_specifie": _fmt(ligne["score_specifie"]),
                }
                for ligne in lignes
            ],
        )


def _fmt(valeur):
    if valeur is None:
        return ""
    return f"{valeur:.6f}"


def exemple_au_crayon():
    """Trois questions, deux candidats. Les valeurs sont reprises dans l'étude."""
    notes_a = {1: 4, 2: 0, 3: None}
    notes_b = {1: 1, 2: 2, 3: 4}
    cibles = {1: 4, 2: 0, 3: 4}
    poids = {1: 2.0, 2: 1.0, 3: 1.0}
    a = score_candidat(notes_a, cibles, poids)
    b = score_candidat(notes_b, cibles, poids)
    return {
        "notes_a": notes_a,
        "notes_b": notes_b,
        "cibles": cibles,
        "poids": poids,
        "score_a": a["score"],
        "couverture_a": a["couverture"],
        "score_b": b["score"],
        "couverture_b": b["couverture"],
        "pi_b_1": proximite(1, 4),
        "pi_b_2": proximite(2, 0),
    }


def verifier():
    crayon = exemple_au_crayon()
    if abs(crayon["score_a"] - 100.0) > 1e-9:
        raise ErreurMethode("l'exemple au crayon du candidat A ne vaut pas 100")
    if abs(crayon["score_b"] - 50.0) > 1e-9:
        raise ErreurMethode("l'exemple au crayon du candidat B ne vaut pas 50")
    if abs(crayon["couverture_a"] - 0.75) > 1e-9 or abs(crayon["couverture_b"] - 1.0) > 1e-9:
        raise ErreurMethode("couvertures de l'exemple au crayon inattendues")
    if abs(crayon["pi_b_1"] - 0.25) > 1e-9 or abs(crayon["pi_b_2"] - 0.5) > 1e-9:
        raise ErreurMethode("proximités de l'exemple au crayon inattendues")

    # Cible 4 partout : le score est la moyenne pondérée des notes, sur 100.
    notes = {1: 0, 2: 4}
    cibles = {1: 4, 2: 4}
    poids = {1: 1.0, 2: 3.0}
    obtenu = score_candidat(notes, cibles, poids)["score"]
    attendu = 100.0 * (1 * 0 + 3 * 1) / 4
    if abs(obtenu - attendu) > 1e-9:
        raise ErreurMethode("la cible 4 ne se réduit pas à la moyenne pondérée")

    # Cible 0 : la note est retournée.
    cibles_basses = {1: 0, 2: 0}
    obtenu_bas = score_candidat(notes, cibles_basses, poids)["score"]
    attendu_bas = 100.0 * (1 * 1 + 3 * 0) / 4
    if abs(obtenu_bas - attendu_bas) > 1e-9:
        raise ErreurMethode("la cible 0 ne retourne pas la note")

    # Le strict impute une proximité nulle à l'absence.
    strict = score_strict({1: 4, 2: None}, {1: 4, 2: 4}, {1: 1.0, 2: 1.0})["score"]
    if abs(strict - 50.0) > 1e-9:
        raise ErreurMethode("le score strict devrait valoir 50")

    # Kappa parfait, puis désaccord total aux extrêmes.
    parfait = kappa_quadratique([0, 1, 2, 3, 4, 2], [0, 1, 2, 3, 4, 2])
    if abs(parfait["kappa"] - 1.0) > 1e-9:
        raise ErreurMethode("kappa parfait différent de 1")
    oppose = kappa_quadratique([0, 0, 4, 4], [4, 4, 0, 0])
    if oppose["kappa"] >= 0:
        raise ErreurMethode("kappa de désaccords extrêmes devrait être négatif")

    try:
        score_candidat({1: 4}, {1: 4}, {1: 0.0})
    except ErreurMethode:
        pass
    else:
        raise ErreurMethode("un poids total nul aurait dû être refusé")

    decision, motifs = publiable(0.9, 0.8, 0.75, 0.7)
    if not decision or motifs:
        raise ErreurMethode("un cas au-dessus des seuils devrait être publiable")
    decision_basse, motifs_bas = publiable(0.5, 0.9, 0.9, 0.9)
    if decision_basse or "couverture" not in motifs_bas:
        raise ErreurMethode("une couverture basse aurait dû bloquer la publication")
    return True


def main(argv=None):
    parseur = argparse.ArgumentParser(description="Comparer des programmes sur la grille de 100 questions.")
    sous = parseur.add_subparsers(dest="commande", required=True)
    scorer = sous.add_parser("scorer", help="calcule les scores à partir d'un CSV de notes et d'un CSV de profil")
    scorer.add_argument("--notes", required=True)
    scorer.add_argument("--profil", required=True)
    scorer.add_argument("--sortie")
    scorer.add_argument("--exiger-citations", action="store_true")
    sous.add_parser("verifier", help="vérifie les formules sur des cas connus")
    args = parseur.parse_args(argv)
    if args.commande == "verifier":
        verifier()
        print("verification_ok")
        return 0
    commander_scorer(args)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ErreurMethode as erreur:
        print(f"erreur : {erreur}", file=sys.stderr)
        sys.exit(2)
