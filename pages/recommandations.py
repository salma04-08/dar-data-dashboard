"""Page Recommandations — biens similaires par similarité cosinus (Module 6)."""

import streamlit as st

from utils.recommandation import charger_dataset_recommandation, recommander
from utils.theme import rendre_tableau_html

st.title("Recommandations")
st.caption(
    "Choisissez une annonce de référence : le moteur retrouve les biens **à la vente** "
    "les plus similaires selon 7 caractéristiques normalisées (prix, surface, chambres, "
    "prix/m², qualité rédactionnelle, ville, type de bien)."
)

df = charger_dataset_recommandation()

# ============================================================
# Sélection de l'annonce de référence
# ============================================================
col1, col2 = st.columns(2)
with col1:
    ville_sel = st.selectbox("Ville", sorted(df["ville"].unique()))
with col2:
    types_dispo = sorted(df.loc[df["ville"] == ville_sel, "type_bien"].unique())
    type_sel = st.selectbox("Type de bien", types_dispo)

df_filtre = df[(df["ville"] == ville_sel) & (df["type_bien"] == type_sel)].copy()

quartiers_dispo = sorted(df_filtre["quartier"].dropna().unique())
quartier_sel = st.selectbox("Quartier (optionnel)", ["Tous"] + quartiers_dispo)
if quartier_sel != "Tous":
    df_filtre = df_filtre[df_filtre["quartier"] == quartier_sel]

if df_filtre.empty:
    st.warning("Aucune annonce ne correspond à ces filtres.")
    st.stop()

df_filtre = df_filtre.sort_values("prix_affiche_mad")
options_labels = {}
for _, row in df_filtre.iterrows():
    prix_fmt = f"{row['prix_affiche_mad']:,.0f}".replace(",", " ")
    options_labels[row["id_annonce"]] = (
        f"{row['quartier']} — {row['surface_m2']:.0f} m², "
        f"{row['nb_chambres']:.0f} ch. — {prix_fmt} MAD"
    )

id_reference = st.selectbox(
    f"Annonce de référence ({len(options_labels)} disponibles)",
    options=list(options_labels.keys()),
    format_func=lambda x: options_labels[x],
)

st.divider()

# ============================================================
# Options de recommandation
# ============================================================
col3, col4, col5 = st.columns(3)
with col3:
    top_n = st.slider("Nombre de recommandations", 3, 15, 5)
with col4:
    meme_ville = st.checkbox("Même ville", value=True)
with col5:
    meme_type = st.checkbox("Même type de bien", value=True)

if st.button("Trouver des biens similaires", type="primary"):
    resultats = recommander(id_reference, top_n=top_n, meme_ville=meme_ville, meme_type=meme_type)

    if resultats is None or resultats.empty:
        st.info("Aucun bien similaire trouvé avec ces critères — essayez de décocher un filtre.")
    else:
        st.subheader(f"{len(resultats)} biens similaires")

        affichage = resultats[[
            "ville", "quartier", "type_bien", "surface_m2", "nb_chambres",
            "prix_affiche_mad", "score_nlp", "score_similarite", "lien",
        ]].rename(columns={
            "ville": "Ville", "quartier": "Quartier", "type_bien": "Type",
            "surface_m2": "Surface (m²)", "nb_chambres": "Chambres",
            "prix_affiche_mad": "Prix (MAD)", "score_nlp": "Score NLP",
            "score_similarite": "Similarité", "lien": "Annonce",
        })
        affichage["Prix (MAD)"] = affichage["Prix (MAD)"].round(0)
        affichage["Score NLP"] = affichage["Score NLP"].round(2)
        affichage["Similarité"] = affichage["Similarité"].round(3)

        st.iframe(rendre_tableau_html(affichage), height=340)

st.divider()
st.caption(
    "💡 La similarité cosinus mesure la proximité entre annonces sur les 7 features "
    "normalisées listées ci-dessus — elle ne préjuge pas de la disponibilité réelle "
    "du bien (annonces scrapées à un instant donné)."
)
