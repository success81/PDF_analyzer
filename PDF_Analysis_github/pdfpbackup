import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import os

def add_mlx_to_pdf(input_pdf_path, output_pdf_path):
    reader = PyPDF2.PdfReader(input_pdf_path)
    writer = PyPDF2.PdfWriter()

    for i, page in enumerate(reader.pages):
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica", 10)
        mlx_number = f"MLX{i+1:02d}"
        can.drawString(30, 750, mlx_number)  # Adjust position as needed
        can.save()

        packet.seek(0)
        new_pdf = PyPDF2.PdfReader(packet)
        page.merge_page(new_pdf.pages[0])
        writer.add_page(page)

    with open(output_pdf_path, "wb") as output_file:
        writer.write(output_file)

def extract_pdf_content(pdf_path):
    reader = PyPDF2.PdfReader(pdf_path)
    processed_content = []
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        mlx_number = f"MLX{i+1:02d}"
        processed_content.append(f"{mlx_number}\n\n{text}")
    
    return "\n\n".join(processed_content)