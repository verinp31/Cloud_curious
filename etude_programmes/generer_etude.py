"""Génère le PDF de l'étude à partir des formules et de l'exemple fictif.

La mise en page dépend de WeasyPrint. Le calcul des scores, non.
"""

from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path

from weasyprint import HTML

from algorithme import (
    N_SIM_CODAGE,
    N_SIM_POIDS,
    P_BRUIT_CODAGE,
    SEUIL_COUVERTURE,
    SEUIL_KAPPA,
    SEUIL_STABILITE,
    SIGMA_POIDS,
    exemple_au_crayon,
    verifier,
)
from donnees_exemple import (
    CANDIDATS,
    QUESTIONS_DEPENSE,
    QUESTIONS_RECETTE,
    ecrire_modeles,
    nom_affiche,
    tout_calculer,
)
from grille import LEVIERS, QUESTIONS, par_domaine

ICI = Path(__file__).resolve().parent
DEPOT = ICI.parent
PDF = ICI / "Comparaison_objective_des_programmes_presidentiels.pdf"
MODELES = ICI / "modeles"

COULEURS = {
    "ancrage": "#1e3a5f",
    "ouverture": "#1d6a4f",
    "equilibre": "#8a5a2a",
}


def typo(texte):
    texte = texte.replace("'", "’")
    texte = re.sub(r"\s+([;:!?»])", "\u202f\\1", texte)
    texte = re.sub(r"(«)\s+", "\\1\u202f", texte)
    texte = re.sub(r"(\d)\s+%", lambda correspondance: correspondance.group(1) + "\u202f%", texte)
    return texte


def tx(texte):
    return typo(html.escape(texte, quote=False))


def rich(texte):
    morceaux = re.split(r"(\*\*[^*]+\*\*)", texte)
    rendu = []
    for morceau in morceaux:
        if morceau.startswith("**") and morceau.endswith("**") and len(morceau) > 4:
            rendu.append(f"<strong>{tx(morceau[2:-2])}</strong>")
        else:
            rendu.append(tx(morceau))
    return "".join(rendu)


def paras(bloc):
    paragraphes = re.split(r"\n\s*\n", bloc.strip())
    sorties = []
    for paragraphe in paragraphes:
        ligne = " ".join(part.strip() for part in paragraphe.splitlines())
        if ligne:
            sorties.append(f"<p>{rich(ligne)}</p>")
    return "\n".join(sorties)


def ul(items):
    return "<ul>\n" + "\n".join(f"<li>{rich(item)}</li>" for item in items) + "\n</ul>"


def ol(items):
    return "<ol>\n" + "\n".join(f"<li>{rich(item)}</li>" for item in items) + "\n</ol>"


def fr(valeur, decimales=1):
    if valeur is None:
        return "—"
    arrondi = round(float(valeur), decimales)
    if abs(arrondi) < 0.5 * 10 ** (-decimales):
        arrondi = 0.0
    return f"{arrondi:.{decimales}f}".replace(".", ",")


def chapitre(identifiant, titre, contenu):
    return f'<section class="chapitre" id="{identifiant}"><h2>{tx(titre)}</h2>\n{contenu}\n</section>'


def appel(titre, corps, sorte="note"):
    return f'<aside class="{sorte}"><p class="etiquette">{tx(titre)}</p>{paras(corps)}</aside>'


def ligne_candidat(evaluation, candidat_id):
    for ligne in evaluation["ordre"]:
        if ligne["id"] == candidat_id:
            return ligne
    raise KeyError(candidat_id)


