"""
Palette de couleurs Dar & Data — fidèle à TailAdmin v1.3
(https://github.com/TailAdmin/tailadmin-free-tailwind-dashboard-template/tree/1.3),
avec un vrai mode clair/sombre fonctionnel.

Le mode sombre est piloté par un seul interrupteur (st.session_state
"mode_sombre", réglé par un st.toggle() dans app.py) — toutes les
fonctions ci-dessous lisent cet état automatiquement, donc aucune page
n'a besoin d'être modifiée pour suivre le changement de thème.

Valeurs reprises de tailwind.config.js (v1.3) : couleurs claires et
sombres (boxdark, strokedark, bodydark...), structure de carte (icône
circulaire teintée), police Caviar Dreams.
"""

import streamlit as st

# ============================================================
# Palette terracotta en dégradé (clair -> foncé) — couleur
# dominante du thème, mode clair
# ============================================================
TERRACOTTA_50 = "#EFE8E4"
TERRACOTTA_100 = "#D9C9BF"
TERRACOTTA_200 = "#BEA292"
TERRACOTTA_300 = "#A8836D"
TERRACOTTA_500 = "#926449"  # couleur principale
TERRACOTTA_600 = "#7C553E"
TERRACOTTA_700 = "#664633"
TERRACOTTA_800 = "#493225"

PRIMARY = TERRACOTTA_500
SECONDARY = TERRACOTTA_300
TEXTE = "#1C2434"
STROKE = "#E2E8F0"
META_2 = TERRACOTTA_50    # fond teinté du cercle d'icône (clair)
BG_LIGHT = "#F1F5F9"

META_ROUGE = "#DC3545"
META_VERT = "#10B981"
META_BLEU = "#259AE6"
META_JAUNE = "#FFBA00"
META_CORAIL = "#FF6766"
META_ORANGE = "#F0950C"

# ============================================================
# Couleurs officielles TailAdmin v1.3 — mode sombre
# ============================================================
BOXDARK = "#3A2E27"      # fond des cartes en mode sombre (brun foncé terracotta)
BOXDARK_CHART = "#524234"  # fond plus clair pour les cartes graphique, meilleur contraste avec les courbes
BOXDARK_2 = "#241C17"    # fond de page / sidebar en mode sombre (brun très foncé terracotta)
SIDEBAR_BG = "#2B1D16"   # fond de la sidebar — brun terracotta foncé, cohérent avec le thème
STROKEDARK = "#4A3B31"
BODYDARK = "#AEB7C0"     # texte secondaire en mode sombre
BODYDARK1 = "#DEE4EE"    # texte principal en mode sombre

# Alias pour compatibilité avec les pages existantes
BLEU = PRIMARY

# Palette catégorielle en dégradé terracotta (du plus foncé au plus
# clair) — look "moderne" monochrome plutôt qu'un arc-en-ciel de couleurs
PALETTE_CATEGORIELLE = [TERRACOTTA_800, TERRACOTTA_600, TERRACOTTA_500, TERRACOTTA_300, TERRACOTTA_200, TERRACOTTA_100]

ECHELLE_CONTINUE_VIOLET = [
    [0.0, TERRACOTTA_50],
    [0.5, TERRACOTTA_300],
    [1.0, TERRACOTTA_800],
]


def _mode_sombre() -> bool:
    """Lit l'état actuel de l'interrupteur clair/sombre (réglé dans app.py)."""
    return st.session_state.get("mode_sombre", False)


