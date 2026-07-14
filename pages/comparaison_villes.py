"""Page Comparaison des villes — prix, démographie, climat, indices BKAM (bonus, Phase 5)."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.db import (
    get_climat,
    get_demographie,
    get_historique_ipai,
    get_repartition_par_ville,
    get_villes_disponibles,
)
from utils.theme import PALETTE_CATEGORIELLE, appliquer_theme, rendre_carte_graphique_html, rendre_cartes_kpi_grille_html

st.title("Comparaison des villes")
st.caption("Comparez deux villes sur le prix, la démographie, le climat et l'évolution des prix (indice BKAM).")

villes_dispo = get_villes_disponibles()

col1, col2 = st.columns(2)
with col1:
    ville_a = st.selectbox("Ville A", villes_dispo, index=0)
with col2:
    autres = [v for v in villes_dispo if v != ville_a]
    ville_b = st.selectbox("Ville B", autres, index=0)

villes = [ville_a, ville_b]
st.divider()

# ============================================================
# Prix
# ============================================================
st.subheader("Prix")
df_prix = get_repartition_par_ville()
df_prix = df_prix[df_prix["ville"].isin(villes)]

cartes_prix = []
for ville in villes:
    ligne = df_prix[df_prix["ville"] == ville]
    if not ligne.empty:
        cartes_prix.append(("regle", f"{ville} — Prix moyen / m²", f"{ligne['prix_m2_moyen'].iloc[0]:,.0f} MAD".replace(",", " ")))
        cartes_prix.append(("maison", f"{ville} — Annonces", f"{int(ligne['nb_annonces'].iloc[0]):,}".replace(",", " ")))
if cartes_prix:
    st.iframe(rendre_cartes_kpi_grille_html([cartes_prix]), height=150)
else:
    st.info("Pas de données.")

st.divider()

# ============================================================
# Démographie — uniquement population (le reste est national, pas
# spécifique à la ville, voir note ci-dessous)
# ============================================================
st.subheader("Démographie")
df_demo = get_demographie(villes)

if not df_demo.empty:
    fig_demo = px.bar(
        df_demo, x="ville", y="population_totale",
        labels={"ville": "", "population_totale": "Population"},
        color_discrete_sequence=[PALETTE_CATEGORIELLE[0]],
    )
    html_demo = rendre_carte_graphique_html("Population", PALETTE_CATEGORIELLE[0], appliquer_theme(fig_demo), hauteur=400)
    st.iframe(html_demo, height=400)

    ligne0 = df_demo.iloc[0]
    pib_fmt = f"{ligne0['pib_par_habitant']:,.0f}".replace(",", " ")
    st.caption(
        f"ℹ️ Contexte national (identique pour toutes les villes, non désagrégé par ville "
        f"dans la source HCP/Banque Mondiale) : taux de chômage {ligne0['taux_chomage']:.1f}%, "
        f"PIB/habitant {pib_fmt} USD, "
        f"urbanisation {ligne0['taux_urbanisation']:.1f}%."
    )
else:
    st.info("Pas de données démographiques disponibles.")

st.divider()

# ============================================================
# Climat — relevé instantané, pas une moyenne annuelle
# ============================================================
st.subheader("Climat")
st.caption("⚠️ Relevé ponctuel au moment de la collecte des données — pas une moyenne climatique annuelle.")

df_climat = get_climat(villes)
cartes_climat = []
descriptions = []
for ville in villes:
    ligne = df_climat[df_climat["ville"] == ville]
    if not ligne.empty:
        r = ligne.iloc[0]
        cartes_climat.append(("argent", f"{ville} — Température", f"{r['temperature_moyenne']:.1f} °C"))
        cartes_climat.append(("lien", f"{ville} — Humidité", f"{r['humidite']:.0f} %"))
        cartes_climat.append(("surface", f"{ville} — Vent", f"{r['vent_kmh']:.1f} km/h"))
        descriptions.append(f"{ville} : {r['description']}")

if cartes_climat:
    st.iframe(rendre_cartes_kpi_grille_html([cartes_climat[:3], cartes_climat[3:]]), height=290)
    st.caption(" · ".join(descriptions))
else:
    st.info("Pas de données.")

st.divider()

# ============================================================
# Évolution des prix — indice IPAI (BKAM)
# ============================================================
st.subheader("Évolution de l'indice IPAI (BKAM)")
type_sel = st.selectbox("Type de bien", ["Appartement", "Maison", "Terrain", "Villa"])

fig_ipai = go.Figure()
for i, ville in enumerate(villes):
    df_hist = get_historique_ipai(ville, type_sel)
    if not df_hist.empty:
        fig_ipai.add_trace(go.Scatter(
            x=df_hist["date_calculee"], y=df_hist["indice_ipai_bkam"],
            mode="lines", name=ville, line=dict(color=PALETTE_CATEGORIELLE[i]),
        ))

if fig_ipai.data:
    fig_ipai.update_layout(xaxis_title="", yaxis_title="Indice IPAI (base 100 = T1 2006)")
    html_ipai = rendre_carte_graphique_html("Évolution de l'indice IPAI", PALETTE_CATEGORIELLE[4], appliquer_theme(fig_ipai), hauteur=440)
    st.iframe(html_ipai, height=440)
else:
    st.info("Pas de données IPAI pour ce type de bien dans ces villes.")

st.caption(
    "💡 Rappel méthodologique : l'indice IPAI est interpolé entre les points officiels "
    "publiés par Bank Al-Maghrib (voir page Prévisions du marché pour le détail)."
)