def css():
    serif = "/usr/share/fonts/truetype/liberation/LiberationSerif"
    sans = "/usr/share/fonts/truetype/liberation/LiberationSans"
    mono = "/usr/share/fonts/truetype/liberation/LiberationMono"
    return f"""
@font-face {{ font-family: "Body"; src: url("file://{serif}-Regular.ttf"); font-weight: 400; }}
@font-face {{ font-family: "Body"; src: url("file://{serif}-Bold.ttf"); font-weight: 700; }}
@font-face {{ font-family: "Body"; src: url("file://{serif}-Italic.ttf"); font-weight: 400; font-style: italic; }}
@font-face {{ font-family: "Body"; src: url("file://{serif}-BoldItalic.ttf"); font-weight: 700; font-style: italic; }}
@font-face {{ font-family: "Sans"; src: url("file://{sans}-Regular.ttf"); font-weight: 400; }}
@font-face {{ font-family: "Sans"; src: url("file://{sans}-Bold.ttf"); font-weight: 700; }}
@font-face {{ font-family: "Sans"; src: url("file://{sans}-Italic.ttf"); font-weight: 400; font-style: italic; }}
@font-face {{ font-family: "Mono"; src: url("file://{mono}-Regular.ttf"); }}
@page {{
  size: A4;
  margin: 16mm 15mm 16mm 15mm;
  @top-left {{
    content: "Comparer les programmes présidentiels";
    font-family: "Sans", sans-serif; font-size: 8pt; color: #6e675e;
  }}
  @top-right {{
    content: counter(page);
    font-family: "Sans", sans-serif; font-size: 8pt; color: #6e675e;
  }}
  @bottom-left {{
    content: "Classement conditionnel aux cibles et aux poids déclarés";
    font-family: "Sans", sans-serif; font-size: 7.5pt; color: #8a837a;
  }}
}}
@page:first {{
  margin-top: 0;
  @top-left {{ content: none; }}
  @top-right {{ content: none; }}
  @bottom-left {{ content: none; }}
}}
* {{ box-sizing: border-box; }}
html {{ hyphens: auto; }}
body {{
  font-family: "Body", "Liberation Serif", serif;
  font-size: 10.5pt; line-height: 1.46; color: #221e1a;
}}
h1, h2, h3, h4 {{ font-family: "Sans", sans-serif; hyphens: none; line-height: 1.2; color: #1a2744; }}
h1 {{ font-size: 26pt; margin: 0 0 8px; font-weight: 700; }}
h2 {{ font-size: 16pt; margin: 16px 0 10px; break-after: avoid; }}
h3 {{ font-size: 12pt; margin: 14px 0 6px; break-after: avoid; }}
h4 {{ font-size: 10.5pt; margin: 0; color: #221e1a; }}
.q h4 {{ display: inline; }}
p {{ margin: 0 0 8px; orphans: 3; widows: 3; }}
strong {{ font-weight: 700; }}
a {{ color: #1e3a5f; text-decoration: none; }}
code, .mono {{ font-family: "Mono", monospace; font-size: 8.5pt; hyphens: none; }}
.chapitre {{ break-before: auto; }}
section.chapitre:first-of-type {{ break-before: page; }}
.bandeau {{ height: 8mm; background: #1e3a5f; margin: 0 -15mm 12mm; }}
.surtitre {{
  font-family: "Sans", sans-serif; font-size: 9pt; letter-spacing: 0.12em;
  text-transform: uppercase; color: #1e3a5f; margin: 0 0 8px;
}}
.chapo {{ font-size: 12.5pt; line-height: 1.35; color: #3a342c; margin: 0 0 12px; hyphens: none; }}
.meta {{ font-family: "Sans", sans-serif; font-size: 9pt; color: #5c564e; margin: 0 0 14px; }}
.faits {{ width: 100%; border-collapse: separate; border-spacing: 6px 0; margin: 0 0 12px; }}
.faits td {{
  width: 33%; background: #f4f0e8; padding: 8px 10px; vertical-align: top; hyphens: none;
}}
.faits .nombre {{ display: block; font-family: "Sans", sans-serif; font-size: 13pt; font-weight: 700; color: #1e3a5f; }}
.faits .legende {{ display: block; font-family: "Sans", sans-serif; font-size: 8pt; color: #5c564e; margin-top: 2px; }}
aside {{ break-inside: avoid; margin: 8px 0 12px; padding: 8px 10px; }}
aside.note {{ background: #f4f0e8; }}
aside.alerte {{ background: #f8efe6; border-left: 3px solid #8a5a2a; }}
aside .etiquette {{
  font-family: "Sans", sans-serif; font-size: 8pt; font-weight: 700;
  letter-spacing: 0.06em; text-transform: uppercase; margin: 0 0 4px; color: #1e3a5f;
}}
aside.alerte .etiquette {{ color: #6e3d12; }}
ul, ol {{ margin: 0 0 8px; padding-left: 18px; }}
li {{ margin: 0 0 3px; }}
table {{ width: 100%; border-collapse: collapse; margin: 6px 0 10px; hyphens: none; }}
th, td {{ text-align: left; vertical-align: top; padding: 3px 5px; border-bottom: 0.4pt solid #e0d8cc; }}
thead {{ display: table-header-group; }}
tr {{ break-inside: avoid; }}
th {{
  font-family: "Sans", sans-serif; font-size: 7.5pt; font-weight: 700;
  color: #5c564e; border-bottom: 1pt solid #1e3a5f;
}}
td {{ font-size: 9pt; }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; font-family: "Sans", sans-serif; }}
caption {{
  caption-side: bottom; text-align: left; font-size: 8pt; color: #5c564e;
  margin-top: 3px; font-family: "Sans", sans-serif;
}}
.formule {{
  break-inside: avoid; background: #f7f5f1; border-left: 3px solid #1e3a5f;
  padding: 8px 12px; margin: 8px 0 12px;
}}
.formule .nom {{
  font-family: "Sans", sans-serif; font-size: 8pt; font-weight: 700;
  letter-spacing: 0.04em; text-transform: uppercase; color: #1e3a5f; margin: 0;
}}
.formule .eq {{
  font-family: "Sans", sans-serif; font-size: 12pt; margin: 2px 0 0; hyphens: none;
}}
.sommaire a {{ color: #221e1a; display: block; }}
.sommaire li {{ margin: 0 0 4px; }}
.sommaire a::after {{
  content: target-counter(attr(href), page);
  float: right; font-family: "Sans", sans-serif; color: #6e675e;
}}
.q {{
  break-inside: avoid; margin: 0 0 7px; padding: 6px 8px 5px;
  background: #fbf9f5; border-left: 2.5pt solid #1e3a5f;
}}
.q header {{ display: flex; justify-content: space-between; align-items: baseline; gap: 8px; margin: 0 0 3px; }}
.qid {{
  font-family: "Sans", sans-serif; font-weight: 700; color: #1e3a5f;
  margin-right: 6px;
}}
.levier {{
  flex: none; font-family: "Sans", sans-serif; font-size: 7.5pt;
  color: #5c564e; border: 0.4pt solid #d9d0c3; padding: 0 4px;
}}
.pole {{ margin: 0; font-size: 9.5pt; }}
.pole b {{ font-family: "Sans", sans-serif; color: #1e3a5f; }}
.consigne {{ margin: 2px 0 0; font-size: 8.5pt; color: #5c564e; font-style: italic; }}
.etapes {{ width: 100%; margin: 6px 0 10px; }}
.etapes td {{
  width: 25%; background: #f4f0e8; border-bottom: none; padding: 6px;
  font-family: "Sans", sans-serif; font-size: 8pt;
}}
.etapes .n {{ display: block; font-weight: 700; color: #1e3a5f; font-size: 9pt; }}
table.matrice td {{ font-size: 7.6pt; padding: 2px 3px; }}
table.matrice {{ break-inside: auto; }}
table.compacte td, table.compacte th {{ font-size: 8pt; }}
svg {{ display: block; margin: 4px 0 2px; }}
.legende-graphique {{ font-family: "Sans", sans-serif; font-size: 8pt; color: #5c564e; margin: 0 0 8px; hyphens: none; }}
.puce {{ display: inline-block; width: 8px; height: 8px; margin: 0 4px 0 10px; }}
"""


def graphique(evaluations):
    profils = [e for e in evaluations if e["id"] != "serre"]
    largeur, hauteur = 680, 232
    gauche, droite, haut, bas = 36, 12, 18, 36
    zone_l = largeur - gauche - droite
    zone_h = hauteur - haut - bas
    barres = []
    legende = []
    largeur_barre = 26
    ecart = 5
    for index, evaluation in enumerate(profils):
        centre = gauche + (index + 0.5) * zone_l / len(profils)
        depart = centre - (3 * largeur_barre + 2 * ecart) / 2
        for rang, candidat in enumerate(CANDIDATS):
            ligne = ligne_candidat(evaluation, candidat["id"])
            score = ligne["score"]
            x = depart + rang * (largeur_barre + ecart)
            h = zone_h * score / 100
            y = haut + zone_h - h
            couleur = COULEURS[candidat["id"]]
            barres.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{largeur_barre}" height="{h:.1f}" fill="{couleur}"/>'
            )
            barres.append(
                f'<text x="{x + largeur_barre / 2:.1f}" y="{y - 3:.1f}" text-anchor="middle" '
                f'font-family="Sans" font-size="8" fill="#221e1a">{fr(score)}</text>'
            )
        legende.append(
            f'<text x="{centre:.1f}" y="{hauteur - 8}" text-anchor="middle" '
            f'font-family="Sans" font-size="8.5" fill="#221e1a">{tx(evaluation["court"])}</text>'
        )
    grille = []
    for palier in (0, 25, 50, 75, 100):
        y = haut + zone_h * (1 - palier / 100)
        grille.append(
            f'<line x1="{gauche}" y1="{y:.1f}" x2="{largeur - droite}" y2="{y:.1f}" stroke="#e0d8cc" stroke-width="0.6"/>'
        )
        grille.append(
            f'<text x="{gauche - 4}" y="{y + 3:.1f}" text-anchor="end" font-family="Sans" font-size="8" fill="#6e675e">{palier}</text>'
        )
    pastilles = "".join(
        f'<span class="puce" style="background:{COULEURS[candidat["id"]]}"></span>{tx(candidat["etiquette"])}'
        for candidat in CANDIDATS
    )
    return (
        f'<p class="legende-graphique">{pastilles}</p>'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largeur} {hauteur}" width="100%">'
        + "".join(grille + barres + legende)
        + "</svg>"
        '<p class="legende-graphique">Score de proximité, de 0 à 100. Le même codage, trois profils. '
        "Les valeurs du graphique sont celles du tableau.</p>"
    )


