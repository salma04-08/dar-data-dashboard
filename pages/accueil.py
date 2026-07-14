"""Page Accueil — vue d'ensemble du marché immobilier marocain."""

import plotly.express as px
import streamlit as st

from utils.db import get_kpis_globaux, get_repartition_par_type, get_repartition_par_ville
from utils.theme import (
    ECHELLE_CONTINUE_VIOLET,
    PALETTE_CATEGORIELLE,
    BLEU,
    appliquer_theme,
    rendre_carte_graphique_html,
    rendre_cartes_kpi_grille_html,
)

_logo = "06_dashboard/static/logo_dar_data_sombre.png" if st.session_state.get("mode_sombre", False) else "06_dashboard/static/logo_dar_data.png"
st.image(_logo, width=320)
st.caption(
    "Plateforme intelligente d'analyse, de prédiction et de recommandation "
    "du marché immobilier marocain — biens à la vente, 8 villes principales"
)

with st.spinner("Chargement des indicateurs..."):
    kpis = get_kpis_globaux()


def _fmt(n):
    return f"{n:,.0f}".replace(",", " ") if n is not None else "—"


def _fmt_montant(n):
    """Abrège les grands montants (ex: 6 597 612 -> 6,60 M) pour rester lisible."""
    if n is None:
        return "—"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f} M".replace(".", ",")
    return _fmt(n)


cartes = [
    ("argent", "Prix moyen du marché", f"{_fmt_montant(kpis['prix_moyen'])} MAD"),
    ("maison", "Annonces analysées", _fmt(kpis["nb_annonces"])),
    ("regle", "Prix moyen / m²", f"{_fmt(kpis['prix_m2_moyen'])} MAD"),
    ("villes", "Villes couvertes", str(kpis["nb_villes"])),
    ("pin", "Quartiers référencés", str(kpis["nb_quartiers"])),
    ("lien", "Sources de données", str(kpis["nb_sources"])),
    ("surface", "Surface moyenne", f"{_fmt(kpis['surface_moyenne'])} m²"),
]

# Les 7 cartes KPI passent par une seule grille CSS (dans un seul iframe)
# plutôt qu'un iframe par carte, pour contrôler précisément l'espacement
# entre la rangée du haut (4 cartes) et celle du bas (3 cartes étirées).
st.iframe(rendre_cartes_kpi_grille_html([cartes[:4], cartes[4:]]), height=290)

st.write("")

c1, c2 = st.columns(2, gap="small")

df_ville = get_repartition_par_ville()

with c1:
    fig = px.bar(
        df_ville,
        x="ville",
        y="nb_annonces",
        color="prix_m2_moyen",
        color_continuous_scale=ECHELLE_CONTINUE_VIOLET,
        labels={"nb_annonces": "Annonces", "ville": "Ville", "prix_m2_moyen": "Prix/m² (MAD)"},
    )
    html = rendre_carte_graphique_html("Annonces par ville", PALETTE_CATEGORIELLE[0], appliquer_theme(fig), hauteur=500)
    st.iframe(html, height=500)

with c2:
    df_type = get_repartition_par_type()
    fig2 = px.pie(
        df_type,
        names="type_bien",
        values="nb_annonces",
        hole=0.55,
        color_discrete_sequence=PALETTE_CATEGORIELLE,
    )
    html2 = rendre_carte_graphique_html("Répartition par type de bien", PALETTE_CATEGORIELLE[1], appliquer_theme(fig2), hauteur=500)
    st.iframe(html2, height=500)

df_ville_sorted = df_ville.sort_values("prix_m2_moyen", ascending=True)
fig3 = px.bar(
    df_ville_sorted,
    x="prix_m2_moyen",
    y="ville",
    orientation="h",
    labels={"prix_m2_moyen": "Prix moyen / m² (MAD)", "ville": ""},
    color_discrete_sequence=[BLEU],
)
html3 = rendre_carte_graphique_html("Prix moyen au m² par ville", PALETTE_CATEGORIELLE[4], appliquer_theme(fig3), hauteur=460)
st.iframe(html3, height=460)

st.caption(
    "💡 Naviguez via le menu à gauche pour explorer le marché en détail, "
    "obtenir une estimation de prix, ou découvrir des opportunités d'investissement."
)
