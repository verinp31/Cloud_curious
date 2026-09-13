# Médias BE / CH / PT / ES

Livrable : **`ref_media.csv`**.

Les **valeurs** (type, famille, thématique, couverture) reprennent le vocabulaire de la base France [`OXYHUB_PROD_REF_MEDIA.sql`](https://github.com/verinp31/Cloud_curious/blob/master/OXYHUB_PROD_REF_MEDIA.sql). Pas de format dump / MySQL — tu changes de base plus tard.

## Colonnes

| Colonne | Valeurs |
|---|---|
| `id` | `MED-BE-0001` … |
| `nom` | Titre, casse d’origine |
| `pays_code` / `pays_nom` | BE Belgique · CH Suisse · PT Portugal · ES Espagne |
| `langue` | `fr` `nl` `de` `pt` `es` `it` … |
| `type_media` | `WEB` `PRESSE` `TV` `RADIO` `AGENCES` |
| `famille_media` | PQN, PQR, radios nationales, TV grandes chaînes, blogs… |
| `thematique_media` | `Actualités-Infos Générales`, `Economie - Services`, … |
| `couverture_geo` | `Nationale` · `Régionale/Départementale` · `Internationale` |
| `url` `groupe_media` `ville` `periodicite` | Quand la source les donne |
| `source_liste` | `SEED` `ERC` `SWISSDOX` `WIKIPEDIA` |
| `priorite_rp` | 1 = incontournable · 2 = important · 3 = registre |

France exclue (tu as déjà les 13 771).

## Rebuild

```sh
python3 ref-data/ref_media/test_oxyhub_map.py
python3 ref-data/ref_media/build_oxyhub.py
```

`build_oxyhub.py` relit `ref_media.json` (harvest) et réécrit le CSV. Pas de réseau.

## Sources harvest

| Pays | Source |
|---|---|
| Portugal | ERC (registres 01/09/2026) |
| Suisse | Swissdox + Wikipedia |
| Belgique | Wikipedia + seed RP |
| Espagne | Wikipedia + seed RP |

## « Média étranger » — dérivé, pas stocké

Le dump France mettait `famille_media = Médias étrangers` **sur la fiche média**. Ça ne tient que pour un observateur unique (la France). Dès qu’un client belge ou suisse utilise le même référentiel, la fiche devient fausse.

**Règle :** une seule fiche par titre, avec son `pays_code`. « Étranger » se calcule :

```
is_foreign = (media.pays_code != marche.pays_code)
```

- **Runtime (app)** : comparaison à la volée, pas de seconde ligne dans le CSV.
- **BI / warehouse** : même règle à la synchro, dénormalisée **par marché** (pas sur `dim_media` seule).

Le bon comparateur n’est pas le siège de l’agence ni le pays de l’utilisateur connecté : c’est le **marché de la campagne** (ou le pays de l’annonceur). Une agence parisienne qui pitche pour une marque suisse doit voir la NZZ comme domestique.

À ne pas confondre avec `couverture_geo = Internationale` (portée éditoriale : AFP, EFE) : un fil d’agence n’est pas « étranger », c’est un *wire*.

Filtres utiles en plus, toujours dérivés : même zone linguistique (`langue` média ∩ langues du marché), voisinage (FR↔BE francophone).
