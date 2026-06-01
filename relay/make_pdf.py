"""Génère un PDF récap des 2 stratégies, déposé dans ~/Downloads."""
from pathlib import Path

from fpdf import FPDF

NAVY = (16, 42, 67)
BLUE = (32, 92, 158)
GREY = (90, 90, 90)
LIGHT = (235, 240, 246)


class PDF(FPDF):
    def header(self):
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 22, "F")
        self.set_xy(10, 6)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 15)
        self.cell(0, 10, "AXONE CAPITAL  -  Strategies de signaux", align="L")
        self.set_xy(10, 14)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, "Futures indices US (NQ / ES / YM)  -  Prop firm Apex EOD & LucidFlex 50k")
        self.ln(16)

    def footer(self):
        self.set_y(-12)
        self.set_text_color(*GREY)
        self.set_font("Helvetica", "I", 7)
        self.cell(0, 5, "Document de travail - 31/05/2026 - usage personnel", align="C")
        self.set_x(-25)
        self.cell(0, 5, f"p. {self.page_no()}", align="R")


def h2(pdf, txt):
    pdf.ln(2)
    pdf.set_fill_color(*BLUE)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "  " + txt, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_text_color(20, 20, 20)


def para(pdf, txt, bold=False):
    pdf.set_font("Helvetica", "B" if bold else "", 9.5)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 5, txt, new_x="LMARGIN", new_y="NEXT")


def bullet(pdf, txt):
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_x(pdf.l_margin + 2)
    pdf.multi_cell(0, 5, "-  " + txt, new_x="LMARGIN", new_y="NEXT")