def tableau_scores(evaluation):
    lignes = []
    for ligne in evaluation["ordre"]:
        lignes.append(
            "<tr>"
            f"<td>{tx(ligne['nom'])}</td>"
            f"<td class='num'>{fr(ligne['score'])}</td>"
            f"<td class='num'>{fr(100 * ligne['couverture'])}\u202f%</td>"
            f"<td class='num'>{ligne['n_observe']}</td>"
            f"<td class='num'>{fr(ligne['score_strict'])}</td>"
            f"<td class='num'>{fr(ligne['precision'])}</td>"
            f"<td class='num'>{fr(ligne['score_specifie'])}</td>"
            "</tr>"
        )
    return (
        "<table class='compacte'><thead><tr>"
        "<th>Candidat fictif</th><th class='num'>Proximité</th><th class='num'>Couverture</th>"
        "<th class='num'>Questions notées</th><th class='num'>Score strict</th>"
        "<th class='num'>Précision</th><th class='num'>Accord spécifié</th>"
        "</tr></thead><tbody>"
        + "".join(lignes)
        + "</tbody></table>"
    )


def tableau_domaines(evaluation):
    by_id = {ligne["id"]: ligne for ligne in evaluation["ordre"]}
    parts = {part["code"]: part for part in evaluation["parts_domaines"]}
    lignes = []
    for domaine in by_id["ancrage"]["domaines"]:
        code = domaine["code"]
        cellules = []
        for candidat in CANDIDATS:
            score = next(d["score"] for d in by_id[candidat["id"]]["domaines"] if d["code"] == code)
            cellules.append(f"<td class='num'>{fr(score)}</td>")
        lignes.append(
            "<tr>"
            f"<td>{tx(domaine['nom'])}</td>"
            f"<td class='num'>{fr(100 * parts[code]['part'])}\u202f%</td>"
            + "".join(cellules)
            + "</tr>"
        )
    return (
        "<table class='compacte'><thead><tr><th>Domaine</th><th class='num'>Poids</th>"
        "<th class='num'>A</th><th class='num'>B</th><th class='num'>C</th></tr></thead><tbody>"
        + "".join(lignes)
        + "</tbody></table>"
    )


def tableau_contributions(evaluation, sens):
    """sens = 1 pour l'avantage de B sur A, -1 pour l'avantage de A sur B."""
    face = evaluation["face_a_face"]
    total = sum(ligne["poids"] for ligne in face)
    tries = sorted(face, key=lambda ligne: sens * ligne["contribution"], reverse=True)[:8]
    questions = {q["id"]: q for q in QUESTIONS}
    lignes = []
    somme = 0.0
    for ligne in tries:
        points = 100 * ligne["contribution"] / total
        somme += points
        question = questions[ligne["question"]]
        lignes.append(
            "<tr>"
            f"<td class='num'>{ligne['question']}</td>"
            f"<td>{tx(question['titre'])}</td>"
            f"<td class='num'>{fr(100 * ligne['proximite_a'])}</td>"
            f"<td class='num'>{fr(100 * ligne['proximite_b'])}</td>"
            f"<td class='num'>{fr(points, 2)}</td>"
            "</tr>"
        )
    score_b = ligne_candidat(evaluation, "ouverture")["score"]
    score_a = ligne_candidat(evaluation, "ancrage")["score"]
    ecart = score_b - score_a
    return (
        "<table class='compacte'><thead><tr>"
        "<th class='num'>N°</th><th>Question</th>"
        "<th class='num'>Proximité B</th><th class='num'>Proximité A</th>"
        "<th class='num'>Points d’écart</th></tr></thead><tbody>"
        + "".join(lignes)
        + "</tbody><caption>Un nombre positif est un avantage de B sur A, un nombre négatif un avantage de A. "
        f"L’écart total B − A est de {fr(ecart, 2)} points. Ces huit questions en additionnent {fr(somme, 2)}.</caption></table>"
    )


def paragraphe_stabilite(evaluation):
    domaines = evaluation["domaines_qui_changent"]
    if domaines:
        retrait = "Retirer l’un de ces domaines change la tête : " + ", ".join(domaines) + "."
    else:
        retrait = "Retirer un domaine, n’importe lequel, ne change pas la tête du classement."
    return paras(
        f"""
        En perturbant les poids ({N_SIM_POIDS} tirages, écart-type logarithmique {fr(SIGMA_POIDS, 2)}),
        {tx(evaluation['premier'])} reste seul en tête dans {fr(100 * evaluation['stabilite_poids'])} % des cas.
        En décalant au hasard 15 % des notes d’un cran ({N_SIM_CODAGE} tirages),
        cette part est de {fr(100 * evaluation['stabilite_codage'])} %.
        Le seuil retenu pour dire le classement stable est {fr(100 * SEUIL_STABILITE, 0)} % dans les deux épreuves.
        {retrait}
        """
    )


def section_ouverture(calculs):
    return f"""
    <div class="bandeau"></div>
    <p class="surtitre">Note méthodologique · 19 novembre 2026</p>
    <h1>Comparer les programmes, question par question</h1>
    <p class="chapo">Une méthode pour noter 100 questions, leur donner un poids, et obtenir un classement que quelqu’un d’autre peut refaire.</p>
    <p class="meta">Élection présidentielle française · Les formules ne dépendent pas du pays · L’exemple chiffré est fictif</p>
    <table class="faits"><tr>
      <td><span class="nombre">100</span><span class="legende">questions, chacune entre deux pôles écrits à l’avance</span></td>
      <td><span class="nombre">0 à 100</span><span class="legende">score de proximité, moyenne pondérée des écarts à vos cibles</span></td>
      <td><span class="nombre">Aucun</span><span class="legende">classement publié sans profil, sans sources et sans robustesse</span></td>
    </tr></table>
    {appel("Ce que ce document est", '''
    Il fixe un algorithme. Il ne classe aucun candidat réel et ne recommande aucun vote.
    La grille est écrite pour l’élection présidentielle française : beaucoup de questions se décident par la loi,
    certaines par le président, d’autres avec l’Union européenne. Changer de pays impose de réécrire les questions, pas les formules.
    ''')}
    {paras('''
    On peut comparer des programmes de façon reproductible. On ne peut pas en déduire, par le seul calcul, lequel est le bon.
    La note dit où le programme se place sur un axe. La cible dit où l’électeur veut qu’il se place. Le poids dit si cet axe compte.
    Le classement est le résultat de ces trois choix. Il est objectif au sens où deux équipes qui partent des mêmes textes,
    des mêmes cibles et des mêmes poids doivent trouver le même ordre. Il n’est pas objectif au sens où il dirait la vérité politique
    indépendamment de ce que l’on cherche.
    ''')}
    <h3>Sommaire</h3>
    <ol class="sommaire">
      <li><a href="#resume">L’algorithme en une page</a></li>
      <li><a href="#sens">Ce que « objectif » veut dire ici</a></li>
      <li><a href="#formules">Les formules</a></li>
      <li><a href="#protocole">Le protocole de codage</a></li>
      <li><a href="#poids">Déclarer les poids</a></li>
      <li><a href="#grille">Les 100 questions</a></li>
      <li><a href="#exemple">Exemple sur trois candidats fictifs</a></li>
      <li><a href="#emploi">Refaire le calcul</a></li>
      <li><a href="#limites">Limites</a></li>
      <li><a href="#matrice">Annexe. Matrice de l’exemple</a></li>
    </ol>
    <p class="meta">Empreinte de cette grille : <span class="mono">{calculs['empreinte']}</span>. Elle change si une question change.</p>
    """


