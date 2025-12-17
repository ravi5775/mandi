# Automatic Question Paper Generator (Web)

## Overview
A small Flask web application that accepts a question bank (.txt or .pdf) and generates multiple randomized question papers in the specified format. Papers are returned as a ZIP of PDFs.

## Run locally
1. Create and activate a virtual environment (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux / macOS
   venv\Scripts\activate    # Windows
   ```
2. Install requirements
   ```bash
   pip install -r requirements.txt
   ```
3. Start the app
   ```bash
   python app.py
   ```
4. Open http://127.0.0.1:5000 in your browser.

## Notes
- The app expects the question bank to include `Unit ...`, `Section A`, and `Section B` headings. See sample file for format.
- PDF extraction requires `pdfplumber` (included in requirements).
