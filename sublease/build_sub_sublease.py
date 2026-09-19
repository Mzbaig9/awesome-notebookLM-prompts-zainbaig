#!/usr/bin/env python3
"""Build the bilingual Residential Sub-Sublease Agreement for 2775 Bd Toupin.

Usage: python3 build_sub_sublease.py <original_sublease.pdf> <output.pdf>

Produces: notice + acknowledgement page, French contract, English contract,
then appends the original signed Residential Sublease Agreement as Schedule A.
"""
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, PageBreak, Table, TableStyle, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter

FONT_DIR = "/usr/share/fonts/truetype/liberation/"
pdfmetrics.registerFont(TTFont("Serif", FONT_DIR + "LiberationSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Bold", FONT_DIR + "LiberationSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Italic", FONT_DIR + "LiberationSerif-Italic.ttf"))
pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif-Bold", italic="Serif-Italic")

TITLE = "Residential Sub-Sublease Agreement"

body = ParagraphStyle("body", fontName="Serif", fontSize=11, leading=15, alignment=TA_JUSTIFY, spaceAfter=8)
num = ParagraphStyle("num", parent=body, leftIndent=24, firstLineIndent=-24)
sub = ParagraphStyle("sub", parent=body, leftIndent=48, firstLineIndent=-20)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=48, firstLineIndent=0, spaceAfter=4)
center = ParagraphStyle("center", parent=body, alignment=TA_CENTER)
centerb = ParagraphStyle("centerb", parent=center, fontName="Serif-Bold")
right = ParagraphStyle("right", parent=body, alignment=TA_RIGHT, fontName="Serif-Bold")
h = ParagraphStyle("h", parent=body, fontName="Serif-Bold", spaceBefore=6, spaceAfter=4, keepWithNext=1)
title = ParagraphStyle("title", parent=center, fontName="Serif-Bold", fontSize=12, spaceAfter=12)
small = ParagraphStyle("small", parent=body, fontSize=9.5, leading=12)


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self.setFont("Serif-Italic", 10)
            self.drawString(0.9 * inch, 10.35 * inch, TITLE)
            self.setFont("Serif", 10)
            self.drawRightString(7.6 * inch, 10.35 * inch, f"Page {self._pageNumber} of {total}")
            self.setLineWidth(0.5)
            self.line(0.9 * inch, 10.28 * inch, 7.6 * inch, 10.28 * inch)
            super().showPage()
        super().save()


def P(t, s=body):
    return Paragraph(t, s)


def sig_block(entries, witness_label):
    """entries: list of names. Renders witness / signatory pairs."""
    rows = []
    for name in entries:
        rows.append([P("_____________________________<br/>" + witness_label, small),
                     P("_____________________________<br/>" + name, small)])
    t = Table(rows, colWidths=[3.1 * inch, 3.3 * inch], rowHeights=None)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                           ("TOPPADDING", (0, 0), (-1, -1), 18),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


SIGNATORIES = ["Mirza-Zain Baig", "Nithin Goud Maragoni", "Kulwinder Singh", "Parveen Sharma", "Mohit Panchal"]

# --------------------------------------------------------------------------------------
# Page 1-2 : Notice + Acknowledgement
# --------------------------------------------------------------------------------------
def notice_pages():
    s = []
    s.append(P("<u>Notice of French Translation / Avis de traduction française</u>", centerb))
    s.append(Spacer(1, 8))
    s.append(P("Under the Charter of the French language (Quebec Bill 96), every party to this contract must have been "
               "given a French version and must expressly wish to be bound by the English version before signing it. "
               "The French version of this Sub-Sublease Agreement appears first, followed by the English version. "
               "Schedule A (the Residential Sublease Agreement dated July 19, 2026) is attached in the bilingual form in which it was signed."))
    s.append(P("En vertu de la Charte de la langue française (projet de loi 96), chaque partie doit avoir reçu une version "
               "française du contrat et avoir exprimé la volonté expresse d'être liée par la version anglaise avant de la signer. "
               "La version française du présent Contrat de sous-sous-location figure en premier, suivie de la version anglaise. "
               "L'Annexe A (le Contrat de sous-location résidentielle du 19 juillet 2026) est jointe dans la forme bilingue dans laquelle il a été signé."))
    s.append(PageBreak())
    s.append(P("<u>Acknowledgement of English Language Contract</u><br/><u>Reconnaissance du choix de la langue anglaise</u>", centerb))
    s.append(Spacer(1, 8))
    s.append(P("I have seen a French and an English version of the Residential Sub-Sublease Agreement dated "
               "________________ ____, 2026 concerning 2775 Bd Toupin, Montréal, QC H4R 1G7, and I am choosing to enter "
               "into this contract exclusively in English."))
    s.append(P("J'ai pris connaissance d'une version française et d'une version anglaise du Contrat de sous-sous-location "
               "résidentielle daté du ____ ________________ 2026 concernant le 2775, boul. Toupin, Montréal (Québec) H4R 1G7, "
               "et je choisis de conclure ce contrat exclusivement en anglais."))
    s.append(sig_block(SIGNATORIES, "Witness / Témoin"))
    s.append(PageBreak())
    return s


