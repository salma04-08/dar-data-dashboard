"""Page Opportunités d'investissement — détection d'annonces sous/sur-évaluées (Module 3)."""

import plotly.express as px
import streamlit as st

from utils.db import get_opportunites, get_villes_disponibles
from utils.ml import TYPES_DISPONIBLES
from utils.theme import PALETTE_CATEGORIELLE, appliquer_theme, rendre_carte_graphique_html, rendre_cartes_kpi_grille_html, rendre_tableau_html

st.title("Opportunités d'investissement")
st.caption(
    "Annonces dont le prix réel s'écarte significativement du prix prédit par les "
    "modèles ML (Module 3) — potentielles bonnes affaires, ou survalorisations à éviter."
)

villes_dispo = get_villes_disponibles()

with st.sidebar:
    st.header("Filtres")
    villes_sel = st.multiselect("Villes", villes_dispo, default=villes_dispo)
    types_sel = st.multiselect("Types de bien", TYPES_DISPONIBLES, default=TYPES_DISPONIBLES)

st.info(
    "ℹ️ Seuls les 4 types de bien ayant un modèle de prix entraîné "
    "(Appartement, Riad, Maison, Villa) sont couverts ici."
)

if not villes_sel or not types_sel:
    st.warning("Sélectionnez au moins une ville et un type de bien.")
    st.stop()

df = get_opportunites(villes=villes_sel, types_bien=types_sel)

if df.empty:
    st.info("Aucune annonce ne correspond à ces filtres.")
    st.stop()

# ============================================================
# KPIs de répartition
# ============================================================
compte = df["statut_prix"].value_counts()
cartes = [
    ("argent", "Sous-évaluées", str(int(compte.get("Sous-évalué", 0)))),
    ("maison", "Normales", str(int(compte.get("Normal", 0)))),
    ("regle", "Sur-évaluées", str(int(compte.get("Sur-évalué", 0)))),
    ("pin", "Anomalies suspectes", str(int(compte.get("Anomalie suspecte", 0)))),
]
st.iframe(rendre_cartes_kpi_grille_html([cartes]), height=150)

st.warning(
    "⚠️ Les **anomalies suspectes** (ratio < 0,29 ou > 1,89) ne sont **pas** des opportunités "
    "d'investissement — ce sont des cas extrêmes qui signalent probablement une erreur de "
    "saisie (surface ou prix mal renseigné) plutôt qu'une vraie bonne affaire. Elles sont "
    "exclues du tableau des meilleures opportunités ci-dessous, mais restent visibles dans "
    "le graphique pour transparence."
)

st.divider()

# ============================================================
# Visualisation : prix réel vs prix prédit, coloré par statut
# ============================================================
st.subheader("Prix réel vs prix prédit par le modèle")
fig = px.scatter(
    df,
    x="prix_m2",
    y="ratio_prix_marche",
    color="statut_prix",
    opacity=0.6,
    color_discrete_map={
        "Sous-évalué": PALETTE_CATEGORIELLE[1],
        "Normal": PALETTE_CATEGORIELLE[5],
        "Sur-évalué": PALETTE_CATEGORIELLE[2],
        "Anomalie suspecte": PALETTE_CATEGORIELLE[3],
    },
    labels={"prix_m2": "Prix/m² réel (MAD)", "ratio_prix_marche": "Ratio (réel / prédit)"},
    hover_data=["ville", "quartier", "type_bien"],
)
fig.add_hline(y=1.0, line_dash="dot", line_color="gray", annotation_text="Prix conforme au marché")
html_scatter = rendre_carte_graphique_html("Prix réel vs prix prédit par le modèle", PALETTE_CATEGORIELLE[0], appliquer_theme(fig), hauteur=460)
st.iframe(html_scatter, height=460)

st.divider()

# ============================================================
# Tableau des meilleures opportunités (Sous-évalué uniquement)
# ============================================================
st.subheader("Meilleures opportunités (les plus sous-évaluées en premier)")

df_opportunites = df[df["statut_prix"] == "Sous-évalué"].copy().head(30)

if df_opportunites.empty:
    st.info("Aucune opportunité sous-évaluée pour ces filtres.")
else:
    df_affichage = df_opportunites[[
        "ville", "quartier", "type_bien", "surface_m2", "nb_chambres",
        "prix_affiche_mad", "prix_m2", "ratio_prix_marche",
    ]].rename(columns={
        "ville": "Ville", "quartier": "Quartier", "type_bien": "Type",
        "surface_m2": "Surface (m²)", "nb_chambres": "Chambres",
        "prix_affiche_mad": "Prix affiché (MAD)", "prix_m2": "Prix/m² (MAD)",
        "ratio_prix_marche": "Ratio",
    })
    df_affichage["Prix affiché (MAD)"] = df_affichage["Prix affiché (MAD)"].round(0)
    df_affichage["Prix/m² (MAD)"] = df_affichage["Prix/m² (MAD)"].round(0)
    df_affichage["Ratio"] = df_affichage["Ratio"].round(3)
    st.iframe(rendre_tableau_html(df_affichage), height=340)

st.caption(
    "💡 Ratio = prix/m² réel ÷ prix/m² prédit par le modèle ML de ce type de bien. "
    "Un ratio de 0,60 signifie que l'annonce est affichée 40% moins cher que ce que "
    "le modèle attendrait pour un bien comparable (ville, quartier, surface, chambres)."
)
