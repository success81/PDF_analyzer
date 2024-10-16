import pikepdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import os
import logging
from decimal import Decimal
import fitz  # PyMuPDF

# Setup logging
logging.basicConfig(level=logging.INFO)

def add_mlx_to_pdf(input_pdf_path, output_pdf_path):
    try:
        with pikepdf.Pdf.open(input_pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                try:
                    # Convert dimensions to float, handling Decimal type
                    page_width = float(page.MediaBox[2]) if isinstance(page.MediaBox[2], Decimal) else page.MediaBox[2]
                    page_height = float(page.MediaBox[3]) if isinstance(page.MediaBox[3], Decimal) else page.MediaBox[3]

                    # Create a new PDF with Reportlab
                    packet = BytesIO()
                    can = canvas.Canvas(packet, pagesize=(page_width, page_height))
                    can.setFont("Helvetica", 10)
                    mlx_number = f"MLX{i+1:02d}"
                    can.drawString(30, page_height - 30, mlx_number)
                    can.save()

                    # Move to the beginning of the BytesIO buffer
                    packet.seek(0)
                    new_pdf = pikepdf.Pdf.open(packet)

                    # Overlay the new content onto the existing page
                    page.add_overlay(new_pdf.pages[0])

                except Exception as e:
                    logging.error(f"Error processing page {i + 1} of '{input_pdf_path}': {e}")
                    # If there's an error, we'll skip modifying this page

            pdf.save(output_pdf_path)

    except Exception as e:
        logging.error(f"Error processing file '{input_pdf_path}': {e}")
        # If we can't process the file at all, copy the original file to the output path
        import shutil
        shutil.copy2(input_pdf_path, output_pdf_path)

def extract_pdf_content(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        processed_content = []
        for i in range(len(doc)):
            try:
                page = doc[i]
                text = page.get_text()
                if not text.strip():
                    text = "No extractable text on this page."
                mlx_number = f"MLX{i+1:02d}"
                processed_content.append(f"{mlx_number}\n\n{text}")
            except Exception as e:
                logging.error(f"Error extracting content from page {i + 1} of '{pdf_path}': {e}")
                processed_content.append(f"Error extracting text from page {i+1}.\n\n")
        doc.close()
        return "\n\n".join(processed_content)
    except Exception as e:
        logging.error(f"Error processing file '{pdf_path}': {e}")
        return f"Error processing file. Please check if '{os.path.basename(pdf_path)}' is a valid PDF."