# --------------------------------------------------------------------------------------
# French contract
# --------------------------------------------------------------------------------------
def french():
    s = []
    s.append(P("CONTRAT DE SOUS-SOUS-LOCATION RÉSIDENTIELLE", title))
    s.append(P("<b>CONTRAT DE SOUS-SOUS-LOCATION RÉSIDENTIELLE</b> en date du ____ ________________ 2026"))
    s.append(P("<b>ENTRE :</b>"))
    s.append(P("Nithin Goud Maragoni", center))
    s.append(P("(le « Sous-sous-locateur »)", center))
    s.append(P("D'UNE PART", right))
    s.append(P("- ET -", center))
    s.append(P("Kulwinder Singh, domicilié au 61 Loftsmoor Dr, Brampton (Ontario) L6R 3R3<br/>"
               "Parveen Sharma, domicilié au 12 Marchbank Cres, Brampton (Ontario) L6S 3B1<br/>"
               "Mohit Panchal, domicilié au 309-595, boul. Marcel-Laurin, Saint-Laurent (Québec) H4M 2M1", center))
    s.append(P("(collectivement et individuellement le « Sous-sous-locataire »)", center))
    s.append(P("D'AUTRE PART", right))
    s.append(P("- ET -", center))
    s.append(P("Mirza-Zain Baig, domicilié au 39, rue de Dinan, Laval (Québec) H7N 2X8", center))
    s.append(P("(le « Sous-locateur », intervenant aux présentes pour donner son consentement)", center))
    s.append(P("DE TROISIÈME PART", right))

    s.append(P("<u>Le contexte</u>", h))
    s.append(P("A. Aux termes d'un bail initial en date du 1<sup>er</sup> avril 2021 (le « Bail initial »), Johnny Moncada (le « Locateur ») "
               "a loué au Sous-locateur la maison et toutes les améliorations situées au 2775, boul. Toupin, Montréal (Québec) "
               "H4R 1G7, Canada (les « Locaux »).", num))
    s.append(P("B. Aux termes d'un Contrat de sous-location résidentielle en date du 19 juillet 2026 (le « Contrat de sous-location »), "
               "dont une copie est jointe à l'Annexe A et fait partie intégrante des présentes, le Sous-locateur a sous-loué la "
               "totalité des Locaux à Nithin Goud Maragoni et Abineshwaran Selvaraj (collectivement le « Sous-locataire ») pour "
               "une durée du 1<sup>er</sup> août 2026 au 30 juin 2027, moyennant un loyer de 2 450,00 $ par mois payable au plus tard "
               "le 30 de chaque mois.", num))
    s.append(P("C. L'article 24 du Contrat de sous-location interdit au Sous-locataire de sous-louer les Locaux sans le consentement "
               "écrit préalable du Sous-locateur et du Locateur. Le Sous-sous-locateur souhaite sous-louer la totalité des Locaux "
               "au Sous-sous-locataire et le Sous-locateur y consent aux conditions ci-dessous.", num))
    s.append(P("D. Le présent contrat (le « Contrat de sous-sous-location ») a pour objet la sous-location de second rang des Locaux "
               "selon les modalités ci-dessous. Toutes les dispositions du Contrat de sous-location reproduites à l'Annexe A "
               "s'appliquent au présent Contrat de sous-sous-location, tel que prévu à l'article 13.", num))
    s.append(P("<b>COMPTE TENU DE</b> la sous-location par le Sous-sous-locateur et de la location par le Sous-sous-locataire des "
               "Locaux, et du consentement du Sous-locateur, les parties s'engagent à tenir, à exécuter et à respecter les "
               "promesses, conditions et accords ci-dessous :"))

    s.append(P("<u>Locaux sous-sous-loués</u>", h))
    s.append(P("1. Le Sous-sous-locateur sous-loue au Sous-sous-locataire la totalité des Locaux (les « Locaux sous-sous-loués »), "
               "pour usage exclusif de résidence privée d'au plus 5 personnes. Les Locaux ne seront utilisés à aucun moment pour "
               "l'exercice d'une profession, d'un métier ou d'une activité commerciale de quelque nature que ce soit.", num))
    s.append(P("2. Aucun animal ne peut être gardé dans les Locaux sans l'autorisation écrite préalable du Sous-locateur et du "
               "Sous-sous-locateur. Moyennant un préavis de trente (30) jours, cette autorisation peut être révoquée.", num))
    s.append(P("3. Le Sous-sous-locataire et les membres de son ménage ne fumeront ni ne vapoteront nulle part dans les Locaux et "
               "n'autoriseront aucun invité ou visiteur à y fumer ou à y vapoter.", num))

    s.append(P("<u>Durée</u>", h))
    s.append(P("4. La durée (la « Durée ») du présent Contrat de sous-sous-location débute à midi le 1<sup>er</sup> octobre 2026 et prend fin "
               "à midi le 30 juin 2027.", num))
    s.append(P("5. La Durée ne peut en aucun cas excéder la durée du Contrat de sous-location ni celle du Bail initial. Le présent "
               "Contrat de sous-sous-location prend fin de plein droit à l'expiration, à la résiliation ou à l'annulation "
               "anticipée du Contrat de sous-location ou du Bail initial.", num))

    s.append(P("<u>Loyer</u>", h))
    s.append(P("6. Sous réserve des dispositions du présent contrat, le loyer des Locaux est de 2 450,00 $ (le « Loyer ») par mois.", num))
    s.append(P("7. <b>Le Sous-sous-locataire paiera le Loyer à Nithin Goud Maragoni au plus tard le 30 de chaque mois de la Durée</b> "
               "(et, pour le mois de février, au plus tard le dernier jour du mois), par virement Interac ou selon tout autre mode "
               "ou à toute autre adresse que Nithin Goud Maragoni indiquera par écrit.", num))
    s.append(P("8. Les personnes formant le Sous-sous-locataire sont tenues <b>solidairement</b> (art. 1523 C.c.Q.) envers le "
               "Sous-sous-locateur et le Sous-locateur au paiement du Loyer et à l'exécution de toutes les obligations du présent contrat.", num))
    s.append(P("9. Conformément à l'article 1904 du Code civil du Québec, aucun dépôt de garantie ni aucun versement anticipé "
               "excédant un mois de loyer n'est exigé.", num))

    s.append(P("<u>Obligations continues du Sous-sous-locateur envers le Sous-locateur</u>", h))
    s.append(P("10. Le Sous-sous-locateur demeure pleinement lié envers le Sous-locateur par le Contrat de sous-location, y compris "
               "l'obligation de payer le loyer de 2 450,00 $ à Mirza-Zain Baig au plus tard le 30 de chaque mois, <b>que le "
               "Sous-sous-locataire ait ou non payé le Loyer</b>. Le présent contrat ne constitue pas une cession du Contrat de "
               "sous-location et ne libère ni Nithin Goud Maragoni ni Abineshwaran Selvaraj de leurs obligations envers le Sous-locateur.", num))
    s.append(P("11. <b>Le Sous-sous-locateur est responsable envers le Sous-locateur de veiller à ce que le Sous-sous-locataire</b> : "
               "a) paie le Loyer à échéance; b) prenne soin des Locaux, de leur contenu et de l'immeuble et les maintienne en bon "
               "état; et c) respecte chacune des conditions du présent contrat, du Contrat de sous-location et du Bail initial. "
               "Tout acte, omission ou défaut du Sous-sous-locataire est réputé être un acte, une omission ou un défaut du "
               "Sous-sous-locateur aux termes du Contrat de sous-location, et le Sous-sous-locateur indemnisera le Sous-locateur "
               "de toute perte, dommage, frais ou loyer impayé en résultant.", num))
    s.append(P("12. Si le Sous-sous-locateur fait défaut de payer le loyer dû au Sous-locateur, ce dernier peut, sur avis écrit au "
               "Sous-sous-locataire, exiger que le Loyer lui soit payé directement; tout paiement ainsi fait libère le "
               "Sous-sous-locataire envers le Sous-sous-locateur jusqu'à concurrence du montant payé. Le Sous-locateur conserve "
               "en outre tous ses recours prévus au Contrat de sous-location et au Code civil du Québec, notamment le droit de "
               "demander la résiliation de la sous-location de second rang lorsque l'inexécution du Sous-sous-locataire lui cause "
               "un préjudice sérieux (art. 1875 C.c.Q.).", num))

    s.append(P("<u>Application du Contrat de sous-location (Annexe A)</u>", h))
    s.append(P("13. Le Sous-sous-locataire reconnaît avoir reçu et lu le Contrat de sous-location joint à l'Annexe A, dans ses "
               "versions française et anglaise. <b>Toutes les conditions, clauses, restrictions et obligations du Contrat de "
               "sous-location</b> (articles 1 à 34 de la version française, articles 1 à 36 de la version anglaise), ainsi que "
               "celles du Bail initial qui y sont incorporées, <b>s'appliquent au présent Contrat de sous-sous-location et lient "
               "le Sous-sous-locataire</b>, avec les adaptations nécessaires, comme si le Sous-sous-locataire était le "
               "« Sous-locataire » et le Sous-sous-locateur le « Sous-locateur » qui y sont désignés, sauf modification expresse "
               "aux présentes. Sont visées notamment les dispositions relatives aux charges, à l'entretien et aux dommages, aux "
               "travaux, aux taxes, aux cas de défaillance et aux recours, à la loi applicable, à la divisibilité, à la "
               "sous-location, aux avis, au droit d'accès et aux dispositions générales.", num))
    s.append(P("14. Le présent contrat ne peut conférer au Sous-sous-locataire plus de droits que ceux dont le Sous-sous-locateur "
               "dispose aux termes du Contrat de sous-location. En cas de conflit, le Bail initial prévaut sur le Contrat de "
               "sous-location, et le Contrat de sous-location prévaut sur le présent contrat, sauf en ce qui concerne le Loyer, "
               "le bénéficiaire du Loyer et la Durée prévus aux articles 4, 6 et 7, qui régissent les rapports entre le "
               "Sous-sous-locateur et le Sous-sous-locataire.", num))
    s.append(P("15. Le Sous-sous-locataire paiera, pendant la Durée, toutes les charges (électricité, chauffage, eau chaude, "
               "internet et autres) et dépenses liées aux Locaux que le Sous-locataire est tenu de payer aux termes de l'article 8 "
               "du Contrat de sous-location.", num))
    s.append(P("16. Le Sous-sous-locataire remettra les Locaux, les meubles et les décorations qui s'y trouvent en aussi bon état "
               "qu'au début de la Durée, sauf usure normale, et sera responsable envers le Sous-sous-locateur, le Sous-locateur et "
               "le Locateur de tout dommage causé aux Locaux, à leur contenu ou à l'immeuble par lui-même ou par ses invités.", num))
    s.append(P("17. Le Sous-sous-locataire ne cédera pas, ne transférera pas et ne sous-louera pas les Locaux, en tout ou en partie, "
               "sans le consentement écrit préalable du Sous-sous-locateur, du Sous-locateur et du Locateur.", num))

    s.append(P("<u>Consentement du Sous-locateur</u>", h))
    s.append(P("18. Par sa signature, le Sous-locateur consent à la présente sous-location de second rang conformément à l'article 24 "
               "du Contrat de sous-location. Ce consentement est limité aux personnes nommément désignées comme Sous-sous-locataire, "
               "ne libère pas le Sous-locataire de ses obligations, ne crée aucun lien contractuel direct entre le Sous-locateur et "
               "le Sous-sous-locataire autre que les droits réservés à l'article 12, et ne peut être invoqué pour toute autre "
               "sous-location ou cession.", num))

    s.append(P("<u>Cas de défaillance et recours</u>", h))
    s.append(P("19. Le Sous-sous-locataire est en défaut s'il ne paie pas le Loyer à échéance, manque à l'une de ses obligations "
               "aux termes du présent contrat, du Contrat de sous-location ou du Bail initial, abandonne les Locaux, les utilise "
               "à des fins non autorisées ou illégales, ou si les Locaux sont endommagés par sa négligence ou celle de ses invités. "
               "Le Sous-sous-locateur dispose alors des recours prévus à l'article 14 du Contrat de sous-location et au Code civil "
               "du Québec, sans préjudice des recours du Sous-locateur.", num))

    s.append(P("<u>Loi applicable et langue</u>", h))
    s.append(P("20. Le présent contrat est régi par les lois de la province de Québec, notamment le Code civil du Québec "
               "(art. 1851 et suivants, 1870 à 1876 et 1892 et suivants). Tout litige relève de la compétence du Tribunal "
               "administratif du logement ou, selon le cas, des tribunaux de droit commun du district de Montréal. En cas de "
               "conflit entre le présent contrat et une disposition d'ordre public, cette dernière prévaut et le contrat est "
               "réputé modifié en conséquence.", num))
    s.append(P("21. Les parties ont reçu une version française du présent contrat et de l'Annexe A et ont expressément demandé, "
               "conformément à l'article 55 de la Charte de la langue française, à être liées par la version anglaise.", num))

    s.append(P("<u>Avis</u>", h))
    s.append(P("22. Tout avis au Sous-locateur sera signifié ou envoyé à : Mirza-Zain Baig, 39, rue de Dinan, Laval (Québec) H7N 2X8, "
               "ou mzbaig9@gmail.com.", num))
    s.append(P("23. Tout avis au Sous-sous-locateur sera signifié ou envoyé à : Nithin Goud Maragoni, "
               "adresse : ______________________________________________, courriel : ______________________________.", num))
    s.append(P("24. Tout avis au Sous-sous-locataire sera signifié ou envoyé à Kulwinder Singh, Parveen Sharma et Mohit Panchal au "
               "2775, boul. Toupin, Montréal (Québec) H4R 1G7. Les avis seront faits par écrit et signifiés en personne, par "
               "courrier recommandé (Postes Canada) ou par courriel avec confirmation de réception.", num))

    s.append(P("<u>Dispositions générales</u>", h))
    s.append(P("25. Le Sous-sous-locateur ou le Sous-locateur peut pénétrer dans les Locaux moyennant un préavis de 24 heures pour "
               "les inspecter, les entretenir ou y effectuer des réparations.", num))
    s.append(P("26. Au moment de la prise de possession ou dans les 7 jours qui suivent, le Sous-sous-locateur remettra au "
               "Sous-sous-locataire un formulaire d'inspection décrivant l'état des Locaux et de leur contenu.", num))
    s.append(P("27. Le présent contrat, avec l'Annexe A, constitue l'entente complète entre les parties; toute modification doit "
               "être faite par écrit et signée par le Sous-sous-locateur, le Sous-sous-locataire et le Sous-locateur.", num))
    s.append(P("28. Le présent contrat peut être signé en plusieurs exemplaires et par signature électronique, chacun valant original. "
               "Chaque signataire reconnaît avoir reçu un exemplaire signé.", num))

    s.append(P("<b>EN FOI DE QUOI</b> les parties ont signé le ____ ________________ 2026."))
    s.append(P("<b>Consentement du Sous-locateur (art. 24 du Contrat de sous-location) :</b>", h))
    s.append(sig_block(["Mirza-Zain Baig, Sous-locateur"], "Témoin"))
    s.append(P("<b>Sous-sous-locateur :</b>", h))
    s.append(sig_block(["Nithin Goud Maragoni, Sous-sous-locateur"], "Témoin"))
    s.append(P("<b>Sous-sous-locataire (solidairement) :</b>", h))
    s.append(sig_block(["Kulwinder Singh", "Parveen Sharma", "Mohit Panchal"], "Témoin"))
    s.append(PageBreak())
    return s


