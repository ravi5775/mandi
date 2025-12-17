import re
import random
import os
import zipfile

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Try to import pdf extraction library
try:
    import pdfplumber
except Exception:
    pdfplumber = None


# --------------------------------------------------
# PDF TEXT EXTRACTION
# --------------------------------------------------
def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file using pdfplumber."""
    if pdfplumber is None:
        raise RuntimeError("pdfplumber is not installed")

    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


# --------------------------------------------------
# QUESTION BANK PARSING
# --------------------------------------------------
def parse_question_bank_from_text(text):
    """
    Parse question bank text into:
    {
        "Unit I - Title": {
            "A": [q1, q2, ...],
            "B": [q1, q2, ...]
        }
    }
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("—", "-").replace("–", "-")

    units = {}

    # Split by Unit headings
    unit_blocks = re.split(r'(?m)^(Unit\s+.*)$', text)

    it = iter(unit_blocks)
    for part in it:
        if not part.strip():
            continue

        if part.lower().startswith("unit"):
            unit_title = part.strip()
            content = next(it, "")

            # Extract Section A
            a_match = re.search(
                r'(?i)section\s*a.*?\n(.*?)(?=section\s*b|$)',
                content,
                re.S
            )

            # Extract Section B
            b_match = re.search(
                r'(?i)section\s*b.*?\n(.*)',
                content,
                re.S
            )

            a_questions = []
            b_questions = []

            if a_match:
                a_questions = [
                    re.sub(r'^\d+[\).\s]*', '', q).strip()
                    for q in re.split(r'\n+', a_match.group(1))
                    if q.strip()
                ]

            if b_match:
                b_questions = [
                    re.sub(r'^\d+[\).\s]*', '', q).strip()
                    for q in re.split(r'\n+', b_match.group(1))
                    if q.strip()
                ]

            if a_questions and b_questions:
                units[unit_title] = {
                    "A": a_questions,
                    "B": b_questions
                }

    return units


# --------------------------------------------------
# PDF GENERATION
# --------------------------------------------------
def generate_question_paper(units, set_number, subject_name, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)

    pdf_path = os.path.join(
        output_dir, f"Question_Paper_Set_{set_number}.pdf"
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TitleCenter", parent=styles["Title"], alignment=1
    ))
    styles.add(ParagraphStyle(
        name="HeadingCenter", parent=styles["Heading2"], alignment=1
    ))
    styles.add(ParagraphStyle(
        name="BodyJustify", parent=styles["BodyText"], leading=14
    ))

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    story = []

    # Header
    story.append(Paragraph(
        f"{subject_name} – Question Paper",
        styles["TitleCenter"]
    ))
    story.append(Paragraph(
        f"Set {set_number}",
        styles["HeadingCenter"]
    ))
    story.append(Spacer(1, 0.3 * inch))

    # ---------------- SECTION A ----------------
    story.append(Paragraph(
        "Section A – (2 Marks Each)",
        styles["Heading2"]
    ))

    q_no = 1
    for unit, sections in units.items():
        pool = sections["A"]
        selected = random.sample(pool, min(2, len(pool)))

        while len(selected) < 2:
            selected.append(random.choice(pool))

        for q in selected:
            story.append(
                Paragraph(f"{q_no}. {q}", styles["BodyJustify"])
            )
            q_no += 1

    story.append(Spacer(1, 0.4 * inch))

    # ---------------- SECTION B ----------------
    story.append(Paragraph(
        "Section B – (8 Marks Each)",
        styles["Heading2"]
    ))

    q_no = 11
    for unit, sections in units.items():
        pool = sections["B"]
        selected = random.sample(pool, min(2, len(pool)))

        while len(selected) < 2:
            selected.append(random.choice(pool))

        story.append(
            Paragraph(f"{q_no}. (a) {selected[0]}", styles["BodyJustify"])
        )
        story.append(
            Paragraph("     OR", styles["BodyJustify"])
        )
        story.append(
            Paragraph(f"     (b) {selected[1]}", styles["BodyJustify"])
        )
        story.append(Spacer(1, 0.25 * inch))

        q_no += 1

    doc.build(story)
    return pdf_path


# --------------------------------------------------
# ZIP CREATION
# --------------------------------------------------
def create_zip(pdf_files, output_dir="output", zip_name="Question_Papers.zip"):
    zip_path = os.path.join(output_dir, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in pdf_files:
            zf.write(file_path, os.path.basename(file_path))

    return zip_path
