"""
Connexion PostgreSQL et fonctions de requêtage pour le dashboard ImmoInsight Maroc.

Toutes les fonctions de lecture sont décorées avec @st.cache_data pour éviter
de re-solliciter la base à chaque interaction utilisateur (changement de page,
de filtre, etc.). Le moteur SQLAlchemy est mis en cache avec @st.cache_resource
car il doit être créé une seule fois et réutilisé (connexion persistante).

Schéma DWH (constellation) — rappel des tables utilisées ici :
    dim_geographie   (id_geo, quartier, commune, ville, region, pays, latitude, longitude)
    dim_type_bien    (id_type_bien, categorie_bkam, type_precision, type_usage)
    dim_source_web   (id_source, nom_plateforme, url_base, date_scraping)
    fait_annonces_actuelles (id_annonce, id_geo, id_temps, id_type_bien, id_source,
                              titre, prix_affiche_mad, surface_m2, prix_m2, nb_pieces,
                              nb_chambres, nb_salles_bains, etage, ascenseur, terrasse,
                              parking, ratio_prix_marche, score_nlp, ...)
"""

import os
from typing import Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


def _get_db_credentials() -> dict:
    """
    Renvoie les identifiants de connexion PostgreSQL.

    - En local : lus depuis le fichier .env (DB_HOST, DB_PORT, DB_NAME, DB_USER,
      DB_PASSWORD), comme actuellement.
    - Sur Streamlit Community Cloud : lus depuis st.secrets, configurés dans les
      "Secrets" de l'app sous la forme :

          [postgres]
          host = "..."
          port = "5432"
          dbname = "..."
          user = "..."
          password = "..."

      (ce sera votre base Neon, au moment du déploiement)
    """
    try:
        if "postgres" in st.secrets:
            s = st.secrets["postgres"]
            return {
                "host": s["host"],
                "port": s["port"],
                "dbname": s["dbname"],
                "user": s["user"],
                "password": s["password"],
            }
    except Exception:
        pass  # pas de secrets.toml -> environnement local, on utilise .env

    return {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }


@st.cache_resource(show_spinner=False)
def get_engine():
    """Crée (une seule fois grâce au cache) le moteur SQLAlchemy vers PostgreSQL."""
    creds = _get_db_credentials()
    url = (
        f"postgresql+psycopg2://{creds['user']}:{creds['password']}"
        f"@{creds['host']}:{creds['port']}/{creds['dbname']}"
    )
    return create_engine(url, pool_pre_ping=True)