def section_resume():
    return chapitre("resume", "L’algorithme en une page", paras('''
    On fige d’abord quatre choses : le corpus, la liste des questions, la cible de chaque question, le poids de chaque question.
    On les date. On ne les change plus après avoir ouvert les programmes.

    Chaque question a un pôle bas, noté 0, et un pôle haut, noté 4. Le codeur place le programme sur cet axe.
    0, le programme choisit le pôle bas. 1, il penche vers le pôle bas. 2, il se tait, ou il choisit explicitement le milieu.
    3, il penche vers le pôle haut. 4, il choisit le pôle haut. Une deuxième note, l’opérationnalité, dit si ce choix est outillé :
    0 aucun instrument, 1 un instrument nommé, 2 un instrument accompagné d’un chiffre, d’une date ou d’un financement.

    La cible de l’électeur est un nombre de 0 à 4 sur la même échelle. La proximité d’une question vaut 1 quand la note est sur la cible,
    et 0 quand elle est à l’autre bout. Le score du programme est la moyenne de ces proximités, pondérée par les poids, ramenée de 0 à 100.
    Si toutes les cibles valent 4, ce score est exactement la moyenne pondérée des notes. C’est le cas particulier que l’on obtient
    quand on a écrit les questions de telle sorte que « plus c’est haut, plus je suis d’accord ».

    On publie, à côté du score, la couverture (la part du poids réellement notée), un score strict qui compte les silences de corpus
    comme une proximité nulle, et la précision des prises de position. On publie les citations. On publie l’accord entre deux codeurs
    indépendants. On ne publie un classement que si cet accord, la couverture et deux épreuves de bruit dépassent des seuils écrits plus bas.
    ''') + appel("Règle de lecture", '''
    Un score élevé veut dire : ce programme est proche du profil déclaré. Il ne veut pas dire : ce programme est meilleur.
    Deux citoyens qui remplissent des cibles différentes doivent obtenir deux classements différents à partir de la même matrice de notes.
    Si ce n’est pas le cas, le calcul ne sert à rien.
    '''))


def section_sens():
    return chapitre("sens", "Ce que « objectif » veut dire ici", paras('''
    Trois demandes se mélangent souvent. La première est descriptive : que dit le texte ? La deuxième est comparative :
    lequel de ces textes est le plus proche de ce que je cherche ? La troisième est normative : lequel devrait l’emporter ?
    Cette méthode fait la première, puis la deuxième si le profil est écrit. Elle ne fait pas la troisième.

    Le codage descriptif s’appuie sur des pratiques déjà utilisées pour comparer des programmes : on découpe le texte en prises de position
    sur des échelles fixes, comme le font les projets de codage de manifestes et les enquêtes d’experts sur les partis.
    L’idée de situer un électeur et un programme dans le même espace, puis de mesurer une distance, est celle du vote spatial.
    Rien ici ne remplace ces travaux. Les seuils chiffrés plus loin sont des conventions de cette note, choisies pour qu’un classement fragile
    ne soit pas présenté comme un résultat.

    L’objectivité praticable tient dans sept contraintes.

    Le corpus est le même pour tous. On le définit avant de coder : programme publié sur le site de campagne, projet présidentiel daté,
    et rien d’autre, sauf si les entretiens sont inclus pour tout le monde et clos à la même date.

    La grille est la même pour tous. Une question ambiguë se retire avant le calcul, pas après avoir vu qu’elle gêne un candidat.

    L’échelle est ancrée. Deux codeurs n’ont pas à deviner ce que « ambitieux » veut dire. Ils ont les deux pôles et la consigne.

    Le profil est antérieur au codage. Écrire ses cibles après avoir lu les programmes est permis pour un usage personnel,
    à condition de le dire. Ce n’est plus une comparaison pré-enregistrée.

    Chaque note autre que le silence renvoie à un passage. Le silence aussi laisse une trace : le codeur indique avoir cherché
    dans le corpus défini, et n’y avoir rien trouvé.

    Deux personnes codent sans se concerter. On mesure leur accord avant de discuter les cas qui les séparent.

    Le classement est accompagné de ce qui peut le renverser : autre profil, questions absentes, poids un peu différents, erreur d’un cran.
    ''') + appel("Ce qui n’est pas neutre", '''
    La liste des questions ne l’est pas : une grille qui contient dix questions sur un sujet et une sur un autre a déjà choisi.
    Les pôles ne le sont pas : leur rédaction oriente ce que « 4 » veut dire. Les poids égaux ne le sont pas non plus.
    Ils disent que chaque question compte autant, ce qui est une préférence comme une autre. Le gain de la méthode est de rendre
    ces choix visibles, pas de les faire disparaître.
    '''))


def section_formules(crayon):
    return chapitre("formules", "Les formules", paras('''
    Notons x la note du programme, t la cible, w le poids, o l’opérationnalité. x, t et o sont des entiers.
    x et t vont de 0 à 4. o va de 0 à 2. w est un nombre positif ou nul. Une question de poids nul est ignorée.
    ''') + """
    <div class="formule"><p class="nom">Proximité d’une question</p>
    <p class="eq">π = 1 − |x − t| / 4</p></div>
    """ + paras('''
    La proximité vaut 1 sur la cible, 0,75 à un cran, 0,50 à deux crans, 0,25 à trois crans, 0 à l’opposé.
    Elle ne récompense pas une note élevée. Elle récompense une note proche de la cible.
    ''') + """
    <div class="formule"><p class="nom">Score de proximité</p>
    <p class="eq">P = 100 × Σ (w × π) / Σ w</p></div>
    """ + paras('''
    Les sommes portent sur les questions observées dont le poids est positif. P va de 0 à 100.
    Quand t vaut 4 pour toutes les questions, π vaut x/4, et P est la moyenne pondérée des notes, exprimée sur 100.
    Quand t vaut 0, π vaut 1 − x/4 : la note est retournée. C’est utile quand le pôle haut de la question n’est pas celui que l’on cherche.

    Une question absente du corpus n’est pas un 2. Le 2 est réservé au silence dans un texte que l’on a, ou au choix explicite du milieu.
    L’absence, notée vide, sort de la somme, et les poids des questions restantes sont ainsi renormalisés.
    La couverture est la part du poids total qui a pu être notée. On la publie à côté de P.
    Un candidat qui ne traite que les questions où il est proche de la cible peut avoir un P élevé et une couverture faible.
    Le score, seul, le ferait gagner. La couverture l’empêche.
    ''') + """
    <div class="formule"><p class="nom">Score strict</p>
    <p class="eq">même formule, avec π = 0 si la question est absente</p></div>
    """ + paras(f'''
    Le score strict ne renormalise pas. Il compte l’absence comme le désaccord le plus fort.
    Si le premier du score de proximité n’est pas le premier du score strict, on ne publie pas un classement unique.
    On publie les deux. Le seuil de couverture en dessous duquel on s’abstient d’un classement unique,
    même si les deux scores désignent la même personne, est {fr(100 * SEUIL_COUVERTURE, 0)} %.
    ''') + """
    <div class="formule"><p class="nom">Précision et accord spécifié</p>
    <p class="eq">précision = moyenne de o / 2, sur les questions où le programme a pris parti</p>
    <p class="eq">accord spécifié = moyenne de π × (0,5 + o / 4)</p></div>
    """ + paras('''
    La précision ne classe personne politiquement. Elle dit si les prises de position sont outillées.
    Le parti pris est x différent de 2. Une position muette n’entre pas dans cette moyenne : elle est déjà comptée comme milieu dans la proximité.

    L’accord spécifié mélange les deux. Un accord parfait sans instrument compte moitié moins qu’un accord parfait outillé.
    Un désaccord reste bas, parce que π est bas. Ce mélange est facultatif. Il n’est pas le score principal :
    il répond à une autre question, celle de savoir si l’on veut qu’un slogan pèse autant qu’une mesure.
    L’exemple montrera qu’il peut changer le vainqueur.
    ''') + paras('''
    L’écart entre deux programmes dont la couverture est complète se décompose question par question.
    La contribution d’une question est w × (π du premier − π du second). La somme de ces contributions,
    divisée par la somme des poids et multipliée par 100, redonne l’écart de score. On peut donc dire quelles questions font le classement.
    Dès que les questions absentes ne sont pas les mêmes, les dénominateurs diffèrent et cette addition n’est plus l’écart des scores renormalisés.
    On le signale au lieu de forcer une décomposition fausse.
    ''') + appel("Exemple au crayon", f'''
    Trois questions suffisent à vérifier la formule à la main. Poids : 2, 1 et 1. Cibles : 4, 0 et 4.
    Le candidat A a les notes 4, 0, et rien sur la troisième. Le candidat B a les notes 1, 2 et 4.

    Proximité de A sur la première : 1. Sur la deuxième : 1. La troisième est absente.
    Score de A = 100 × (2 × 1 + 1 × 1) / 3 = {fr(crayon['score_a'], 0)}. Couverture {fr(100 * crayon['couverture_a'], 0)} %.

    Proximité de B : {fr(crayon['pi_b_1'], 2)} sur la première, {fr(crayon['pi_b_2'], 2)} sur la deuxième, 1 sur la troisième.
    Score de B = 100 × (2 × {fr(crayon['pi_b_1'], 2)} + 1 × {fr(crayon['pi_b_2'], 2)} + 1 × 1) / 4 = {fr(crayon['score_b'], 0)}.
    Couverture {fr(100 * crayon['couverture_b'], 0)} %.

    A est plus proche du profil, sur un corpus incomplet. Le score strict de A vaut 50, pas 100 :
    la question manquante y compte comme un désaccord total. Les deux nombres doivent être lus ensemble.
    '''))


