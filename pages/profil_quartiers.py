"""Page Profil des quartiers — fiche détaillée d'un quartier (clustering K-Means/DBSCAN, Module 4)."""

import plotly.express as px
import streamlit as st

from utils.db import (
    get_profil_quartier,
    get_quartiers_profil_disponibles,
    get_quartiers_similaires,
    get_repartition_par_ville,
    get_villes_avec_profils,
)
from utils.theme import PALETTE_CATEGORIELLE, appliquer_theme, rendre_carte_graphique_html, rendre_cartes_kpi_grille_html, rendre_tableau_html

st.title("Profil des quartiers")
st.caption(
    "Fiche détaillée d'un quartier : profil de marché (clustering K-Means), "
    "répartition par type de bien et comparaison avec des quartiers similaires."
)

villes_dispo = get_villes_avec_profils()

with st.sidebar:
    st.header("Sélection")
    ville_sel = st.selectbox("Ville", villes_dispo)

quartiers_dispo = get_quartiers_profil_disponibles(ville_sel)

with st.sidebar:
    quartier_sel = st.selectbox("Quartier", quartiers_dispo)

st.info(
    f"ℹ️ Seuls les quartiers ayant eu suffisamment d'annonces pour un clustering "
    f"fiable sont disponibles ici ({len(quartiers_dispo)} quartiers profilés à {ville_sel})."
)

profil = get_profil_quartier(ville_sel, quartier_sel)

if profil is None:
    st.warning("Aucun profil trouvé pour ce quartier.")
    st.stop()

# ============================================================
# En-tête : nom, ville, label de profil, alerte atypique
# ============================================================
st.divider()
col_titre, col_badge = st.columns([3, 1])
with col_titre:
    st.subheader(f"{profil['quartier']}, {profil['ville']}")
with col_badge:
    st.success(f"Profil : **{profil['label_profil']}**")

if profil["quartier_atypique"]:
    st.warning(
        "🔍 Ce quartier a été signalé comme **atypique** par le clustering DBSCAN : "
        "son profil ne ressemble à aucun groupe dense de quartiers — à traiter avec "
        "prudence dans les comparaisons (petit échantillon ou marché très particulier)."
    )

# ============================================================
# KPIs du quartier
# ============================================================
cartes = [
    ("lien", "Annonces", str(int(profil["n_annonces"]))),
    ("regle", "Prix moyen / m²", f"{profil['prix_m2_moyen']:,.0f} MAD".replace(",", " ")),
    ("surface", "Surface moyenne", f"{profil['surface_moyenne']:,.0f} m²".replace(",", " ")),
    ("maison", "Chambres (moy.)", f"{profil['chambres_moyenne']:.1f}"),
]
st.iframe(rendre_cartes_kpi_grille_html([cartes]), height=150)

st.write("")

# ============================================================
# Comparaison avec la moyenne de la ville
# ============================================================
c1, c2 = st.columns(2, gap="small")

with c1:
    df_villes = get_repartition_par_ville()
    prix_ville = df_villes.loc[df_villes["ville"] == ville_sel, "prix_m2_moyen"]
    prix_ville_moyen = float(prix_ville.iloc[0]) if not prix_ville.empty else None

    if prix_ville_moyen:
        ecart_pct = (profil["prix_m2_moyen"] / prix_ville_moyen - 1) * 100
        st.metric(
            f"{profil['quartier']} vs moyenne {ville_sel}",
            f"{profil['prix_m2_moyen']:,.0f} MAD".replace(",", " "),
            delta=f"{ecart_pct:+.1f}% vs {prix_ville_moyen:,.0f} MAD ville".replace(",", " "),
        )
    else:
        st.info("Pas de moyenne ville disponible pour comparaison.")

with c2:
    types_pct = {
        "Appartement": profil["pct_appartement"],
        "Maison": profil["pct_maison"],
        "Riad": profil["pct_riad"],
        "Villa": profil["pct_villa"],
    }
    autres_pct = max(0.0, 1 - sum(types_pct.values()))
    if autres_pct > 0.001:
        types_pct["Autres"] = autres_pct

    fig = px.pie(
        names=list(types_pct.keys()),
        values=list(types_pct.values()),
        hole=0.5,
        color_discrete_sequence=PALETTE_CATEGORIELLE,
    )
    html = rendre_carte_graphique_html("Répartition par type de bien", PALETTE_CATEGORIELLE[1], appliquer_theme(fig), hauteur=380)
    st.iframe(html, height=380)

st.divider()

# ============================================================
# Localisation
# ============================================================
if profil["latitude"] and profil["longitude"]:
    st.subheader("Localisation")
    st.map(
        data=[{"lat": profil["latitude"], "lon": profil["longitude"]}],
        zoom=13,
    )
    st.divider()

# ============================================================
# Quartiers similaires (même profil K-Means)
# ============================================================
st.subheader(f"Quartiers au profil similaire (« {profil['label_profil']} »)")
similaires = get_quartiers_similaires(
    label_profil=profil["label_profil"],
    ville=ville_sel,
    exclure_quartier=quartier_sel,
    limit=6,
)

if similaires.empty:
    st.info("Aucun autre quartier avec ce profil pour l'instant.")
else:
    similaires_affichage = similaires.rename(columns={
        "quartier": "Quartier",
        "ville": "Ville",
        "prix_m2_moyen": "Prix/m² moyen (MAD)",
        "n_annonces": "Annonces",
    })
    similaires_affichage["Prix/m² moyen (MAD)"] = similaires_affichage["Prix/m² moyen (MAD)"].round(0)
    st.iframe(rendre_tableau_html(similaires_affichage), height=280)

st.caption(
    "💡 Profil calculé une fois via K-Means (Module 4) sur les quartiers ayant "
    "suffisamment d'annonces. Le flag « atypique » vient d'un clustering DBSCAN "
    "distinct, qui isole les quartiers ne ressemblant à aucun groupe dense."
)
