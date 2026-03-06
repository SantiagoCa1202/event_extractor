import pdfplumber
from pdf2image import convert_from_path
import pytesseract


def safe_extract_text(pdf_path: str, page_index: int) -> str:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[page_index].extract_text()
            if text and text.strip():
                return text
    except Exception as exc:
        print(f"pdfplumber failed for page {page_index + 1}: {exc}. Falling back to OCR.")

    try:
        images = convert_from_path(pdf_path, first_page=page_index + 1, last_page=page_index + 1)
        if images:
            return pytesseract.image_to_string(images[0])
    except Exception as exc:
        print(f"OCR failed for page {page_index + 1}: {exc}.")

    return ""