def run_query(sql: str, params: Optional[dict] = None) -> pd.DataFrame:
    """Exécute une requête SQL brute et retourne un DataFrame."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


# ============================================================
# Listes de référence (pour peupler les filtres)
# ============================================================

@st.cache_data(ttl=600, show_spinner=False)
def get_villes_disponibles() -> list:
    df = run_query("SELECT DISTINCT ville FROM dim_geographie WHERE ville IS NOT NULL ORDER BY ville;")
    return df["ville"].tolist()


@st.cache_data(ttl=600, show_spinner=False)
def get_types_bien_disponibles() -> list:
    df = run_query("SELECT DISTINCT type_precision FROM dim_type_bien ORDER BY type_precision;")
    return df["type_precision"].tolist()


@st.cache_data(ttl=600, show_spinner=False)
def get_quartiers_disponibles(ville: Optional[str] = None) -> list:
    if ville:
        df = run_query(
            "SELECT DISTINCT quartier FROM dim_geographie "
            "WHERE ville = :ville AND quartier IS NOT NULL ORDER BY quartier;",
            {"ville": ville},
        )
    else:
        df = run_query("SELECT DISTINCT quartier FROM dim_geographie WHERE quartier IS NOT NULL ORDER BY quartier;")
    return df["quartier"].tolist()


# ============================================================
# Données annonces (table de faits principale)
# ============================================================

@st.cache_data(ttl=600, show_spinner="Chargement des annonces...")
def get_annonces(villes: Optional[list] = None, types_bien: Optional[list] = None) -> pd.DataFrame:
    """
    Charge les annonces actuelles jointes aux dimensions géographie, type de bien
    et source. Filtrable par ville(s) et type(s) de bien pour limiter le volume
    transféré depuis PostgreSQL.
    """
    sql = """
        SELECT
            a.id_annonce,
            g.ville,
            g.quartier,
            g.latitude,
            g.longitude,
            tb.type_precision AS type_bien,
            src.nom_plateforme AS source,
            a.prix_affiche_mad,
            a.surface_m2,
            a.prix_m2,
            a.nb_pieces,
            a.nb_chambres,
            a.nb_salles_bains,
            a.etage,
            a.ascenseur,
            a.terrasse,
            a.parking,
            a.score_nlp,
            a.ratio_prix_marche
        FROM fait_annonces_actuelles a
        JOIN dim_geographie g   ON a.id_geo = g.id_geo
        JOIN dim_type_bien  tb  ON a.id_type_bien = tb.id_type_bien
        JOIN dim_source_web src ON a.id_source = src.id_source
        WHERE a.prix_affiche_mad IS NOT NULL
          AND a.surface_m2 IS NOT NULL
    """
    conditions = []
    params: dict = {}
    if villes:
        conditions.append("g.ville = ANY(:villes)")
        params["villes"] = villes
    if types_bien:
        conditions.append("tb.type_precision = ANY(:types_bien)")
        params["types_bien"] = types_bien
    if conditions:
        sql += " AND " + " AND ".join(conditions)

    return run_query(sql, params)


# ============================================================
# Agrégats pour la page Accueil
# ============================================================

@st.cache_data(ttl=600, show_spinner=False)
def get_kpis_globaux() -> dict:
    """KPIs globaux : volumétrie, prix moyens, couverture géographique et sources."""
    df = run_query("""
        SELECT
            COUNT(*)                     AS nb_annonces,
            ROUND(AVG(prix_affiche_mad)) AS prix_moyen,
            ROUND(AVG(prix_m2))          AS prix_m2_moyen,
            ROUND(AVG(surface_m2))       AS surface_moyenne
        FROM fait_annonces_actuelles
        WHERE prix_affiche_mad IS NOT NULL;
    """)
    nb_villes = run_query("SELECT COUNT(DISTINCT ville) AS n FROM dim_geographie WHERE ville IS NOT NULL;")
    nb_quartiers = run_query("SELECT COUNT(DISTINCT quartier) AS n FROM dim_geographie WHERE quartier IS NOT NULL;")
    nb_sources = run_query("SELECT COUNT(DISTINCT id_source) AS n FROM dim_source_web;")

    row = df.iloc[0]
    return {
        "nb_annonces": int(row["nb_annonces"] or 0),
        "prix_moyen": float(row["prix_moyen"]) if row["prix_moyen"] is not None else None,
        "prix_m2_moyen": float(row["prix_m2_moyen"]) if row["prix_m2_moyen"] is not None else None,
        "surface_moyenne": float(row["surface_moyenne"]) if row["surface_moyenne"] is not None else None,
        "nb_villes": int(nb_villes.iloc[0]["n"] or 0),
        "nb_quartiers": int(nb_quartiers.iloc[0]["n"] or 0),
        "nb_sources": int(nb_sources.iloc[0]["n"] or 0),
    }


@st.cache_data(ttl=600, show_spinner="Chargement des quartiers...")
def get_carte_quartiers(villes: Optional[list] = None) -> pd.DataFrame:
    """
    Agrégats par quartier (nb annonces, prix moyen, prix/m² moyen) avec
    coordonnées, pour alimenter la carte interactive. Un quartier doit avoir
    au moins 3 annonces pour apparaître, afin d'éviter que des quartiers avec
    une seule annonce isolée ne faussent visuellement l'échelle de couleur.
    """
    sql = """
        SELECT
            g.quartier,
            g.ville,
            g.latitude,
            g.longitude,
            COUNT(*) AS nb_annonces,
            ROUND(AVG(a.prix_m2)) AS prix_m2_moyen,
            ROUND(AVG(a.prix_affiche_mad)) AS prix_moyen
        FROM fait_annonces_actuelles a
        JOIN dim_geographie g ON a.id_geo = g.id_geo
        WHERE g.quartier IS NOT NULL
          AND g.latitude IS NOT NULL
          AND g.longitude IS NOT NULL
          AND a.prix_m2 IS NOT NULL
    """
    params: dict = {}
    if villes:
        sql += " AND g.ville = ANY(:villes)"
        params["villes"] = villes

    sql += """
        GROUP BY g.quartier, g.ville, g.latitude, g.longitude
        HAVING COUNT(*) >= 3
        ORDER BY nb_annonces DESC;
    """
    return run_query(sql, params)



@st.cache_data(ttl=600, show_spinner=False)
def get_villes_avec_profils() -> list:
    """Villes ayant au moins un quartier profilé (clustering K-Means/DBSCAN)."""
    df = run_query("""
        SELECT DISTINCT g.ville
        FROM dim_profil_quartier p
        JOIN dim_geographie g ON p.id_geo = g.id_geo
        ORDER BY g.ville;
    """)
    return df["ville"].tolist()


@st.cache_data(ttl=600, show_spinner=False)
def get_quartiers_profil_disponibles(ville: str) -> list:
    """Quartiers profilés pour une ville donnée."""
    df = run_query("""
        SELECT g.quartier
        FROM dim_profil_quartier p
        JOIN dim_geographie g ON p.id_geo = g.id_geo
        WHERE g.ville = :ville
        ORDER BY g.quartier;
    """, {"ville": ville})
    return df["quartier"].tolist()


@st.cache_data(ttl=600, show_spinner=False)
def get_profil_quartier(ville: str, quartier: str):
    """Profil complet d'un quartier : stats, cluster, label, coordonnées."""
    df = run_query("""
        SELECT
            g.quartier, g.ville, g.latitude, g.longitude,
            p.n_annonces, p.prix_m2_moyen, p.prix_m2_median, p.prix_m2_std,
            p.surface_moyenne, p.chambres_moyenne,
            p.pct_appartement, p.pct_maison, p.pct_riad, p.pct_villa,
            p.cluster_kmeans, p.cluster_dbscan, p.label_profil, p.quartier_atypique
        FROM dim_profil_quartier p
        JOIN dim_geographie g ON p.id_geo = g.id_geo
        WHERE g.ville = :ville AND g.quartier = :quartier;
    """, {"ville": ville, "quartier": quartier})
    return df.iloc[0] if not df.empty else None


