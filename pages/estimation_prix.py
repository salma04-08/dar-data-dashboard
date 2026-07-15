"""Page Estimation du prix — simulateur basé sur les modèles XGBoost/RF entraînés (Module 3)."""

import streamlit as st

from utils.db import get_repartition_par_ville
from utils.theme import rendre_cartes_kpi_grille_html
from utils.ml import (
    R2_MODELES,
    SOURCE_PAR_DEFAUT,
    TYPES_DISPONIBLES,
    estimer_prix,
    get_quartiers_par_ville,
    label_quartier,
)

st.title("Estimation du prix")
st.caption(
    "Simulateur de prix basé sur les modèles XGBoost / Random Forest "
    "entraînés séparément par type de bien (Module 3)."
)

quartiers_par_ville = get_quartiers_par_ville()
villes_dispo = sorted(quartiers_par_ville.keys())

col1, col2 = st.columns(2)
with col1:
    type_bien = st.selectbox("Type de bien", TYPES_DISPONIBLES)
    ville = st.selectbox("Ville", villes_dispo)
with col2:
    quartiers_options = quartiers_par_ville[ville]
    quartier_groupe = st.selectbox("Quartier", quartiers_options, format_func=label_quartier)

col3, col4 = st.columns(2)
with col3:
    surface_m2 = st.number_input("Surface (m²)", min_value=15, max_value=1500, value=90, step=5)
with col4:
    nb_chambres = st.number_input("Nombre de chambres", min_value=1, max_value=10, value=2, step=1)

st.divider()

if st.button("Estimer le prix", type="primary"):
    resultat = estimer_prix(type_bien, ville, quartier_groupe, surface_m2, nb_chambres)
    prix_total = resultat["prix_total_predit"]
    prix_m2 = resultat["prix_m2_predit"]
    r2 = resultat["r2_modele"]

    cartes_resultat = [
        ("argent", "Prix total estimé", f"{prix_total:,.0f} MAD".replace(",", " ")),
        ("regle", "Prix / m² estimé", f"{prix_m2:,.0f} MAD/m²".replace(",", " ")),
    ]
    st.iframe(rendre_cartes_kpi_grille_html([cartes_resultat]), height=150)

    prix_bas = prix_total * 0.70
    prix_haut = prix_total * 0.90
    st.info(
        f"💬 **Fourchette ajustée pour marge de négociation** : "
        f"{prix_bas:,.0f} — {prix_haut:,.0f} MAD".replace(",", " ") + "\n\n"
        "Le prix estimé ci-dessus reflète le prix *affiché* sur les annonces. Sur le marché "
        "immobilier marocain, les prix affichés sont généralement supérieurs de 10 à 30% au "
        "prix de vente réellement conclu (source : ReaConsult, expert RICS Maroc). Cette "
        "fourchette applique cet écart documenté au prix estimé — ce n'est pas une correction "
        "du modèle, mais un ajustement de contexte de marché, à considérer comme indicatif."
    )

    if r2 is not None:
        if r2 >= 0.6:
            st.success(f"Fiabilité du modèle {type_bien} : R² = {r2:.2f} (bonne)")
        elif r2 >= 0.4:
            st.warning(
                f"Fiabilité du modèle {type_bien} : R² = {r2:.2f} (modérée — "
                "à prendre comme un ordre de grandeur, pas une valeur exacte)"
            )
        else:
            st.warning(
                f"Fiabilité du modèle {type_bien} : R² = {r2:.2f} (limitée — "
                f"peu de données {type_bien.lower()} disponibles à l'entraînement, "
                "estimation indicative uniquement)"
            )

    df_ville = get_repartition_par_ville()
    ligne_ville = df_ville.loc[df_ville["ville"] == ville, "prix_m2_moyen"]
    if not ligne_ville.empty:
        prix_moyen_ville_fmt = f"{float(ligne_ville.iloc[0]):,.0f}".replace(",", " ")
        st.caption(
            f"À titre de comparaison, le prix moyen au m² toutes annonces confondues "
            f"à {ville} est de {prix_moyen_ville_fmt} MAD."
        )

st.divider()
st.caption(
    "💡 La variable « source » (plateforme d'origine de l'annonce) fait partie "
    f"des features d'entraînement mais n'est pas demandée ici : elle est fixée à "
    f"« {SOURCE_PAR_DEFAUT} » (valeur la plus fréquente à l'entraînement), car "
    "elle capture des différences de style d'annonce entre plateformes plutôt "
    "qu'une caractéristique réelle du bien."
)
