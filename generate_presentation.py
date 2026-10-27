"""
DocuVault — Executive Capstone Presentation Generator (Refactored Clean Edition)
Generates an executive-grade 16:9 widescreen presentation in PPTX and exports to native PDF.
Matches the signature DocuVault Dark Mode theme (#08080C black, #FF7A2E electric orange).
Completely reorganized to eliminate cluttered div/boxes: all pointers unified into single cohesive panels with internal hairline dividers.
"""

import os
import sys
import subprocess
from pathlib import Path

import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

# -----------------------------------------------------------------------------
# COLOR PALETTE (DocuVault Dark Mode Theme)
# -----------------------------------------------------------------------------
BG_COLOR = RGBColor(8, 8, 12)             # #08080C Pitch Black Canvas
PANEL_BG = RGBColor(14, 14, 20)           # #0E0E14 Unified Deep Charcoal Container
PANEL_BORDER = RGBColor(35, 35, 48)       # #232330 Subtle Hairline Border
DIVIDER_COLOR = RGBColor(38, 38, 52)      # #262634 Internal Hairline Divider

ORANGE = RGBColor(255, 122, 46)           # #FF7A2E Electric Brand Orange
ORANGE_LIGHT = RGBColor(255, 157, 102)    # #FF9D66 Light Orange Accent
ORANGE_BG = RGBColor(43, 22, 12)          # #2B160C Dark Orange Badge Background

WHITE = RGBColor(255, 255, 255)           # #FFFFFF Crisp White Headings
TEXT_PRIMARY = RGBColor(248, 250, 252)    # #F8FAFC
TEXT_SECONDARY = RGBColor(203, 213, 225)  # #CBD5E1 Slate Light
TEXT_MUTED = RGBColor(148, 163, 184)      # #94A3B8 Slate Muted
TEXT_DARK_MUTED = RGBColor(100, 116, 139) # #64748B Footer Muted

GREEN = RGBColor(16, 185, 129)            # #10B981 Emerald
GREEN_BG = RGBColor(10, 38, 28)           # #0A261C
BLUE = RGBColor(59, 130, 246)             # #3B82F6 Accent Blue
BLUE_BG = RGBColor(15, 29, 58)            # #0F1D3A

TOTAL_SLIDES = 13


def set_slide_background(slide):
    """Sets deep black background and a top glowing orange accent hairline."""
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_COLOR
    bg.line.fill.background()

    top_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(0.05))
    top_line.fill.solid()
    top_line.fill.fore_color.rgb = ORANGE
    top_line.line.fill.background()


def add_header(slide, tag_text: str, title_text: str, subtitle_text: str):
    """Adds unified category badge, main title, and subtitle."""
    tag_box = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.8), Inches(0.38), Inches(3.2), Inches(0.30)
    )
    tag_box.fill.solid()
    tag_box.fill.fore_color.rgb = ORANGE_BG
    tag_box.line.color.rgb = ORANGE
    tag_box.line.width = Pt(1)
    tf = tag_box.text_frame
    tf.word_wrap = False
    tf.margin_left = Inches(0.12)
    tf.margin_top = Inches(0.01)
    p = tf.paragraphs[0]
    p.text = tag_text.upper()
    p.font.name = "Segoe UI"
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = ORANGE

    title_box = slide.shapes.add_textbox(Inches(0.78), Inches(0.72), Inches(11.8), Inches(0.95))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    tf_t.margin_left = Inches(0)
    tf_t.margin_top = Inches(0)

    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.name = "Segoe UI"
    p_t.font.size = Pt(23)
    p_t.font.bold = True
    p_t.font.color.rgb = WHITE

    if subtitle_text:
        p_sub = tf_t.add_paragraph()
        p_sub.text = subtitle_text
        p_sub.font.name = "Segoe UI"
        p_sub.font.size = Pt(11.5)
        p_sub.font.color.rgb = TEXT_MUTED


def add_footer(slide, current_slide: int, total_slides: int = TOTAL_SLIDES):
    """Adds subtle footer rule and running academic metadata."""
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.8), Inches(7.05), Inches(11.733), Inches(0.015)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = PANEL_BORDER
    line.line.fill.background()

    ft_left = slide.shapes.add_textbox(Inches(0.8), Inches(7.08), Inches(4.5), Inches(0.3))
    p = ft_left.text_frame.paragraphs[0]
    p.text = "DocuVaultAI • Smart Document Management System"
    p.font.name = "Segoe UI"
    p.font.size = Pt(9)
    p.font.color.rgb = TEXT_DARK_MUTED

    ft_mid = slide.shapes.add_textbox(Inches(5.0), Inches(7.08), Inches(4.5), Inches(0.3))
    p = ft_mid.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "Advanced Python ESE Project • Group 2"
    p.font.name = "Segoe UI"
    p.font.size = Pt(9)
    p.font.color.rgb = TEXT_DARK_MUTED

    ft_right = slide.shapes.add_textbox(Inches(9.5), Inches(7.08), Inches(3.0), Inches(0.3))
    p = ft_right.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    p.text = f"{current_slide:02d} / {total_slides:02d}"
    p.font.name = "Segoe UI"
    p.font.bold = True
    p.font.size = Pt(9.5)
    p.font.color.rgb = ORANGE


def add_unified_panel(slide, left, top, width, height, bg=PANEL_BG, border=PANEL_BORDER, border_width=1):
    """Creates a single large unified container panel."""
    panel = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    panel.fill.solid()
    panel.fill.fore_color.rgb = bg
    panel.line.color.rgb = border
    panel.line.width = Pt(border_width)
    return panel


def add_vdivider(slide, x, top, height, color=DIVIDER_COLOR):
    """Draws a vertical hairline divider inside a unified panel."""
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, top, Inches(0.015), height)
    line.fill.solid()
    line.fill.fore_color.rgb = color
    line.line.fill.background()
    return line


def add_hdivider(slide, left, y, width, color=DIVIDER_COLOR):
    """Draws a horizontal hairline divider inside a unified panel."""
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, y, width, Inches(0.015))
    line.fill.solid()
    line.fill.fore_color.rgb = color
    line.line.fill.background()
    return line


def add_window_mockup(slide, img_path: str, left, top, width, height, window_title: str):
    """Draws a sleek application window frame with control dots and embeds the screenshot."""
    frame = add_unified_panel(slide, left, top, width, height, bg=RGBColor(12, 12, 17), border=PANEL_BORDER, border_width=1)

    bar_height = Inches(0.34)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left + Inches(0.01), top + Inches(0.01), width - Inches(0.02), bar_height)
    bar.fill.solid()
    bar.fill.fore_color.rgb = RGBColor(18, 18, 25)
    bar.line.fill.background()

    dot_colors = [RGBColor(239, 68, 68), RGBColor(245, 158, 11), RGBColor(16, 185, 129)]
    dot_x = left + Inches(0.14)
    dot_y = top + Inches(0.11)
    for c in dot_colors:
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, dot_x, dot_y, Inches(0.10), Inches(0.10))
        dot.fill.solid()
        dot.fill.fore_color.rgb = c
        dot.line.fill.background()
        dot_x += Inches(0.16)

    tb = slide.shapes.add_textbox(left + Inches(0.65), top + Inches(0.03), width - Inches(0.75), bar_height)
    p = tb.text_frame.paragraphs[0]
    p.text = window_title
    p.font.name = "Segoe UI"
    p.font.size = Pt(8.5)
    p.font.color.rgb = TEXT_MUTED

    img_left = left + Inches(0.02)
    img_top = top + bar_height + Inches(0.02)
    img_width = width - Inches(0.04)
    img_height = height - bar_height - Inches(0.04)

    if os.path.exists(img_path):
        slide.shapes.add_picture(img_path, img_left, img_top, img_width, img_height)


