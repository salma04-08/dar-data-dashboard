"""
Chargement des modèles de prédiction de prix (XGBoost/Random Forest,
Module 3) et utilitaires d'encodage pour la page Estimation du prix.

Les 5 features utilisées à l'entraînement (voir 03_ml/02_entrainer_modeles.py) :
    surface_m2, nb_chambres, ville_enc, quartier_enc, source_enc

- ville_enc / quartier_enc / source_enc viennent de LabelEncoder sauvegardés
  (07_data/models/encodeur_*.joblib), entraînés sur les valeurs vues dans
  07_data/processed/dataset_ml_residentiel.csv.
- quartier_enc encode "quartier_groupe" : les quartiers avec moins de 15
  annonces dans le dataset d'entraînement ont été fusionnés en
  "Autre_<ville>" pour limiter la cardinalité (voir 03_ml/01_prepare_dataset.py).
- source_enc n'a pas de sens à demander à l'utilisateur final (ce n'est pas
  une caractéristique du bien) : on la fixe à sa valeur la plus fréquente
  à l'entraînement.
"""

import joblib
import pandas as pd
import streamlit as st

MODELS_DIR = "07_data/models"
DATASET_ML = "07_data/processed/dataset_ml_residentiel.csv"

TYPES_DISPONIBLES = ["Appartement", "Maison", "Riad", "Villa"]

# R² annoncés lors de l'entraînement (Module 3) — affichés à l'utilisateur
# comme indicateur de fiabilité, jamais fabriqués ici.
R2_MODELES = {
    "Appartement": 0.71,
    "Maison": 0.40,
    "Riad": 0.34,
    "Villa": 0.34,
}

# Valeur la plus fréquente de 'source' dans le dataset d'entraînement
# (Avito : 7754/13511, ~57%).
SOURCE_PAR_DEFAUT = "Avito"


@st.cache_resource(show_spinner=False)
def _charger_encodeurs():
    return {
        "ville": joblib.load(f"{MODELS_DIR}/encodeur_ville.joblib"),
        "quartier": joblib.load(f"{MODELS_DIR}/encodeur_quartier.joblib"),
        "source": joblib.load(f"{MODELS_DIR}/encodeur_source.joblib"),
    }


@st.cache_resource(show_spinner=False)
def _charger_modele(type_bien: str):
    return joblib.load(f"{MODELS_DIR}/modele_prix_{type_bien.lower()}.joblib")


@st.cache_data(ttl=3600, show_spinner=False)
def get_quartiers_par_ville() -> dict:
    """
    Renvoie, pour chaque ville, la liste des quartier_groupe connus du
    modèle : quartiers réels (>= 15 annonces à l'entraînement) + une
    entrée "Autre_<ville>" pour les quartiers trop peu représentés.
    """
    df = pd.read_csv(DATASET_ML, usecols=["ville", "quartier_groupe"]).drop_duplicates()
    resultat = {}
    for ville, sous_df in df.groupby("ville"):
        quartiers = sorted(q for q in sous_df["quartier_groupe"] if not q.startswith("Autre_"))
        quartiers.append(f"Autre_{ville}")
        resultat[ville] = quartiers
    return resultat


def label_quartier(quartier_groupe: str) -> str:
    """Libellé lisible pour un quartier_groupe (plus clair que 'Autre_Ville')."""
    if quartier_groupe.startswith("Autre_"):
        return "Autre / quartier non listé"
    return quartier_groupe


def estimer_prix(type_bien: str, ville: str, quartier_groupe: str, surface_m2: float, nb_chambres: int) -> dict:
    """
    Estime le prix d'un bien à partir des 5 features de l'entraînement.
    Renvoie aussi le R² du modèle utilisé, pour que l'utilisateur puisse
    juger de la fiabilité de l'estimation.
    """
    encodeurs = _charger_encodeurs()
    modele = _charger_modele(type_bien)

    ville_enc = encodeurs["ville"].transform([ville])[0]

    try:
        quartier_enc = encodeurs["quartier"].transform([quartier_groupe])[0]
    except ValueError:
        # Filet de sécurité : ne devrait pas arriver si l'UI ne propose que
        # des valeurs de get_quartiers_par_ville(), mais on se protège quand
        # même en repliant sur la catégorie "Autre_<ville>".
        quartier_enc = encodeurs["quartier"].transform([f"Autre_{ville}"])[0]

    source_enc = encodeurs["source"].transform([SOURCE_PAR_DEFAUT])[0]

    X = pd.DataFrame(
        [[surface_m2, nb_chambres, ville_enc, quartier_enc, source_enc]],
        columns=["surface_m2", "nb_chambres", "ville_enc", "quartier_enc", "source_enc"],
    )
    # Le modèle a été entraîné pour prédire prix_m2 (voir 03_ml/02_entrainer_modeles.py :
    # y = sous_df["prix_m2"]), PAS le prix total du bien. Le prix total s'obtient en
    # multipliant par la surface.
    prix_m2_predit = float(modele.predict(X)[0])
    prix_total_predit = prix_m2_predit * surface_m2

    return {
        "prix_total_predit": prix_total_predit,
        "prix_m2_predit": prix_m2_predit,
        "r2_modele": R2_MODELES.get(type_bien),
    }