@st.cache_data(ttl=600, show_spinner=False)
def get_quartiers_similaires(label_profil: str, ville: str, exclure_quartier: str, limit: int = 5):
    """
    Autres quartiers du même profil (même label K-Means), dans la même ville
    en priorité, pour donner du contexte comparatif.
    """
    df = run_query("""
        SELECT g.quartier, g.ville, p.prix_m2_moyen, p.n_annonces
        FROM dim_profil_quartier p
        JOIN dim_geographie g ON p.id_geo = g.id_geo
        WHERE p.label_profil = :label
          AND NOT (g.ville = :ville AND g.quartier = :quartier)
        ORDER BY (g.ville = :ville) DESC, p.n_annonces DESC
        LIMIT :limit;
    """, {"label": label_profil, "ville": ville, "quartier": exclure_quartier, "limit": limit})
    return df


@st.cache_data(ttl=600, show_spinner=False)
def get_historique_ipai(ville: str, type_bien: str) -> pd.DataFrame:
    """
    Historique trimestriel de l'indice IPAI (BKAM) pour une ville et un
    type de bien donnés. Rappel méthodologique : les valeurs intermédiaires
    entre les points officiels publiés par BKAM ont été interpolées, faute
    de série complète en accès libre (voir note méthodologique du rapport).

    Note technique : dim_temps.date_exacte est NULL pour ces lignes (seuls
    annee/trimestre ont été renseignés à l'origine) — la date est donc
    reconstruite ici via MAKE_DATE plutôt que d'utiliser date_exacte.
    """
    return run_query("""
        SELECT
            MAKE_DATE(t.annee, (t.trimestre - 1) * 3 + 1, 1) AS date_calculee,
            t.annee, t.trimestre, f.indice_ipai_bkam, f.variation_trimestrielle
        FROM fait_historique_prix f
        JOIN dim_geographie g ON f.id_geo = g.id_geo
        JOIN dim_type_bien tb ON f.id_type_bien = tb.id_type_bien
        JOIN dim_temps t ON f.id_temps = t.id_temps
        WHERE g.ville = :ville AND tb.type_precision = :type_bien
        ORDER BY t.annee, t.trimestre;
    """, {"ville": ville, "type_bien": type_bien})