# =============================================================================
# SLIDE 01: COVER & HERO
# =============================================================================
def build_slide_01_cover(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)

    # Hero branding area (unboxed, clean, authoritative)
    logo_path = r"d:\Programming\Projects\DocuVault\assets\logo.png"
    if os.path.exists(logo_path):
        slide.shapes.add_picture(logo_path, Inches(0.8), Inches(1.1), Inches(1.0), Inches(1.0))

    tag = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(1.95), Inches(1.15), Inches(5.8), Inches(0.34)
    )
    tag.fill.solid()
    tag.fill.fore_color.rgb = ORANGE_BG
    tag.line.color.rgb = ORANGE
    tag.line.width = Pt(1)
    tf = tag.text_frame
    tf.word_wrap = False
    tf.margin_left = Inches(0.15)
    tf.margin_top = Inches(0.03)
    p = tf.paragraphs[0]
    p.text = "ESE – PART A: SDG-BASED PYTHON APPLICATION DEVELOPMENT"
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = ORANGE

    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(2.2), Inches(11.7), Inches(2.3))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True

    p_t = tf_t.paragraphs[0]
    p_t.text = "DocuVault"
    p_t.font.name = "Segoe UI"
    p_t.font.size = Pt(48)
    p_t.font.bold = True
    p_t.font.color.rgb = WHITE

    p_sub = tf_t.add_paragraph()
    p_sub.text = "Smart Document Management System"
    p_sub.font.name = "Segoe UI"
    p_sub.font.size = Pt(22)
    p_sub.font.bold = True
    p_sub.font.color.rgb = ORANGE

    p_desc = tf_t.add_paragraph()
    p_desc.text = (
        "An enterprise-grade, offline-first Python ecosystem engineered for cryptographic file integrity, "
        "automated multi-class classification, explainable TF-IDF AI retrieval, and proactive compliance governance."
    )
    p_desc.font.name = "Segoe UI"
    p_desc.font.size = Pt(13)
    p_desc.font.color.rgb = TEXT_SECONDARY

    # Unified bottom meta-panel (ONE container with 3 internally separated columns)
    meta_panel = add_unified_panel(slide, Inches(0.8), Inches(4.9), Inches(11.733), Inches(1.85))

    col_w = Inches(3.911)
    add_vdivider(slide, Inches(0.8) + col_w, Inches(4.9), Inches(1.85))
    add_vdivider(slide, Inches(0.8) + col_w * 2, Inches(4.9), Inches(1.85))

    # Col 1: Academic Institution
    tb1 = slide.shapes.add_textbox(Inches(1.0), Inches(5.05), col_w - Inches(0.4), Inches(1.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = Inches(0); tf1.margin_right = Inches(0); tf1.margin_top = Inches(0); tf1.margin_bottom = Inches(0)
    p = tf1.paragraphs[0]
    p.text = "INSTITUTION & COURSE"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = ORANGE
    p = tf1.add_paragraph()
    p.text = "Christ University Pune, Lavasa"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p = tf1.add_paragraph()
    p.text = "Course: Advanced Python (Postgraduate / M.Sc.)\nProject Group Number: 02"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_MUTED

    # Col 2: Development Team
    tb2 = slide.shapes.add_textbox(Inches(0.8) + col_w + Inches(0.2), Inches(5.05), col_w - Inches(0.4), Inches(1.5))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = Inches(0); tf2.margin_right = Inches(0); tf2.margin_top = Inches(0); tf2.margin_bottom = Inches(0)
    p = tf2.paragraphs[0]
    p.text = "DEVELOPMENT TEAM"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = ORANGE
    p = tf2.add_paragraph()
    p.text = "Siddharth Shakyawal (24112517)\nShanya (24112520)"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p = tf2.add_paragraph()
    p.text = "Architecture, PyQt6 GUI, Vector ML & Forensics"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_MUTED

    # Col 3: Faculty Supervisor
    tb3 = slide.shapes.add_textbox(Inches(0.8) + col_w * 2 + Inches(0.2), Inches(5.05), col_w - Inches(0.4), Inches(1.5))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = Inches(0); tf3.margin_right = Inches(0); tf3.margin_top = Inches(0); tf3.margin_bottom = Inches(0)
    p = tf3.paragraphs[0]
    p.text = "FACULTY SUPERVISOR"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = ORANGE
    p = tf3.add_paragraph()
    p.text = "Prof. Rohit Gupta"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p = tf3.add_paragraph()
    p.text = "Assistant Professor, Dept. of Computer Science\nDemonstration & Academic Review: Oct 2026"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_MUTED

    add_footer(slide, 1)


# =============================================================================
# SLIDE 02: PROBLEM STATEMENT (ONE UNIFIED CONSOLE WITH 4 QUADRANTS)
# =============================================================================
def build_slide_02_problem(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "01 / PROJECT NEED & CHALLENGE",
        "The Challenge in Modern Document Governance",
        "Organizations face mounting risks from unstructured silos, undetected file tampering, and buried clauses."
    )

    # ONE unified panel for all 4 problems + solution
    panel_top = Inches(1.85)
    panel_h = Inches(4.9)
    panel_w = Inches(11.733)
    add_unified_panel(slide, Inches(0.8), panel_top, panel_w, panel_h)

    # Hairline dividers: 1 vertical down the middle, 1 horizontal across the middle, 1 above solution
    mid_x = Inches(0.8) + panel_w / 2
    quad_h = Inches(2.05)
    mid_y = panel_top + quad_h
    sol_y = panel_top + Inches(4.15)

    add_vdivider(slide, mid_x, panel_top, Inches(4.15))
    add_hdivider(slide, Inches(0.8), mid_y, panel_w)
    add_hdivider(slide, Inches(0.8), sol_y, panel_w)

    half_w = panel_w / 2 - Inches(0.5)

    # Q1: File Fragmentation
    tb1 = slide.shapes.add_textbox(Inches(1.05), panel_top + Inches(0.12), half_w, quad_h - Inches(0.2))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = Inches(0); tf1.margin_right = Inches(0); tf1.margin_top = Inches(0); tf1.margin_bottom = Inches(0)
    p = tf1.paragraphs[0]
    p.text = "01 / Severe File Fragmentation & Sprawl"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12.5)
    p.font.bold = True
    p.font.color.rgb = ORANGE
    for bullet_txt in [
        "Documents scattered across unorganized directories, user desktops, and shared drives.",
        "Conflicting draft revisions cause operational mistakes and administrative confusion.",
        "Manual folder browsing wastes hours locating routine contracts, invoices, and reports."
    ]:
        p = tf1.add_paragraph()
        p.text = f"•  {bullet_txt}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_SECONDARY

    # Q2: Silent Corruption
    tb2 = slide.shapes.add_textbox(mid_x + Inches(0.3), panel_top + Inches(0.12), half_w, quad_h - Inches(0.2))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = Inches(0); tf2.margin_right = Inches(0); tf2.margin_top = Inches(0); tf2.margin_bottom = Inches(0)
    p = tf2.paragraphs[0]
    p.text = "02 / Silent Corruption & Tamper Vulnerabilities"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12.5)
    p.font.bold = True
    p.font.color.rgb = ORANGE
    for bullet_txt in [
        "Standard operating systems cannot detect if a stored PDF was maliciously altered.",
        "Disguised executable payloads exploit file extension spoofing without inspection.",
        "Lack of continuous cryptographic verification compromises legal provenance."
    ]:
        p = tf2.add_paragraph()
        p.text = f"•  {bullet_txt}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_SECONDARY

    # Q3: Search Friction
    tb3 = slide.shapes.add_textbox(Inches(1.05), mid_y + Inches(0.12), half_w, quad_h - Inches(0.2))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = Inches(0); tf3.margin_right = Inches(0); tf3.margin_top = Inches(0); tf3.margin_bottom = Inches(0)
    p = tf3.paragraphs[0]
    p.text = "03 / Search Friction & Buried Intelligence"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12.5)
    p.font.bold = True
    p.font.color.rgb = ORANGE
    for bullet_txt in [
        "Critical clauses (indemnity limits, milestones) remain buried in lengthy 50+ page PDFs.",
        "Routine keyword lookups fail across unstructured document formats and clause variations.",
        "Zero attribution: operators cannot easily verify the exact source page for answers."
    ]:
        p = tf3.add_paragraph()
        p.text = f"•  {bullet_txt}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_SECONDARY

    # Q4: Compliance Lapses
    tb4 = slide.shapes.add_textbox(mid_x + Inches(0.3), mid_y + Inches(0.12), half_w, quad_h - Inches(0.2))
    tf4 = tb4.text_frame
    tf4.word_wrap = True
    tf4.margin_left = Inches(0); tf4.margin_right = Inches(0); tf4.margin_top = Inches(0); tf4.margin_bottom = Inches(0)
    p = tf4.paragraphs[0]
    p.text = "04 / Compliance Lapses & PII Exposure"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12.5)
    p.font.bold = True
    p.font.color.rgb = ORANGE
    for bullet_txt in [
        "Missed renewal deadlines and statutory compliance milestones without holiday awareness.",
        "Unprotected Personally Identifiable Information (phone numbers, emails, payment cards).",
        "Absence of immutable, timestamped audit logging for institutional governance."
    ]:
        p = tf4.add_paragraph()
        p.text = f"•  {bullet_txt}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_SECONDARY

    # Integrated Solution Strip at Bottom of Panel
    tb_sol = slide.shapes.add_textbox(Inches(1.05), sol_y + Inches(0.1), panel_w - Inches(0.5), Inches(0.6))
    tf_sol = tb_sol.text_frame
    tf_sol.word_wrap = True
    tf_sol.margin_left = Inches(0); tf_sol.margin_right = Inches(0); tf_sol.margin_top = Inches(0); tf_sol.margin_bottom = Inches(0)
    p = tf_sol.paragraphs[0]
    p.text = "THE DOCUVAULT SOLUTION"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = ORANGE
    p = tf_sol.add_paragraph()
    p.text = "Unifies binary validation, SHA-256 fingerprinting, automated taxonomy, explainable TF-IDF AI retrieval, and compliance into a coordinated offline Python architecture."
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.color.rgb = WHITE

    add_footer(slide, 2)


