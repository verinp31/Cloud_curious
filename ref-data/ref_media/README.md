# Table `ref_media`

Référentiel des médias à pitcher en relations presse.

La table `ref_media` n’est pas présente dans ce dépôt. Le schéma ci-dessous reprend le format habituel d’un référentiel RP (SaaS relations presse / phase Amon) : un média = une ligne, identifiée par pays, type, langue, groupe et priorité de pitching.

Les **10 titres français** servent d’**exemple de colonnes**. Les listes demandées sont **Belgique, Suisse, Portugal, Espagne**.

## Fichiers

| Fichier | Usage |
|---|---|
| `ref_media.csv` | Import tableur / AppSheet / Liferay |
| `ref_media.sql` | Création + seed PostgreSQL |
| `ref_media.json` | API / mock CRM |
| `CATALOGUE.md` | Lecture humaine par pays |
| `generate_ref_media.py` | Source unique — régénère les 4 livrables |

## Colonnes

| Colonne | Type | Règle |
|---|---|---|
| `id_media` | `MED-{pays}-{nnn}` | Clé primaire stable |
| `code` | slug majuscule | Unique, pour jointures |
| `nom` | texte | Marque éditoriale |
| `pays_code` | ISO 3166-1 alpha-2 | `FR` `BE` `CH` `PT` `ES` |
| `pays_nom` | texte FR | |
| `langue` | ISO 639-1 | `fr` `nl` `de` `it` `rm` `pt` `es` `ca` |
| `type_media` | enum | Presse quotidienne, Presse magazine, Web natif, Télévision, Radio, Agence de presse |
| `support` | enum | Print+Digital, Digital, Audiovisuel, Agence |
| `periodicite` | enum | Quotidien, Hebdomadaire, Bihebdomadaire, Bimensuel, Mensuel, Continu |
| `thematique` | enum | Généraliste, Économie, Sport, People, Régional, Tech |
| `couverture` | enum | Nationale, Régionale, Internationale |
| `groupe_media` | texte | Propriétaire / éditeur |
| `ville` | texte | Siège rédactionnel principal |
| `url` | URL | Site officiel |
| `priorite_rp` | 1–3 | 1 = incontournable, 2 = important, 3 = complémentaire |
| `actif` | booléen | Titre encore édité |
| `notes` | texte | Usage pitching, audience, particularité |
| `source_liste` | enum | `EXEMPLE` (FR) ou `CIBLE` (BE/CH/PT/ES) |

## Périmètre

Ce n’est **pas** un annuaire exhaustif (Presscloud suit 950+ médias en Belgique seule). C’est la **liste prioritaire** pour une agence RP : nationaux de référence, éco, TV/radio leaders, agences de presse, quelques PQR et pure players à forte portée.

| Pays | Lignes | Point d’attention |
|---|---|---|
| France | 10 | Exemple de structure uniquement |
| Belgique | 32 | FR + NL + 1 titre germanophone |
| Suisse | 30 | DE + FR + IT + 1 titre romanche ; aligné liste COPA |
| Portugal | 28 | Impresa / Medialivre / Media Capital / RTP / Lusa |
| Espagne | 35 | Nationaux + éco + TV/radio EGM 2026 + CA + PQR |

**135 médias** au total.

## Sources (septembre 2026)

- Belgique : Belga (clients / marques), Presscloud, AJP (audiovisuel)
- Suisse : circulaire COPA n°4 (médias principaux), Monitoring médias Suisse, Swissdox
- Portugal : Reuters Institute *Digital News Report 2026*, groupes Impresa / Medialivre / RTP / Lusa
- Espagne : 2e vague EGM 2026 (AIMC)

Les audiences citées dans `notes` datent de 2026 et sont des ordres de grandeur pour prioriser, pas des KPI contractuels.

## Rechargement

```sh
python3 ref-data/ref_media/generate_ref_media.py
```
