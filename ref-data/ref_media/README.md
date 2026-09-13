# Table `ref_media`

Référentiel médias calé sur la **base France** (13 000 titres) :

1. **Type** : `Web` · `Print` · `TV` · `Radio`
2. **Couverture** : `Nationale` · `Régionale`

La France n’est pas rechargée ici (tu as déjà les 13 000). Les listes cibles sont **Belgique, Suisse, Portugal, Espagne**.

## Volumes (rebuild septembre 2026)

| Pays | Web | Print | TV | Radio | Nationale | Régionale | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| Belgique | 11 | 302 | 95 | 121 | 343 | 186 | 529 |
| Suisse | 173 | 255 | 105 | 64 | 316 | 281 | 597 |
| Portugal | 685 | 1 094 | 157 | 509 | 1 161 | 1 284 | 2 445 |
| Espagne | 9 | 691 | 188 | 169 | 227 | 830 | 1 057 |
| France (mapping) | 2 | 4 | 3 | 1 | 10 | 0 | 10 |

**4 638 médias** après dédoublonnage. Détail : `CATALOGUE.md`.

Ce n’est **pas** 13 000 par pays. En France, ce volume vient d’un fichier métier (locaux, associatifs, newsletters, web de niche). Les sources publiques équivalentes :

| Pays | Source principale | Plafond réaliste |
|---|---|---|
| Portugal | **ERC** — registres officiels au 01/09/2026 | ~2 200 OCS actifs (quasi complet) |
| Suisse | **Swissdox** (titres *aktuell*) + Wikipedia | centaines, pas des milliers |
| Belgique | Wikipedia + seed RP | Presscloud cite 950+ ; on est en dessous |
| Espagne | Wikipedia (journaux régionaux, radios, TV) | le registre audiovisuel d’État + CCAA ferait monter le TV/radio |

## Colonnes

| Colonne | Valeurs |
|---|---|
| `type_media` | `Web` `Print` `TV` `Radio` |
| `couverture` | `Nationale` `Régionale` |
| `priorite_rp` | 1–2 = seed pitching, 3 = registre / Wikipedia |
| `source_liste` | `SEED` `ERC` `SWISSDOX` `WIKIPEDIA` |

Les champs `support`, `periodicite`, `thematique`, `groupe_media`, `ville`, `url` sont remplis quand la source les donne (surtout ERC).

Mapping seed → tes catégories : quotidien / magazine → Print ; web natif / agence → Web ; télévision → TV ; radio → Radio. `Internationale` → `Nationale`.

## Fichiers

| Fichier | Usage |
|---|---|
| `ref_media.csv` | Import tableur / AppSheet |
| `ref_media.sql` | PostgreSQL |
| `ref_media.json` | API / mock |
| `CATALOGUE.md` | Synthèse + titres prioritaires |
| `harvest/official/pt_*.csv` | Extraits ERC 01/09/2026 |
| `harvest_and_build.py` | Rebuild |

## Rebuild

```sh
python3 ref-data/ref_media/harvest_and_build.py
```

`generate_ref_media.py` conserve le **seed prioritaire** (titres RP incontournables).
