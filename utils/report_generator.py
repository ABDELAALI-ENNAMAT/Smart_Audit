import streamlit as st

"""
SmartAudit — Generateur de rapports PDF et Excel.
Utilise fpdf2 pour les PDF et openpyxl pour les exports Excel.
"""

import os
import io
from datetime import datetime
from fpdf import FPDF
import pandas as pd
from utils.data_loader import format_currency

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "company_logo.png")

# Palette couleurs corporate pour PDF (neutre/bleu, indépendant du thème web)
C_PRIMARY = (0, 48, 135)
C_SECONDARY = (0, 102, 204)
C_ACCENT = (255, 107, 0)
C_DARK = (10, 14, 26)
C_WHITE = (255, 255, 255)
C_GRAY = (156, 163, 175)
C_SUCCESS = (16, 185, 129)
C_WARNING = (245, 158, 11)
C_DANGER = (239, 68, 68)

from utils.constants import SHIFT_MAP_FR, DOWNTIME_REASON_MAP_FR

class CompanyPDF(FPDF):
    """Classe PDF personnalisee avec en-tete et pied de page corporate."""

    def header(self):
        """En-tete avec logo et ligne bleue."""
        if os.path.exists(LOGO_PATH):
            try:
                self.image(LOGO_PATH, 10, 8, 35)
            except Exception:
                pass
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*C_GRAY)
        self.cell(0, 10, "SmartAudit — Performance Intelligence", align="R")
        self.ln(12)
        self.set_draw_color(*C_SECONDARY)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        """Pied de page avec numero de page."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*C_GRAY)
        self.cell(0, 10, f"Généré automatiquement - SmartAudit — Système de Performance | Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        """Titre de section formate."""
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*C_PRIMARY)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*C_SECONDARY)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(4)

    def kpi_box(self, label, value, x, y, w=42, h=22, val_color=C_PRIMARY):
        """Boite KPI stylee."""
        self.set_fill_color(248, 250, 252)
        self.set_draw_color(226, 232, 240)
        self.rect(x, y, w, h, style="DF")
        self.set_xy(x + 2, y + 2)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 116, 139)
        self.cell(w - 4, 5, label, align="C")
        self.set_xy(x + 2, y + 8)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*val_color)
        self.cell(w - 4, 10, str(value), align="C")


def _safe_pdf_bytes(pdf):
    """Safely get bytes from pdf.output(), handling both str and bytes returns."""
    result = pdf.output()
    if isinstance(result, str):
        return result.encode('latin-1')
    elif isinstance(result, bytearray):
        return bytes(result)
    return result


def generate_daily_report(df, date):
    """Genere un rapport flash journalier PDF de 2 pages."""
    day_data = df[df["Date"].dt.date == pd.to_datetime(date).date()]
    if day_data.empty:
        pdf = CompanyPDF()
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*C_PRIMARY)
        pdf.cell(0, 12, "Rapport Flash Journalier", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(20)
        pdf.set_font("Helvetica", "", 14)
        pdf.set_text_color(*C_DANGER)
        pdf.cell(0, 10, f"Aucune donnee de production pour le {pd.to_datetime(date).strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT", align="C")
        return _safe_pdf_bytes(pdf)

    pdf = CompanyPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # -- Page 1 --
    pdf.add_page()

    # Confidentiel stamp
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(224, 242, 254)  # Light blue
    pdf.set_xy(120, 25)
    pdf.cell(80, 10, "CONFIDENTIEL - Usage interne", align="R")
    pdf.set_xy(10, 30)

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*C_PRIMARY)
    pdf.cell(0, 12, "Rapport Flash Journalier", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(0, 8, f"Performance Production -- {pd.to_datetime(date).strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(8)

    # KPI boxes
    avg_oee = day_data["OEE"].mean() * 100
    total_hc = day_data["Total_Hidden_Cost"].sum()
    n_alerts = int(day_data["Anomaly_Flag"].sum()) if "Anomaly_Flag" in day_data.columns else 0
    conformity = (day_data["OEE"] >= 0.75).mean() * 100

    oee_color = C_SUCCESS if avg_oee >= 85 else (C_WARNING if avg_oee >= 75 else C_DANGER)
    hc_color = C_DANGER if total_hc > 15000 else C_WARNING

    y = pdf.get_y()
    pdf.kpi_box("OEE Moyen", f"{avg_oee:.1f}%", 12, y, val_color=oee_color)
    pdf.kpi_box("Coûts Cachés", format_currency(total_hc), 58, y, val_color=hc_color)
    pdf.kpi_box("Alertes", str(n_alerts), 104, y, val_color=C_DANGER if n_alerts > 0 else C_SUCCESS)
    pdf.kpi_box("Conformité", f"{conformity:.0f}%", 150, y, val_color=C_SUCCESS if conformity >= 75 else C_DANGER)
    pdf.set_y(y + 30)

    # --- SYNTHESE MANAGERIALE ---
    pdf.section_title("Synthèse Managériale")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*C_DARK)
    
    worst_line = day_data.groupby("Production_Line")["OEE"].mean().idxmin() if not day_data.empty else "N/A"
    worst_oee = day_data.groupby("Production_Line")["OEE"].mean().min() * 100 if not day_data.empty else 0
    
    oee_status = "atteint l'objectif" if avg_oee >= 85 else "est en deçà de l'objectif (85%)"
    synthese_text = (
        f"La journée du {pd.to_datetime(date).strftime('%d/%m/%Y')} s'est clôturée avec un OEE moyen de {avg_oee:.1f}%, "
        f"ce qui {oee_status}. Le total des coûts cachés induits par les différentes anomalies s'élève à {format_currency(total_hc)}. "
    )
    if worst_line != "N/A":
        synthese_text += f"L'attention doit se porter particulièrement sur la ligne {worst_line}, qui affiche la plus faible performance ({worst_oee:.1f}%)."
        
    pdf.multi_cell(0, 5, synthese_text)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*C_ACCENT)
    pdf.cell(0, 5, "Recommandation Action : ", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*C_DARK)
    pdf.multi_cell(0, 5, f"Planifier une vérification préventive immédiate sur la ligne {worst_line} et analyser le premier motif d'arrêt.")
    pdf.ln(8)
    # --- END SYNTHESE ---

    # Tableau des equipes
    pdf.section_title("Performance par Équipe")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(*C_PRIMARY)
    pdf.set_text_color(*C_WHITE)
    headers = ["Ligne", "Équipe", "OEE %", "Dispo %", "Perf %", "Qualité %", "Coût Caché"]
    widths = [22, 22, 20, 22, 22, 22, 32]
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 7, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for _, row in day_data.iterrows():
        oee_val = row.get("OEE", 0) * 100
        if oee_val >= 85:
            pdf.set_fill_color(220, 252, 231)  # Green
            pdf.set_text_color(22, 101, 52)
        elif oee_val >= 75:
            pdf.set_fill_color(254, 249, 195)  # Yellow
            pdf.set_text_color(133, 77, 14)
        else:
            pdf.set_fill_color(254, 226, 226)  # Red
            pdf.set_text_color(153, 27, 27)

        pdf.cell(widths[0], 6, str(row.get("Production_Line", "")), border=1, fill=True, align="C")
        SHIFT_MAP_FR = {"Morning": "Matin", "Afternoon": "Après-midi", "Night": "Nuit"}
        shift_fr = SHIFT_MAP_FR.get(row.get("Shift_Type", ""), row.get("Shift_Type", ""))
        pdf.cell(widths[1], 6, str(shift_fr), border=1, fill=True, align="C")
        pdf.cell(widths[2], 6, f"{oee_val:.1f}", border=1, fill=True, align="C")
        
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(50, 50, 50)
        vals = [
            f"{row.get('Availability', 0)*100:.1f}",
            f"{row.get('Performance', 0)*100:.1f}",
            f"{row.get('Quality', 0)*100:.1f}",
            format_currency(row.get("Total_Hidden_Cost", 0)),
        ]
        for i, v in enumerate(vals, 3):
            pdf.cell(widths[i], 6, v, border=1, fill=True, align="C")
        pdf.ln()

    pdf.ln(8)
    pdf.section_title("Alertes de la Période")
    if "Anomaly_Flag" in day_data.columns:
        anomalies = day_data[day_data["Anomaly_Flag"] == True]
    else:
        anomalies = pd.DataFrame()
    if anomalies.empty:
        pdf.set_fill_color(220, 252, 231)
        pdf.set_text_color(22, 101, 52)
        pdf.cell(0, 10, "  Aucune anomalie détectée (OK)", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(*C_DANGER)
        pdf.set_text_color(*C_WHITE)
        pdf.cell(30, 7, "Équipe", border=1, fill=True, align="C")
        pdf.cell(50, 7, "Cause Probable", border=1, fill=True, align="C")
        pdf.cell(40, 7, "OEE Impacté", border=1, fill=True, align="C")
        pdf.cell(0, 7, "Coût Supplémentaire", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(50, 50, 50)
        if "Anomaly_Flag" in df.columns:
            avg_normal_hc = df[df["Anomaly_Flag"] == False]["Total_Hidden_Cost"].mean()
        else:
            avg_normal_hc = df["Total_Hidden_Cost"].mean() if "Total_Hidden_Cost" in df.columns else 0
        
        SHIFT_MAP_FR = {"Morning": "Matin", "Afternoon": "Après-midi", "Night": "Nuit"}
        for _, row in anomalies.iterrows():
            shift_fr = SHIFT_MAP_FR.get(row.get('Shift_Type'), row.get('Shift_Type'))
            shift = f"{row.get('Production_Line')} - {shift_fr}"
            cause_val = row.get('Downtime_Reason')
            cause = DOWNTIME_REASON_MAP_FR.get(cause_val, str(cause_val) if not pd.isna(cause_val) else 'Non spécifié')
            oee = f"{row.get('OEE', 0)*100:.1f}%"
            extra = format_currency(max(0, row.get('Total_Hidden_Cost', 0) - avg_normal_hc))
            
            pdf.cell(30, 6, shift, border=1, align="C")
            pdf.cell(50, 6, cause, border=1, align="C")
            pdf.cell(40, 6, oee, border=1, align="C")
            pdf.cell(0, 6, extra, border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    # -- Page 2 --
    pdf.add_page()
    pdf.section_title("Analyse des Coûts Cachés (approche inspirée ISEOR)")

    hc_a = day_data.get("Hidden_Cost_Availability", pd.Series([0])).sum()
    hc_p = day_data.get("Hidden_Cost_Performance", pd.Series([0])).sum()
    hc_q = day_data.get("Hidden_Cost_Quality", pd.Series([0])).sum()
    tot = hc_a + hc_p + hc_q

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(240, 245, 255)
    pdf.set_text_color(*C_PRIMARY)
    pdf.cell(50, 8, "Catégorie", border=1, fill=True, align="C")
    pdf.cell(50, 8, f"Montant ({st.session_state.get('app_currency', 'MAD')})", border=1, fill=True, align="C")
    pdf.cell(40, 8, "% du Total", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)
    cats = [
        ("Pertes de Disponibilité", hc_a),
        ("Pertes de Performance", hc_p),
        ("Pertes de Qualité", hc_q),
    ]
    for name, val in cats:
        pdf.cell(50, 7, name, border=1)
        pdf.cell(50, 7, format_currency(val), border=1, align="R")
        pct = f"{val/tot*100:.1f}%" if tot > 0 else "0%"
        pdf.cell(40, 7, pct, border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(50, 8, "TOTAL COÛTS CACHÉS", border=1)
    pdf.cell(50, 8, format_currency(tot), border=1, align="R")
    pdf.cell(40, 8, "100%", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    if tot > 0:
        main_cat = max(cats, key=lambda item: item[1])
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 6, f"Interprétation: Les {main_cat[0].lower()} représentent la source principale de pertes financières ({main_cat[1]/tot*100:.0f}% du total), indiquant le domaine prioritaire d'amélioration.")

    pdf.ln(10)
    pdf.section_title("Recommandations Managériales")
    
    recs = []
    # Data-driven recommendations
    if avg_oee < 72:
        recs.append(("URGENT", "Réunion de crise production recommandée", "L'OEE moyen est significativement sous le seuil critique de 75%. Analyser les causes racines des arrêts immédiatement."))
    elif avg_oee < 80:
        recs.append(("NORMAL", "Optimisation des temps de cycle", "L'OEE est moyen. Se concentrer sur la réduction des micro-arrêts et l'optimisation des changements de série."))
    
    att = day_data.get("Workforce_Attendance_Rate", pd.Series([1])).mean()
    if att < 0.87:
        recs.append(("URGENT", "Action RH préventive requise", f"Le taux de présence ({att*100:.1f}%) est trop bas et impacte directement la disponibilité des lignes."))
        
    line_hc = day_data.groupby("Production_Line")["Total_Hidden_Cost"].sum()
    if not line_hc.empty:
        worst_line = line_hc.idxmax()
        worst_hc = line_hc.max()
        if worst_hc > (tot / len(line_hc)) * 1.5:
            recs.append(("PLANIFIE", f"Audit de la ligne {worst_line}", f"Cette ligne concentre une part disproportionnée des coûts cachés ({format_currency(worst_hc)}). Une inspection approfondie est nécessaire."))

    if not recs:
        recs.append(("NORMAL", "Maintien des standards", "La performance globale est bonne. Maintenir les pratiques actuelles et cibler le statut World Class."))

    for i, (prio, title, desc) in enumerate(recs, 1):
        pdf.set_font("Helvetica", "B", 10)
        prio_color = C_DANGER if prio == "URGENT" else (C_SECONDARY if prio == "NORMAL" else C_ACCENT)
        pdf.set_text_color(*prio_color)
        pdf.cell(25, 6, f"[{prio}]")
        pdf.set_text_color(*C_PRIMARY)
        pdf.cell(0, 6, f"{i}. {title}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 5, f"   {desc}")
        pdf.ln(3)

    return _safe_pdf_bytes(pdf)


def generate_monthly_report(df, month_name):
    """Genere un rapport mensuel de performance (Controle de Gestion)."""
    if df.empty:
        pdf = CompanyPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, "Rapport Mensuel", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.cell(0, 10, f"Aucune donnee pour {month_name}", new_x="LMARGIN", new_y="NEXT", align="C")
        return _safe_pdf_bytes(pdf)

    pdf = CompanyPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # -- Page 1 : Couverture --
    pdf.add_page()
    pdf.ln(40)
    if os.path.exists(LOGO_PATH):
        try:
            pdf.image(LOGO_PATH, x=70, y=50, w=70)
        except Exception:
            pass
    pdf.set_y(95)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*C_PRIMARY)
    pdf.cell(0, 15, "Rapport Mensuel", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "de Performance", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(0, 10, "Controle de Gestion -- Production", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*C_ACCENT)
    data_year = df["Date"].dt.year.max() if not df.empty else datetime.now().year
    pdf.cell(0, 12, f"{month_name} {data_year}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    
    # Stamp
    pdf.set_fill_color(254, 226, 226)
    pdf.set_draw_color(*C_DANGER)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*C_DANGER)
    pdf.set_x(70)
    pdf.cell(70, 12, "CONFIDENTIEL", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(0, 8, "Préparé par : SmartAudit — Système de Performance", align="C", new_x="LMARGIN", new_y="NEXT")

    # -- Page 2 : Executive Summary --
    pdf.add_page()
    pdf.section_title("Résumé Exécutif")
    avg_oee = df["OEE"].mean() * 100
    total_hc = df["Total_Hidden_Cost"].sum()
    n_shifts = len(df)
    conformity = (df["OEE"] >= 0.75).mean() * 100
    n_anomalies = df["Anomaly_Flag"].sum() if "Anomaly_Flag" in df.columns else 0
    avg_qual = df["Quality"].mean() * 100
    avg_att = df["Workforce_Attendance_Rate"].mean() * 100 if "Workforce_Attendance_Rate" in df.columns else 95

    # Traffic light table
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 245, 255)
    pdf.set_text_color(*C_PRIMARY)
    pdf.cell(60, 8, "Indicateur", border=1, fill=True, align="C")
    pdf.cell(40, 8, "Valeur", border=1, fill=True, align="C")
    pdf.cell(40, 8, "Objectif", border=1, fill=True, align="C")
    pdf.cell(30, 8, "Statut", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    def print_traffic_row(name, val_str, target_str, is_good, is_warn):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(60, 8, f"  {name}", border=1)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(40, 8, val_str, border=1, align="C")
        pdf.cell(40, 8, target_str, border=1, align="C")
        
        pdf.set_font("Helvetica", "B", 9)
        if is_good:
            pdf.set_text_color(*C_SUCCESS)
            status = "OK"
        elif is_warn:
            pdf.set_text_color(*C_WARNING)
            status = "ATTENTION"
        else:
            pdf.set_text_color(*C_DANGER)
            status = "CRITIQUE"
        pdf.cell(30, 8, status, border=1, align="C")
        pdf.set_text_color(50, 50, 50)
        pdf.ln()

    print_traffic_row("OEE Moyen", f"{avg_oee:.1f}%", "> 85%", avg_oee >= 85, avg_oee >= 75)
    print_traffic_row("Taux de Conformité", f"{conformity:.0f}%", "> 90%", conformity >= 90, conformity >= 75)
    print_traffic_row("Coûts Cachés Totaux", format_currency(total_hc), "Minimiser", total_hc < n_shifts*500, total_hc < n_shifts*1000)
    print_traffic_row("Anomalies Détectées", str(n_anomalies), "< 5%", n_anomalies < n_shifts*0.05, n_anomalies < n_shifts*0.1)
    print_traffic_row("Qualité Moyenne", f"{avg_qual:.1f}%", "> 99%", avg_qual >= 99, avg_qual >= 97)
    print_traffic_row("Taux de Présence", f"{avg_att:.1f}%", "> 95%", avg_att >= 95, avg_att >= 90)

    pdf.ln(10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    narrative = f"Au cours du mois de {month_name}, l'usine a fonctionné sur {n_shifts} équipes de production. La performance globale mesurée par l'OEE s'établit à {avg_oee:.1f}%. Les pertes financières associées aux inefficacités (Coûts Cachés) ont été évaluées à {format_currency(total_hc)} par un modèle de coûts cachés inspiré de l'approche ISEOR.\n\n"
    if avg_oee < 75:
        narrative += "La performance est jugée critique. Des plans d'action immédiats sont nécessaires sur la disponibilité et la vitesse des lignes pour revenir aux standards de l'entreprise."
    elif avg_oee < 85:
        narrative += "La performance est sous l'objectif World Class mais reste dans la zone de contrôle. Des actions d'amélioration continue ciblent les pertes majeures."
    else:
        narrative += "Excellente performance globale, dépassant les objectifs World Class de 85%. Le focus doit rester sur le maintien des standards de qualité."
    pdf.multi_cell(0, 6, narrative)
    pdf.ln(4)
    
    # ── Top 3 des causes de défaillance — plan d'action prioritaire
    top_anomalies = []
    if "Anomaly_Flag" in df.columns and "Downtime_Reason" in df.columns:
        anoms = df[df["Anomaly_Flag"] == True]
        if not anoms.empty:
            top = anoms["Downtime_Reason"].value_counts().head(3)
            top_anomalies = [(DOWNTIME_REASON_MAP_FR.get(k, k), v) for k, v in top.items()]
            
    if top_anomalies:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*C_DANGER)
        pdf.cell(0, 5, "Top 3 des Causes de Défaillances (Plan d'Action Prioritaire):", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*C_DARK)
        for idx, (cause, count) in enumerate(top_anomalies, 1):
            pdf.cell(5, 5, "")
            pdf.cell(0, 5, f"{idx}. {cause} ({count} occurrences)", ln=True)
    pdf.ln(8)

    # -- Page 3 : Analyse OEE --
    pdf.add_page()
    pdf.section_title("Analyse OEE et Operationnelle")
    
    # Table by Shift and Line
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 10, "Performance par Ligne et Équipe", new_x="LMARGIN", new_y="NEXT")
    
    oee_pivot = df.pivot_table(values="OEE", index="Production_Line", columns="Shift_Type", aggfunc="mean") * 100
    
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(*C_PRIMARY)
    pdf.set_text_color(*C_WHITE)
    pdf.cell(40, 7, "Ligne", border=1, fill=True, align="C")
    shifts = ["Morning", "Afternoon", "Night"]
    SHIFT_MAP_FR = {"Morning": "Matin", "Afternoon": "Après-midi", "Night": "Nuit"}
    for s in shifts:
        if s in oee_pivot.columns:
            pdf.cell(40, 7, SHIFT_MAP_FR.get(s, s), border=1, fill=True, align="C")
    pdf.cell(30, 7, "Moyenne Ligne", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    for idx, row in oee_pivot.iterrows():
        pdf.cell(40, 6, str(idx), border=1, align="C")
        line_sum = 0
        line_count = 0
        for s in shifts:
            if s in oee_pivot.columns:
                val = row.get(s, float('nan'))
                if pd.isna(val):
                    pdf.cell(40, 6, "-", border=1, align="C")
                else:
                    pdf.cell(40, 6, f"{val:.1f}%", border=1, align="C")
                    line_sum += val
                    line_count += 1
        line_avg = line_sum / line_count if line_count > 0 else 0
        pdf.cell(30, 6, f"{line_avg:.1f}%", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    
    best = df.loc[df['OEE'].idxmax()]
    worst = df.loc[df['OEE'].idxmin()]
    
    SHIFT_MAP_FR = {"Morning": "Matin", "Afternoon": "Après-midi", "Night": "Nuit"}
    best_shift_fr = SHIFT_MAP_FR.get(best['Shift_Type'], best['Shift_Type'])
    worst_shift_fr = SHIFT_MAP_FR.get(worst['Shift_Type'], worst['Shift_Type'])
    pdf.set_fill_color(220, 252, 231)
    pdf.set_text_color(22, 101, 52)
    pdf.cell(0, 8, f"Meilleure équipe : {best['Production_Line']} - {best_shift_fr} le {best['Date'].strftime('%d/%m')} (OEE: {best['OEE']*100:.1f}%)", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_fill_color(254, 226, 226)
    pdf.set_text_color(153, 27, 27)
    pdf.cell(0, 8, f"Moins bonne équipe : {worst['Production_Line']} - {worst_shift_fr} le {worst['Date'].strftime('%d/%m')} (OEE: {worst['OEE']*100:.1f}%)", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    # -- Page 4 : Hidden Costs --
    pdf.add_page()
    pdf.section_title("Analyse Approfondie des Coûts Cachés (approche inspirée ISEOR)")
    
    hc_a = df.get("Hidden_Cost_Availability", pd.Series([0])).sum()
    hc_p = df.get("Hidden_Cost_Performance", pd.Series([0])).sum()
    hc_q = df.get("Hidden_Cost_Quality", pd.Series([0])).sum()
    tot = hc_a + hc_p + hc_q
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(240, 245, 255)
    pdf.set_text_color(*C_PRIMARY)
    pdf.cell(60, 8, "Catégorie (approche ISEOR)", border=1, fill=True, align="C")
    pdf.cell(50, 8, f"Montant Total ({st.session_state.get('app_currency', 'MAD')})", border=1, fill=True, align="C")
    pdf.cell(40, 8, "% du Total", border=1, fill=True, align="C")
    pdf.cell(40, 8, "Coût / Équipe", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)
    cats = [
        ("Surcoûts de Non-Disponibilité", hc_a),
        ("Surcoûts de Sous-Performance", hc_p),
        ("Surcoûts de Non-Qualité", hc_q),
    ]
    for name, val in cats:
        pdf.cell(60, 7, name, border=1)
        pdf.cell(50, 7, format_currency(val), border=1, align="R")
        pct = f"{val/tot*100:.1f}%" if tot > 0 else "0%"
        pdf.cell(40, 7, pct, border=1, align="C")
        pdf.cell(40, 7, format_currency(val/n_shifts), border=1, align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(60, 8, "TOTAL COÛTS CACHÉS", border=1)
    pdf.cell(50, 8, format_currency(tot), border=1, align="R")
    pdf.cell(40, 8, "100%", border=1, align="C")
    pdf.cell(40, 8, format_currency(tot/n_shifts), border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(10)
    total_good = df["Good_Units"].sum() if "Good_Units" in df.columns else 1
    hc_per_unit = tot / total_good if total_good > 0 else 0
    pdf.set_font("Helvetica", "I", 11)
    pdf.cell(0, 10, f"Coût caché moyen par unité bonne produite : {hc_per_unit:.2f} {st.session_state.get('app_currency', 'MAD')} / unité", new_x="LMARGIN", new_y="NEXT")
    
    if avg_oee < 85:
        # Savings formula: proportional reduction of hidden costs if OEE gap closed to 85%
        # Equivalent to: calculate_potential_savings(df) from utils.oee_calculations
        # Formula: total_hc_per_shift × (gap / (1 − current_oee)) × n_shifts
        savings = (tot / n_shifts) * (0.85 - (avg_oee/100)) / (1 - (avg_oee/100)) * n_shifts
        pdf.set_text_color(*C_SUCCESS)
        pdf.cell(0, 10, f"Économie mensuelle potentielle (si OEE = 85%) : {format_currency(savings)}", new_x="LMARGIN", new_y="NEXT")

    # -- Page 5 : Appendix --
    pdf.add_page()
    pdf.section_title("Annexe et Méthodologie")
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*C_PRIMARY)
    pdf.cell(0, 8, "Intelligence Artificielle et Prédiction", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)
    # Load model metrics dynamically if available
    _model_info = "Les modèles prédictifs embarqués dans le système (XGBoost et Random Forest) utilisent l'historique de production pour anticiper l'OEE avant le démarrage de chaque équipe."
    try:
        import joblib as _jl
        _models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
        _meta_path = os.path.join(_models_dir, "model_metadata.json")
        if os.path.exists(_meta_path):
            import json
            with open(_meta_path, "r") as _mf:
                _meta = json.load(_mf)
            _model_info += f"\n- Modèle sélectionné : {_meta.get('selected_model', 'XGBoost')}"
            _model_info += f"\n- R2 (Test) : {_meta.get('r2_test', 'N/A')}"
            _model_info += f"\n- MAE : {_meta.get('mae_test', 'N/A')}"
        else:
            _model_info += "\n- Modèle sélectionné : XGBoost"
            _model_info += "\n- R2 et MAE : voir model_metadata.json après entraînement"
    except Exception:
        pass
    _model_info += "\n- Les anomalies sont détectées par un modèle Isolation Forest (contamination = 5%)."
    pdf.multi_cell(0, 5, _model_info)
    
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*C_PRIMARY)
    pdf.cell(0, 8, "Notes sur le modèle de coûts cachés (approche inspirée ISEOR)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5, "La quantification financière des pertes utilise un modèle de coûts cachés inspiré de la méthode socio-économique de Savall & Zardet (ISEOR). Les pertes de capacité sont converties en manque à gagner en utilisant la marge sur le revenu unitaire (38%), évitant ainsi la double comptabilisation des coûts.")

    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(0, 5, "Ce rapport est généré automatiquement par le SmartAudit — Système de Performance Industrielle.", align="C")

    return _safe_pdf_bytes(pdf)


def generate_excel_report(df, period_label="Période"):
    """Génère un rapport Excel multi-feuilles avec style corporate."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Feuille Résumé
        summary_data = {
            "Indicateur": ["OEE Moyen", "Coût Caché Total", "Nb Équipes", "Taux Conformité", "Nb Anomalies"],
            "Valeur": [
                f"{df['OEE'].mean()*100:.1f}%",
                format_currency(df['Total_Hidden_Cost'].sum()),
                str(len(df)),
                f"{(df['OEE']>=0.75).mean()*100:.0f}%",
                str(int(df['Anomaly_Flag'].sum())) if 'Anomaly_Flag' in df.columns else "0",
            ],
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Résumé", index=False)

        # Feuille Donnees Brutes
        export_cols = [c for c in ["Date","Production_Line","Shift_Type","OEE","Availability",
                       "Performance","Quality","Total_Hidden_Cost","OEE_Category","Anomaly_Flag"] if c in df.columns]
        df[export_cols].to_excel(writer, sheet_name="Donnees", index=False)

        # Feuille Analyse OEE
        if "Production_Line" in df.columns:
            oee_pivot = df.pivot_table(values="OEE", index="Production_Line",
                                        columns="Shift_Type", aggfunc="mean")
            (oee_pivot * 100).round(1).to_excel(writer, sheet_name="Analyse OEE")

        # Feuille Coûts Cachés
        hc_cols = [c for c in ["Hidden_Cost_Availability","Hidden_Cost_Performance",
                   "Hidden_Cost_Quality","Total_Hidden_Cost"] if c in df.columns]
        if hc_cols:
            hc_by_line = df.groupby("Production_Line")[hc_cols].sum()
            hc_by_line.to_excel(writer, sheet_name="Coûts Cachés")

        # Feuille Anomalies
        if "Anomaly_Flag" in df.columns:
            anomalies = df[df["Anomaly_Flag"] == True]
            if not anomalies.empty:
                anomalies[export_cols].to_excel(writer, sheet_name="Anomalies", index=False)

    output.seek(0)
    return output.getvalue()