def section_protocole(kappa):
    acceptable = kappa["acceptable"]
    refuse = kappa["refuse"]
    return chapitre("protocole", "Le protocole de codage", paras('''
    Le calcul ne vaut que ce que vaut la matrice. Le protocole sert à empêcher qu’une matrice arrangeable devienne un classement.
    ''') + """
    <table class="etapes"><tr>
      <td><span class="n">1</span>Figer corpus, grille, cibles et poids. Dater le fichier. Calculer l’empreinte de la grille.</td>
      <td><span class="n">2</span>Deux codeurs, séparément, sans le profil sous les yeux si l’on veut limiter l’attraction vers la cible.</td>
      <td><span class="n">3</span>Kappa quadratique. Sous le seuil, on révise la consigne. On ne classe pas.</td>
      <td><span class="n">4</span>Arbitrage des écarts d’au moins deux crans, puis scores, couverture, strict, précision, robustesse.</td>
    </tr></table>
    """ + paras(f'''
    L’accord retenu est le kappa de Cohen pondéré par le carré de l’écart, sur les cinq crans.
    Un désaccord d’un cran pèse (1/4)², un désaccord de deux crans (2/4)², et ainsi de suite jusqu’à 1 pour un désaccord de 0 contre 4.
    Le seuil de publication est {fr(SEUIL_KAPPA, 2)}. Il s’applique au double codage indépendant, avant l’arbitrage.
    Le kappa calculé après s’être mis d’accord ne mesure plus rien.

    Deux tirages, faits sur les 100 notes fictives du candidat A, montrent le seuil.
    Avec {kappa['parametres_acceptables']}, le kappa vaut {fr(acceptable['kappa'], 2)} et l’accord brut {fr(100 * acceptable['accord_brut'], 0)} %.
    Avec {kappa['parametres_refuses']}, le kappa vaut {fr(refuse['kappa'], 2)} et l’accord brut {fr(100 * refuse['accord_brut'], 0)} %.
    Le second tirage interdit le classement. Le premier l’autoriserait, pour ce seul critère.
    ''') + paras(f'''
    Après le kappa, on arbitre toute question où les deux codeurs diffèrent d’au moins deux crans. On peut garder un écart d’un cran
    en prenant la moyenne arrondie, et le dire. On ne rouvre pas une question parce que son effet sur le classement déplaît.

    Viennent ensuite deux bruits. Les poids sont multipliés par l’exponentielle d’une loi normale d’écart-type {fr(SIGMA_POIDS, 2)},
    {N_SIM_POIDS} fois. Indépendamment, chaque note observée est décalée d’un cran, vers le haut ou vers le bas, avec une probabilité
    {fr(100 * P_BRUIT_CODAGE, 0)} %, {N_SIM_CODAGE} fois, sans sortir de 0 à 4. La graine des tirages de l’exemple est 20261119.
    Si la tête du classement l’emporte dans moins de {fr(100 * SEUIL_STABILITE, 0)} % des tirages de l’une ou l’autre épreuve,
    le classement est dit fragile et n’est pas publié comme résultat stable.

    Ces bruits ne cherchent pas les fautes grossières. L’arbitrage des écarts de deux crans est fait pour cela.
    Ils cherchent l’effet des désaccords qui restent, et l’effet d’un profil dont on n’est pas sûr des poids à 25 % près.
    ''') + appel("Publication", '''
    Un classement publié contient la matrice, les citations, le profil daté, l’empreinte de la grille, la couverture,
    le score strict, le kappa d’avant arbitrage, et les deux fréquences de stabilité. Sans l’un de ces éléments, ce document
    considère que l’on a une opinion, pas un résultat de la méthode.
    '''))


