import os
import json
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
from pdf_processor import add_mlx_to_pdf, extract_pdf_content
from ai_caller import call_ai_model
from fpdf import FPDF

# Setup logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Set the temporary folder for file uploads
UPLOAD_FOLDER = '/tmp'  # Changed to /tmp
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set the maximum allowed payload to 32MB (max for App Engine Standard)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    uploaded_files = request.files.getlist("file[]")
    filenames = []
    for file in uploaded_files:
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(original_path)
            # Add MLX numbers to the PDF
            mlx_filename = f"MLX_{filename}"
            mlx_path = os.path.join(app.config['UPLOAD_FOLDER'], mlx_filename)
            add_mlx_to_pdf(original_path, mlx_path)
            # Remove the original file and keep the MLX version
            os.remove(original_path)
            filenames.append(mlx_filename)
    return jsonify({"message": "Files uploaded and processed successfully", "files": filenames})

@app.route('/delete_pdf', methods=['POST'])
def delete_pdf():
    filename = request.json['filename']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"message": f"{filename} deleted successfully"})
    return jsonify({"error": "File not found"})

@app.route('/process', methods=['POST'])
def process_questions():
    files = json.loads(request.form.get('files'))
    questions = request.form.get('questions').split('|')
    results = []
    for file in files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
        if os.path.exists(file_path):
            pdf_content = extract_pdf_content(file_path)
            answers = []
            for question in questions:
                try:
                    answer = call_ai_model(pdf_content, question.strip())
                    answers.append({"question": question.strip(), "answer": answer})
                except Exception as e:
                    logging.error(f"Error processing question for file {file}: {str(e)}")
                    answers.append({"question": question.strip(), "answer": f"Error processing this question: {str(e)}"})
            results.append({"file": file, "answers": answers})
    return render_template('viewer.html', results=results)

@app.route('/pdf/<filename>')
def view_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    results = json.loads(request.form.get('results'))
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for result in results:
        pdf.cell(200, 10, txt=f"Answers for {result['file']}", ln=True, align='C')
        for qa in result['answers']:
            pdf.multi_cell(0, 10, txt=f"Q: {qa['question']}")
            pdf.multi_cell(0, 10, txt=f"A: {qa['answer']}")
            pdf.ln(10)
    pdf_output = os.path.join(app.config['UPLOAD_FOLDER'], "answers.pdf")
    pdf.output(pdf_output)
    return send_file(pdf_output, as_attachment=True)

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File is too large"}), 413

@app.errorhandler(500)
def server_error(e):
    logging.error(f"An error occurred: {str(e)}")
    return jsonify({"error": "An internal server error occurred"}), 500

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app.
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
else:
    # This is used when running on Google Cloud Run
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)