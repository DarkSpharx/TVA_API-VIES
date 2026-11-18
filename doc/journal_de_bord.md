# Journal de Bord — Projet TVA API VIES
> Meridian Distribution

## Phase 1 : Exploration (`exploration.ipynb`)

**Choix de la source (Q1)**
- Choix du CSV : plus léger, sans reformatage Excel

**Pays déclarés (Q2)**
- 15 valeurs distinctes dans `pays_declare`
  - 10 États membres UE : FR, DK, BE, LU, SE, PT, NL, IT, PL, FI
  - GB / UK (hors UE post-Brexit)
  - ZZ, QQ, XX (ne correspondent à aucun pays)
- Pour la France : 8 longueurs différentes, 44 préfixes distincts
  - Majuscule `FR`, minuscule `fr`, espaces, tirets, chiffres directs sans code pays

**Caractères parasites (Q3)**
- 18,13 % des lignes contiennent un caractère non alphanumérique
  - Espaces : 2 236 
  - Tirets : 471
  - Points : 404

**Valeurs vides (Q4)**
- `pandas` convertit `null` et `N/A` en `NaN` au chargement
  - `keep_default_na=False` permet de voir les valeurs brutes
- 261 valeurs vides sous 6 formes : `""`, `"   "`, `"-"`, `"N/A"`, `"null"`, `"NU.LL"`

**Incohérences pays / préfixe (Q5)**
- Sans `.strip().upper()` : 1 645 faux positifs
- 793 véritables incohérences

**Canaux de saisie et périmètre temporel (Q6)**
- Canaux de saisie homogènes (~2 000 lignes chacun, taux d'anomalies identiques)
- 21 mois : 01/01/2024 → 01/10/2025, ~475 saisies/mois

## Phase 2 : Nettoyage (`nettoyage.ipynb`)

**Restructuration**
- Les notebooks ajoutent le dossier `api` au chemin d'import avec `sys.path.append(str(Path("../api").resolve()))`

**Blocage résolu — `normaliser()` plante sur les `NaN`**
- `df["numero_tva"].apply(normaliser)` → `AttributeError: 'float' object has no attribute 'upper'`
- Cause : pandas stocke les vides en `NaN` (float), pas en `None`
  - `(None or "")` → `""` ✅ — `(float("nan") or "")` → `NaN` ❌
- Première solution : `df["numero_tva"].fillna("").apply(normaliser)`

**Consigne du formateur — chargement et normalisation**
- Le CSV est chargé avec `pd.read_csv(data_dir / "numeros_tva.csv", dtype=str, keep_default_na=False)`.
- `dtype=str` conserve les colonnes comme du texte et `keep_default_na=False` empêche pandas de convertir les valeurs vides ou les textes comme `N/A` et `null` en `NaN`.
- Avec ce chargement, `df["numero_tva"].apply(normaliser)` suffit ; `.fillna("")` n'est plus utilisé.

**Normalisation et doublons**
- `normaliser()` met les numéros en majuscules et retire les caractères non alphanumériques.
- Le comptage des numéros normalisés exclut les marqueurs vides `""`, `NA` et `NULL`.
- 396 numéros normalisés apparaissent plusieurs fois, soit 438 occurrences supplémentaires.
- Après avoir gardé une seule ligne par numéro normalisé renseigné, le tableau contient 9 562 lignes. Les lignes avec un marqueur vide sont conservées.

**Validation structurelle**
- Les motifs renvoyés par `valider()` et leur traitement sont documentés dans le notebook.
- Après normalisation, `N/A` devient `NA`, et `null` ou `NU.LL` deviennent `NULL`. Transmis directement à `valider()`, ces marqueurs seraient classés `pays_non_couvert` plutôt que `vide`. Ils sont donc remplacés temporairement par une chaîne vide avant la validation, sans modifier la colonne normalisée.
- Sur les 9 562 lignes, 5 802 ont le motif `ok`, 2 499 `cle_invalide`, 1 000 `pays_non_couvert` et 261 `vide`.
- Le motif `ok` indique que le numéro passe le contrôle structurel ; il reste à vérifier dans VIES.

**Entonnoir chiffré**
- Le fichier contient 10 000 lignes au départ.
- Après avoir gardé une seule ligne par numéro normalisé renseigné, il en reste 9 562.
- 5 802 lignes sont candidates à une vérification par VIES.
- Le nettoyage évite 4 198 appels par rapport à un appel par ligne du fichier de départ.

**Échantillon de test VIES**
- Vérification réussie sur un échantillon de 20 numéros (`ok`). 
- Validation manuelle confirmée sur le portail officiel pour `LU32431802` (voir preuve dans `rapport_reconciliation.md`).
- Évaluation des limites techniques : les erreurs `MS_MAX_CONCURRENT_REQ` et `MS_UNAVAILABLE` ont été identifiées, justifiant la temporisation et la reprise sur interruption intégrées au script de collecte.

**Optimisation du pipeline de données**
- Export des candidats valides (`motif == "ok"`) dans un fichier dédié `data/numeros_tva_nettoyes.csv` pour séparer les données brutes des données nettoyées et éviter de manipuler le fichier de départ lors des appels API.


> Glossaire des erreurs API rencontrées
> - `MS_MAX_CONCURRENT_REQ` : Le serveur VIES est surchargé par trop de requêtes simultanées. Nécessite une pause entre les appels.
> - `MS_UNAVAILABLE` : Service VIES temporairement indisponible (maintenance ou panne serveur). Nécessite de relancer le script plus tard.
> - `INVALID` : Numéro de TVA inexistant ou inconnu dans le registre officiel européen.

## Phase 3 : Collecte API VIES (`api/collecte.py`)

- Mise à jour du script de collecte `api/collecte.py` pour qu'il cible directement ce fichier propre `numeros_tva_nettoyes.csv`.
- Implémentation du mode échantillon, de la temporisation (`time.sleep`), de la reprise sur interruption et de la journalisation des erreurs dans `doc/journal_collecte.log`.

## Phase 4 : Analyse et Restitution (`notebook/analyse.ipynb`)

- Création du rapport de réconciliation (`doc/rapport_reconciliation.md`) des 10 000 numéros TVA.
- Création du notebook d'analyse pour calculer les totaux de réconciliation (Valides, Invalides, Non tranchés) par extrapolation de l'échantillon.
- Génération des visualisations graphiques et sauvegarde dans `doc/graph/` pour intégration dans la note de synthèse.
- Rédaction de la note de synthèse à la direction financière.

> Glossaire des catégories (Phase 4)
> - **Valides** : Structure conforme et confirmé par l'API VIES.
> - **Invalides** : Numéro rejeté par la structure (clé fausse) OU rejeté par l'API (non existant).
> - **Non tranchés** : Numéro structurellement correct mais sans réponse définitive de l'API (erreurs techniques).
> - **Clé invalide** : Échec de l'algorithme mathématique national.
> - **Pays non couvert** : Numéro hors périmètre des 10 pays gérés.
> - **Valeurs vides** : Absence de donnée (NA, NULL, vide).