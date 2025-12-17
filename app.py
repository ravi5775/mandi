from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import shutil
import os
import tempfile
from question_paper_generator import parse_question_bank_from_text, generate_question_paper, create_zip, extract_text_from_pdf

app = Flask(__name__)
app.secret_key = 'replace-this-with-a-secure-key'

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    subject_name = request.form.get('subject') or 'Subject'
    try:
        num_papers = int(request.form.get('num_papers', 9))
    except ValueError:
        num_papers = 9

    uploaded_file = request.files.get('file')
    if not uploaded_file:
        flash('No file uploaded. Please upload a .txt or .pdf question bank.')
        return redirect(url_for('home'))

    # Save uploaded file
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, uploaded_file.filename)
    uploaded_file.save(file_path)

    # If PDF, extract text
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext == '.pdf':
        try:
            text = extract_text_from_pdf(file_path)
        except Exception as e:
            flash('Failed to extract text from PDF: ' + str(e))
            return redirect(url_for('home'))
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

    # Parse units and questions
    units = parse_question_bank_from_text(text)
    if not units:
        flash('Could not parse any units/questions from the uploaded file. Ensure it follows the sample format.')
        return redirect(url_for('home'))

    # Generate papers in an output folder inside the project for download
    output_dir = os.path.join(os.getcwd(), 'output')
    if os.path.exists(output_dir):
        # clear previous outputs
        try:
            for name in os.listdir(output_dir):
                path = os.path.join(output_dir, name)
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
        except Exception:
            pass
    os.makedirs(output_dir, exist_ok=True)

    pdf_files = []
    # create papers
    for i in range(1, num_papers + 1):
        pdf_files.append(generate_question_paper(units, i, subject_name, output_dir=output_dir))

    zip_path = create_zip(pdf_files, output_dir=output_dir)
    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