def section_poids(evaluations):
    electeurs = [e for e in evaluations if e["id"] != "serre"]
    entetes = "".join(f"<th class='num'>{tx(e['court'])}</th>" for e in electeurs)
    lignes = []
    codes = [partie["code"] for partie in electeurs[0]["parts_domaines"]]
    noms = {partie["code"]: partie["nom"] for partie in electeurs[0]["parts_domaines"]}
    questions = {partie["code"]: partie["questions"] for partie in electeurs[0]["parts_domaines"]}
    for code in codes:
        cellules = []
        for evaluation in electeurs:
            part = next(p["part"] for p in evaluation["parts_domaines"] if p["code"] == code)
            cellules.append(f"<td class='num'>{fr(100 * part)}\u202f%</td>")
        lignes.append(
            f"<tr><td>{tx(noms[code])}</td><td class='num'>{questions[code]}</td>{''.join(cellules)}</tr>"
        )
    levier_lignes = []
    for code, nom in LEVIERS.items():
        cellules = []
        for evaluation in electeurs:
            cellules.append(f"<td class='num'>{fr(100 * evaluation['parts_leviers'].get(code, 0))}\u202f%</td>")
        levier_lignes.append(f"<tr><td>{tx(nom)}</td>{''.join(cellules)}</tr>")
    return chapitre("poids", "Déclarer les poids", paras('''
    Le poids est un nombre par question. Seules les proportions comptent : multiplier tous les poids par dix ne change pas le score.
    Un poids nul retire la question. C’est la bonne façon d’ignorer un sujet, plutôt que de lui inventer une cible.

    Trois profils d’illustration sont fournis avec le code. Aucun n’est un profil neutre.
    Le premier met plus de poids sur le climat, la santé, l’école, le travail et la protection sociale, et ses cibles vont vers les services publics,
    la redistribution et la baisse des émissions. Il ne demande pas la sortie du nucléaire : sa cible sur le parc est 3.
    Le deuxième met plus de poids sur la sûreté, l’immigration, la fiscalité et la défense, et ses cibles vont vers la baisse des prélèvements,
    le contrôle de l’immigration et la réponse pénale ferme. Sa cible sur le salaire minimum est le milieu, pas la baisse.
    Le troisième met la cible 2 partout et le même poids partout. Il récompense le centre et le silence, puisque les deux sont codés 2.
    ''') + f"""
    <table class="compacte"><thead><tr><th>Domaine</th><th class="num">Questions</th>{entetes}</tr></thead>
    <tbody>{''.join(lignes)}</tbody>
    <caption>Part du poids total. Les questions d’un même domaine ont ici le même poids. Rien n’oblige à faire ainsi :
    le fichier de profil a une ligne par question.</caption></table>
    <table class="compacte"><thead><tr><th>Levier principal</th>{entetes}</tr></thead>
    <tbody>{''.join(levier_lignes)}</tbody>
    <caption>Part du poids selon que la décision relève d’abord du président, de la loi, de l’Union européenne, ou de plusieurs de ces leviers.</caption></table>
    """ + paras('''
    La colonne du levier est une information, pas un abattement. Un électeur qui ne veut noter que ce qu’un président décide sans la loi
    met un poids nul sur le reste. Il verra alors un score plus étroit, et il devra le dire. Sur les trois profils ci-dessus,
    la part parlementaire est la plus grande : une présidentielle française se joue en grande partie sur des promesses de loi.
    Le score mesure ces promesses. Il ne mesure pas la probabilité d’avoir une majorité pour les voter.
    '''))


def section_grille():
    blocs = []
    for groupe in par_domaine():
        cartes = [f"<h3>{tx(groupe['nom'])}</h3>"]
        for question in groupe["questions"]:
            consigne = (
                f"<p class='consigne'>{tx(question['consigne'])}</p>" if question["consigne"] else ""
            )
            cartes.append(
                "<article class='q'>"
                "<header>"
                "<div>"
                f"<span class='qid'>{question['id']:02d}</span>"
                f"<h4>{tx(question['titre'])}</h4>"
                "</div>"
                f"<span class='levier'>{tx(LEVIERS[question['levier']])}</span>"
                "</header>"
                f"<p class='pole'><b>0 </b>{tx(question['pole0'])}</p>"
                f"<p class='pole'><b>4 </b>{tx(question['pole4'])}</p>"
                f"{consigne}</article>"
            )
        blocs.append("\n".join(cartes))
    intro = paras('''
    Chaque question est un axe. Le pôle 0 et le pôle 4 sont les deux bouts. Ni l’un ni l’autre n’est la bonne réponse de la méthode.
    La consigne en italique ne sert que là où la frontière entre les crans prête à confusion. Partout ailleurs, l’échelle générale s’applique :
    0 choix net du pôle bas, 1 penchant vers ce pôle, 2 silence ou milieu explicite, 3 penchant vers le pôle haut, 4 choix net du pôle haut.

    L’opérationnalité se code à part. 0, aucun instrument. 1, un dispositif, une loi, une taxe, un organisme. 2, cet instrument plus
    au moins un élément parmi une cible chiffrée, un calendrier, un financement. Quand le pôle lui-même décrit déjà un instrument,
    la note de position dit si le programme choisit ce pôle, et l’opérationnalité dit s’il en précise la dose.

    Deux questions voisines ne doivent pas être moyennées l’une avec l’autre avant la saisie. Le nucléaire et les renouvelables se codent séparément :
    un programme peut être haut sur les deux. L’âge de la retraite et la pénibilité aussi. L’usage de stupéfiants se code sur l’usage,
    pas sur la seule répression du trafic.
    ''')
    return chapitre("grille", "Les 100 questions", intro + "\n".join(blocs))


