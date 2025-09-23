import fitz  # PyMuPDF
from tkinter import filedialog
import pdfplumber
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pdf_path = filedialog.askopenfilename(
    title="Selecciona el archivo PDF",
    filetypes=[("Archivos PDF", "*.pdf")]
)

if not pdf_path:
    print("❌ No se seleccionó ningún archivo.")
    exit()

print(f"Archivo PDF que se va a abrir: {pdf_path}")


with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages, start=1):
        im = page.to_image(resolution=300).original
        texto = pytesseract.image_to_string(im, lang="eng")
        print(f"--- Página {i} ---")
        print(texto[:500])