# --------------------------------------------------------------------------------------
# English contract
# --------------------------------------------------------------------------------------
def english():
    s = []
    s.append(P("RESIDENTIAL SUB-SUBLEASE AGREEMENT", title))
    s.append(P("<b>THIS SUB-SUBLEASE AGREEMENT</b> dated this ________ day of ________________, 2026"))
    s.append(P("<b>BETWEEN:</b>"))
    s.append(P("Nithin Goud Maragoni", center))
    s.append(P("(the \"Sub-Sublandlord\")", center))
    s.append(P("OF THE FIRST PART", right))
    s.append(P("- AND -", center))
    s.append(P("Kulwinder Singh, of 61 Loftsmoor Dr, Brampton, ON L6R 3R3<br/>"
               "Parveen Sharma, of 12 Marchbank Cres, Brampton, ON L6S 3B1<br/>"
               "Mohit Panchal, of 309-595 Boul. Marcel-Laurin, Saint-Laurent, QC H4M 2M1", center))
    s.append(P("(collectively and individually the \"Sub-Subtenant\")", center))
    s.append(P("OF THE SECOND PART", right))
    s.append(P("- AND -", center))
    s.append(P("Mirza-Zain Baig, of 39 Rue de Dinan, Laval, QC H7N 2X8", center))
    s.append(P("(the \"Sublandlord\", intervening to give consent)", center))
    s.append(P("OF THE THIRD PART", right))

    s.append(P("<u>Background</u>", h))
    s.append(P("A. By a master lease dated April 1, 2021 (the \"Master Lease\"), Johnny Moncada (the \"Landlord\") leased to the "
               "Sublandlord the house and any improvements municipally described as 2775 Bd Toupin, Montréal, QC H4R 1G7, "
               "Canada (the \"Premises\").", num))
    s.append(P("B. By a Residential Sublease Agreement dated July 19, 2026 (the \"Sublease\"), a copy of which is attached as "
               "Schedule A and forms an integral part of this Agreement, the Sublandlord subleased all of the Premises to Nithin "
               "Goud Maragoni and Abineshwaran Selvaraj (collectively the \"Subtenant\") for a term from August 1, 2026 to "
               "June 30, 2027 at a rent of $2,450.00 per month payable on or before the 30th of each month.", num))
    s.append(P("C. Clause 24 of the Sublease prohibits the Subtenant from further subletting the Premises without the prior "
               "written consent of the Sublandlord and the Landlord. The Sub-Sublandlord wishes to sub-sublease all of the "
               "Premises to the Sub-Subtenant, and the Sublandlord consents on the terms set out below.", num))
    s.append(P("D. This is an agreement (the \"Sub-Sublease Agreement\") to sub-sublet the Premises according to the terms below. "
               "All of the terms of the Sublease reproduced in Schedule A apply to this Sub-Sublease Agreement as provided in clause 13.", num))
    s.append(P("<b>IN CONSIDERATION OF</b> the Sub-Sublandlord sub-subletting and the Sub-Subtenant renting the Premises, and of "
               "the Sublandlord's consent, the parties agree to keep, perform and fulfill the promises, conditions and agreements below:"))

    s.append(P("<u>Sub-Subleased Premises</u>", h))
    s.append(P("1. The Sub-Sublandlord sub-subleases to the Sub-Subtenant all of the Premises (the \"Sub-Subleased Premises\"), for "
               "use as a private residence of not more than 5 people only. Neither the Premises nor any part of them will be used "
               "at any time for the purpose of carrying on any business, profession or trade of any kind.", num))
    s.append(P("2. No pets or animals are allowed to be kept in the Premises without the prior written permission of the Sublandlord "
               "and the Sub-Sublandlord. Upon thirty (30) days' notice, any such permission may be revoked.", num))
    s.append(P("3. The Sub-Subtenant and members of the Sub-Subtenant's household will not smoke or vape anywhere in the Premises "
               "nor permit any guests or visitors to smoke or vape in the Premises.", num))

    s.append(P("<u>Term</u>", h))
    s.append(P("4. The term (the \"Term\") of this Sub-Sublease Agreement commences at 12:00 noon on October 1, 2026 and ends at "
               "12:00 noon on June 30, 2027.", num))
    s.append(P("5. In no event will the Term extend beyond the term of the Sublease or of the Master Lease. This Sub-Sublease "
               "Agreement ends automatically upon the earlier expiration, termination, resiliation or cancellation of the "
               "Sublease or the Master Lease.", num))

    s.append(P("<u>Rent</u>", h))
    s.append(P("6. Subject to the provisions of this Agreement, the rent for the Premises is $2,450.00 (the \"Rent\") per month.", num))
    s.append(P("7. <b>The Sub-Subtenant will pay the Rent to Nithin Goud Maragoni on or before the 30th of each and every month of "
               "the Term</b> (and, for the month of February, on or before the last day of the month), by Interac e-Transfer or "
               "by such other method or at such other place as Nithin Goud Maragoni may designate in writing.", num))
    s.append(P("8. The persons comprising the Sub-Subtenant are <b>jointly and solidarily</b> liable (art. 1523 C.C.Q.) to the "
               "Sub-Sublandlord and the Sublandlord for the Rent and for the performance of every obligation under this Agreement.", num))
    s.append(P("9. In accordance with article 1904 of the Civil Code of Québec, no security deposit and no advance payment "
               "exceeding one month's rent is required.", num))

    s.append(P("<u>Continuing Obligations of the Sub-Sublandlord to the Sublandlord</u>", h))
    s.append(P("10. The Sub-Sublandlord remains fully bound to the Sublandlord under the Sublease, including the obligation to pay "
               "the Sublease rent of $2,450.00 to Mirza-Zain Baig on or before the 30th of each month, <b>whether or not the "
               "Sub-Subtenant has paid the Rent</b>. This Agreement is not an assignment of the Sublease and does not release "
               "Nithin Goud Maragoni or Abineshwaran Selvaraj from any of their obligations to the Sublandlord.", num))
    s.append(P("11. <b>The Sub-Sublandlord is responsible to the Sublandlord for ensuring that the Sub-Subtenant</b> (a) pays the "
               "Rent when due; (b) takes proper care of the Premises, their contents and the building and keeps them in good "
               "condition; and (c) complies with every term of this Agreement, the Sublease and the Master Lease. Any act, "
               "omission or default of the Sub-Subtenant is deemed to be an act, omission or default of the Sub-Sublandlord under "
               "the Sublease, and the Sub-Sublandlord will indemnify the Sublandlord for any loss, damage, cost or unpaid rent "
               "resulting from it.", num))
    s.append(P("12. If the Sub-Sublandlord fails to pay the rent due to the Sublandlord, the Sublandlord may, upon written notice to "
               "the Sub-Subtenant, require that the Rent be paid directly to the Sublandlord; any payment so made discharges the "
               "Sub-Subtenant's obligation to the Sub-Sublandlord to the extent of the amount paid. The Sublandlord also retains "
               "every remedy under the Sublease and the Civil Code of Québec, including the right to apply for resiliation of "
               "this sub-sublease where the Sub-Subtenant's non-performance causes the Sublandlord serious injury (art. 1875 C.C.Q.).", num))

    s.append(P("<u>Application of the Sublease (Schedule A)</u>", h))
    s.append(P("13. The Sub-Subtenant acknowledges having received and read the Sublease attached as Schedule A, in both its French "
               "and English versions. <b>All of the terms, conditions, covenants, restrictions and obligations of the Sublease</b> "
               "(clauses 1 to 36 of the English version and clauses 1 to 34 of the French version), and those of the Master Lease "
               "incorporated in it, <b>apply to this Sub-Sublease Agreement and bind the Sub-Subtenant</b>, with the necessary "
               "changes, as if the Sub-Subtenant were the \"Subtenant\" and the Sub-Sublandlord were the \"Sublandlord\" named in "
               "it, except as expressly modified by this Agreement. Without limitation, this includes the Sublease provisions on "
               "utilities, maintenance and damages, alterations and improvements, taxes, events of default and remedies, "
               "governing law, severability, subletting, notices, right of entry and general provisions.", num))
    s.append(P("14. This Agreement cannot grant the Sub-Subtenant greater rights than the Sub-Sublandlord holds under the Sublease. "
               "In the event of a conflict, the Master Lease prevails over the Sublease, and the Sublease prevails over this "
               "Agreement, except that the Rent, the payee of the Rent and the Term set out in clauses 4, 6 and 7 govern as "
               "between the Sub-Sublandlord and the Sub-Subtenant.", num))
    s.append(P("15. During the Term, the Sub-Subtenant will pay all utilities (electricity, heating, hot water, internet and the like) "
               "and other charges connected with the Premises which the Subtenant is required to pay under clause 8 of the Sublease.", num))
    s.append(P("16. The Sub-Subtenant will surrender the Premises and all furniture and decorations within them in as good a "
               "condition as at the beginning of the Term, reasonable wear and tear excepted, and will be liable to the "
               "Sub-Sublandlord, the Sublandlord and the Landlord for any damage to the Premises, their contents or the building "
               "caused by the Sub-Subtenant or the Sub-Subtenant's guests.", num))
    s.append(P("17. The Sub-Subtenant will not assign, transfer or further sublet the Premises or any part of them without the "
               "prior written consent of the Sub-Sublandlord, the Sublandlord and the Landlord.", num))

    s.append(P("<u>Consent of the Sublandlord</u>", h))
    s.append(P("18. By signing this Agreement the Sublandlord consents to this sub-sublease pursuant to clause 24 of the Sublease. "
               "This consent is limited to the persons named as Sub-Subtenant, does not release the Subtenant from any "
               "obligation, creates no direct contractual relationship between the Sublandlord and the Sub-Subtenant other than "
               "the rights reserved in clause 12, and may not be relied upon for any other sublease or assignment.", num))

    s.append(P("<u>Event of Default and Remedies</u>", h))
    s.append(P("19. The Sub-Subtenant is in default if it fails to pay the Rent when due, fails to perform any obligation under this "
               "Agreement, the Sublease or the Master Lease, abandons the Premises, uses them for any unpermitted or illegal "
               "purpose, or if the Premises are damaged through the negligence or wilful act of the Sub-Subtenant or its guests. "
               "The Sub-Sublandlord then has the remedies set out in clause 14 of the Sublease and in the Civil Code of Québec, "
               "without prejudice to the remedies of the Sublandlord.", num))

    s.append(P("<u>Governing Law and Language</u>", h))
    s.append(P("20. This Agreement is governed by the laws of the Province of Quebec, including the Civil Code of Québec "
               "(arts. 1851 et seq., 1870 to 1876 and 1892 et seq.). Any dispute falls within the jurisdiction of the Tribunal "
               "administratif du logement or, as the case may be, the courts of the district of Montréal. If any provision of "
               "this Agreement conflicts with a provision of public order, the latter prevails and this Agreement is deemed "
               "amended accordingly.", num))
    s.append(P("21. The parties have received a French version of this Agreement and of Schedule A and have expressly requested, "
               "in accordance with section 55 of the Charter of the French language, to be bound by the English version.", num))

    s.append(P("<u>Notices</u>", h))
    s.append(P("22. All notices to the Sublandlord will be served or sent to: Mirza-Zain Baig, 39 Rue de Dinan, Laval, QC H7N 2X8, "
               "or mzbaig9@gmail.com.", num))
    s.append(P("23. All notices to the Sub-Sublandlord will be served or sent to: Nithin Goud Maragoni, "
               "Address: ______________________________________________, Email: ______________________________.", num))
    s.append(P("24. All notices to the Sub-Subtenant will be served or sent to Kulwinder Singh, Parveen Sharma and Mohit Panchal at "
               "2775 Bd Toupin, Montréal, QC H4R 1G7. All notices will be in writing and served personally, sent by registered "
               "mail (Canada Post), or sent by email with confirmation of receipt.", num))

    s.append(P("<u>General Provisions</u>", h))
    s.append(P("25. The Sub-Sublandlord or the Sublandlord may enter the Premises upon 24 hours' notice to inspect them, to "
               "maintain them, or to make repairs.", num))
    s.append(P("26. At the time the Sub-Subtenant takes possession, or within 7 days of possession, the Sub-Sublandlord will "
               "provide the Sub-Subtenant with an inspection form recording the condition of the Premises and their contents.", num))
    s.append(P("27. This Agreement, together with Schedule A, constitutes the entire agreement between the parties; no amendment "
               "is effective unless in writing and signed by the Sub-Sublandlord, the Sub-Subtenant and the Sublandlord.", num))
    s.append(P("28. This Agreement may be signed in counterparts and by electronic signature, each of which is an original. "
               "Each signatory acknowledges receipt of an executed copy.", num))

    s.append(P("<b>IN WITNESS WHEREOF</b> the parties have signed this Agreement on this ________ day of ________________, 2026."))
    s.append(P("<b>Consented to by the Sublandlord (clause 24 of the Sublease):</b>", h))
    s.append(sig_block(["Mirza-Zain Baig, Sublandlord"], "Witness"))
    s.append(P("<b>Sub-Sublandlord:</b>", h))
    s.append(sig_block(["Nithin Goud Maragoni, Sub-Sublandlord"], "Witness"))
    s.append(P("<b>Sub-Subtenant (jointly and solidarily):</b>", h))
    s.append(sig_block(["Kulwinder Singh", "Parveen Sharma", "Mohit Panchal"], "Witness"))
    s.append(PageBreak())
    return s