def section_exemple(calculs):
    evaluations = calculs["evaluations"]
    services, surete, centre, banc = evaluations
    b_services = ligne_candidat(services, "ouverture")
    a_services = ligne_candidat(services, "ancrage")
    c_centre = ligne_candidat(centre, "equilibre")
    a_centre = ligne_candidat(centre, "ancrage")
    specifie = sorted(centre["ordre"], key=lambda ligne: -ligne["score_specifie"])
    banc_strict = sorted(banc["ordre"], key=lambda ligne: -ligne["score_strict"])
    alertes = []
    for candidat in CANDIDATS:
        budget = ligne_candidat(services, candidat["id"])["budget"]
        alertes.append(
            "<tr>"
            f"<td>{tx(candidat['etiquette'])}</td>"
            f"<td class='num'>{fr(budget['depense'], 2)}</td>"
            f"<td class='num'>{fr(budget['recette'], 2)}</td>"
            f"<td class='num'>{fr(budget['ecart'], 2)}</td>"
            "</tr>"
        )
    depenses = ", ".join(str(n) for n in QUESTIONS_DEPENSE)
    recettes = ", ".join(str(n) for n in QUESTIONS_RECETTE)
    return chapitre("exemple", "Exemple sur trois candidats fictifs", appel("Avertissement", '''
    Les candidats A, B et C n’existent pas. Leurs notes n’ont pas été lues dans un programme.
    Elles ont été écrites pour que le calcul ait quelque chose à classer, et pour que l’ordre change avec le profil.
    Aucun nom de personne réelle n’est utilisé. Reprendre ces scores comme une indication de vote serait un contresens.
    ''') + paras(f'''
    A est étiqueté Ancrage, B Ouverture, C Équilibre.     C laisse huit questions sans note : les questions 4, 13, 36, 44, 54, 70, 82 et 93.
    A et B ont une note sur les 100. Dans cet exemple, et dans cet exemple seulement, l’opérationnalité n’est pas lue :
    elle est déduite de la note. Pour A et pour B, un 0 ou un 4 donne une opérationnalité de 2, un 1 ou un 3 donne 1, un 2 donne 0.
    Pour C, un 0 ou un 4 donne 1, et tout le reste donne 0. Un vrai compromis chiffré serait un 2 avec une opérationnalité de 2.
    L’exemple n’en contient pas. La précision de C, très basse, vient de cette règle mécanique. Elle ne prouve rien sur les programmes centristes réels.
    ''') + graphique(evaluations) + "<h3>Services publics et climat</h3>"
    + paras(services["intention"])
    + tableau_scores(services)
    + paras(f'''
    B est en tête, avec {fr(b_services['score'])}, devant C puis A, à {fr(a_services['score'])}.
    L’écart entre B et A est large. Les deux couvertures sont complètes, donc l’écart se décompose.
    ''')
    + tableau_contributions(services, sens=1)
    + tableau_domaines(services)
    + paragraphe_stabilite(services)
    + "<h3>Sûreté et pouvoir d’achat</h3>"
    + paras(surete["intention"])
    + tableau_scores(surete)
    + paras('''
    La tête change. A passe devant, B tombe en dernier. C reste au milieu. Les questions qui portent cet avantage de A sur B
    sont, pour l’essentiel, l’inverse du tableau précédent : sûreté, immigration, fiscalité, défense.
    ''')
    + tableau_contributions(surete, sens=-1)
    + tableau_domaines(surete)
    + paragraphe_stabilite(surete)
    + "<h3>Cibles au milieu, poids égaux</h3>"
    + paras(centre["intention"])
    + tableau_scores(centre)
    + paras(f'''
    C passe en tête sur la proximité, avec {fr(c_centre['score'])}, devant A à {fr(a_centre['score'])}.
    Le score strict ne change pas cette tête : C reste devant, parce que son avance de proximité est plus grande que le coût des huit questions vides.

    L’accord spécifié, lui, change la tête. Il place **{specifie[0]['nom']}** en premier, avec {fr(specifie[0]['score_specifie'])},
    puis {specifie[1]['nom']} à {fr(specifie[1]['score_specifie'])}, et {specifie[2]['nom']} à {fr(specifie[2]['score_specifie'])}.
    La raison est dans la règle mécanique de l’exemple : les notes 2 de C, qui font sa victoire de proximité, ont une opérationnalité nulle,
    et ne comptent plus que pour moitié. Les notes extrêmes mais outillées de A gardent une partie de leur proximité.
    Dès que l’on mélange « êtes-vous d’accord avec moi » et « votre mesure est-elle spécifiée », on répond aux deux questions à la fois,
    et l’on peut couronner un autre programme. C’est pour cela que le score principal ne fait pas ce mélange.
    ''')
    + paragraphe_stabilite(centre)
    + "<h3>Ce que l’exemple enseigne</h3>"
    + paras('''
    Le même codage produit trois têtes différentes. B gagne le profil de services et de climat, A gagne le profil de sûreté,
    C gagne le profil dont les cibles sont au milieu. Publier un seul podium sans le profil serait choisir, en le cachant,
    l’un de ces trois électeurs.

    Sur ces trois profils, l’écart de tête est assez grand pour que ni le retrait d’un domaine, ni le bruit de poids,
    ni le bruit d’un cran ne changent le premier. La stabilité n’est pas une vertu du programme. C’est une propriété de l’écart.
    Elle disparaît dès que l’écart devient petit. Le banc d’essai suivant le montre, et il montre aussi la limite du procédé :
    ses cibles ont été calculées à partir des notes, ce qu’un usage réel de la méthode interdit.
    ''')
    + "<h3>Banc d’essai, écart inférieur à un point</h3>"
    + paras(banc["intention"])
    + tableau_scores(banc)
    + paras(f'''
    Sur le score renormalisé, C devance A de {fr(banc['ecart_tete'], 2)} point.
    Sur le score strict, la tête passe à **{banc_strict[0]['nom']}**, à {fr(banc_strict[0]['score_strict'])},
    parce que les huit questions vides de C y valent zéro. Les deux règles de lecture ne désignent pas la même personne.
    On publierait les deux scores, pas un vainqueur.

    Le bruit sur les poids laisse C en tête dans {fr(100 * banc['stabilite_poids'])} % des tirages, au-dessus du seuil de {fr(100 * SEUIL_STABILITE, 0)} %.
    Le bruit d’un cran sur les notes ne le laisse en tête que dans {fr(100 * banc['stabilite_codage'])} % des tirages.
    Le classement est donc fragile au sens de cette note. Un écart qui se voit à la décimale ne survit pas à une erreur de codage ordinaire.
    ''')
    + "<h3>Alerte de lecture budgétaire</h3>"
    + paras(f'''
    Le score additionne des questions qui coûtent et des questions qui rapportent sans vérifier qu’elles tiennent ensemble.
    Une alerte grossière compare la position moyenne sur une liste fermée de questions de dépense
    ({depenses}) à la position moyenne sur une liste fermée de questions de recette ({recettes}).
    L’écart est en crans de la grille, pas en euros. Un écart positif veut dire que le programme est plus haut sur ces pôles de dépense
    que sur ces pôles de recette. Ce n’est pas une soutenabilité.
    ''')
    + "<table class='compacte'><thead><tr><th>Étiquette</th><th class='num'>Dépense</th>"
    + "<th class='num'>Recette</th><th class='num'>Écart</th></tr></thead><tbody>"
    + "".join(alertes)
    + "</tbody><caption>Positions moyennes sur les listes fermées, lues sur les notes, pas sur les proximités. "
    "Les trois candidats fictifs donnent le même ordre de grandeur quel que soit le profil, parce que l’alerte n’utilise pas les cibles.</caption></table>"
    + paras('''
    Sur ces listes, A est à 2,00 sur les dépenses retenues et à 1,00 sur les recettes retenues : les baisses d’impôt codées ne sont pas
    accompagnées d’un même mouvement vers les pôles de baisse de dépense. B est haut des deux côtés, à 3,83 et 3,67, donc plus aligné
    sur ce seul indicateur, tout en promettant beaucoup des deux. C est entre les deux. L’indicateur est trop court pour conclure.
    Il empêche seulement de lire un score élevé comme une preuve que « tout est financé ».
    ''')
    + appel("Cet exemple ne serait pas publiable", '''
    Il n’y a pas de citations, le mot FICTIF tient leur place, et il n’y a pas de double codage de la matrice.
    Le kappa montré plus haut est un tirage séparé, pas la mesure de cet exemple. La commande qui exige des citations refuse ces fichiers.
    C’est le comportement attendu.
    '''))


def section_emploi():
    return chapitre("emploi", "Refaire le calcul", paras('''
    Le calcul des scores n’a besoin que de Python, sans bibliothèque ajoutée. La présente note PDF a, elle, besoin de WeasyPrint.
    Les commandes se lancent depuis la racine du dépôt.
    ''') + """
    <p class="mono">python3 etude_programmes/algorithme.py verifier</p>
    <p class="mono">python3 etude_programmes/algorithme.py scorer --notes etude_programmes/modeles/notes_exemple.csv --profil etude_programmes/modeles/profil_services.csv</p>
    <p class="mono">python3 etude_programmes/algorithme.py scorer --notes etude_programmes/modeles/notes_exemple.csv --profil etude_programmes/modeles/profil_services.csv --exiger-citations</p>
    """ + paras('''
    La première commande vérifie les cas connus, dont l’exemple au crayon : 100 et 50. La deuxième calcule l’exemple fictif.
    La troisième doit échouer, parce que la colonne de citation contient FICTIF.

    Pour un usage réel, on copie un fichier de profil. On remplace chaque cible et chaque poids avant d’ouvrir les programmes.
    On remplit un fichier de notes, une ligne par candidat et par question : candidat, question, note, operationnalite, citation.
    Une note vide signifie que la question est hors corpus. Une citation vide, ou égale à FICTIF, est refusée dès que l’on demande
    le contrôle des sources, pour toute note autre que 2. Le 2, silence ou milieu, doit quand même être justifié dans le dossier de codage :
    la commande n’automatise pas ce contrôle-là.

    On régénère ce PDF, si l’on a WeasyPrint, par python3 etude_programmes/generer_etude.py. Le fichier requirements-pdf.txt fixe la version utilisée.
    ''') + appel("Ordre de travail", '''
    Écrire le profil. Calculer l’empreinte de la grille. Coder à deux. Mesurer le kappa. Arbitrer les écarts d’au moins deux crans.
    Lancer le score. Lire la couverture, le score strict et les deux stabilités. Publier la matrice avec les sources, ou ne pas classer.
    '''))


