"""Page Analyse du marché — exploration des annonces avec filtres, distributions et comparaisons."""

import plotly.express as px
import streamlit as st

from utils.db import get_annonces, get_types_bien_disponibles, get_villes_disponibles
from utils.theme import BLEU, PALETTE_CATEGORIELLE, appliquer_theme, rendre_carte_graphique_html, rendre_cartes_kpi_grille_html, rendre_tableau_html

st.title("Analyse du marché")
st.caption("Exploration des annonces immobilières : distribution des prix, comparaisons villes et types de biens")

villes_dispo = get_villes_disponibles()
types_dispo = get_types_bien_disponibles()

with st.sidebar:
    st.header("Filtres")
    villes_sel = st.multiselect("Villes", villes_dispo, default=villes_dispo)
    types_sel = st.multiselect("Types de bien", types_dispo, default=types_dispo)

if not villes_sel or not types_sel:
    st.warning("Sélectionnez au moins une ville et un type de bien pour afficher les résultats.")
    st.stop()

with st.spinner("Chargement des annonces..."):
    df = get_annonces(villes=villes_sel, types_bien=types_sel)

if df.empty:
    st.info("Aucune annonce ne correspond à ces filtres.")
    st.stop()

nb_annonces_fmt = f"{len(df):,}".replace(",", " ")
st.iframe(
    rendre_cartes_kpi_grille_html([[("lien", "Annonces sélectionnées", nb_annonces_fmt)]]),
    height=150,
)

st.write("")

tab1, tab2, tab3 = st.tabs(["Distribution des prix", "Comparaison villes", "Comparaison types de biens"])

with tab1:
    c1, c2 = st.columns(2, gap="small")
    with c1:
        fig = px.histogram(df, x="prix_affiche_mad", nbins=50, color_discrete_sequence=[BLEU])
        fig.update_layout(xaxis_title="Prix (MAD)", yaxis_title="Nombre d'annonces")
        html = rendre_carte_graphique_html("Distribution du prix affiché", PALETTE_CATEGORIELLE[0], appliquer_theme(fig), hauteur=420)
        st.iframe(html, height=420)
    with c2:
        fig2 = px.histogram(df, x="prix_m2", nbins=50, color_discrete_sequence=[BLEU])
        fig2.update_layout(xaxis_title="Prix / m² (MAD)", yaxis_title="Nombre d'annonces")
        html2 = rendre_carte_graphique_html("Distribution du prix au m²", PALETTE_CATEGORIELLE[1], appliquer_theme(fig2), hauteur=420)
        st.iframe(html2, height=420)

    fig3 = px.box(df, x="ville", y="prix_m2", color="ville", color_discrete_sequence=PALETTE_CATEGORIELLE)
    fig3.update_layout(showlegend=False, yaxis_title="Prix / m² (MAD)")
    html3 = rendre_carte_graphique_html("Prix au m² par ville", PALETTE_CATEGORIELLE[2], appliquer_theme(fig3), hauteur=440)
    st.iframe(html3, height=440)

with tab2:
    agg_ville = (
        df.groupby("ville")
        .agg(
            nb_annonces=("id_annonce", "count"),
            prix_moyen=("prix_affiche_mad", "mean"),
            prix_m2_moyen=("prix_m2", "mean"),
            surface_moyenne=("surface_m2", "mean"),
        )
        .round(0)
        .reset_index()
        .sort_values("prix_m2_moyen", ascending=False)
    )
    st.iframe(rendre_tableau_html(agg_ville), height=340)

    fig4 = px.bar(agg_ville, x="ville", y="prix_m2_moyen", color_discrete_sequence=[BLEU])
    html4 = rendre_carte_graphique_html("Prix moyen au m² par ville", PALETTE_CATEGORIELLE[0], appliquer_theme(fig4), hauteur=420)
    st.iframe(html4, height=420)

with tab3:
    agg_type = (
        df.groupby("type_bien")
        .agg(
            nb_annonces=("id_annonce", "count"),
            prix_moyen=("prix_affiche_mad", "mean"),
            prix_m2_moyen=("prix_m2", "mean"),
            surface_moyenne=("surface_m2", "mean"),
        )
        .round(0)
        .reset_index()
        .sort_values("nb_annonces", ascending=False)
    )
    st.iframe(rendre_tableau_html(agg_type), height=340)

    fig5 = px.scatter(
        df, x="surface_m2", y="prix_affiche_mad", color="type_bien", opacity=0.5,
        labels={"surface_m2": "Surface (m²)", "prix_affiche_mad": "Prix (MAD)"},
        color_discrete_sequence=PALETTE_CATEGORIELLE,
    )
    html5 = rendre_carte_graphique_html("Prix vs surface, par type de bien", PALETTE_CATEGORIELLE[1], appliquer_theme(fig5), hauteur=460)
    st.iframe(html5, height=460)
