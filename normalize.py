from tkinter import filedialog

# Diálogo para seleccionar archivo PDF
pdf_path = filedialog.askopenfilename(
    title="Selecciona el archivo PDF",
    filetypes=[("Archivos PDF", "*.pdf")]
)

if not pdf_path:
    print("❌ No se seleccionó ningún archivo.")
    exit()

print(f"Archivo PDF que se va a abrir: {pdf_path}")

from PyPDF2 import PdfReader, PdfWriter

reader = PdfReader(pdf_path)
writer = PdfWriter()

for page in reader.pages:
    if "/CropBox" not in page:
        page.cropbox = page.mediabox
    writer.add_page(page)

with open("fixed.pdf", "wb") as f:
    writer.write(f)