def section_limites():
    return chapitre("limites", "Limites", paras('''
    Le code 2 confond le silence et le choix explicite du milieu. Les deux ne sont pas la même chose politique.
    Les séparer demanderait un champ de plus. On ne l’a pas mis dans la formule principale, pour qu’elle reste une moyenne pondérée
    que l’on peut refaire dans un tableur. Quand la distinction compte, on la dit dans la citation, et l’on peut retirer la question
    avant le gel de la grille plutôt que de la coder de force.

    Les questions ne sont pas indépendantes. Un budget ne peut pas tout financer. L’alerte de lecture ne remplace pas un chiffrage.
    Elle utilise deux listes courtes, choisies dans cette note, qui ne couvrent ni toutes les dépenses ni toutes les recettes.

    Le levier indiqué est le levier principal, pas une étude juridique. Une même mesure passe souvent par la loi et par un décret,
    parfois par un texte européen. Le badge sert à ne pas oublier la question, pas à la trancher.

    La grille date de novembre 2026. La question sur l’agression d’un État européen prend l’Ukraine comme cas d’application à cette date.
    Une autre guerre, ou un accord de paix, n’annule pas la doctrine que la question cherche à coder, mais elle change les textes que les candidats écriront.
    On révise alors la consigne, on change l’empreinte, et l’on ne compare pas sans le dire une matrice ancienne à une matrice nouvelle.

    Le codage lit des intentions publiées. Il ne lit ni les votes passés, ni la crédibilité, ni la compétence, ni la personne.
    Deux programmes identiques sur les 100 questions sont égaux pour cette méthode, même si l’on a d’autres raisons de les distinguer.
    Ces autres raisons ne doivent pas être réintroduites en silence dans une note.

    Les seuils, 0,60 pour le kappa, 80 % pour la couverture, 70 % pour les deux stabilités, sont des conventions.
    Les abaisser fait apparaître des classements. Les relever en fait disparaître. On peut en choisir d’autres.
    On ne peut pas les choisir après avoir vu qui gagne.

    Enfin, un électeur peut remplir des cibles qu’aucun programme ne peut atteindre ensemble. Le meilleur score est alors un moins mauvais,
    et il peut rester médiocre. Le nombre le dit, si on le laisse dire. Un classement de trois scores à 40, 38 et 36 n’est pas une adhésion.
    ''') + appel("Usage", '''
    La méthode est faite pour un citoyen, une rédaction ou une équipe qui accepte de montrer son profil.
    Elle n’est pas faite pour produire une note unique de « qualité du programme » à diffuser sans la grille, sans les poids et sans les sources.
    '''))


def section_matrice(calculs):
    notes = calculs["notes"]
    services = next(e for e in calculs["evaluations"] if e["id"] == "services")
    surete = next(e for e in calculs["evaluations"] if e["id"] == "surete")
    # cibles reconstruites depuis les profils via les contributions ? Better import profil
    from donnees_exemple import PROFILS, profil_par_id
    cibles = {}
    for profil in PROFILS:
        if profil["id"] in ("services", "surete"):
            cibles[profil["id"]], _ = profil_par_id(profil)
    lignes = []
    for question in QUESTIONS:
        qid = question["id"]

        def note(cle):
            valeur = notes[cle][qid]
            return "—" if valeur is None else str(valeur)

        lignes.append(
            "<tr>"
            f"<td class='num'>{qid}</td>"
            f"<td>{tx(question['titre'])}</td>"
            f"<td class='num'>{note('ancrage')}</td>"
            f"<td class='num'>{note('ouverture')}</td>"
            f"<td class='num'>{note('equilibre')}</td>"
            f"<td class='num'>{cibles['services'][qid]}</td>"
            f"<td class='num'>{cibles['surete'][qid]}</td>"
            "</tr>"
        )
    return chapitre("matrice", "Annexe. Matrice de l’exemple", paras(f'''
    Les cibles du profil centriste valent 2 partout, et ses poids valent 1. Les cibles du banc d’essai sont le milieu arrondi
    des notes de A et de C, ou la note de A quand C est vide. Les poids par domaine des deux profils politiques sont dans le chapitre sur les poids.
    Cette annexe permet de refaire un score à la main sur un domaine. Empreinte de la grille : {calculs['empreinte']}.
    Valeurs de contrôle, au centième, du profil Services publics et climat : B {fr(ligne_candidat(services, 'ouverture')['score'], 2)},
    A {fr(ligne_candidat(services, 'ancrage')['score'], 2)}.
    Profil Sûreté : A {fr(ligne_candidat(surete, 'ancrage')['score'], 2)}, B {fr(ligne_candidat(surete, 'ouverture')['score'], 2)}.
    ''') + """
    <table class="matrice"><thead><tr>
      <th class="num">N°</th><th>Question</th>
      <th class="num">A</th><th class="num">B</th><th class="num">C</th>
      <th class="num">Cible services</th><th class="num">Cible sûreté</th>
    </tr></thead><tbody>
    """ + "".join(lignes) + "</tbody></table>")


def verifier_fichiers(calculs):
    notes, profils = ecrire_modeles(MODELES)
    commande = [
        sys.executable,
        str(ICI / "algorithme.py"),
        "scorer",
        "--notes",
        str(notes),
        "--profil",
        str(profils["services"]),
    ]
    fait = subprocess.run(commande, cwd=DEPOT, check=True, capture_output=True, text=True)
    score_commande = None
    for ligne in fait.stdout.splitlines():
        if ligne.startswith("ouverture\t"):
            score_commande = float(ligne.split("score=")[1].split("\t")[0])
    attendu = next(ligne["score"] for ligne in calculs["evaluations"][0]["ordre"] if ligne["id"] == "ouverture")
    if score_commande is None or abs(score_commande - attendu) > 1e-6:
        raise RuntimeError(f"le score de la ligne de commande ne correspond pas à l'étude :\n{fait.stdout}")
    refuse = subprocess.run(
        commande + ["--exiger-citations"],
        cwd=DEPOT,
        capture_output=True,
        text=True,
    )
    if refuse.returncode == 0 or "citations manquantes" not in refuse.stderr:
        raise RuntimeError(f"les citations FICTIF auraient dû être refusées : {refuse.stderr}")


def assembler(calculs, crayon):
    corps = "\n".join([
        section_ouverture(calculs),
        section_resume(),
        section_sens(),
        section_formules(crayon),
        section_protocole(calculs["kappa"]),
        section_poids(calculs["evaluations"]),
        section_grille(),
        section_exemple(calculs),
        section_emploi(),
        section_limites(),
        section_matrice(calculs),
    ])
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<title>Comparer les programmes, question par question</title>
<meta name="author" content="Note méthodologique"/>
<meta name="description" content="Algorithme pour noter 100 questions de programmes présidentiels et les pondérer."/>
<style>{css()}</style>
</head>
<body>
{corps}
</body>
</html>
"""


def main():
    verifier()
    calculs = tout_calculer(avec_simulation=True)
    question_45 = next(
        ligne for ligne in calculs["evaluations"][0]["face_a_face"] if ligne["question"] == 45
    )
    # face_a_face est appelé avec Ouverture en premier : proximite_a est B.
    if question_45["proximite_a"] <= question_45["proximite_b"]:
        raise RuntimeError("les colonnes de proximité B et A seraient inversées")
    verifier_fichiers(calculs)
    page = assembler(calculs, exemple_au_crayon())
    HTML(string=page, base_url=str(ICI)).write_pdf(str(PDF))
    print(PDF)


if __name__ == "__main__":
    main()
