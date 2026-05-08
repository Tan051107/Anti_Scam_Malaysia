# -*- coding: utf-8 -*-
"""
Report Router
Generates a styled PDF scam incident report from form data submitted by the frontend.
"""

import io
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, Table, TableStyle, ListFlowable, ListItem,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from models.schemas import ReportExportRequest

router = APIRouter(prefix="/api/report", tags=["report"])

# ─────────────────────────────────────────────
# Colour palette
# ─────────────────────────────────────────────
NAVY   = colors.HexColor("#003893")
YELLOW = colors.HexColor("#FFCC00")
RED    = colors.HexColor("#C0392B")
GREEN  = colors.HexColor("#27AE60")
DARK   = colors.HexColor("#1A1A2E")
GREY   = colors.HexColor("#7F8C8D")
LGREY  = colors.HexColor("#F4F6F8")
WHITE  = colors.white


def _build_pdf(data: ReportExportRequest) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Scam Incident Report — {data.reportId}",
    )

    styles = getSampleStyleSheet()

    s_title = ParagraphStyle("s_title", fontSize=20, textColor=WHITE,
                              fontName="Helvetica-Bold", alignment=TA_LEFT, leading=24)
    s_subtitle = ParagraphStyle("s_subtitle", fontSize=10, textColor=colors.HexColor("#BDD7FF"),
                                 alignment=TA_LEFT)
    s_report_id = ParagraphStyle("s_report_id", fontSize=14, textColor=YELLOW,
                                  fontName="Helvetica-Bold", alignment=TA_RIGHT)
    s_meta = ParagraphStyle("s_meta", fontSize=8, textColor=colors.HexColor("#BDD7FF"),
                             alignment=TA_RIGHT)
    s_section = ParagraphStyle("s_section", fontSize=11, textColor=NAVY,
                                fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=4)
    s_label = ParagraphStyle("s_label", fontSize=8, textColor=GREY, spaceAfter=1)
    s_value = ParagraphStyle("s_value", fontSize=10, textColor=DARK,
                              fontName="Helvetica-Bold", spaceAfter=2)
    s_body = ParagraphStyle("s_body", fontSize=10, textColor=DARK, leading=15, spaceAfter=4)
    s_flag = ParagraphStyle("s_flag", fontSize=10, textColor=DARK, leading=14)
    s_warning_head = ParagraphStyle("s_warning_head", fontSize=11, textColor=RED,
                                     fontName="Helvetica-Bold", spaceAfter=4)
    s_warning_item = ParagraphStyle("s_warning_item", fontSize=9, textColor=RED, leading=14)
    s_footer = ParagraphStyle("s_footer", fontSize=8, textColor=GREY,
                               alignment=TA_CENTER, spaceBefore=6)
    s_status = ParagraphStyle("s_status", fontSize=9, textColor=colors.HexColor("#7D6608"),
                               alignment=TA_CENTER)

    story = []

    # ── Header banner ──────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("SCAM INCIDENT REPORT<br/><font size='10' color='#BDD7FF'>Laporan Insiden Penipuan</font>", s_title),
        [
            Paragraph(data.reportId, s_report_id),
            Paragraph(data.generatedAt, s_meta),
        ],
    ]]
    header_table = Table(header_data, colWidths=["60%", "40%"])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING",   (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [6, 6, 6, 6]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3 * cm))

    # ── Status badge ──────────────────────────────────────────────────────────
    status_table = Table([[Paragraph("⚠️  DRAFT — For Reference Only / Untuk Rujukan Sahaja", s_status)]],
                          colWidths=["100%"])
    status_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#FEF9C3")),
        ("BOX",          (0, 0), (-1, -1), 1, colors.HexColor("#F59E0B")),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [4, 4, 4, 4]),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 0.3 * cm))

    # ── Incident details grid ─────────────────────────────────────────────────
    story.append(Paragraph("Incident Details / Butiran Insiden", s_section))

    amount_str = (
        f"{data.currency} {float(data.amountLost):,.2f}" if data.amountLost else "Not specified"
    )

    def cell(label, value):
        return [Paragraph(label, s_label), Paragraph(value or "Not provided", s_value)]

    grid_data = [
        [cell("Incident Date / Tarikh", data.incidentDate),
         cell("Scam Type / Jenis Penipuan", data.scamType)],
        [cell("Contact Method / Kaedah Hubungan", data.contactMethod),
         cell("Scammer's Contact / Hubungan Penipu", data.scammerContact or "Not provided")],
        [cell("Amount Lost / Kerugian", amount_str),
         cell("Scammer's Bank / Bank Penipu", data.bankAccount or "Not provided")],
    ]

    col_w = (doc.width - 0.4 * cm) / 2
    for row in grid_data:
        t = Table([row], colWidths=[col_w, col_w], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), LGREY),
            ("TOPPADDING",   (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
            ("LEFTPADDING",  (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("ROUNDEDCORNERS", (0, 0), (-1, -1), [4, 4, 4, 4]),
            ("LINEBELOW",    (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.15 * cm))

    # ── Description ───────────────────────────────────────────────────────────
    story.append(Paragraph("Description of Incident / Penerangan Insiden", s_section))
    desc_table = Table([[Paragraph(data.description, s_body)]], colWidths=[doc.width])
    desc_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LGREY),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [4, 4, 4, 4]),
    ]))
    story.append(desc_table)

    # ── Victim info ───────────────────────────────────────────────────────────
    if any([data.victimName, data.victimIC, data.victimPhone]):
        story.append(Paragraph("Victim Information / Maklumat Mangsa", s_section))
        victim_row = []
        if data.victimName:
            victim_row.append(cell("Name / Nama", data.victimName))
        if data.victimIC:
            victim_row.append(cell("IC Number / Nombor IC", data.victimIC))
        if data.victimPhone:
            victim_row.append(cell("Phone / Telefon", data.victimPhone))

        col_w_v = doc.width / len(victim_row)
        vt = Table([victim_row], colWidths=[col_w_v] * len(victim_row))
        vt.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
            ("BOX",          (0, 0), (-1, -1), 1, colors.HexColor("#BFDBFE")),
            ("TOPPADDING",   (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
            ("LEFTPADDING",  (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(vt)

    # ── Reported status ───────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * cm))
    polis_color = GREEN if data.reportedToPolis else GREY
    bnm_color   = GREEN if data.reportedToBNM   else GREY
    polis_text  = "✔ Reported to PDRM" if data.reportedToPolis else "✘ Not yet reported to PDRM"
    bnm_text    = "✔ Reported to BNM"  if data.reportedToBNM   else "✘ Not yet reported to BNM"

    status_row = [[
        Paragraph(polis_text, ParagraphStyle("ps", fontSize=9, textColor=polis_color,
                                              fontName="Helvetica-Bold", alignment=TA_CENTER)),
        Paragraph(bnm_text,   ParagraphStyle("bs", fontSize=9, textColor=bnm_color,
                                              fontName="Helvetica-Bold", alignment=TA_CENTER)),
    ]]
    st = Table(status_row, colWidths=[doc.width / 2, doc.width / 2])
    st.setStyle(TableStyle([
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("BACKGROUND",   (0, 0), (0, 0), colors.HexColor("#F0FDF4") if data.reportedToPolis else LGREY),
        ("BACKGROUND",   (1, 0), (1, 0), colors.HexColor("#F0FDF4") if data.reportedToBNM   else LGREY),
        ("LINEAFTER",    (0, 0), (0, 0), 1, colors.HexColor("#E2E8F0")),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [4, 4, 4, 4]),
    ]))
    story.append(st)

    # ── Next steps ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=RED))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("🚨 Next Steps / Langkah Seterusnya", s_warning_head))

    steps = [
        "File a police report at your nearest police station / Buat laporan polis di balai polis berhampiran",
        "Contact your bank immediately if money was transferred / Hubungi bank anda segera jika wang telah dipindahkan",
        "Report to CCID: 03-2610 5000",
        "Report to BNM TELELINK: 1-300-88-5465",
        "Check mule accounts at: www.semakmule.rmp.gov.my",
        "Report to MCMC: aduan.mcmc.gov.my",
    ]
    items = [ListItem(Paragraph(s, s_warning_item), leftIndent=12) for s in steps]
    story.append(ListFlowable(items, bulletType="bullet", leftIndent=16,
                               bulletColor=RED, bulletFontSize=8))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.6 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=GREY))
    story.append(Paragraph(
        "This report is generated for reference purposes only and does not constitute an official police report. "
        "Anti-Scam Malaysia — Protecting Malaysians from fraud.",
        s_footer,
    ))

    doc.build(story)
    return buffer.getvalue()


# ─────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────

@router.post("/export-pdf")
async def export_report_pdf(data: ReportExportRequest):
    """
    Accept report form data from the frontend and return a styled PDF file.
    """
    pdf_bytes = _build_pdf(data)
    filename = f"scam-report-{data.reportId}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
