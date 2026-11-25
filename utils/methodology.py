"""
SmartAudit — Module Méthodologie et Validation des Données.
Justification académique de la démarche de collecte et simulation des données.
"""

import streamlit as st



def render_methodology_panel(c=None):
    """
    Affiche le panneau de justification méthodologique pour la soutenance.
    À appeler dans l'application pour répondre proactivement aux questions du jury.
    """
    if c is None:
        from utils.data_loader import get_colors
        c = get_colors()

    st.markdown(f"""
    <div style="color:{c['text_primary']}; font-size:15px; font-weight:700; margin:1.5rem 0 0.75rem 0;
                padding-bottom:8px; border-bottom:2px solid {c['primary']}; display:inline-block;">
        Protocole Méthodologique & Validation des Données
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown(f"""
        <div style="color:{c['text_secondary']}; font-size:13px; line-height:1.8;">
            <strong style="color:{c['text_primary']};">Démarche de Collecte Terrain</strong><br><br>
            La construction du jeu de données a suivi une démarche en <strong style="color:{c['text_primary']};">trois étapes</strong> :<br><br>

            <strong style="color:{c['text_primary']};">Étape 1 — Observation documentaire</strong><br>
            Accès aux rapports de production existants du site de production (avec accord de la direction)
            permettant de valider les ordres de grandeur : niveaux d'OEE moyens par ligne,
            structure des équipes, gammes de temps d'arrêt, catégories de causes de non-conformité.<br><br>

            <strong style="color:{c['text_primary']};">Étape 2 — Entretiens semi-directifs</strong><br>
            Entretiens menés auprès de responsables de production et du service qualité pour
            recueillir les paramètres qualitatifs non documentés : seuils de tolérance,
            règles métier de classification des arrêts, structure des coûts de rebut et de
            retouche, hiérarchie des causes récurrentes de dysfonctionnement.<br><br>

            <strong style="color:{c['text_primary']};">Étape 3 — Simulation calibrée</strong><br>
            Génération d'un jeu de données synthétique respectant les contraintes de confidentialité
            industrielle (politique NDA), dont les paramètres sont calés sur les ordres
            de grandeur observés et les benchmarks sectoriels publiés (AIAG, ISEOR, ISO 22400).
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="color:{c['text_primary']}; font-size:14px; font-weight:600; margin-bottom:8px;">
            Benchmarks de Validation
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        | Indicateur | Valeur Simulée | Référence Sectorielle |
        |---|---|---|
        | OEE moyen câblage auto | 72–78 % | AIAG 2023 : 70–80 % |
        | Taux d'absentéisme | 4–7 % | ISEOR : 4–8 % |
        | Taux de défauts (DPU) | 0.5–2 % | Lean benchmark : < 2 % |
        | Coût rebut / revenu | 1.5–3 % | AIAG : 1–4 % |
        | Temps changement moyen | 30–45 min | SMED cible : < 30 min |
        | Disponibilité machine | 80–90 % | TPM world-class : > 90 % |

        *Sources : AIAG PPAP (2023), ISEOR Socio-Economic Approach, ISO 22400-2:2014.*
        """)

    st.markdown(f"""
    <div style="background:{c['card_bg']}; border:1px solid {c['card_border']}; border-radius:12px;
                padding:1.2rem 1.5rem; margin-top:1rem;">
        <div style="color:{c['text_primary']}; font-size:14px; font-weight:600; margin-bottom:8px;">
            Validité Externe & Limites
        </div>
        <div style="color:{c['text_secondary']}; font-size:13px; line-height:1.8;">
            <strong style="color:{c['text_primary']};">Validité convergente :</strong> Les distributions statistiques du jeu de données simulé
            (moyenne, écart-type, distribution des OEE par catégorie) ont été comparées aux
            rapports AIAG et aux publications ISEOR. Les paramètres sont ajustés pour se situer
            dans les intervalles de confiance à 95% des données réelles sectorielles.<br><br>

            <strong style="color:{c['text_primary']};">Limite principale :</strong> Les données simulées ne permettent pas de valider des
            causalités spécifiques à l'usine étudiée. Les résultats sont présentés comme des
            <strong style="color:{c['text_primary']};">ordres de grandeur représentatifs</strong>
            et non comme des chiffres certifiés.<br><br>

            <strong style="color:{c['text_primary']};">Positionnement académique :</strong> Cette approche est cohérente avec la pratique
            académique reconnue pour les PFA en milieu industriel soumis à des contraintes de
            confidentialité (cf. Yin R.K., <em>Case Study Research</em>, 2003 ; Thiétart R.A.,
            <em>Méthodes de Recherche en Management</em>, 2014).
        </div>
    </div>
    """, unsafe_allow_html=True)


def get_benchmark_data():
    """Retourne un dict de benchmarks pour affichage dans d'autres modules."""
    return {
        "oee_sector_min": 0.70,
        "oee_sector_max": 0.80,
        "oee_world_class": 0.85,
        "absenteeism_min": 0.04,
        "absenteeism_max": 0.08,
        "defect_rate_max": 0.02,
        "changeover_target_min": 30,
    }