def schedule_cover():
    s = []
    s.append(Spacer(1, 2.5 * inch))
    s.append(P("SCHEDULE A / ANNEXE A", title))
    s.append(P("Residential Sublease Agreement dated July 19, 2026<br/>"
               "Contrat de sous-location résidentielle en date du 19 juillet 2026", centerb))
    s.append(Spacer(1, 12))
    s.append(P("Mirza-Zain Baig (Sublandlord / Sous-locateur)<br/>"
               "Nithin Goud Maragoni and Abineshwaran Selvaraj (Subtenant / Sous-locataire)<br/>"
               "2775 Bd Toupin, Montréal, QC H4R 1G7", center))
    s.append(Spacer(1, 12))
    s.append(P("The following 17 pages are the executed Sublease. Under clause 13 of the Sub-Sublease Agreement, "
               "every term of the Sublease applies to and binds the Sub-Subtenant.<br/>"
               "Les 17 pages suivantes constituent le Contrat de sous-location signé. En vertu de l'article 13 du "
               "Contrat de sous-sous-location, toutes ses dispositions s'appliquent au Sous-sous-locataire et le lient.", center))
    return s


def build(original_pdf, out_pdf):
    tmp = out_pdf + ".body.pdf"
    doc = BaseDocTemplate(tmp, pagesize=letter, leftMargin=0.9 * inch, rightMargin=0.9 * inch,
                          topMargin=1.0 * inch, bottomMargin=0.9 * inch,
                          title=TITLE, author="Mirza-Zain Baig")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame])])
    story = notice_pages() + french() + english() + schedule_cover()
    doc.build(story, canvasmaker=NumberedCanvas)

    w = PdfWriter()
    for p in PdfReader(tmp).pages:
        w.add_page(p)
    for p in PdfReader(original_pdf).pages:
        w.add_page(p)
    w.add_metadata({"/Title": TITLE + " - 2775 Bd Toupin", "/Author": "Mirza-Zain Baig"})
    with open(out_pdf, "wb") as f:
        w.write(f)
    import os
    os.remove(tmp)
    print("wrote", out_pdf, "pages:", len(PdfReader(out_pdf).pages))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
