\
    import re, random, os, zipfile
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

    # Try to import pdf extraction library; used by app.py when needed.
    try:
        import pdfplumber
    except Exception:
        pdfplumber = None

    def extract_text_from_pdf(pdf_path):
        \"\"\"Extract text from a PDF file using pdfplumber when available, else raise an error.\"\"\"
        if pdfplumber is None:
            raise RuntimeError('pdfplumber is not installed. Please install requirements from requirements.txt')
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or '')
        return '\\n'.join(text_parts)

    def parse_question_bank_from_text(text):
        \"\"\"Parse text of a question bank into a dictionary: {Unit Title: {'A': [...], 'B': [...]}}\"\"\"
        # Normalize dashes and whitespace
        text = text.replace('\\r\\n', '\\n').replace('\\r', '\\n')
        text = text.replace('—', '-').replace('–', '-')

        # Split by occurrences of lines starting with 'Unit'
        unit_splits = re.split(r'(?m)^(Unit\\s+[IVXLC]+\\s*-.*)$', text)
        units = {}
        if len(unit_splits) < 2:
            # fallback: try splitting by 'Unit ' without roman numerals
            unit_splits = re.split(r'(?m)^(Unit\\s+.*)$', text)
        # unit_splits will be like ['', 'Unit I - title', 'content', 'Unit II - title', 'content', ...]
        it = iter(unit_splits)
        for part in it:
            if part.strip() == '':
                continue
            # part is unit title if it starts with 'Unit'
            if part.strip().lower().startswith('unit'):
                title = part.strip()
                try:
                    content = next(it)
                except StopIteration:
                    content = ''
                # Extract Section A and Section B
                a_match = re.search(r'Section\\s*A\\s*-.*?\\n(.*?)(?=Section\\s*B\\s*-|$)', content, re.S | re.I)
                b_match = re.search(r'Section\\s*B\\s*-.*?\\n(.*?)(?=(?:Unit\\s+|$))', content, re.S | re.I)
                a_qs = []
                b_qs = []
                if a_match:
                    a_qs = [line.strip() for line in re.split(r'\\n+', a_match.group(1)) if line.strip() and not re.match(r'^[0-9]+\\.', line.strip())==False or line.strip()]
                    # further clean numeric prefixes like '1. ' or '1) '
                    a_qs = [re.sub(r'^[0-9]+[\\)\\.]\\s*', '', q).strip() for q in a_qs if q.strip()]
                if b_match:
                    b_qs = [line.strip() for line in re.split(r'\\n+', b_match.group(1)) if line.strip() and not re.match(r'^[0-9]+\\.', line.strip())==False or line.strip()]
                    b_qs = [re.sub(r'^[0-9]+[\\)\\.]\\s*', '', q).strip() for q in b_qs if q.strip()]
                # fallback: if regex fails, try naive split by lines
                if not a_qs or not b_qs:
                    # try to find lines starting with digits in the content and split by 'Section B' marker
                    if 'section b' in content.lower():
                        parts = re.split(r'(?i)section\\s*b', content)
                        a_section = parts[0]
                        b_section = parts[1] if len(parts) > 1 else ''
                        a_qs = [re.sub(r'^[0-9]+[\\)\\.]\\s*', '', l).strip() for l in re.findall(r'^[0-9]+[\\)\\.]\\s*(.*)', a_section, re.M)]
                        b_qs = [re.sub(r'^[0-9]+[\\)\\.]\\s*', '', l).strip() for l in re.findall(r'^[0-9]+[\\)\\.]\\s*(.*)', b_section, re.M)]
                if a_qs and b_qs:
                    units[title] = {'A': a_qs, 'B': b_qs}
        # If still empty, try an alternate parsing: split by 'Unit' lines manually
        if not units:
            # naive approach: find headings like 'Unit I' and collect until next 'Unit'
            for match in re.finditer(r'(?m)^(Unit\\b.*)$', text):
                start = match.start()
                # find next unit
                next_match = re.search(r'(?m)^Unit\\b', text[match.end():])
                end = match.end() + next_match.start() if next_match else len(text)
                block = text[match.start():end]
                title_line = block.splitlines()[0].strip()
                a_qs = re.findall(r'(?i)section\\s*a[\\s\\S]*?^(?=section\\s*b|$)', block, re.M)
                # skip complex fallback for brevity
            # We keep units as found

        return units

    def generate_question_paper(units, set_number, subject_name, output_dir='output'):
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, f\"Question_Paper_Set_{set_number}.pdf\")

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='TitleCenter', parent=styles['Title'], alignment=1))
        styles.add(ParagraphStyle(name='Heading2Center', parent=styles['Heading2'], alignment=1))
        styles.add(ParagraphStyle(name='BodyTextJustify', parent=styles['BodyText'], leading=14))

        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                rightMargin=40, leftMargin=40,
                                topMargin=40, bottomMargin=40)
        story = []

        story.append(Paragraph(f\"{subject_name} – Question Paper\", styles['TitleCenter']))
        story.append(Paragraph(f\"Set {set_number}\", styles['Heading2Center']))
        story.append(Spacer(1, 0.2 * inch))

        # SECTION A: pick 2 from each unit
        story.append(Paragraph(\"Section A – (2 Marks Each)\", styles['Heading2']))
        all_A_questions = []
        for unit_title, sections in units.items():
            # ensure at least 2 questions exist
            pool = sections.get('A', [])
            if len(pool) < 2:
                # if not enough, repeat or take all
                selected = pool[:] + (pool[:] if pool else [])
                selected = (selected * 2)[:2]
            else:
                selected = random.sample(pool, 2)
            all_A_questions.extend(selected)

        for i, q in enumerate(all_A_questions, 1):
            story.append(Paragraph(f\"{i}. {q}\", styles['BodyTextJustify']))

        story.append(Spacer(1, 0.3 * inch))

        # SECTION B: either/or pairs (without unit labels)
        story.append(Paragraph(\"Section B – (8 Marks Each)\", styles['Heading2']))
        q_no = 11
        for unit_title, sections in units.items():
            pool = sections.get('B', [])
            if len(pool) < 2:
                selected = pool[:] + (pool[:] if pool else [])
                selected = (selected * 2)[:2]
            else:
                selected = random.sample(pool, 2)
            story.append(Paragraph(f\"{q_no}. (a) {selected[0]}\", styles['BodyTextJustify']))
            story.append(Paragraph(\"     OR\", styles['BodyTextJustify']))
            story.append(Paragraph(f\"     (b) {selected[1]}\", styles['BodyTextJustify']))
            story.append(Spacer(1, 0.2 * inch))
            q_no += 1

        doc.build(story)
        return pdf_path

    def create_zip(pdf_files, output_dir='output', zip_name='Question_Papers.zip'):
        zip_path = os.path.join(output_dir, zip_name)
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for f in pdf_files:
                zf.write(f, os.path.basename(f))
        return zip_path
