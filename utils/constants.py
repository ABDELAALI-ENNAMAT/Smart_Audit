"""
SmartAudit — Constantes partagées.
Référentiel unique pour les mappings de traduction utilisés à travers l'application.
"""

SHIFT_MAP_FR = {
    "Morning": "Matin",
    "Afternoon": "Après-midi",
    "Night": "Nuit",
}
SHIFT_MAP_EN = {v: k for k, v in SHIFT_MAP_FR.items()}

DOWNTIME_REASON_MAP_FR = {
    "Supplier_Delay": "Retard Fournisseur",
    "Supplier Delay": "Retard Fournisseur",
    "IT_SAP_Issue": "Problème IT/SAP",
    "IT SAP Issue": "Problème IT/SAP",
    "Changeover_Issue": "Changement de Série",
    "Changeover Issue": "Changement de Série",
    "Operator_Absence": "Absence Opérateur",
    "Operator Absence": "Absence Opérateur",
    "Tool_Breakage": "Casse d\'Outil",
    "Tool Breakage": "Casse d\'Outil",
    "Quality_Hold": "Blocage Qualité",
    "Quality Hold": "Blocage Qualité",
    "Machine_Failure": "Panne Machine",
    "Machine Failure": "Panne Machine",
    "Material_Shortage": "Manque Matière",
    "Material Shortage": "Manque Matière",
    "Safety_Stop": "Arrêt Sécurité",
    "Safety Stop": "Arrêt Sécurité",
    "None": "Non spécifié",
}

# Currency conversion factor EUR/MAD
EUR_MAD_RATE = 10.8

# OEE classification thresholds (ISO 22400)
OEE_WORLD_CLASS = 0.85
OEE_ON_TARGET = 0.75

# Hidden cost margin coefficient (ISEOR methodology)
MARGIN_COEFFICIENT = 0.38