# =============================================================================
# SLIDE 03: ARCHITECTURAL OBJECTIVES (ONE UNIFIED 4-COLUMN CONSOLE)
# =============================================================================
def build_slide_03_objectives(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "02 / PROJECT OBJECTIVES",
        "Architectural Objectives & Engineering Pillars",
        "Designed to establish an immutable, intelligent, and privacy-preserving document management ecosystem."
    )

    panel_top = Inches(1.85)
    panel_h = Inches(4.9)
    panel_w = Inches(11.733)
    add_unified_panel(slide, Inches(0.8), panel_top, panel_w, panel_h)

    col_w = panel_w / 4
    add_vdivider(slide, Inches(0.8) + col_w, panel_top, panel_h)
    add_vdivider(slide, Inches(0.8) + col_w * 2, panel_top, panel_h)
    add_vdivider(slide, Inches(0.8) + col_w * 3, panel_top, panel_h)

    pillars = [
        {
            "num": "01",
            "title": "Cryptographic Integrity",
            "color": ORANGE,
            "bullets": [
                "Binary magic-byte inspection (%PDF-, PK\\x03\\x04) definitively validating file formats.",
                "Deterministic SHA-256 digital fingerprinting computed on intake and indexed in MongoDB.",
                "Continuous background integrity scans detecting silent bit-rot and unauthorized edits.",
                "Instant quarantine isolation for corrupted files, maintaining 100/100 health score."
            ]
        },
        {
            "num": "02",
            "title": "Automated Taxonomy",
            "color": BLUE,
            "bullets": [
                "Streaming multi-format parsing (PDF, XML, TXT) powered by PyMuPDF.",
                "Automatic classification into 5 semantic domains: Legal, Medical, Financial, Academic, General.",
                "Regex-driven entity extraction: counterparties, governing law, invoice amounts, and terms.",
                "Two-tier deduplication: O(1) hash matches + SequenceMatcher near-duplicate similarity."
            ]
        },
        {
            "num": "03",
            "title": "Explainable AI Retrieval",
            "color": ORANGE,
            "bullets": [
                "Air-gapped TF-IDF vector matrix built from first principles using NumPy arrays.",
                "Mathematical cosine similarity dot-product ranking in 0.12 s on standard CPU.",
                "Verifiable source citations linking answers to exact document filenames and page numbers.",
                "100% offline execution guaranteeing zero cloud exfiltration of confidential intelligence."
            ]
        },
        {
            "num": "04",
            "title": "Compliance & Security",
            "color": GREEN,
            "bullets": [
                "Automated regex redaction masking phone numbers, emails, and payment card numbers.",
                "Holiday-aware deadline calculation engine shifting dates past weekends and official holidays.",
                "Nager.Date public REST API integration with standard iCalendar (.ics) export.",
                "Tamper-evident SQLite3 audit logging recording user actions with 1-click CSV export."
            ]
        }
    ]

    for i, col in enumerate(pillars):
        x = Inches(0.8) + col_w * i + Inches(0.2)
        tb = slide.shapes.add_textbox(x, panel_top + Inches(0.2), col_w - Inches(0.4), panel_h - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = f"{col['num']}  •  {col['title']}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(12.5)
        p.font.bold = True
        p.font.color.rgb = col["color"]

        # Small accent rule under header
        p_space = tf.add_paragraph()
        p_space.text = "—" * 18
        p_space.font.name = "Segoe UI"
        p_space.font.size = Pt(8)
        p_space.font.color.rgb = PANEL_BORDER

        for b in col["bullets"]:
            p_b = tf.add_paragraph()
            p_b.text = f"•  {b}"
            p_b.font.name = "Segoe UI"
            p_b.font.size = Pt(9.5)
            p_b.font.color.rgb = TEXT_SECONDARY

    add_footer(slide, 3)


# =============================================================================
# SLIDE 04: SDG ALIGNMENT (ONE UNIFIED PANEL WITH DUAL FOCUS)
# =============================================================================
def build_slide_04_sdg(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "03 / SOCIAL RELEVANCE & SDGS",
        "Sustainable Development Goals (SDG) Alignment",
        "Directly advancing institutional transparency, paperless sustainability, and resilient software infrastructure."
    )

    panel_top = Inches(1.85)
    panel_h = Inches(4.9)
    panel_w = Inches(11.733)
    add_unified_panel(slide, Inches(0.8), panel_top, panel_w, panel_h)

    mid_x = Inches(0.8) + Inches(5.8)
    add_vdivider(slide, mid_x, panel_top, Inches(4.2))
    add_hdivider(slide, mid_x, panel_top + Inches(2.1), panel_w - Inches(5.8))
    add_hdivider(slide, Inches(0.8), panel_top + Inches(4.2), panel_w)

    # Left: Primary Focus SDG 16
    tb_l = slide.shapes.add_textbox(Inches(1.05), panel_top + Inches(0.18), Inches(5.35), Inches(3.9))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = Inches(0); tf_l.margin_right = Inches(0); tf_l.margin_top = Inches(0); tf_l.margin_bottom = Inches(0)
    p = tf_l.paragraphs[0]
    p.text = "PRIMARY GOAL • UN SDG 16"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = ORANGE

    p = tf_l.add_paragraph()
    p.text = "Peace, Justice & Strong Institutions"
    p.font.name = "Segoe UI"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = WHITE

    for heading, detail in [
        ("Target 16.6 — Accountable Institutions", "Cryptographic SHA-256 fingerprinting ensures record immutability. If any document is altered, the system flags the discrepancy and isolates the file, preventing administrative corruption."),
        ("Target 16.10 — Public & Transparent Access", "High-speed TF-IDF semantic search allows authorized auditors and users to immediately verify contractual clauses, legal obligations, and rights without technical friction."),
        ("Granular Traceability & Evidence", "Every file save, query, and verification event is immutably logged into an audit trail with exact timestamps, user credentials, and 1-click CSV export.")
    ]:
        p = tf_l.add_paragraph()
        p.text = f"✓  {heading}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = ORANGE_LIGHT

        p_sub = tf_l.add_paragraph()
        p_sub.text = detail
        p_sub.font.name = "Segoe UI"
        p_sub.font.size = Pt(9.5)
        p_sub.font.color.rgb = TEXT_SECONDARY

    # Right Top: Supporting Focus SDG 9
    tb_r1 = slide.shapes.add_textbox(mid_x + Inches(0.3), panel_top + Inches(0.18), Inches(5.3), Inches(1.8))
    tf_r1 = tb_r1.text_frame
    tf_r1.word_wrap = True
    tf_r1.margin_left = Inches(0); tf_r1.margin_right = Inches(0); tf_r1.margin_top = Inches(0); tf_r1.margin_bottom = Inches(0)
    p = tf_r1.paragraphs[0]
    p.text = "SUPPORTING GOAL • UN SDG 9"
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = BLUE

    p = tf_r1.add_paragraph()
    p.text = "Industry, Innovation & Infrastructure"
    p.font.name = "Segoe UI"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = WHITE

    for b in [
        "Built on a modular, decoupled Python architecture (PyQt6 + Flask + Streamlit).",
        "Operates 100% air-gapped / offline, providing resilient digital infrastructure for resource-constrained or sensitive environments without cloud paywalls."
    ]:
        p = tf_r1.add_paragraph()
        p.text = f"•  {b}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(9)
        p.font.color.rgb = TEXT_SECONDARY

    # Right Bottom: Supporting Focus SDG 12
    tb_r2 = slide.shapes.add_textbox(mid_x + Inches(0.3), panel_top + Inches(2.25), Inches(5.3), Inches(1.8))
    tf_r2 = tb_r2.text_frame
    tf_r2.word_wrap = True
    tf_r2.margin_left = Inches(0); tf_r2.margin_right = Inches(0); tf_r2.margin_top = Inches(0); tf_r2.margin_bottom = Inches(0)
    p = tf_r2.paragraphs[0]
    p.text = "SUPPORTING GOAL • UN SDG 12"
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = GREEN

    p = tf_r2.add_paragraph()
    p.text = "Responsible Consumption & Production"
    p.font.name = "Segoe UI"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = WHITE

    for b in [
        "Replaces physical filing and paper duplication with high-speed digital indexing.",
        "Reduces unnecessary printing waste, duplicate storage overhead, and enforces structured digital retention policies."
    ]:
        p = tf_r2.add_paragraph()
        p.text = f"•  {b}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(9)
        p.font.color.rgb = TEXT_SECONDARY

    # Integrated Empirical Evaluation Banner at Bottom
    tb_bench = slide.shapes.add_textbox(Inches(1.05), panel_top + Inches(4.28), panel_w - Inches(0.5), Inches(0.55))
    tf_b = tb_bench.text_frame
    tf_b.word_wrap = True
    tf_b.margin_left = Inches(0); tf_b.margin_right = Inches(0); tf_b.margin_top = Inches(0); tf_b.margin_bottom = Inches(0)
    p = tf_b.paragraphs[0]
    p.text = "EMPIRICAL EVALUATION"
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = ORANGE
    p = tf_b.add_paragraph()
    p.text = "Replaces slow manual folder browsing with sub-second TF-IDF search, verified 42/42 hashes with zero false-positives, and eliminates physical paper waste."
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.color.rgb = WHITE

    add_footer(slide, 4)


# =============================================================================
# SLIDE 05: SYSTEM ARCHITECTURE & 6-STAGE PIPELINE (TWO UNIFIED STRIPS)
# =============================================================================
def build_slide_05_architecture(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "04 / SYSTEM ARCHITECTURE",
        "End-to-End 6-Stage Processing Pipeline & Modular Layers",
        "A decoupled 5-tier architecture that processes raw files into cryptographically secured, searchable assets."
    )

    # Top Unified Strip: 6-Stage Processing Pipeline
    p1_top = Inches(1.85)
    p1_h = Inches(2.35)
    panel_w = Inches(11.733)
    add_unified_panel(slide, Inches(0.8), p1_top, panel_w, p1_h)

    stages = [
        ("01", "INGEST", "Upload / Import", "Drag & drop or directory watcher receives multi-format files (PDF, XML, TXT)."),
        ("02", "VALIDATE", "Magic-Bytes", "Header signatures inspect binary bytes, rejecting extension-spoofed malicious files."),
        ("03", "HASH", "SHA-256 Digest", "Computes immutable 256-bit cryptographic hash for continuous tamper checking."),
        ("04", "EXTRACT", "PyMuPDF Parse", "Extracts structured text streams; classifies into Legal, Medical, Finance, Academic."),
        ("05", "INDEX", "Vector Index", "Constructs TF-IDF term-document matrices and inverted indices via NumPy."),
        ("06", "RETRIEVE", "Query & Audit", "Ranks queries via cosine similarity, flags duplicates, logs audit trail.")
    ]

    col6_w = panel_w / 6
    for i, (num, tag, title, desc) in enumerate(stages):
        if i > 0:
            add_vdivider(slide, Inches(0.8) + col6_w * i, p1_top, p1_h)

        x = Inches(0.8) + col6_w * i + Inches(0.12)
        tb = slide.shapes.add_textbox(x, p1_top + Inches(0.12), col6_w - Inches(0.24), p1_h - Inches(0.24))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = f"{num}  {tag}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(8.5)
        p.font.bold = True
        p.font.color.rgb = ORANGE

        p_t = tf.add_paragraph()
        p_t.text = title
        p_t.font.name = "Segoe UI"
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = WHITE

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.name = "Segoe UI"
        p_d.font.size = Pt(8.5)
        p_d.font.color.rgb = TEXT_SECONDARY

    # Bottom Unified Strip: 5-Tier Modular Architectural Layers
    p2_top = Inches(4.35)
    p2_h = Inches(2.4)
    add_unified_panel(slide, Inches(0.8), p2_top, panel_w, p2_h)

    # Title inside bottom panel
    tb_t = slide.shapes.add_textbox(Inches(1.0), p2_top + Inches(0.08), panel_w - Inches(0.4), Inches(0.3))
    p = tb_t.text_frame.paragraphs[0]
    p.text = "5-TIER MODULAR DECOUPLED ARCHITECTURE"
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = ORANGE

    add_hdivider(slide, Inches(0.8), p2_top + Inches(0.42), panel_w)

    tiers = [
        ("Tier 1: Presentation Layer", "PyQt6 GPU-accelerated desktop UI + Streamlit interactive analytics dashboard with Plotly charts."),
        ("Tier 2: Application & REST", "Flask RESTful micro-endpoints, CORS handling, multi-route request dispatching."),
        ("Tier 3: Identity & Access", "SessionManager, PBKDF2 credential hashing, user workspace isolation."),
        ("Tier 4: Document Intelligence", "PyMuPDF parser, NumPy TF-IDF matrix builder, difflib near-duplicate engine."),
        ("Tier 5: Persistence & Vault", "MongoDB document catalogue, SQLite3 authentication records, encrypted storage vault.")
    ]

    col5_w = panel_w / 5
    for i, (t_title, t_desc) in enumerate(tiers):
        if i > 0:
            add_vdivider(slide, Inches(0.8) + col5_w * i, p2_top + Inches(0.42), p2_h - Inches(0.42))

        x = Inches(0.8) + col5_w * i + Inches(0.12)
        tb = slide.shapes.add_textbox(x, p2_top + Inches(0.5), col5_w - Inches(0.24), p2_h - Inches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = t_title
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = WHITE

        p_d = tf.add_paragraph()
        p_d.text = t_desc
        p_d.font.name = "Segoe UI"
        p_d.font.size = Pt(8.5)
        p_d.font.color.rgb = TEXT_SECONDARY

    add_footer(slide, 5)


# =============================================================================
# SLIDE 06: PRODUCTION SOFTWARE STACK & CURRICULUM MAPPING (ONE DUAL-PANE BOARD)
# =============================================================================
def build_slide_06_tech_stack(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "05 / TECHNICAL IMPLEMENTATION",
        "Full-Stack Python Libraries & Curriculum Unit Mapping",
        "Rigorous application of Advanced Python principles across graphical, API, scientific, and data layers."
    )

    panel_top = Inches(1.85)
    panel_h = Inches(4.9)
    panel_w = Inches(11.733)
    add_unified_panel(slide, Inches(0.8), panel_top, panel_w, panel_h)

    mid_x = Inches(0.8) + Inches(5.6)
    add_vdivider(slide, mid_x, panel_top, panel_h)

    # Left: Production Software Stack
    tb_l = slide.shapes.add_textbox(Inches(1.05), panel_top + Inches(0.15), Inches(5.15), panel_h - Inches(0.3))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = Inches(0); tf_l.margin_right = Inches(0); tf_l.margin_top = Inches(0); tf_l.margin_bottom = Inches(0)
    p = tf_l.paragraphs[0]
    p.text = "CORE PRODUCTION LIBRARIES & TOOLS"
    p.font.name = "Segoe UI"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ORANGE

    tech_items = [
        ("Python 3.12+", "Core runtime language driving the entire decoupled application stack."),
        ("PyQt6", "Rich desktop interface, customizable QSS dark stylesheet, reactive event loop."),
        ("Flask & Flask-CORS", "REST API layer connecting desktop client with backend services."),
        ("Streamlit & Plotly", "Interactive browser web hub rendering real-time storage doughnut charts."),
        ("NumPy", "High-performance vector operations, TF-IDF calculation, cosine similarity."),
        ("Pandas", "Document catalogue tabular structures and audit trail CSV export handling."),
        ("PyMuPDF (fitz)", "High-speed text extraction from multi-page PDFs, layout and clause parsing."),
        ("hashlib & hmac", "SHA-256 cryptographic fingerprints and PBKDF2 password security."),
        ("SQLite3 & PyMongo", "Hybrid database backend: relational session auth + NoSQL document store.")
    ]

    for lib, desc in tech_items:
        p = tf_l.add_paragraph()
        p.text = f"•  {lib}: {desc}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(9)
        p.font.color.rgb = TEXT_SECONDARY

    # Right: Advanced Python Curriculum Unit Mapping
    tb_r = slide.shapes.add_textbox(mid_x + Inches(0.3), panel_top + Inches(0.15), Inches(5.5), panel_h - Inches(0.3))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = Inches(0); tf_r.margin_right = Inches(0); tf_r.margin_top = Inches(0); tf_r.margin_bottom = Inches(0)
    p = tf_r.paragraphs[0]
    p.text = "ADVANCED PYTHON CURRICULUM MAPPING"
    p.font.name = "Segoe UI"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ORANGE

    units = [
        ("✓ Unit 1: OOP, ABCs & GUI Architecture", "Abstract Base Class 'BaseDocument' with polymorphic subclasses (Legal, Medical, Financial), custom exceptions, regex entity matching, and PyQt6 desktop interface."),
        ("✓ Unit 2: APIs, Authentication & Web Services", "Secure REST endpoints, PBKDF2 salted password hashing, user session management, and external Nager.Date Public Holiday API integration."),
        ("✓ Unit 3: Flask & Streamlit Multi-Frameworks", "Decoupled backend service architecture with Flask API endpoints and an interactive Streamlit data dashboard with real-time Plotly visualization."),
        ("✓ Unit 4: Binary Files, Signatures & Pandas", "Deep magic-byte inspection (checking file headers vs extensions), streaming PDF extraction, SHA-256 cryptographic digests, and Pandas document catalogues."),
        ("✓ Unit 5: NumPy, Vector Algebra & Retrieval", "Sparse TF-IDF matrix construction from scratch, cosine similarity query ranking, Boolean array masking, and difflib near-duplicate matching.")
    ]

    for title, desc in units:
        p = tf_r.add_paragraph()
        p.text = title
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = WHITE

        p_desc = tf_r.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = "Segoe UI"
        p_desc.font.size = Pt(8.8)
        p_desc.font.color.rgb = TEXT_SECONDARY

    add_footer(slide, 6)


# =============================================================================
# SLIDE 07: CORE FEATURES & SECURITY SAFEGUARDS (ONE UNIFIED QUADRANT PANEL)
# =============================================================================
def build_slide_07_core_features(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "06 / SYSTEM CAPABILITIES",
        "Core Feature Highlights & Security Safeguards",
        "A multi-layered defense and intelligence framework protecting institutional knowledge."
    )

    panel_top = Inches(1.85)
    panel_h = Inches(4.9)
    panel_w = Inches(11.733)
    add_unified_panel(slide, Inches(0.8), panel_top, panel_w, panel_h)

    mid_x = Inches(0.8) + panel_w / 2
    mid_y = panel_top + panel_h / 2
    add_vdivider(slide, mid_x, panel_top, panel_h)
    add_hdivider(slide, Inches(0.8), mid_y, panel_w)

    quad_w = panel_w / 2 - Inches(0.55)
    quad_h = panel_h / 2 - Inches(0.25)

    quadrants = [
        (Inches(1.05), panel_top + Inches(0.15), "01 / Cryptographic Verification & Tamper Defense", [
            "Magic-byte inspection validates file format from header signatures, rejecting disguised malware payloads.",
            "SHA-256 cryptographic hashes detect any subsequent byte-level alteration or accidental bit-rot.",
            "Automated quarantine center isolates corrupted files immediately, preserving system integrity."
        ]),
        (mid_x + Inches(0.3), panel_top + Inches(0.15), "02 / Source-Grounded AI Search & Attribution", [
            "TF-IDF sparse vector representations enable rapid, completely offline query-document matching.",
            "Cosine similarity ranking retrieves top relevant passages without cloud latency or subscription fees.",
            "Every generated answer includes verified citations: exact document title, page number, and clause text."
        ]),
        (Inches(1.05), mid_y + Inches(0.15), "03 / Smart Deduplication & Version Intelligence", [
            "Zero-overhead exact duplicate detection via instant SHA-256 hash lookup in the document vault.",
            "Near-duplicate text similarity analysis utilizing Jaccard distance and Python's difflib SequenceMatcher.",
            "Reclaims storage space and prevents staff from referencing out-of-date document revisions."
        ]),
        (mid_x + Inches(0.3), mid_y + Inches(0.15), "04 / Privacy Governance & Deadline Tracking", [
            "Automated regex redaction engine masks sensitive PII (emails, phone numbers, credit card numbers).",
            "Business-day deadline shifting engine moves contract milestones past weekends and official holidays.",
            "Tamper-proof audit logging of every database save, navigation, and export action with CSV download."
        ])
    ]

    for x, y, title, bullets in quadrants:
        tb = slide.shapes.add_textbox(x, y, quad_w, quad_h)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0); tf.margin_right = Inches(0); tf.margin_top = Inches(0); tf.margin_bottom = Inches(0)
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = "Segoe UI"
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = ORANGE

        for b in bullets:
            p = tf.add_paragraph()
            p.text = f"•  {b}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(9.5)
            p.font.color.rgb = TEXT_SECONDARY
            p.font.color.rgb = TEXT_SECONDARY

    add_footer(slide, 7)


# =============================================================================
# HELPER FOR EVIDENCE SLIDES (SCREENSHOTS + UNIFIED BOTTOM STATUS RIBBON)
# =============================================================================
def build_evidence_slide(prs, slide_num: int, tag: str, title: str, subtitle: str,
                         w1_title: str, img1_path: str,
                         w2_title: str, img2_path: str,
                         metrics: list):
    """
    Renders 2 application window mockups at the top and ONE single unified status ribbon at the bottom.
    Completely eliminates separate button boxes!
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(slide, tag, title, subtitle)

    # Top window mockups side-by-side
    w_width = Inches(5.75)
    w_height = Inches(3.45)
    top_y = Inches(1.85)

    add_window_mockup(slide, img1_path, Inches(0.8), top_y, w_width, w_height, w1_title)
    add_window_mockup(slide, img2_path, Inches(6.78), top_y, w_width, w_height, w2_title)

    # Bottom UNIFIED status ribbon (ONE single container with 4 internally separated columns)
    ribbon_y = Inches(5.48)
    ribbon_h = Inches(1.35)
    ribbon_w = Inches(11.733)
    add_unified_panel(slide, Inches(0.8), ribbon_y, ribbon_w, ribbon_h)

    col4_w = ribbon_w / 4
    for i in range(1, 4):
        add_vdivider(slide, Inches(0.8) + col4_w * i, ribbon_y, ribbon_h)

    for i, (m_title, m_desc) in enumerate(metrics):
        x = Inches(0.8) + col4_w * i + Inches(0.15)
        tb = slide.shapes.add_textbox(x, ribbon_y + Inches(0.12), col4_w - Inches(0.3), ribbon_h - Inches(0.24))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = f"✓  {m_title}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = ORANGE

        p_desc = tf.add_paragraph()
        p_desc.text = m_desc
        p_desc.font.name = "Segoe UI"
        p_desc.font.size = Pt(8.8)
        p_desc.font.color.rgb = TEXT_SECONDARY

    add_footer(slide, slide_num)


# =============================================================================
# SLIDES 08, 09, 10: EVIDENCE SLIDES WITH UNIFIED RIBBONS
# =============================================================================
def build_slide_08_evidence_workspace(prs):
    media_dir = Path(r"C:\Users\siddh\.gemini\antigravity-ide\brain\b6d2c48b-dac1-447b-ba18-3ce7f04f23d0\.tempmediaStorage")
    img1 = str(media_dir / "test_vault_dark.png")
    img2 = str(media_dir / "test_page_1_storage_dark.png")

    metrics = [
        ("Multi-Format Ingestion", "Categorized across Legal, Medical, Financial, Academic, General."),
        ("Storage Quota Monitored", "Live real-time monitoring with interactive Plotly doughnut breakdown."),
        ("100% Authentic Hashes", "Every file verified via deterministic SHA-256 on intake."),
        ("Directory Watcher Active", "Automated background sync thread monitors local folder changes.")
    ]

    build_evidence_slide(
        prs, 8,
        "07 / LIVE APPLICATION EVIDENCE",
        "Document Workspace & Real-Time Storage Tracking",
        "High-resolution screenshots captured from the running DocuVault desktop client in dark mode.",
        "DocuVault — Enterprise Document Management [Documents Workspace & Ingestion]", img1,
        "DocuVault — Storage Vault & Encrypted Backup Analytics [Doughnut Breakdown]", img2,
        metrics
    )


def build_slide_09_evidence_security(prs):
    img_dir = Path(r"d:\Programming\Projects\DocuVault\assets\presentation")
    img1 = str(img_dir / "integrity_health.png")
    img2 = str(img_dir / "audit_trail.png")

    metrics = [
        ("Tamper-Evident Hashing", "Continuous SHA-256 re-hashing with constant-time verification."),
        ("100/100 Health Score", "42/42 repository documents verified authentic with zero tampering."),
        ("Granular Audit Logging", "Chronologically records DB saves, queries, and logins with microsecond stamps."),
        ("1-Click CSV Export", "Structured compliance export compatible with regulatory audit reviews.")
    ]

    build_evidence_slide(
        prs, 9,
        "08 / FORENSIC & INTEGRITY EVIDENCE",
        "Cryptographic Health Forensics & Immutable Audit Trail",
        "Live verification of SHA-256 digests, tamper detection score, and comprehensive activity logging.",
        "DocuVault — Security Forensics & File Tamper Scan Center [100% Health Score]", img1,
        "DocuVault — Comprehensive Activity & Audit Logging [Chronological Event Stream]", img2,
        metrics
    )


def build_slide_10_evidence_ai(prs):
    img_dir = Path(r"d:\Programming\Projects\DocuVault\assets\presentation")
    img1 = str(img_dir / "ai_assistant.png")
    img2 = str(img_dir / "deadlines_compliance.png")

    metrics = [
        ("Zero Cloud Exfiltration", "100% offline air-gapped retrieval ensures private documents never leak."),
        ("Source-Grounded Citations", "Answers display exact file title, target page number, and quoted clause."),
        ("Holiday-Aware Shifting", "Contracts shift past weekends and official public holidays via API."),
        ("Universal Search (Ctrl+K)", "Instant fuzzy search across filenames, metadata, and extracted text.")
    ]

    build_evidence_slide(
        prs, 10,
        "09 / INTELLIGENCE & GOVERNANCE EVIDENCE",
        "Air-Gapped AI Assistant & Compliance Calendar",
        "Offline-first neural vector search with verified source attribution and holiday-aware deadline management.",
        "DocuVault — Explainable AI Assistant [Document Intelligence RAG]", img1,
        "DocuVault — Deadlines, Calendar Shifting & iCal Export", img2,
        metrics
    )


# =============================================================================
# SLIDE 11: TEST MATRIX & EVALUATION (ONE UNIFIED MATRIX CONSOLE)
# =============================================================================
def build_slide_11_evaluation(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "10 / TESTING & VERIFICATION",
        "Empirical Test Matrix & Demonstration Outcomes",
        "Verified outcomes from controlled test scenarios conducted during the capstone application demonstration."
    )

    panel_top = Inches(1.85)
    panel_h = Inches(4.9)
    panel_w = Inches(11.733)
    add_unified_panel(slide, Inches(0.8), panel_top, panel_w, panel_h)

    # Test Matrix Table inside the unified panel
    table_shape = slide.shapes.add_table(6, 5, Inches(1.0), panel_top + Inches(0.15), panel_w - Inches(0.4), Inches(3.6))
    table = table_shape.table

    table.columns[0].width = Inches(2.2)
    table.columns[1].width = Inches(2.4)
    table.columns[2].width = Inches(2.8)
    table.columns[3].width = Inches(2.7)
    table.columns[4].width = Inches(1.233)

    headers = ["Test Scenario", "Test Procedure", "Expected Technical Result", "Demonstrated Result", "Status"]
    for col_idx, h_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(22, 22, 32)
        p = cell.text_frame.paragraphs[0]
        p.text = h_text
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = ORANGE

    rows = [
        ("Document Ingestion & Magic-Bytes", "Import valid PDF and disguised .exe/.bat binary", "Magic-byte inspection validates binary header; rejects spoofed extensions", "Validated 42 authentic documents; correctly blocked disguised payload", "PASSED"),
        ("Cryptographic Integrity Check", "Execute full integrity scan across stored documents", "Live SHA-256 hashes match stored MongoDB database digests", "42/42 hashes verified authentic; 100/100 health score maintained", "PASSED"),
        ("Explainable AI Vector Search", "Submit query: 'What is the governing law of the agreement?'", "TF-IDF cosine similarity retrieves relevant passage with citations", "Returned 'State of Delaware' clause with Mutual_NDA.pdf page 1 citation", "PASSED"),
        ("Duplicate & Near-Duplicate Check", "Ingest exact copy and slightly edited revision of existing doc", "Zero-overhead hash match flags exact duplicate; difflib rates similarity", "Identified exact duplicate via SHA-256; flagged 94% text similarity", "PASSED"),
        ("Activity Audit Trail & Export", "Perform file ingestion, view document, and export session log", "Events logged with timestamp, user session, and operation type to CSV", "All events recorded chronologically; successfully exported audit CSV", "PASSED")
    ]

    for row_idx, r_data in enumerate(rows, start=1):
        bg = RGBColor(16, 16, 24) if row_idx % 2 == 1 else RGBColor(12, 12, 18)
        for col_idx, text in enumerate(r_data):
            cell = table.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            p = cell.text_frame.paragraphs[0]
            p.text = text
            p.font.name = "Segoe UI"
            p.font.size = Pt(9)
            if col_idx == 4:
                p.font.bold = True
                p.font.color.rgb = GREEN
                p.alignment = PP_ALIGN.CENTER
            elif col_idx == 0:
                p.font.bold = True
                p.font.color.rgb = WHITE
            else:
                p.font.color.rgb = TEXT_SECONDARY

    # Integrated Findings Strip at bottom of table
    add_hdivider(slide, Inches(1.0), panel_top + Inches(3.95), panel_w - Inches(0.4))

    tb_eval = slide.shapes.add_textbox(Inches(1.05), panel_top + Inches(4.05), panel_w - Inches(0.5), Inches(0.75))
    tf_e = tb_eval.text_frame
    tf_e.word_wrap = True
    tf_e.margin_left = Inches(0); tf_e.margin_right = Inches(0); tf_e.margin_top = Inches(0); tf_e.margin_bottom = Inches(0)
    p = tf_e.paragraphs[0]
    p.text = "SECTION 8.2 RESULTS SUMMARY & VERIFICATION FINDINGS"
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = ORANGE

    p = tf_e.add_paragraph()
    p.text = (
        "During live project evaluation, the system successfully demonstrated continuous document workspace management, "
        "cryptographic health verification, and granular activity monitoring. The test corpus of 42 authentic documents was processed "
        "with zero unhandled exceptions under Python 3.12, maintaining a 100/100 health score with zero false-positive warnings."
    )
    p.font.name = "Segoe UI"
    p.font.size = Pt(9)
    p.font.color.rgb = TEXT_SECONDARY

    add_footer(slide, 11)


# =============================================================================
# SLIDE 12: CONCLUSION, LIMITATIONS & FUTURE ROADMAP (ONE 3-COLUMN BOARD)
# =============================================================================
def build_slide_12_conclusion(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "11 / SUMMARY & ROADMAP",
        "Conclusion, Project Limitations & Future Roadmap",
        "Synthesizing key engineering outcomes, practical operational boundaries, and future research vectors."
    )

    panel_top = Inches(1.85)
    panel_h = Inches(4.9)
    panel_w = Inches(11.733)
    add_unified_panel(slide, Inches(0.8), panel_top, panel_w, panel_h)

    col3_w = panel_w / 3
    add_vdivider(slide, Inches(0.8) + col3_w, panel_top, panel_h)
    add_vdivider(slide, Inches(0.8) + col3_w * 2, panel_top, panel_h)

    sections = [
        {
            "tag": "01 / CONCLUSION",
            "title": "Project Conclusion",
            "color": ORANGE,
            "bullets": [
                "DocuVault successfully combines cryptographic file validation, automated classification, and explainable TF-IDF AI retrieval into a cohesive Python application.",
                "Bridges document security with accessible, citation-grounded intelligence.",
                "Directly advances SDG 16 (Peace, Justice & Strong Institutions) by promoting tamper-proof record keeping and accountable governance.",
                "Successfully validates the modular 5-tier architecture across live demonstrations."
            ]
        },
        {
            "tag": "02 / LIMITATIONS",
            "title": "Technical Limitations",
            "color": BLUE,
            "bullets": [
                "Identified real-world constraints for transparent academic reporting:",
                "OCR Variance: Text extraction accuracy may degrade on low-resolution, blurred, or degraded scanned documents.",
                "Similarity Thresholds: Near-duplicate detection requires manual calibration depending on document genre.",
                "Offline Scope: Advanced cloud mirroring and subscription features are gated in demonstration mode."
            ]
        },
        {
            "tag": "03 / ROADMAP",
            "title": "Future Engineering Roadmap",
            "color": GREEN,
            "bullets": [
                "Strategic enhancements planned for subsequent development iterations:",
                "Transformer OCR: Integrate multi-modal vision models (TrOCR / Donut) for handwritten manuscripts.",
                "Mobile Companion: Cross-platform Flutter / React Native client syncing via Flask REST APIs.",
                "Multi-Tenant RBAC: Role-based access control with Keycloak enterprise federation.",
                "Blockchain Notarization: Decentralized smart contract hashing for cross-institutional legal proof."
            ]
        }
    ]

    for i, sec in enumerate(sections):
        x = Inches(0.8) + col3_w * i + Inches(0.2)
        tb = slide.shapes.add_textbox(x, panel_top + Inches(0.15), col3_w - Inches(0.4), panel_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0); tf.margin_right = Inches(0); tf.margin_top = Inches(0); tf.margin_bottom = Inches(0)

        p = tf.paragraphs[0]
        p.text = sec["tag"]
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = sec["color"]

        p_t = tf.add_paragraph()
        p_t.text = sec["title"]
        p_t.font.name = "Segoe UI"
        p_t.font.size = Pt(14)
        p_t.font.bold = True
        p_t.font.color.rgb = WHITE

        p_space = tf.add_paragraph()
        p_space.text = "—" * 24
        p_space.font.name = "Segoe UI"
        p_space.font.size = Pt(8)
        p_space.font.color.rgb = PANEL_BORDER

        for b in sec["bullets"]:
            p = tf.add_paragraph()
            p.text = f"•  {b}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(9.5)
            p.font.color.rgb = TEXT_SECONDARY

    add_footer(slide, 12)


# =============================================================================
# SLIDE 13: CLOSING & Q&A (ONE UNIFIED SHOWCASE CONSOLE)
# =============================================================================
def build_slide_13_qa(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)

    # Hero top
    logo_path = r"d:\Programming\Projects\DocuVault\assets\logo.png"
    if os.path.exists(logo_path):
        slide.shapes.add_picture(logo_path, Inches(0.8), Inches(0.8), Inches(0.85), Inches(0.85))

    tb_hero = slide.shapes.add_textbox(Inches(1.85), Inches(0.75), Inches(10.5), Inches(1.2))
    tf_h = tb_hero.text_frame
    p = tf_h.paragraphs[0]
    p.text = "DocuVault — Demonstration Complete"
    p.font.name = "Segoe UI"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE

    p_sub = tf_h.add_paragraph()
    p_sub.text = "Questions & Technical Discussion • Christ University Pune, Lavasa"
    p_sub.font.name = "Segoe UI"
    p_sub.font.size = Pt(13)
    p_sub.font.bold = True
    p_sub.font.color.rgb = ORANGE

    # ONE unified closing board
    panel_top = Inches(2.1)
    panel_h = Inches(4.65)
    panel_w = Inches(11.733)
    add_unified_panel(slide, Inches(0.8), panel_top, panel_w, panel_h)

    mid_x = Inches(0.8) + panel_w / 2
    add_vdivider(slide, mid_x, panel_top, panel_h)

    half_w = panel_w / 2 - Inches(0.55)

    # Left: Core achievements
    tb_l = slide.shapes.add_textbox(Inches(1.05), panel_top + Inches(0.2), half_w, panel_h - Inches(0.4))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = Inches(0); tf_l.margin_right = Inches(0); tf_l.margin_top = Inches(0); tf_l.margin_bottom = Inches(0)
    p = tf_l.paragraphs[0]
    p.text = "KEY PROJECT ACHIEVEMENTS"
    p.font.name = "Segoe UI"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ORANGE

    achievements = [
        "100% Cryptographic Health: SHA-256 fingerprinting baseline across 42 files with 0 tampering.",
        "Air-Gapped Vector Retrieval: In-memory TF-IDF sparse matrix with 0.12 s query latency.",
        "Verifiable Source Attribution: Every answer paired with exact document title and page number.",
        "Proactive Governance: Public-holiday deadline shifting engine and regex PII redaction.",
        "Full Curriculum Synthesis: Concrete implementations across Units 1–5 of Advanced Python."
    ]
    for a in achievements:
        p = tf_l.add_paragraph()
        p.text = f"✓  {a}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_SECONDARY

    # Right: Repository Details & Acknowledgements
    tb_r = slide.shapes.add_textbox(mid_x + Inches(0.3), panel_top + Inches(0.2), half_w, panel_h - Inches(0.4))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = Inches(0); tf_r.margin_right = Inches(0); tf_r.margin_top = Inches(0); tf_r.margin_bottom = Inches(0)
    p = tf_r.paragraphs[0]
    p.text = "REPOSITORY SPECIFICATIONS & CREDITS"
    p.font.name = "Segoe UI"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ORANGE

    p = tf_r.add_paragraph()
    p.text = "Source Repository Architecture"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p = tf_r.add_paragraph()
    p.text = "•  Desktop Client: PyQt6 6.6.0+ (Custom dark stylesheet)\n•  REST Backend: Flask 3.0.0+ with CORS microservices\n•  Persistence: Hybrid SQLite3 + MongoDB + local filesystem\n•  Web Analytics: Streamlit 1.30.0+ with Plotly charts"
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_SECONDARY

    p = tf_r.add_paragraph()
    p.text = "Acknowledgements & Guidance"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p = tf_r.add_paragraph()
    p.text = "Special thanks to Prof. Rohit Gupta for mentorship and evaluation during the Advanced Python Capstone development lifecycle."
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_SECONDARY

    add_footer(slide, 13)


# =============================================================================
# EXPORT ENGINE: PPTX TO NATIVE VECTOR PDF
# =============================================================================
def export_pptx_to_pdf(pptx_path: str, pdf_path: str):
    """Exports PPTX to PDF via PowerPoint COM automation on Windows."""
    abs_pptx = os.path.abspath(pptx_path)
    abs_pdf = os.path.abspath(pdf_path)

    ps_code = f"""
$ErrorActionPreference = 'Stop'
try {{
    $ppt = New-Object -ComObject PowerPoint.Application
    $pres = $ppt.Presentations.Open('{abs_pptx}', [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    $pres.SaveAs('{abs_pdf}', 32)
    $pres.Close()
    $ppt.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
    Write-Output "SUCCESS"
}} catch {{
    Write-Error $_
    exit 1
}}
"""
    tmp_ps = Path("temp_export.ps1")
    tmp_ps.write_text(ps_code, encoding="utf-8")
    try:
        res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(tmp_ps)], capture_output=True, text=True, check=True)
        print("PowerPoint COM PDF export completed successfully.")
    finally:
        if tmp_ps.exists():
            tmp_ps.unlink()


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    print("Building Slide 01: Cover Slide...")
    build_slide_01_cover(prs)

    print("Building Slide 02: Problem Statement (Unified Console)...")
    build_slide_02_problem(prs)

    print("Building Slide 03: Architectural Objectives (Unified 4-Pillars)...")
    build_slide_03_objectives(prs)

    print("Building Slide 04: SDG Alignment (Unified Dual-Focus Panel)...")
    build_slide_04_sdg(prs)

    print("Building Slide 05: 6-Stage Pipeline & 5-Tier Layers...")
    build_slide_05_architecture(prs)

    print("Building Slide 06: Production Software Stack & Curriculum Mapping...")
    build_slide_06_tech_stack(prs)

    print("Building Slide 07: Core Feature Highlights & Security Safeguards...")
    build_slide_07_core_features(prs)

    print("Building Slide 08: Evidence — Workspace & Storage Tracking...")
    build_slide_08_evidence_workspace(prs)

    print("Building Slide 09: Evidence — Security Forensics & Audit Trail...")
    build_slide_09_evidence_security(prs)

    print("Building Slide 10: Evidence — AI Assistant & Compliance Calendar...")
    build_slide_10_evidence_ai(prs)

    print("Building Slide 11: Empirical Test Matrix & Verification Outcomes...")
    build_slide_11_evaluation(prs)

    print("Building Slide 12: Conclusion, Limitations & Future Roadmap...")
    build_slide_12_conclusion(prs)

    print("Building Slide 13: Summary & Q&A...")
    build_slide_13_qa(prs)

    pptx_path = r"d:\Programming\Projects\DocuVault\DocuVault_Presentation.pptx"
    pdf_path = r"d:\Programming\Projects\DocuVault\DocuVault_Presentation.pdf"

    prs.save(pptx_path)
    print(f"Presentation saved to: {pptx_path}")

    print("Exporting presentation to native vector PDF...")
    try:
        export_pptx_to_pdf(pptx_path, pdf_path)
        print(f"PDF successfully exported to: {pdf_path}")
    except Exception as e:
        print(f"PowerPoint COM export error: {e}")


if __name__ == "__main__":
    main()
