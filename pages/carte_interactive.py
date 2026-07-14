"""Page Carte interactive — carte Folium du prix moyen au m² par quartier."""

import folium
import streamlit as st
from branca.colormap import LinearColormap
from streamlit_folium import st_folium

from utils.db import get_carte_quartiers, get_villes_disponibles
from utils.theme import ECHELLE_CONTINUE_VIOLET, rendre_cartes_kpi_grille_html

st.title("Carte interactive")
st.caption("Prix moyen au m² par quartier — taille du point proportionnelle au nombre d'annonces")

villes_dispo = get_villes_disponibles()

with st.sidebar:
    st.header("Filtres")
    villes_sel = st.multiselect("Villes", villes_dispo, default=villes_dispo)

if not villes_sel:
    st.warning("Sélectionnez au moins une ville.")
    st.stop()

with st.spinner("Chargement des quartiers..."):
    df = get_carte_quartiers(villes=villes_sel)

if df.empty:
    st.info("Aucun quartier avec suffisamment d'annonces pour ces filtres.")
    st.stop()

st.iframe(rendre_cartes_kpi_grille_html([[("pin", "Quartiers affichés", f"{len(df):,}".replace(",", " "))]]), height=150)

# Échelle de couleur terracotta, calée sur les valeurs réelles de prix/m²
colormap = LinearColormap(
    colors=[c[1] for c in ECHELLE_CONTINUE_VIOLET],
    vmin=df["prix_m2_moyen"].min(),
    vmax=df["prix_m2_moyen"].max(),
    caption="Prix moyen au m² (MAD)",
)

centre_lat = df["latitude"].mean()
centre_lon = df["longitude"].mean()
zoom = 6 if len(villes_sel) > 1 else 11

m = folium.Map(location=[centre_lat, centre_lon], zoom_start=zoom, tiles="CartoDB positron")

# Rayon proportionnel au nombre d'annonces (échelle bornée pour rester lisible)
nb_min, nb_max = df["nb_annonces"].min(), df["nb_annonces"].max()


def rayon(nb_annonces):
    if nb_max == nb_min:
        return 8
    ratio = (nb_annonces - nb_min) / (nb_max - nb_min)
    return 5 + ratio * 15  # rayon entre 5 et 20 px


for _, row in df.iterrows():
    popup_html = (
        f"<b>{row['quartier']}</b>, {row['ville']}<br>"
        f"Prix moyen : {row['prix_moyen']:,.0f} MAD<br>"
        f"Prix / m² : {row['prix_m2_moyen']:,.0f} MAD<br>"
        f"Annonces : {int(row['nb_annonces'])}"
    ).replace(",", " ")

    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=rayon(row["nb_annonces"]),
        color=colormap(row["prix_m2_moyen"]),
        fill=True,
        fill_color=colormap(row["prix_m2_moyen"]),
        fill_opacity=0.75,
        weight=1,
        popup=folium.Popup(popup_html, max_width=220),
    ).add_to(m)

colormap.add_to(m)

st_folium(m, use_container_width=True, height=600, returned_objects=[])

st.caption(
    "💡 Certains quartiers créés dynamiquement pendant l'ETL n'ont pas pu être "
    "géocodés individuellement (nom introuvable sur OpenStreetMap ou coupure "
    "réseau) — ils apparaissent au centre-ville par défaut. Voir "
    "`07_data/processed/quartiers_non_geocodes.csv` pour le détail."
)
