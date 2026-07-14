# Déploiement cloud — ImmoInsight Maroc Dashboard

À faire **une seule fois**, quand le dashboard est fonctionnellement complet
(recommandé : ~3-4 jours avant la soutenance, pas avant). Objectif : un lien
public en plus de la version locale, qui reste votre filet de sécurité.

---

## Étape 0 — Décision de structure : un repo GitHub dédié au dashboard

Streamlit Community Cloud impose une contrainte : `.streamlit/config.toml`
doit être **à la racine du repo GitHub**. Plutôt que de pousser tout
`immo_maroc/` (scripts de scraping, notebooks, données brutes, modèles...)
dans un repo public, créez un **repo séparé qui ne contient que le dossier
`06_dashboard/`** — son contenu devient la racine du repo.

```
immoinsight-dashboard/          <- racine du nouveau repo GitHub
├── app.py
├── pages/
├── utils/
├── .streamlit/
│   └── config.toml
├── requirements.txt
└── README_DASHBOARD.md
```

Avantages : pas de fuite accidentelle de données/scripts, `requirements.txt`
et `config.toml` tombent naturellement à la racine (zéro ambiguïté pour
Streamlit Cloud), déploiement plus rapide (repo plus léger).

```powershell
cd C:\Users\fatimazahra\Documents\immo_maroc\06_dashboard
git init
git add .
git commit -m "Dashboard ImmoInsight Maroc"
```

Créez le repo sur GitHub (public ou privé — les deux fonctionnent avec
Community Cloud), puis :

```powershell
git remote add origin https://github.com/<votre_user>/immoinsight-dashboard.git
git branch -M main
git push -u origin main
```

**Important :** ajoutez un `.gitignore` avant le premier commit pour ne
jamais pousser de secrets :

```
__pycache__/
*.pyc
.streamlit/secrets.toml
```

(`.env` n'existe pas dans ce repo puisqu'il ne contient que `06_dashboard/`,
donc pas de risque de le pousser par erreur — mais gardez le réflexe.)

---

## Étape 1 — Migrer la base PostgreSQL locale vers Neon (cloud, gratuit)

1. Créez un compte sur **neon.com** (gratuit, pas de carte bancaire requise).
2. Créez un projet, choisissez une région proche (Europe si possible pour la
   latence). Neon vous donne une **chaîne de connexion** du type :
   ```
   postgresql://<user>:<password>@<host>/<dbname>?sslmode=require
   ```
   Notez séparément `host`, `user`, `password`, `dbname` (port = 5432).

3. Exportez votre base locale avec `pg_dump` (fourni avec votre install
   PostgreSQL 16, dans `C:\Program Files\PostgreSQL\16\bin`) :

   ```powershell
   cd "C:\Program Files\PostgreSQL\16\bin"
   .\pg_dump.exe -h localhost -U immo_user -d immo_maroc -F c -f "C:\Users\fatimazahra\Documents\immo_maroc\immo_maroc.dump"
   ```
   (mot de passe `immo_user` demandé à l'exécution)

4. Restaurez ce dump dans Neon :

   ```powershell
   .\pg_restore.exe -d "postgresql://<user>:<password>@<host>/<dbname>?sslmode=require" "C:\Users\fatimazahra\Documents\immo_maroc\immo_maroc.dump"
   ```

5. Vérifiez rapidement (depuis `psql` ou pgAdmin connecté à Neon) que
   `SELECT COUNT(*) FROM fait_annonces_actuelles;` renvoie bien le même
   nombre de lignes qu'en local.

Votre volumétrie (~48 000 annonces + dimensions + historique BKAM) tient
largement dans le tier gratuit de Neon (0.5 Go de stockage, largement
suffisant pour des données majoritairement numériques/texte à cette échelle).

---

## Étape 2 — Configurer les secrets sur Streamlit Community Cloud

Sur **share.streamlit.io** :

1. "New app" → connectez votre GitHub → sélectionnez le repo
   `immoinsight-dashboard`, branche `main`, fichier principal `app.py`
   (à la racine du repo cette fois, donc pas de chemin `06_dashboard/`).
2. Avant de cliquer "Deploy", ouvrez **"Advanced settings" → Secrets** et
   collez :

   ```toml
   [postgres]
   host = "<host Neon>"
   port = "5432"
   dbname = "<dbname Neon>"
   user = "<user Neon>"
   password = "<password Neon>"
   ```

   C'est exactement la structure que lit `_get_db_credentials()` dans
   `utils/db.py` — aucune modification de code nécessaire.

3. Déployez. Le premier build prend quelques minutes.

---

## Étape 3 — Vérifications post-déploiement

- Testez chaque page déjà construite (Accueil, Analyse du marché).
- Si une page échoue avec `column "..." does not exist`, c'est un décalage
  entre le schéma migré et les requêtes — comparez avec
  `02_etl/01_create_schema.py`.
- Streamlit Community Cloud (tier gratuit) met l'app en veille après une
  période d'inactivité ; le premier visiteur après une pause attend ~30s
  pendant le réveil. Pensez à "réveiller" le lien vous-même 10-15 minutes
  avant de le montrer au jury.

---

## Étape 4 — Garder le local synchronisé

Le dashboard local continue de pointer sur votre PostgreSQL local via
`.env` — aucun changement. Les deux environnements coexistent sans conflit
grâce à `_get_db_credentials()`. Si vous corrigez des données en local après
la migration, il faudra refaire un `pg_dump`/`pg_restore` vers Neon avant la
soutenance si vous comptez présenter le lien cloud.
