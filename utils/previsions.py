"""
Chargement des résultats SARIMA (Module 3), sauvegardés dans
07_data/outputs/resultats_sarima.json.

Important, pour rester honnête dans la page qui utilise ce module :
les "valeurs_predites_test" ne sont PAS une prévision du futur — ce sont
les prédictions du modèle sur les 4 derniers trimestres déjà connus,
mis de côté à l'entraînement (retro-validation / backtesting). On ne
dispose d'aucune prévision au-delà des données actuelles.
"""

import json

import numpy as np
import streamlit as st

RESULTATS_PATH = "07_data/outputs/resultats_sarima.json"


@st.cache_data(ttl=3600, show_spinner=False)
def charger_resultats_sarima() -> dict:
    with open(RESULTATS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data


def get_evaluation(ville: str, type_bien: str) -> dict | None:
    """
    Renvoie l'évaluation SARIMA (rmse, mae, r2, valeurs réelles/prédites
    sur les 4 derniers trimestres) pour une ville et un type de bien.
    None si la combinaison n'a pas été modélisée.
    """
    data = charger_resultats_sarima()
    cle = f"{ville}_{type_bien}"
    return data["performances"].get(cle)


def villes_types_disponibles() -> list:
    """Liste des combinaisons (ville, type_bien) réellement modélisées par SARIMA."""
    data = charger_resultats_sarima()
    paires = []
    for cle in data["performances"]:
        ville, type_bien = cle.split("_", 1)
        paires.append((ville, type_bien))
    return paires


def calculer_baseline_naive(df_historique, evaluation: dict) -> dict:
    """
    Baseline "naïve" (persistance) : prédire qu'un trimestre vaudra ce que
    valait le trimestre précédent réellement observé. Sert de point de
    comparaison objectif pour juger si SARIMA apporte un vrai gain — plutôt
    que de se contenter d'affirmer en texte que le R² est mauvais.
    """
    n_test = evaluation["n_test"]
    valeurs = df_historique["indice_ipai_bkam"].astype(float).tolist()
    reels_test = evaluation["valeurs_reelles_test"]

    dernier_train = valeurs[-(n_test + 1)]
    naif_pred = [dernier_train] + list(reels_test[:-1])

    reels = np.array(reels_test, dtype=float)
    naif = np.array(naif_pred, dtype=float)

    rmse = float(np.sqrt(np.mean((reels - naif) ** 2)))
    mae = float(np.mean(np.abs(reels - naif)))
    ss_res = np.sum((reels - naif) ** 2)
    ss_tot = np.sum((reels - reels.mean()) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")

    return {"rmse": rmse, "mae": mae, "r2": r2, "valeurs_predites": naif_pred}
