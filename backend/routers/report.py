# -*- coding: utf-8 -*-
"""
Report Router
Generates a styled PDF scam incident report from form data submitted by the frontend.

This file contains:
  - The ORIGINAL _build_pdf (commented out, kept for reference / rollback)
  - Layout 1: Modern Card        -> _build_pdf_layout1(data)
  - Layout 2: Official Document  -> _build_pdf_layout2(data)
  - Layout 3: Sidebar Dashboard  -> _build_pdf_layout3(data)
  - Layout 4: Infographic Alert  -> _build_pdf_layout4(data)

Switch the active layout by changing the ACTIVE_LAYOUT constant below.
"""

import io
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfgen import canvas

router = APIRouter()

# ---------------------------------------------------------------------------
# Choose which layout to use: "original", "layout1", "layout2", "layout3", "layout4"
# ---------------------------------------------------------------------------
ACTIVE_LAYOUT = "layout2"


# ===========================================================================
# ORIGINAL LAYOUT (kept for reference — uncomment to use)
# ===========================================================================
# def _build_pdf(data) -> bytes:
#     """
#     ORIGINAL implementation. Preserved here so you can roll back at any time.
#     Paste your original _build_pdf body here exactly as it was.
#     """
#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=A4)
#     styles = getSampleStyleSheet()
#     story = []
#     story.append(Paragraph("Scam Incident Report", styles["Title"]))
#     story.append(Spacer(1, 12))
#     story.append(Paragraph(f"Report ID: {data.reportId}", styles["Normal"]))
#     # ... rest of original code ...
#     doc.build(story)
#     pdf = buffer.getvalue()
#     buffer.close()
#     return pdf


# ===========================================================================
# Shared helpers
# ===========================================================================
def _fmt(value, fallback="—"):
    if value is None or value == "":
        return fallback
    return str(value)


def _money(value, currency="MYR"):
    try:
        return f"{currency} {float(value):,.2f}"
    except Exception:
        return _fmt(value)


