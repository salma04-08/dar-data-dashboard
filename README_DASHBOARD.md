# ImmoInsight Maroc — Dashboard Streamlit (Module 7)

## Structure

```
06_dashboard/
├── app.py                  # Point d'entrée : navigation + thème global
├── pages/
│   ├── accueil.py           # ✅ Phase 1 — KPIs globaux, vue d'ensemble
│   ├── analyse_marche.py    # ✅ Phase 1 — exploration filtrable, distributions
│   ├── carte_interactive.py # 🚧 Phase 2 — carte Folium
│   ├── profil_quartiers.py  # 🚧 Phase 2 — fiche détaillée par quartier
│   ├── estimation_prix.py   # 🚧 Phase 3 — simulateur ML
│   ├── previsions.py        # 🚧 Phase 3 — SARIMA / IPAI
│   ├── opportunites.py      # 🚧 Phase 4 — détection d'anomalies
│   ├── recommandations.py   # 🚧 Phase 4 — moteur de recommandation
│   └── comparaison_villes.py# 🚧 Phase 5 — bonus
├── utils/
│   └── db.py                # Connexion PostgreSQL + requêtes mises en cache
└── .streamlit/
    └── config.toml          # Thème (couleurs, police)
```

## Avant de lancer

Ce squelette utilise `st.navigation` / `st.Page`, l'API multipage moderne de
Streamlit, disponible à partir de la version **1.36**. Votre `requirements.txt`
actuel épingle `streamlit==1.35.0`, il faut donc mettre à jour :

```powershell
pip install --upgrade "streamlit>=1.38,<2.0"
```

Puis mettez à jour la ligne correspondante dans `requirements.txt` pour rester
cohérente (remplacez `streamlit==1.35.0` par la version installée, visible via
`pip show streamlit`).

## Installation dans votre projet

1. Copiez le dossier `06_dashboard/` de cette archive à la racine de votre
   projet (`C:\Users\fatimazahra\Documents\immo_maroc\`), en fusionnant avec
   le dossier `06_dashboard/pages` déjà existant.
2. Vérifiez que votre fichier `.env` à la racine du projet contient bien
   `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

## Lancer le dashboard

Depuis la racine du projet (important pour que `.env` soit trouvé) :

```powershell
cd C:\Users\fatimazahra\Documents\immo_maroc
venv\Scripts\activate
streamlit run 06_dashboard/app.py
```

## Point d'attention sur les noms de colonnes

`utils/db.py` interroge `fait_annonces_actuelles`, `dim_geographie`,
`dim_type_bien` et `dim_source_web` avec les noms de colonnes de votre schéma
validé (`prix_affiche_mad`, `surface_m2`, `prix_m2`, `type_precision`,
`nom_plateforme`, etc.). Si une requête échoue avec une erreur du type
`column "..." does not exist`, comparez avec votre script
`02_etl/01_create_schema.py` — le nom aura probablement légèrement changé
depuis.

## Déploiement cloud (à faire plus tard)

Voir `DEPLOY.md` — guide complet pour déployer sur Streamlit Community Cloud
avec une base Neon (PostgreSQL gratuit). **À faire seulement quand le
dashboard sera fonctionnellement complet**, pas maintenant : une seule
migration en fin de projet coûte moins de temps que plusieurs migrations
au fil des phases. Le code (`utils/db.py`) est déjà prêt pour ça — il
détecte automatiquement s'il tourne en local (`.env`) ou sur le cloud
(`st.secrets`).

## Prochaine étape

Phase 2 : Carte interactive (Folium) + Profil des quartiers.
