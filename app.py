"""
ImmoInsight Maroc — Dashboard Streamlit
Point d'entrée de l'application. Définit la navigation multipage et
le thème global. Chaque page vit dans pages/ et importe ses données
via utils/db.py.

Lancement (depuis la racine du projet C:\\Users\\fatimazahra\\Documents\\immo_maroc) :
    streamlit run 06_dashboard/app.py
"""

import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).parent

from utils.theme import injecter_css

st.set_page_config(
    page_title="Dar & Data",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.logo(str(BASE_DIR / "static" / "logo_dar_data_sombre.png"), size="large")

with st.sidebar:
    st.toggle("🌙 Mode sombre", key="mode_sombre")

injecter_css()

# ============================================================
# Déclaration des pages
# ============================================================
accueil = st.Page("pages/accueil.py", title="Accueil", default=True)
analyse_marche = st.Page("pages/analyse_marche.py", title="Analyse du marché")
carte_interactive = st.Page("pages/carte_interactive.py", title="Carte interactive")

profil_quartiers = st.Page("pages/profil_quartiers.py", title="Profil des quartiers")
comparaison_villes = st.Page("pages/comparaison_villes.py", title="Comparaison des villes")

estimation_prix = st.Page("pages/estimation_prix.py", title="Estimation du prix")
previsions = st.Page("pages/previsions.py", title="Prévisions du marché")
opportunites = st.Page("pages/opportunites.py", title="Opportunités d'investissement")
recommandations = st.Page("pages/recommandations.py", title="Recommandations")

pg = st.navigation(
    {
        "Vue d'ensemble": [accueil, analyse_marche, carte_interactive],
        "Analyses avancées": [profil_quartiers, comparaison_villes],
        "Intelligence artificielle": [estimation_prix, previsions, opportunites, recommandations],
    }
)

# ============================================================
# Habillage commun (sidebar)
# ============================================================
with st.sidebar:
    st.image(str(BASE_DIR / "static" / "logo_dar_data_sombre.png"), width=140)
    st.caption("Analyse, prédiction et recommandation du marché immobilier marocain — biens à la vente")
    st.divider()

pg.run()