def appliquer_theme(fig):
    """Applique la palette Dar & Data à une figure Plotly, adaptée au mode clair/sombre actuel."""
    couleur_texte = BODYDARK1 if _mode_sombre() else TEXTE
    fig.update_layout(
        colorway=PALETTE_CATEGORIELLE,
        font=dict(family="CaviarDreams, -apple-system, sans-serif", color=couleur_texte),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def figure_jauge_circulaire(valeur_pct: float, label: str, couleur: str = None):
    """
    Jauge circulaire (anneau + pourcentage au centre), dans l'esprit
    "dashboard moderne" — un anneau coloré rempli à valeur_pct%, le reste
    en gris clair/foncé selon le mode, avec la valeur affichée au centre.

    Args:
        valeur_pct: valeur entre 0 et 100
        label: texte affiché sous le pourcentage, au centre de l'anneau
        couleur: couleur de la portion remplie (terracotta par défaut)
    """
    import plotly.graph_objects as go

    sombre = _mode_sombre()
    couleur = couleur or PRIMARY
    fond_anneau = STROKEDARK if sombre else TERRACOTTA_50
    couleur_texte = BODYDARK1 if sombre else TEXTE

    fig = go.Figure(data=[go.Pie(
        values=[valeur_pct, max(0, 100 - valeur_pct)],
        hole=0.72,
        marker=dict(colors=[couleur, fond_anneau], line=dict(width=0)),
        textinfo="none",
        sort=False,
        direction="clockwise",
        rotation=90,
    )])
    fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        annotations=[
            dict(text=f"<b>{valeur_pct:.0f}%</b>", x=0.5, y=0.56, font_size=26, showarrow=False, font_color=couleur_texte),
            dict(text=label, x=0.5, y=0.38, font_size=12, showarrow=False, font_color=couleur_texte),
        ],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def appliquer_effet_lumineux(fig, couleur: str = None):
    """
    Ajoute un effet de lueur ("glow") aux courbes d'un graphique en ligne,
    dans l'esprit "dashboard moderne" — superpose 2 traces plus larges et
    semi-transparentes derrière chaque courbe pour simuler un halo, plus
    un remplissage doux en dégradé sous la ligne.

    À appliquer à un go.Figure ou px.line APRÈS l'avoir construit, avant
    appliquer_theme(). Fonctionne mieux sur des graphiques à une seule
    courbe (l'effet devient confus avec beaucoup de courbes superposées).
    """
    import plotly.graph_objects as go

    couleur = couleur or PRIMARY
    r, g, b = int(couleur[1:3], 16), int(couleur[3:5], 16), int(couleur[5:7], 16)

    originaux = list(fig.data)
    halos = []
    for trace in originaux:
        trace.update(
            line=dict(width=3, color=couleur, shape="spline", smoothing=0.6),
        )
        halo_json = trace.to_plotly_json()
        halo_json["line"] = dict(width=9, color=f"rgba({r},{g},{b},0.15)", shape="spline", smoothing=0.6)
        halo_json["showlegend"] = False
        halo_json["hoverinfo"] = "skip"
        halos.append(go.Scatter(halo_json))

    # fig.data ne peut être réassigné directement qu'avec une permutation de
    # lui-même (contrainte interne de Plotly) — on vide puis on rajoute
    # chaque trace via add_trace(), seule méthode officiellement supportée
    # pour insérer de nouvelles traces (les halos) dans une figure existante.
    fig.data = ()
    for halo in halos:
        fig.add_trace(halo)
    for orig in originaux:
        fig.add_trace(orig)

    return fig


def _sans_indentation(html: str) -> str:
    """
    Retire l'indentation en début de ligne d'un bloc HTML/CSS.

    Indispensable ici : le moteur Markdown de Streamlit interprète toute
    ligne commençant par 4 espaces ou plus comme un bloc de code littéral
    (règle CommonMark), ce qui affiche le CSS/HTML en texte brut au lieu
    de l'interpréter si le texte source Python est indenté normalement.
    """
    return "\n".join(ligne.lstrip() for ligne in html.split("\n"))


def injecter_css():
    """
    Injecte le CSS global Dar & Data, adapté au mode clair/sombre actuel.
    À appeler une fois dans app.py — après le toggle "mode_sombre".
    """
    sombre = _mode_sombre()
    bg_app = BOXDARK_2 if sombre else BG_LIGHT
    bg_carte = BOXDARK if sombre else "#FFFFFF"
    bg_alerte = STROKEDARK if sombre else TERRACOTTA_50
    bordure = STROKEDARK if sombre else STROKE
    texte = BODYDARK1 if sombre else TEXTE

    css = f"""
    <style>
    html, body, [class*="css"] {{
    font-family: 'CaviarDreams', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    [data-testid="stAppViewContainer"] {{
    background-color: {bg_app} !important;
    }}
    [data-testid="stAppViewContainer"] * {{
    color: {texte};
    }}
    [data-testid="stHeader"] {{
    background-color: transparent !important;
    }}
    [data-testid="stSidebar"] {{
    background-color: {BOXDARK_2} !important;
    }}
    [data-testid="stSidebar"] * {{
    color: {BODYDARK1} !important;
    }}
    [data-testid="stSidebarNav"] a[aria-current="page"] {{
    background-color: {PRIMARY} !important;
    color: #FFFFFF !important;
    border-radius: 6px;
    }}
    [data-testid="stSidebarNav"] span:not(a *),
    [data-testid="stSidebarNav"] p:not(a *) {{
    font-weight: 700 !important;
    font-size: 15px !important;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    }}
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {{
    background-color: {bg_carte} !important;
    color: {texte} !important;
    border: 1px solid {bordure} !important;
    border-radius: 0px !important;
    }}
    /* Règle universelle : tout élément de la zone principale et de la
       sidebar passe en coins carrés, quel que soit son nom de classe
       interne (qui change entre versions de Streamlit) — sauf nos
       propres iframes, qui sont des documents isolés avec leur propre
       CSS et ne sont donc pas affectés par cette règle de toute façon. */
    [data-testid="stAppViewContainer"] *,
    [data-testid="stMain"] *,
    [data-testid="stSidebar"] * {{
    border-radius: 0px !important;
    }}
    [data-baseweb="select"] span,
    [data-baseweb="select"] div {{
    color: {texte} !important;
    }}
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div,
    [data-baseweb="menu"],
    ul[data-baseweb="menu"] {{
    border-radius: 0px !important;
    background-color: {bg_carte} !important;
    border: 1px solid {bordure} !important;
    }}
    [data-baseweb="popover"] li,
    li[data-baseweb="menu-item"] {{
    background-color: {bg_carte} !important;
    color: {texte} !important;
    border-radius: 0px !important;
    }}
    [data-testid="stCheckbox"] span[data-baseweb],
    [role="checkbox"] {{
    background-color: {bg_carte} !important;
    border: 1px solid {bordure} !important;
    }}
    [data-testid="stCheckbox"] label p,
    [data-testid="stCheckbox"] p {{
    color: {texte} !important;
    }}
    [role="combobox"],
    [role="listbox"] {{
    background-color: {bg_carte} !important;
    color: {texte} !important;
    border: 1px solid {bordure} !important;
    }}
    [role="option"] {{
    background-color: {bg_carte} !important;
    color: {texte} !important;
    }}
    [data-testid="stSlider"] [data-baseweb="slider"] {{
    background: transparent !important;
    }}
    [data-testid="stButton"] button,
    [data-testid="stFormSubmitButton"] button,
    [data-testid^="stBaseButton"] {{
    border-radius: 0px !important;
    border: 1px solid {bordure} !important;
    }}
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] {{
    border-radius: 0px !important;
    background-color: {PRIMARY} !important;
    }}
    [data-testid="stCustomComponentV1"] iframe,
    [data-testid="stIFrame"] {{
    border-radius: 0px !important;
    border: 1px solid {bordure} !important;
    }}
    [data-testid="stAlert"] {{
    background-color: {bg_alerte} !important;
    border-radius: 0px !important;
    border: 1px solid {bordure} !important;
    border-left: 4px solid {PRIMARY} !important;
    }}
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span {{
    color: {texte} !important;
    }}
    [data-testid="stAlert"] svg {{
    fill: {PRIMARY} !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid*="VerticalBlockBorderWrapper"],
    div[class*="stVerticalBlockBorderWrapper"] {{
    background-color: {bg_carte} !important;
    border-radius: 0px !important;
    border: 1px solid {bordure} !important;
    box-shadow: 0px 1px 3px rgba(0,0,0,0.08) !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] > div,
    div[data-testid*="VerticalBlockBorderWrapper"] > div {{
    border-radius: 0px !important;
    }}
    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] > div {{
    border-radius: 0px !important;
    border: 1px solid {bordure} !important;
    box-shadow: 0px 1px 3px rgba(0,0,0,0.08) !important;
    }}
    </style>
    """
    st.markdown(_sans_indentation(css), unsafe_allow_html=True)


# ============================================================
# Icônes — Tabler Icons (chargées via CDN dans le document iframe des
# cartes KPI). Le template original dessine ses SVG à la main ; on garde
# une police d'icônes fiable en CDN plutôt que de recréer chaque tracé.
# ============================================================
ICONES_TI = {
    "maison": "ti-home",
    "argent": "ti-cash",
    "regle": "ti-ruler-2",
    "villes": "ti-building-skyscraper",
    "pin": "ti-map-pin",
    "lien": "ti-database",
    "surface": "ti-square",
}


def rendre_cartes_kpi_grille_html(lignes) -> str:
    """
    Construit un document HTML autonome pour des cartes KPI organisées en
    une grille CSS à 12 colonnes, une ou plusieurs rangées, chaque carte
    d'une rangée occupant une part égale de la largeur (12 / nb de cartes
    de cette rangée) — donc toutes les rangées font la même largeur totale,
    quel que soit le nombre de cartes par rangée.

    Un seul iframe (plutôt qu'un iframe par carte ou par rangée), parce que
    Streamlit ajoute une marge fixe et peu réglable entre deux st.columns()
    consécutifs — une grille CSS unique donne un contrôle total et fiable
    sur l'espacement, y compris entre rangées.

    Args:
        lignes: liste de rangées, chaque rangée étant une liste de tuples
            (cle_icone, label, valeur). Exemple pour 4 puis 3 cartes :
            [[carte1, carte2, carte3, carte4], [carte5, carte6, carte7]]
    """
    sombre = _mode_sombre()
    bg_carte = BOXDARK if sombre else "#FFFFFF"
    bordure = STROKEDARK if sombre else STROKE
    bg_cercle = STROKEDARK if sombre else META_2
    couleur_icone = SECONDARY if sombre else PRIMARY
    couleur_valeur = BODYDARK1 if sombre else TEXTE
    couleur_label = BODYDARK if sombre else "#64748B"
    fond_page_iframe = bg_carte if sombre else "transparent"

    blocs = []
    for ligne in lignes:
        colonnes = max(1, 12 // len(ligne))
        for cle_icone, label, valeur in ligne:
            icone_classe = ICONES_TI.get(cle_icone, "ti-chart-bar")
            blocs.append(f'''<div class="dd-carte" style="grid-column: span {colonnes};">
<div class="dd-cercle"><i class="ti {icone_classe}" style="color:{couleur_icone}; font-size:19px;"></i></div>
<p class="dd-valeur">{valeur}</p>
<p class="dd-label">{label}</p>
</div>''')

    corps = "".join(blocs)

    return _sans_indentation(f'''<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
<style>
@font-face {{ font-family:'CaviarDreams'; src:url('app/static/CaviarDreams.ttf'); font-weight:400; }}
@font-face {{ font-family:'CaviarDreams'; src:url('app/static/CaviarDreams_Bold.ttf'); font-weight:700; }}
html, body {{ margin:6px; padding:0; height:100%; box-sizing:border-box; overflow:hidden; background:{fond_page_iframe}; font-family:'CaviarDreams', sans-serif; }}
.dd-grille {{ display:grid; grid-template-columns: repeat(12, 1fr); gap:6px; height:100%; }}
.dd-carte {{ box-sizing:border-box; border-radius:0px; border:1px solid {bordure}; background:{bg_carte}; box-shadow:0px 1px 3px rgba(0,0,0,0.08); padding:16px 18px; overflow:hidden; }}
.dd-cercle {{ width:36px; height:36px; border-radius:50%; background:{bg_cercle}; display:flex; align-items:center; justify-content:center; }}
.dd-valeur {{ font-size:21px; font-weight:700; color:{couleur_valeur}; margin:14px 0 0; white-space:nowrap; }}
.dd-label {{ font-size:13px; color:{couleur_label}; margin:2px 0 0; }}
@media (max-width: 600px) {{
html, body {{ overflow-y: auto; overflow-x: hidden; height: auto; min-height: 100%; }}
.dd-grille {{ grid-template-columns: repeat(2, 1fr); height: auto; }}
.dd-carte {{ grid-column: span 1 !important; padding: 12px 14px; }}
.dd-valeur {{ font-size: 17px; white-space: normal; }}
.dd-cercle {{ width: 30px; height: 30px; }}
}}
</style>
</head>
<body>
<div class="dd-grille">
{corps}
</div>
</body>
</html>''')


def rendre_titre_carte(titre: str, couleur: str = None) -> str:
    """
    Titre d'en-tête de carte avec puce colorée (point + texte en gras),
    façon en-tête de graphique des dashboards modernes (ex: "● Total Revenue").
    À afficher via st.markdown(..., unsafe_allow_html=True).
    """
    couleur = couleur or PRIMARY
    couleur_texte = BODYDARK1 if _mode_sombre() else TEXTE
    return (
        f'<div style="display:flex; align-items:center; gap:10px; margin-bottom:14px;">'
        f'<span style="width:12px; height:12px; min-width:12px; border-radius:50%; background:{couleur};"></span>'
        f'<span style="font-size:22px; font-weight:700; color:{couleur_texte}; font-family:\'CaviarDreams\', sans-serif;">{titre}</span>'
        f'</div>'
    )


def rendre_tableau_html(df, hauteur: int = 320) -> str:
    """
    Construit un document HTML autonome pour un tableau de données,
    entièrement fabriqué (pas st.dataframe, qui est dessiné sur un canvas
    et ne peut pas être stylisé finement) — contrôle total sur l'en-tête
    (centré, gras, en couleur de marque), le texte (noir/blanc selon le
    mode), les rayures zébrées légères pour un rendu "moderne".

    Args:
        df: DataFrame pandas à afficher (les colonnes sont affichées telles quelles)
        hauteur: hauteur totale en pixels de l'iframe
    """
    sombre = _mode_sombre()
    bg_carte = BOXDARK if sombre else "#FFFFFF"
    bordure = STROKEDARK if sombre else STROKE
    couleur_texte = BODYDARK1 if sombre else TEXTE
    bg_zebre = "rgba(255,255,255,0.03)" if sombre else "rgba(146,100,73,0.04)"
    couleur_entete = SECONDARY if sombre else PRIMARY

    entetes = "".join(f'<th>{col}</th>' for col in df.columns)

    lignes = []
    for i, (_, row) in enumerate(df.iterrows()):
        bg_ligne = bg_zebre if i % 2 == 1 else "transparent"
        cellules = []
        for col in df.columns:
            valeur = row[col]
            if isinstance(valeur, str) and valeur.startswith("http"):
                align = "left"
                contenu = f'<a href="{valeur}" target="_blank" style="color:{couleur_entete}; font-weight:600;">Voir l\'annonce ↗</a>'
            else:
                align = "right" if isinstance(valeur, (int, float)) else "left"
                contenu = str(valeur)
            cellules.append(f'<td style="text-align:{align};">{contenu}</td>')
        lignes.append(f'<tr style="background:{bg_ligne};">{"".join(cellules)}</tr>')

    corps = "".join(lignes)

    return _sans_indentation(f'''<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@font-face {{ font-family:'CaviarDreams'; src:url('app/static/CaviarDreams.ttf'); font-weight:400; }}
@font-face {{ font-family:'CaviarDreams'; src:url('app/static/CaviarDreams_Bold.ttf'); font-weight:700; }}
html, body {{ margin:0; padding:6px; height:100%; box-sizing:border-box; overflow:auto; background:transparent; font-family:'CaviarDreams', sans-serif; }}
.dd-carte {{ box-sizing:border-box; border-radius:0px; border:1px solid {bordure}; background:{bg_carte}; box-shadow:0px 1px 3px rgba(0,0,0,0.08); overflow-x:auto; overflow-y:hidden; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
th {{ text-align:center; font-weight:700; color:{couleur_entete}; padding:12px 14px; border-bottom:2px solid {bordure}; white-space:nowrap; }}
td {{ padding:10px 14px; color:{couleur_texte}; border-bottom:1px solid {bordure}; white-space:nowrap; }}
@media (max-width: 600px) {{
table {{ font-size:12px; }}
th, td {{ padding:8px 10px; }}
}}
</style>
</head>
<body>
<div class="dd-carte">
<table><thead><tr>{entetes}</tr></thead><tbody>{corps}</tbody></table>
</div>
</body>
</html>''')


def rendre_carte_graphique_html(titre: str, couleur_puce: str, fig, hauteur: int = 400) -> str:
    """
    Construit un document HTML autonome pour une carte "graphique" : même
    carte (coins nets, bordure, ombre) que les cartes KPI, avec Plotly.js
    chargé directement dans l'iframe pour tracer la figure.

    Contrairement à st.container(border=True) + st.plotly_chart, cette
    approche ne dépend d'aucun nom de classe interne à Streamlit (qui a
    changé entre versions et empêchait nos règles CSS de s'appliquer) —
    la carte est entièrement fabriquée et contrôlée ici.

    La hauteur du graphique est calculée précisément à partir de `hauteur`
    (moins l'en-tête et le padding), pour que le contenu tienne exactement
    dans l'iframe sans jamais faire apparaître de barre de défilement.

    Args:
        titre: titre affiché en en-tête de carte (avec puce colorée)
        couleur_puce: couleur hex de la puce devant le titre
        fig: figure Plotly (déjà passée par appliquer_theme)
        hauteur: hauteur totale en pixels de l'iframe (carte comprise)
    """
    sombre = _mode_sombre()
    bg_carte = BOXDARK_CHART if sombre else "#FFFFFF"
    bordure = STROKEDARK if sombre else STROKE
    couleur_texte = BODYDARK1 if sombre else TEXTE

    # En-tête (puce + titre) ~30px + padding vertical de la carte (20px haut + 20px bas)
    hauteur_graphique = max(hauteur - 82, 150)
    fig.update_layout(height=hauteur_graphique, autosize=True)
    fig_json = fig.to_json()

    return _sans_indentation(f'''<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
@font-face {{ font-family:'CaviarDreams'; src:url('app/static/CaviarDreams.ttf'); font-weight:400; }}
@font-face {{ font-family:'CaviarDreams'; src:url('app/static/CaviarDreams_Bold.ttf'); font-weight:700; }}
html, body {{ margin: 0; padding: 6px; height: 100%; box-sizing: border-box; overflow: hidden; background: transparent; font-family: 'CaviarDreams', -apple-system, sans-serif; }}
.dd-carte {{
border-radius: 0px;
border: 1px solid {bordure};
background: {bg_carte};
box-shadow: 0px 1px 3px rgba(0,0,0,0.08);
padding: 24px 26px;
box-sizing: border-box;
height: 100%;
overflow: hidden;
}}
.dd-titre {{ display:flex; align-items:center; gap:8px; margin-bottom:12px; }}
.dd-puce {{ width:10px; height:10px; min-width:10px; border-radius:50%; background:{couleur_puce}; }}
.dd-texte {{ font-size:18px; font-weight:700; color:{couleur_texte}; }}
#graphique {{ width:100%; height:{hauteur_graphique}px; }}
@media (max-width: 600px) {{
.dd-carte {{ padding: 14px 12px; }}
.dd-texte {{ font-size: 15px; }}
}}
</style>
</head>
<body>
<div class="dd-carte">
<div class="dd-titre"><span class="dd-puce"></span><span class="dd-texte">{titre}</span></div>
<div id="graphique"></div>
</div>
<script>
var figure = {fig_json};
Plotly.newPlot('graphique', figure.data, figure.layout, {{responsive: true, displaylogo: false}});
</script>
</body>
</html>''')


def rendre_trend(valeur: float) -> str:
    """
    Badge de tendance textuel simple, dans l'esprit sobre de TailAdmin
    v1.3 : vert si positif, rouge si négatif.

    À utiliser uniquement quand une vraie comparaison existe (ex: variation
    trimestrielle réelle) — jamais avec un chiffre fabriqué.
    """
    couleur = META_VERT if valeur >= 0 else META_ROUGE
    icone = "ti-arrow-up" if valeur >= 0 else "ti-arrow-down"
    return (
        f'<span style="color:{couleur}; display:inline-flex; align-items:center; '
        f'gap:2px; font-weight:500;"><i class="ti {icone}"></i> {abs(valeur):.1f}%</span>'
    )