# ===========================================================================
# LAYOUT 1 — Modern Card
# Clean, friendly, lots of whitespace. Big "Amount Lost" hero card.
# ===========================================================================
def _build_pdf_layout1(data) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontSize=22,
                        textColor=colors.HexColor("#0F172A"), alignment=TA_LEFT, spaceAfter=4)
    sub = ParagraphStyle("sub", parent=styles["Normal"], fontSize=10,
                         textColor=colors.HexColor("#64748B"), spaceAfter=14)
    section = ParagraphStyle("section", parent=styles["Heading2"], fontSize=13,
                             textColor=colors.HexColor("#0F172A"), spaceBefore=10, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10,
                          textColor=colors.HexColor("#0F172A"), leading=14)
    hero_label = ParagraphStyle("heroLabel", parent=styles["Normal"], fontSize=9,
                                textColor=colors.HexColor("#FECACA"), alignment=TA_LEFT)
    hero_value = ParagraphStyle("heroValue", parent=styles["Normal"], fontSize=24,
                                textColor=colors.white, alignment=TA_LEFT, leading=28)

    story = []
    story.append(Paragraph("Scam Incident Report", h1))
    story.append(Paragraph(
        f"Report ID {_fmt(getattr(data, 'reportId', None))} · "
        f"Generated {datetime.now().strftime('%d %b %Y, %H:%M')}", sub))

    # Hero "amount lost" card
    hero = Table(
        [[Paragraph("AMOUNT LOST", hero_label)],
         [Paragraph(_money(getattr(data, "amountLost", 0)), hero_value)]],
        colWidths=[doc.width]
    )
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#DC2626")),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (0, 0), 14),
        ("BOTTOMPADDING", (0, 1), (0, 1), 16),
        ("ROUNDEDCORNERS", [10, 10, 10, 10]),
    ]))
    story.append(hero)
    story.append(Spacer(1, 14))

    # Key details rows
    story.append(Paragraph("Incident Details", section))
    rows = [
        ["Date of incident", _fmt(getattr(data, "incidentDate", None))],
        ["Scam type", _fmt(getattr(data, "scamType", None))],
        ["Method", _fmt(getattr(data, "method", None))],
        ["Bank involved", _fmt(getattr(data, "bank", None))],
        ["Contact channel", _fmt(getattr(data, "channel", None))],
    ]
    t = Table(rows, colWidths=[55 * mm, doc.width - 55 * mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#0F172A")),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)

    # Description
    story.append(Paragraph("Description", section))
    story.append(Paragraph(_fmt(getattr(data, "description", None), "No description provided."), body))

    # Next steps card
    story.append(Spacer(1, 14))
    story.append(Paragraph("Recommended Next Steps", section))
    steps = [
        "Contact your bank immediately to freeze affected accounts.",
        "Lodge a police report at the nearest station.",
        "Report to the National Scam Response Centre (997).",
        "Preserve all evidence: screenshots, messages, transaction receipts.",
    ]
    step_rows = [[Paragraph(f"• {s}", body)] for s in steps]
    st = Table(step_rows, colWidths=[doc.width])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(st)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# ===========================================================================
# LAYOUT 2 — Official Document (matches Anti-Scam Malaysia official report)
# Navy header bar, gold accent line, bilingual section titles, no signature.
# ===========================================================================
def _build_pdf_layout2(data) -> bytes:
    buffer = io.BytesIO()
    NAVY  = colors.HexColor("#0B2447")
    GOLD  = colors.HexColor("#B68D40")
    GREY  = colors.HexColor("#475569")
    DARK  = colors.HexColor("#0F172A")
    LIGHT = colors.HexColor("#F8FAFC")
    RED   = colors.HexColor("#C0392B")

    W, H = A4
    generated = datetime.now().strftime("%d/%m/%Y, %I:%M:%S %p")
    ref_id    = _fmt(getattr(data, "reportId", None))

    # ── Page template: header + footer drawn on canvas ──────────────────────
    def _header_footer(canv: canvas.Canvas, doc_):
        canv.saveState()

        # Navy top bar
        canv.setFillColor(NAVY)
        canv.rect(0, H - 28 * mm, W, 28 * mm, stroke=0, fill=1)

        # Gold accent line below navy bar
        canv.setFillColor(GOLD)
        canv.rect(0, H - 30 * mm, W, 2 * mm, stroke=0, fill=1)

        # Header text
        canv.setFillColor(colors.white)
        canv.setFont("Helvetica-Bold", 11)
        canv.drawString(18 * mm, H - 12 * mm, "ANTI-SCAM MALAYSIA  /  LAPORAN RASMI")
        canv.setFont("Helvetica", 8)
        canv.drawRightString(W - 18 * mm, H - 12 * mm, f"Ref: {ref_id}")

        # Footer
        canv.setFillColor(GREY)
        canv.setFont("Helvetica", 7.5)
        footer = (
            f"Page {doc_.page}  •  Generated {generated}  •  For reference only"
        )
        canv.drawCentredString(W / 2, 10 * mm, footer)

        canv.restoreState()

    doc = BaseDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=38 * mm, bottomMargin=20 * mm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="official", frames=[frame], onPage=_header_footer)])

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "title", parent=styles["Title"],
        fontSize=20, textColor=DARK, alignment=TA_CENTER,
        spaceAfter=2, fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "subtitle", parent=styles["Normal"],
        fontSize=10, textColor=GREY, alignment=TA_CENTER, spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "section", parent=styles["Normal"],
        fontSize=10, textColor=colors.white, fontName="Helvetica-Bold",
    )
    label_style = ParagraphStyle(
        "label", parent=styles["Normal"],
        fontSize=9, textColor=GREY,
    )
    value_style = ParagraphStyle(
        "value", parent=styles["Normal"],
        fontSize=10, textColor=DARK, fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "body", parent=styles["Normal"],
        fontSize=10, textColor=DARK, leading=15,
    )
    action_style = ParagraphStyle(
        "action", parent=styles["Normal"],
        fontSize=10, textColor=RED, leading=16,
    )

    story = []

    # ── Report title ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("SCAM INCIDENT REPORT", title_style))
    story.append(Paragraph("Laporan Insiden Penipuan", subtitle_style))

    # ── Helper: section header bar ───────────────────────────────────────────
    def _section_header(en_title, ms_title):
        header = Table(
            [[Paragraph(f"{en_title}  <font size='8' color='#CBD5E1'>/ {ms_title}</font>",
                        section_style)]],
            colWidths=[doc.width],
        )
        header.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(header)

    # ── Helper: two-column data table ────────────────────────────────────────
    def _data_table(rows):
        """rows = list of (label_en / label_ms, value)"""
        table_rows = []
        for label_text, value_text in rows:
            table_rows.append([
                Paragraph(label_text, label_style),
                Paragraph(str(value_text) if value_text else "—", value_style),
            ])
        t = Table(table_rows, colWidths=[65 * mm, doc.width - 65 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), LIGHT),
            ("LINEBELOW",     (0, 0), (-1, -2), 0.4, colors.HexColor("#E2E8F0")),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(t)
        story.append(Spacer(1, 4 * mm))

    # ── SECTION A — Incident Particulars ─────────────────────────────────────
    _section_header("SECTION A — INCIDENT PARTICULARS", "Butiran Insiden")
    _data_table([
        ("Incident Date / Tarikh",                _fmt(getattr(data, "incidentDate",    None))),
        ("Scam Type / Jenis Penipuan",            _fmt(getattr(data, "scamType",        None))),
        ("Contact Method / Kaedah Hubungan",      _fmt(getattr(data, "contactMethod",   None))),
        ("Scammer's Contact / Hubungan Penipu",   _fmt(getattr(data, "scammerContact",  None))),
        ("Amount Lost / Kerugian",                _money(getattr(data, "amountLost", 0),
                                                         getattr(data, "currency", "MYR"))),
        ("Scammer's Bank / Bank Penipu",          _fmt(getattr(data, "bankAccount",     None))),
    ])

    # ── SECTION B — Victim Information ───────────────────────────────────────
    victim_name  = _fmt(getattr(data, "victimName",  None))
    victim_ic    = _fmt(getattr(data, "victimIC",    None))
    victim_phone = _fmt(getattr(data, "victimPhone", None))

    _section_header("SECTION B — VICTIM INFORMATION", "Maklumat Mangsa")
    _data_table([
        ("Name / Nama",              victim_name),
        ("IC Number / Nombor IC",    victim_ic),
        ("Phone / Telefon",          victim_phone),
    ])

    # ── SECTION C — Description of Incident ──────────────────────────────────
    _section_header("SECTION C — DESCRIPTION OF INCIDENT", "Keterangan Insiden")
    desc_table = Table(
        [[Paragraph(_fmt(getattr(data, "description", None), "No description provided."),
                    body_style)]],
        colWidths=[doc.width],
    )
    desc_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(desc_table)
    story.append(Spacer(1, 4 * mm))

    # ── SECTION D — Required Actions ─────────────────────────────────────────
    _section_header("SECTION D — REQUIRED ACTIONS", "Tindakan Diperlukan")
    actions = [
        "File a police report at your nearest police station",
        "Contact your bank immediately if money was transferred",
        "Report to CCID: 03-2610 5000",
        "Report to BNM TELELINK: 1-300-88-5465",
        "Check mule accounts at: www.semakmule.rmp.gov.my",
        "Report to MCMC: aduan.mcmc.gov.my",
    ]
    action_rows = []
    for i, act in enumerate(actions, 1):
        action_rows.append([
            Paragraph(f"<b>{i}</b>", action_style),
            Paragraph(act, action_style),
        ])
    action_table = Table(action_rows, colWidths=[8 * mm, doc.width - 8 * mm])
    action_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT),
        ("LEFTPADDING",   (0, 0), (0, -1), 8),
        ("LEFTPADDING",   (1, 0), (1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW",     (0, 0), (-1, -2), 0.3, colors.HexColor("#E2E8F0")),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(action_table)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# ===========================================================================
# LAYOUT 3 — Sidebar Dashboard
# Dark left sidebar holds metadata; right side reads as the narrative.
# ===========================================================================
def _build_pdf_layout3(data) -> bytes:
    buffer = io.BytesIO()
    SIDEBAR_W = 65 * mm
    DARK = colors.HexColor("#111827")
    ACCENT = colors.HexColor("#22D3EE")

    def _draw_sidebar(canv: canvas.Canvas, doc_):
        canv.saveState()
        canv.setFillColor(DARK)
        canv.rect(0, 0, SIDEBAR_W, A4[1], stroke=0, fill=1)
        # accent
        canv.setFillColor(ACCENT)
        canv.rect(0, A4[1] - 6 * mm, SIDEBAR_W, 2, stroke=0, fill=1)
        # title
        canv.setFillColor(colors.white)
        canv.setFont("Helvetica-Bold", 13)
        canv.drawString(10 * mm, A4[1] - 18 * mm, "Scam Report")
        canv.setFont("Helvetica", 8)
        canv.setFillColor(colors.HexColor("#9CA3AF"))
        canv.drawString(10 * mm, A4[1] - 23 * mm,
                        f"#{_fmt(getattr(data, 'reportId', None))}")

        # Sidebar items
        items = [
            ("DATE", _fmt(getattr(data, "incidentDate", None))),
            ("TYPE", _fmt(getattr(data, "scamType", None))),
            ("METHOD", _fmt(getattr(data, "method", None))),
            ("CHANNEL", _fmt(getattr(data, "channel", None))),
            ("BANK", _fmt(getattr(data, "bank", None))),
            ("LOSS", _money(getattr(data, "amountLost", 0))),
        ]
        y = A4[1] - 40 * mm
        for label_, value in items:
            canv.setFillColor(colors.HexColor("#9CA3AF"))
            canv.setFont("Helvetica-Bold", 7)
            canv.drawString(10 * mm, y, label_)
            canv.setFillColor(colors.white)
            canv.setFont("Helvetica", 10)
            canv.drawString(10 * mm, y - 5 * mm, value[:28])
            y -= 16 * mm

        # Footer
        canv.setFillColor(colors.HexColor("#6B7280"))
        canv.setFont("Helvetica", 7)
        canv.drawString(10 * mm, 12 * mm,
                        datetime.now().strftime("%d %b %Y"))
        canv.restoreState()

    doc = BaseDocTemplate(
        buffer, pagesize=A4,
        leftMargin=SIDEBAR_W + 12 * mm, rightMargin=15 * mm,
        topMargin=20 * mm, bottomMargin=18 * mm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="dash", frames=[frame], onPage=_draw_sidebar)])

    styles = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=styles["Title"], fontSize=20,
                       textColor=DARK, alignment=TA_LEFT, spaceAfter=6)
    section = ParagraphStyle("s", parent=styles["Heading2"], fontSize=12,
                             textColor=DARK, spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("b", parent=styles["Normal"], fontSize=10,
                          textColor=colors.HexColor("#1F2937"), leading=15)

    story = [
        Paragraph("Incident Narrative", h),
        Paragraph(
            "A summary of what happened, in the reporter's own words.",
            ParagraphStyle("sub", parent=styles["Normal"], fontSize=9,
                           textColor=colors.HexColor("#6B7280"), spaceAfter=10),
        ),
        Paragraph("What happened", section),
        Paragraph(_fmt(getattr(data, "description", None), "No description provided."), body),
        Paragraph("Recommended actions", section),
    ]
    actions = [
        "Contact your bank immediately.",
        "File a police report.",
        "Call the National Scam Response Centre (997).",
        "Preserve all evidence.",
    ]
    for a in actions:
        story.append(Paragraph(f"• {a}", body))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# ===========================================================================
# LAYOUT 4 — Infographic Alert
# Bold, alert-driven. Stat tiles, quick-fact chips, numbered action steps.
# ===========================================================================
def _build_pdf_layout4(data) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()
    RED = colors.HexColor("#DC2626")
    DARK = colors.HexColor("#1E293B")

    alert = ParagraphStyle("alert", parent=styles["Title"], fontSize=26,
                           textColor=colors.white, alignment=TA_LEFT, leading=30)
    alert_sub = ParagraphStyle("alertSub", parent=styles["Normal"], fontSize=10,
                               textColor=colors.HexColor("#FECACA"), alignment=TA_LEFT)
    tile_label = ParagraphStyle("tl", parent=styles["Normal"], fontSize=8,
                                textColor=colors.HexColor("#64748B"), alignment=TA_CENTER)
    tile_value = ParagraphStyle("tv", parent=styles["Normal"], fontSize=14,
                                textColor=DARK, alignment=TA_CENTER, leading=16)
    section = ParagraphStyle("s", parent=styles["Heading2"], fontSize=13,
                             textColor=DARK, spaceBefore=12, spaceAfter=6)
    body = ParagraphStyle("b", parent=styles["Normal"], fontSize=10,
                          textColor=DARK, leading=14)

    story = []

    # Alert banner
    banner = Table(
        [[Paragraph("⚠ SCAM ALERT", alert)],
         [Paragraph(
             f"Report #{_fmt(getattr(data, 'reportId', None))} · "
             f"{datetime.now().strftime('%d %b %Y')}", alert_sub)]],
        colWidths=[doc.width],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), RED),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (0, 0), 14),
        ("BOTTOMPADDING", (0, 1), (0, 1), 14),
    ]))
    story.append(banner)
    story.append(Spacer(1, 12))

    # Stat tiles
    def _tile(label_, value):
        t = Table(
            [[Paragraph(label_, tile_label)],
             [Paragraph(value, tile_value)]],
            colWidths=[(doc.width - 16) / 3],
        )
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
        ]))
        return t

    tiles = Table(
        [[
            _tile("AMOUNT LOST", _money(getattr(data, "amountLost", 0))),
            _tile("METHOD", _fmt(getattr(data, "method", None))),
            _tile("BANK", _fmt(getattr(data, "bank", None))),
        ]],
        colWidths=[(doc.width - 16) / 3] * 3,
    )
    tiles.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tiles)

    # Quick-fact chips
    story.append(Paragraph("Quick facts", section))
    chips = [
        ("Type", _fmt(getattr(data, "scamType", None))),
        ("Date", _fmt(getattr(data, "incidentDate", None))),
        ("Channel", _fmt(getattr(data, "channel", None))),
    ]
    chip_row = []
    for k, v in chips:
        chip = Table([[Paragraph(f"<b>{k}:</b> {v}", body)]])
        chip.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        chip_row.append(chip)
    chip_table = Table([chip_row], colWidths=[doc.width / 3] * 3)
    chip_table.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 3),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
    story.append(chip_table)

    # What happened
    story.append(Paragraph("What happened", section))
    story.append(Paragraph(_fmt(getattr(data, "description", None), "No description provided."), body))

    # Numbered action steps
    story.append(Paragraph("Take action now", section))
    steps = [
        "Call your bank to freeze your accounts.",
        "Report to the National Scam Response Centre at 997.",
        "Lodge a police report.",
        "Save all evidence (screenshots, receipts, messages).",
    ]
    rows = []
    for i, s in enumerate(steps, 1):
        num = Table([[Paragraph(f"<b>{i}</b>",
                                ParagraphStyle("n", parent=styles["Normal"],
                                               fontSize=14, textColor=colors.white,
                                               alignment=TA_CENTER))]],
                    colWidths=[10 * mm], rowHeights=[10 * mm])
        num.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), RED),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        rows.append([num, Paragraph(s, body)])
    steps_t = Table(rows, colWidths=[12 * mm, doc.width - 12 * mm])
    steps_t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(steps_t)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# ===========================================================================
# Dispatcher
# ===========================================================================
_LAYOUTS = {
    # "original": _build_pdf,   # uncomment after restoring the original function above
    "layout1": _build_pdf_layout1,
    "layout2": _build_pdf_layout2,
    "layout3": _build_pdf_layout3,
    "layout4": _build_pdf_layout4,
}


def _build_pdf(data) -> bytes:
    """Active builder — switch via ACTIVE_LAYOUT at the top of this file."""
    builder = _LAYOUTS.get(ACTIVE_LAYOUT, _build_pdf_layout1)
    return builder(data)


# ===========================================================================
# Route
# ===========================================================================
@router.post("/report")
async def generate_report(data):
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
