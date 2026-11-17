# Journal de Bord — Projet TVA API VIES
> Meridian Distribution | 16-17 novembre 2026

---

## 16/11/2026 — Initialisation du projet

- Créer `.gitignore` **avant** `.venv` (évite de tracker des milliers de fichiers)
- `.venv` à la racine (détection automatique VS Code)
- `pip freeze > requirements.txt` après l'install

---

## 16/11/2026 — Phase 1 : Exploration (`exploration.ipynb`)

**Source de vérité (Q1)**
- CSV = Excel (`df_csv.equals(df_xlsx) → True`)
- Choix du CSV : plus léger, sans reformatage Excel

**Pays déclarés (Q2)**
- 15 valeurs distinctes dans `pays_declare`
  - 10 États membres UE : FR, DK, BE, LU, SE, PT, NL, IT, PL, FI
  - GB / UK (hors UE post-Brexit)
  - ZZ, QQ, XX (codes fictifs)
- Pour la France : 8 longueurs différentes, 44 préfixes distincts
  - Majuscule `FR`, minuscule `fr`, espaces, tirets, chiffres directs sans code pays

**Caractères parasites (Q3)**
- 18,13 % des lignes contiennent un caractère non alphanumérique
  - Espaces : 2 236 — Tirets : 471 — Points : 404

**Valeurs vides (Q4)**
- `pandas` convertit `null` et `N/A` en `NaN` au chargement
  - Utiliser `keep_default_na=False` pour voir les valeurs brutes
- 261 valeurs vides sous 6 formes : `""`, `"   "`, `"-"`, `"N/A"`, `"null"`, `"NU.LL"`

**Incohérences pays / préfixe (Q5)**
- Sans `.strip().upper()` : 1 645 faux positifs
- 793 vraies incohérences (7,93 %) :
  - ~532 préfixe pays omis
  - ~261 valeurs vides
  - 1 vrai conflit de pays

**Canaux et temporalité (Q6)**
- 5 canaux homogènes (~2 000 lignes chacun, taux d'anomalies identiques)
  - Aucun canal ne valide à la saisie → défaillance systémique
- 21 mois : 01/01/2024 → 01/10/2025, ~475 saisies/mois

---

## 17/11/2026 — Phase 2 : Nettoyage (`nettoyage.ipynb`)

**Restructuration**
- `validation_structure.py` déplacé de la racine vers `api/`
- Import dans les notebooks : `sys.path.append(str(Path("../api").resolve()))`

**Blocage résolu — `normaliser()` plante sur les `NaN`**
- `df["numero_tva"].apply(normaliser)` → `AttributeError: 'float' object has no attribute 'upper'`
- Cause : pandas stocke les vides en `NaN` (float), pas en `None`
  - `(None or "")` → `""` ✅ — `(float("nan") or "")` → `NaN` ❌
- Solution : `df["numero_tva"].fillna("").apply(normaliser)`