@st.cache_data(ttl=600, show_spinner="Chargement des opportunités...")
def get_opportunites(villes: Optional[list] = None, types_bien: Optional[list] = None) -> pd.DataFrame:
    """
    Annonces avec un ratio_prix_marche calculé (prix réel / prix prédit par
    le modèle ML), classées en Sous-évalué / Normal / Sur-évalué / Anomalie
    suspecte selon les seuils calés sur les percentiles réels de la
    distribution (P1=0.294, P10=0.673, P90=1.277, P99=1.889 — voir
    03_ml/06_detection_anomalies.py). Limité aux types de bien ayant un
    modèle de prix (Appartement, Riad, Maison, Villa).
    """
    sql = """
        SELECT
            a.id_annonce, g.ville, g.quartier, tb.type_precision AS type_bien,
            a.surface_m2, a.nb_chambres, a.prix_affiche_mad, a.prix_m2, a.ratio_prix_marche,
            CASE
                WHEN a.ratio_prix_marche < 0.294 OR a.ratio_prix_marche > 1.889 THEN 'Anomalie suspecte'
                WHEN a.ratio_prix_marche < 0.673 THEN 'Sous-évalué'
                WHEN a.ratio_prix_marche > 1.277 THEN 'Sur-évalué'
                ELSE 'Normal'
            END AS statut_prix
        FROM fait_annonces_actuelles a
        JOIN dim_geographie g ON a.id_geo = g.id_geo
        JOIN dim_type_bien tb ON a.id_type_bien = tb.id_type_bien
        WHERE a.ratio_prix_marche IS NOT NULL
    """
    conditions = []
    params: dict = {}
    if villes:
        conditions.append("g.ville = ANY(:villes)")
        params["villes"] = villes
    if types_bien:
        conditions.append("tb.type_precision = ANY(:types_bien)")
        params["types_bien"] = types_bien
    if conditions:
        sql += " AND " + " AND ".join(conditions)
    sql += " ORDER BY a.ratio_prix_marche ASC;"

    return run_query(sql, params)


@st.cache_data(ttl=3600, show_spinner=False)
def get_demographie(villes: list) -> pd.DataFrame:
    """
    Démographie par ville. Seule population_totale varie réellement ;
    taux_chomage/pib_par_habitant/taux_urbanisation sont des chiffres
    nationaux dupliqués (source HCP/Banque Mondiale, non désagrégés par
    ville) — à ne jamais présenter comme une variation entre villes.
    """
    return run_query("""
        SELECT g.ville, f.population_totale, f.taux_chomage,
               f.pib_par_habitant, f.taux_urbanisation
        FROM fait_socio_demographique f
        JOIN dim_geographie g ON f.id_geo = g.id_geo
        WHERE g.ville = ANY(:villes)
        ORDER BY g.ville;
    """, {"villes": villes})


@st.cache_data(ttl=3600, show_spinner=False)
def get_climat(villes: list) -> pd.DataFrame:
    """
    Relevé météo par ville — un instantané au moment du scraping (les
    colonnes min/moyenne/max sont identiques), pas une moyenne climatique
    annuelle. À présenter comme tel dans l'interface.
    """
    return run_query("""
        SELECT g.ville, f.temperature_moyenne, f.humidite, f.vent_kmh, f.description
        FROM fait_climat_meteo f
        JOIN dim_geographie g ON f.id_geo = g.id_geo
        WHERE g.ville = ANY(:villes)
        ORDER BY g.ville;
    """, {"villes": villes})


@st.cache_data(ttl=600, show_spinner=False)
def get_repartition_par_ville() -> pd.DataFrame:
    return run_query("""
        SELECT g.ville, COUNT(*) AS nb_annonces, ROUND(AVG(a.prix_m2)) AS prix_m2_moyen
        FROM fait_annonces_actuelles a
        JOIN dim_geographie g ON a.id_geo = g.id_geo
        WHERE a.prix_m2 IS NOT NULL
        GROUP BY g.ville
        ORDER BY nb_annonces DESC;
    """)


@st.cache_data(ttl=600, show_spinner=False)
def get_repartition_par_type() -> pd.DataFrame:
    """
    Répartition par type de bien, limitée aux 5 catégories les plus
    fréquentes ; le reste est regroupé sous "Autres" pour garder un
    camembert lisible (dim_type_bien compte jusqu'à 13 types normalisés,
    afficher toutes les tranches nuirait à la lisibilité et dépasserait
    la palette catégorielle à 6 couleurs).
    """
    df = run_query("""
        SELECT tb.type_precision AS type_bien, COUNT(*) AS nb_annonces, ROUND(AVG(a.prix_m2)) AS prix_m2_moyen
        FROM fait_annonces_actuelles a
        JOIN dim_type_bien tb ON a.id_type_bien = tb.id_type_bien
        WHERE a.prix_m2 IS NOT NULL
        GROUP BY tb.type_precision
        ORDER BY nb_annonces DESC;
    """)
    if len(df) <= 5:
        return df

    top5 = df.iloc[:5].copy()
    reste = df.iloc[5:]
    ligne_autres = pd.DataFrame([{
        "type_bien": "Autres",
        "nb_annonces": reste["nb_annonces"].sum(),
        "prix_m2_moyen": (reste["nb_annonces"] * reste["prix_m2_moyen"]).sum() / reste["nb_annonces"].sum(),
    }])
    return pd.concat([top5, ligne_autres], ignore_index=True)