def kv_table(pdf, rows, widths=(70, 60, 60)):
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(255, 255, 255)
    headers = rows[0]
    for w, c in zip(widths, headers):
        pdf.cell(w, 6, c, border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_text_color(20, 20, 20)
    fill = False
    for row in rows[1:]:
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_fill_color(*LIGHT)
        for i, (w, c) in enumerate(zip(widths, row)):
            pdf.cell(w, 6, c, border=1, fill=fill, align="L" if i == 0 else "C")
        pdf.ln()
        fill = not fill


pdf = PDF()
pdf.set_auto_page_break(True, margin=16)
pdf.add_page()

# --- Cadre general --------------------------------------------------------
h2(pdf, "1. Cadre general")
bullet(pdf, "Instruments : Nasdaq (NQ), S&P 500 (ES), Dow Jones (YM).")
bullet(pdf, "Timeframe d'execution : M5 AVEC confluence M15 (englobante + divergence exigees sur les deux).")
bullet(pdf, "Tendance : H1 via MA20 vs MA50. MA20 > MA50 = haussier (achats) ; MA20 < MA50 = baissier (ventes).")
bullet(pdf, "On trade la session US. On ne rentre jamais sur les 5 premieres minutes de l'open.")
bullet(pdf, "Un trade par jour en moyenne (parfois deux).")

# --- Strategie 1 ----------------------------------------------------------
h2(pdf, "2. Strategie 1 - Prise de liquidite (range Asie / Londres)")
para(pdf, "On trace le haut et le bas du range de la session asiatique et de la session de Londres (4 niveaux).")
bullet(pdf, "1. Sweep d'un niveau de range = prise de liquidite (sweep du haut = setup vente ; sweep du bas = setup achat).")
bullet(pdf, "2. Reintegration RAPIDE dans le range : 3 bougies maximum (4+ = trop lent = pas de trade).")
bullet(pdf, "3. Entree a la cloture de la bougie de reintegration.")
bullet(pdf, "Regle cle : une liquidite ne se prend QU'UNE FOIS (meme soldee en SL, le setup est mort).")
para(pdf, "Stop-loss : juste au-dela de l'extreme du sweep.", bold=True)

# --- Strategie 2 ----------------------------------------------------------
h2(pdf, "3. Strategie 2 - Reaction sur niveau institutionnel")
para(pdf, "On ne trace pas les ranges : on trace les points pivots et l'open daily (niveaux que tous les acteurs voient).")
bullet(pdf, "Le prix TOUCHE un pivot ou l'open daily (depassement de quelques ticks tolere).")
bullet(pdf, "Reaction confirmee par une englobante / marteau + divergence RSI, SL protege par le pivot.")
bullet(pdf, "Une 2e reaction sur un pivot est toleree (la 1re reste la plus fiable).")
para(pdf, "Stop-loss : de l'autre cote du pivot.", bold=True)

# --- Scoring --------------------------------------------------------------
h2(pdf, "4. Systeme de scoring -> taille de position")
kv_table(pdf, [
    ("Confluence", "Points", ""),
    ("Setup dans le sens de la tendance", "+2", ""),
    ("Englobante ou marteau", "+1", ""),
    ("Divergence RSI", "+1", ""),
    ("Protege par le point pivot", "+1", ""),
], widths=(110, 40, 40))
pdf.ln(1)
bullet(pdf, "Score >= 3 : taille NORMALE (ex. risque 1 %).")
bullet(pdf, "Score = 2 : DEMI-taille (ex. risque 0,5 %).")
bullet(pdf, "Englobante/marteau toujours requis ; en contre-tendance la divergence RSI l'est aussi.")
bullet(pdf, "Ex. vendredi : short contre-tendance sans pivot = englobante + divergence = 2 pts = demi-taille.")

# --- TP -------------------------------------------------------------------
h2(pdf, "5. Take-profit (commun aux deux strategies)")
bullet(pdf, "Cibler le premier niveau institutionnel (pivot ou open daily) donnant un ratio >= 2.")
bullet(pdf, "Si le 1er pivot donne un ratio < 1, viser le pivot suivant.")
bullet(pdf, "Sur les indices, le prix s'arrete souvent au tick pres sur ces niveaux.")

# --- Strategie 3 Elliott --------------------------------------------------
h2(pdf, "6. Strategie 3 - Elliott Level Watcher (Forex CFD)")
para(pdf, "Flux separe des futures : signaux Forex (EUR/USD, GBP/USD, USD/JPY...), sans les regles prop firm.")
bullet(pdf, "TOI tu fais le comptage des vagues (impulsion 1-2-3-4-5, correction ABC/WXY, diagonale, triangle).")
bullet(pdf, "Tu entres 3 niveaux : Confirmation (entree) / Invalidation (SL) / Cible (TP).")
bullet(pdf, "Le bot surveille le prix et alerte : franchissement de la confirmation = ENTREE.")
bullet(pdf, "Puis il gere le trade : passage au breakeven (a 1 R), TP atteint, ou invalidation.")
para(pdf, "Le comptage des vagues reste manuel (non automatisable de facon fiable) ; "
     "le bot automatise seulement le declenchement et la discipline.", bold=False)

# --- Prop firm ------------------------------------------------------------
h2(pdf, "7. Regles prop firm 50k (Risk Manager)")
kv_table(pdf, [
    ("Parametre", "Apex 50k (EOD)", "LucidFlex 50k"),
    ("Profit target", "3 000 $", "3 000 $"),
    ("Drawdown", "EOD trailing ~2 500 $", "EOD trailing 2 000 $"),
    ("Daily loss limit", "1 000 $ (a confirmer)", "aucune"),
    ("Consistance", "aucune", "50 % (jour < 1 500 $)"),
    ("Jours min", "0", "2"),
])
pdf.ln(2)
para(pdf, "Le bot bloque un signal si une perte approcherait le seuil EOD / le daily loss, "
     "ou si le profit du jour (Lucid) approche le plafond de consistance.", bold=False)

out = Path.home() / "Downloads" / "AXONE_Strategies_Signaux.pdf"
pdf.output(str(out))
print("PDF cree :", out)
