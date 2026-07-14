"""Page Prévisions du marché — historique de l'indice IPAI (BKAM) et évaluation SARIMA (Module 3)."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.db import get_historique_ipai
from utils.previsions import calculer_baseline_naive, get_evaluation, villes_types_disponibles
from utils.theme import BLEU, PALETTE_CATEGORIELLE, appliquer_effet_lumineux, appliquer_theme, rendre_carte_graphique_html

st.title("Prévisions du marché")
st.caption(
    "Évolution historique de l'indice des prix (IPAI, Bank Al-Maghrib) et évaluation "
    "de la capacité prédictive d'un modèle SARIMA sur ses 4 derniers trimestres connus."
)

st.info(
    "ℹ️ **Note méthodologique** : Bank Al-Maghrib ne publie l'IPAI qu'au format PDF "
    "trimestriel, sans série téléchargeable. Les valeurs intermédiaires entre les "
    "points officiels publiés ont été interpolées à partir de ces points de "
    "référence réels — méthodologie documentée dans le rapport."
)

paires_disponibles = villes_types_disponibles()
villes_dispo = sorted({v for v, _ in paires_disponibles})

col1, col2 = st.columns(2)
with col1:
    ville_sel = st.selectbox("Ville", villes_dispo)
with col2:
    types_pour_ville = sorted(t for v, t in paires_disponibles if v == ville_sel)
    type_sel = st.selectbox("Type de bien", types_pour_ville)

st.divider()

# ============================================================
# Historique de l'indice IPAI
# ============================================================
st.subheader(f"Évolution de l'indice IPAI — {type_sel}, {ville_sel}")

df_hist = get_historique_ipai(ville_sel, type_sel)

if df_hist.empty:
    st.warning("Pas de données historiques pour cette combinaison.")
    st.stop()

fig_hist = px.line(
    df_hist,
    x="date_calculee",
    y="indice_ipai_bkam",
    labels={"date_calculee": "", "indice_ipai_bkam": "Indice IPAI (base 100 = T1 2006)"},
    color_discrete_sequence=[BLEU],
)
fig_hist.add_hline(y=100, line_dash="dot", line_color="gray", annotation_text="Base 100 (2006)")
fig_hist = appliquer_effet_lumineux(fig_hist, PALETTE_CATEGORIELLE[0])
html_hist = rendre_carte_graphique_html(f"Évolution de l'indice IPAI — {type_sel}, {ville_sel}", PALETTE_CATEGORIELLE[0], appliquer_theme(fig_hist), hauteur=440)
st.iframe(html_hist, height=440)

st.divider()

# ============================================================
# Évaluation SARIMA — rétro-validation sur les 4 derniers trimestres
# ============================================================
st.subheader("Capacité prédictive du modèle SARIMA")
st.caption(
    "SARIMA(1,1,1)(1,0,1)[4], entraîné sur tous les trimestres sauf les 4 derniers, "
    "puis évalué sur ces 4 trimestres mis de côté. Ce ne sont **pas** des prévisions "
    "au-delà des données actuelles, mais un test de fiabilité sur du connu."
)

evaluation = get_evaluation(ville_sel, type_sel)

if evaluation is None:
    st.warning("Pas d'évaluation SARIMA disponible pour cette combinaison.")
else:
    r2 = evaluation["r2"]
    rmse = evaluation["rmse"]
    mae = evaluation["mae"]

    baseline = calculer_baseline_naive(df_hist, evaluation)

    st.markdown("**SARIMA vs baseline naïve** (« le trimestre prochain vaut ce que valait le dernier trimestre réellement observé »)")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("R² — SARIMA", f"{r2:.2f}", delta=f"{r2 - baseline['r2']:+.2f} vs naïve", delta_color="normal")
    col_b.metric("RMSE — SARIMA", f"{rmse:.2f}", delta=f"{rmse - baseline['rmse']:+.2f} vs naïve", delta_color="inverse")
    col_c.metric("MAE — SARIMA", f"{mae:.2f}", delta=f"{mae - baseline['mae']:+.2f} vs naïve", delta_color="inverse")
    st.caption(
        f"Pour repère, la baseline naïve obtient : R² = {baseline['r2']:.2f}, "
        f"RMSE = {baseline['rmse']:.2f}, MAE = {baseline['mae']:.2f} sur la même période de test."
    )

    if r2 >= 0.5:
        st.success(f"R² = {r2:.2f} : le modèle surpasse nettement une prédiction naïve sur cette série.")
    elif r2 > baseline["r2"]:
        st.warning(
            f"R² = {r2:.2f} : le modèle fait légèrement mieux que la baseline naïve "
            f"(R² = {baseline['r2']:.2f}) mais reste peu fiable en valeur absolue."
        )
    else:
        st.error(
            f"R² = {r2:.2f} : sur cette série, le modèle SARIMA fait **moins bien** que la "
            f"baseline naïve (R² = {baseline['r2']:.2f}). Ce résultat négatif est documenté "
            "comme une limite du projet — probablement dû à la courte période de test (4 "
            "trimestres) et à la nature en grande partie interpolée de l'historique."
        )

    # Graphique réel vs prédit sur la période de test
    trimestres = list(range(1, len(evaluation["valeurs_reelles_test"]) + 1))

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Scatter(
        x=trimestres, y=evaluation["valeurs_reelles_test"],
        mode="lines+markers", name="Réel", line=dict(color=PALETTE_CATEGORIELLE[0]),
    ))
    fig_comp.add_trace(go.Scatter(
        x=trimestres, y=evaluation["valeurs_predites_test"],
        mode="lines+markers", name="Prédit (SARIMA)", line=dict(color=PALETTE_CATEGORIELLE[1], dash="dash"),
    ))
    fig_comp.add_trace(go.Scatter(
        x=trimestres, y=baseline["valeurs_predites"],
        mode="lines+markers", name="Baseline naïve", line=dict(color=PALETTE_CATEGORIELLE[5], dash="dot"),
    ))
    fig_comp.update_layout(xaxis_title="Trimestre (période de test, 4 derniers connus)", yaxis_title="Indice IPAI")
    html_comp = rendre_carte_graphique_html("SARIMA vs réel vs baseline naïve", PALETTE_CATEGORIELLE[2], appliquer_theme(fig_comp), hauteur=440)
    st.iframe(html_comp, height=440)

st.divider()
st.caption(
    "💡 Sur l'ensemble des 32 séries modélisées (8 villes × 4 types), le R² médian est "
    "de -0,43 — SARIMA a été testé avec rigueur mais n'apporte pas de gain fiable sur "
    "ces séries trimestrielles courtes. Documenté comme limite assumée du projet plutôt "
    "que présenté comme un outil de prévision opérationnel."
)
