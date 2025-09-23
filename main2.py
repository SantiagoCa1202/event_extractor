import pdfplumber
import tkinter as tk
from tkinter import filedialog
import os
import fitz  # PyMuPDF

import pytesseract
from PIL import Image
import io
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extraer_texto_de_pdf(ruta_pdf):
    """
    Extrae texto de un PDF. Si no hay texto, intenta OCR en las páginas.

    Args:
        ruta_pdf (str): La ruta al archivo PDF.

    Returns:
        str: El texto extraído, incluyendo el texto de OCR.
    """
    if not os.path.exists(ruta_pdf):
        return f"Error: El archivo no se encontró en la ruta: '{ruta_pdf}'."
        
    texto_completo = ""
    try:
        documento = fitz.open(ruta_pdf)
        
        for num_pagina in range(len(documento)):
            pagina = documento.load_page(num_pagina)
            
            # 1. Intentar extracción de texto normal
            texto_de_la_pagina = pagina.get_text()
            
            if texto_de_la_pagina.strip() == "":
                # 2. Si no hay texto, intentar OCR
                print(f"Página {num_pagina + 1}: No se encontró texto. Intentando OCR...")
                
                # Renderizar la página como imagen (PixMap)
                pixmap = pagina.get_pixmap(dpi=300)
                imagen = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                
                # Aplicar OCR a la imagen
                texto_de_la_pagina = pytesseract.image_to_string(imagen, lang='eng') # 'spa' para español
                
            texto_completo += texto_de_la_pagina
            
        documento.close()
        
    except pytesseract.pytesseract.TesseractNotFoundError:
        return "Error: No se encontró el motor de Tesseract. Asegúrate de que esté instalado y en tu PATH."
    except Exception as e:
        return f"Ocurrió un error inesperado al procesar el archivo: {e}"
        
    return texto_completo


# Inicializar Tkinter para el diálogo de selección de archivo
root = tk.Tk()
root.withdraw() # Ocultar la ventana principal de Tkinter

# Abrir el diálogo para seleccionar un archivo PDF
pdf_file_path = filedialog.askopenfilename(
    title="Selecciona un archivo PDF",
    filetypes=[("Archivos PDF", "*.pdf")]
)

# Verificar si se seleccionó un archivo
if pdf_file_path:
    print(f"Archivo seleccionado: {pdf_file_path}")
    
    # Llamar a la función para extraer el texto
    document_text = extraer_texto_de_pdf(pdf_file_path)
    
    # Imprimir el texto extraído
    print("\n--- Texto extraído del PDF ---")
    print(document_text)
else:
    print("❌ No se seleccionó ningún archivo.")