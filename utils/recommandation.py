"""
Moteur de recommandation par similarité cosinus (Module 6), adapté pour
le dashboard à partir de 06_dashboard/recommandation/01_moteur_recommandation.py.

Point important : matrice_similarite.joblib n'est PAS une matrice de
similarité précalculée (ça ferait plus de 4 Go pour 32 207 annonces) —
c'est la matrice des 7 features déjà normalisées (StandardScaler). La
similarité cosinus se calcule à la volée entre l'annonce choisie et les
autres, ce qui reste rapide (quelques millisecondes avec scikit-learn).

La correspondance ligne <-> annonce se fait via l'ordre des lignes de
07_data/processed/dataset_recommandation.csv, généré dans le même ordre
que la matrice au moment de sa construction.
"""

import joblib
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity

MATRICE_PATH = "07_data/models/matrice_similarite.joblib"
DATASET_PATH = "07_data/processed/dataset_recommandation.csv"


@st.cache_resource(show_spinner=False)
def _charger_matrice():
    return joblib.load(MATRICE_PATH)


@st.cache_data(ttl=3600, show_spinner="Chargement du moteur de recommandation...")
def charger_dataset_recommandation() -> pd.DataFrame:
    return pd.read_csv(DATASET_PATH)


def recommander(id_annonce: int, top_n: int = 5, meme_ville: bool = True, meme_type: bool = True):
    """
    Renvoie les top_n biens les plus similaires à l'annonce donnée
    (similarité cosinus sur 7 features normalisées : prix affiché,
    surface, chambres, prix/m², score NLP, ville encodée, type encodé).
    """
    df = charger_dataset_recommandation()
    X_scaled = _charger_matrice()

    if id_annonce not in df["id_annonce"].values:
        return None

    idx = df.index[df["id_annonce"] == id_annonce][0]
    idx_local = df.index.get_loc(idx)
    vecteur = X_scaled[idx_local].reshape(1, -1)

    masque = pd.Series(True, index=df.index)
    if meme_ville:
        masque &= df["ville"] == df.loc[idx, "ville"]
    if meme_type:
        masque &= df["type_bien"] == df.loc[idx, "type_bien"]
    masque.loc[idx] = False

    df_filtre = df[masque]
    if df_filtre.empty:
        return None

    idx_filtres = [df.index.get_loc(i) for i in df_filtre.index]
    X_filtre = X_scaled[idx_filtres]

    similarites = cosine_similarity(vecteur, X_filtre)[0]
    top_indices = np.argsort(similarites)[::-1][:top_n]

    resultats = df_filtre.iloc[top_indices].copy()
    resultats["score_similarite"] = similarites[top_indices]
    return resultats
