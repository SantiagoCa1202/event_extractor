import fitz
import re

from event_functions import EVENT_FUNCTION_REGEX_FRAGMENT, FUNCTION_KEYWORDS
from food_dictionary import cold_items, hot_items, type_events_items


cabecera_evento_regex = re.compile(
    r"(?P<time>\d{1,2}:\d{2}\s*[AP]M)\s+"
    rf"(?P<function>{EVENT_FUNCTION_REGEX_FRAGMENT})\b",
    re.IGNORECASE,
)

schedule_regex = re.compile(
    r"(?P<time>\d{1,2}:\d{2}\s*[AP]M\s*-\s*\d{1,2}:\d{2}\s*[AP]M)\s+"
    rf"(?P<function>{EVENT_FUNCTION_REGEX_FRAGMENT})\s+"
    r"(?P<room>.+?)\s+"
    r"(?P<gtd>\d+)\s*;?\s*$",
    re.IGNORECASE,
)

event_order_regex = re.compile(r"Event Order\s*#\s*[:#]?\s*(\d+)", re.IGNORECASE)
function_date_regex = re.compile(r"FUNCTION DAY/DATE:\s*(.+)", re.IGNORECASE)

FUNCIONES_VALIDAS = FUNCTION_KEYWORDS

HOT_ITEMS_LOWER = [item.lower() for item in hot_items]
COLD_ITEMS_LOWER = [item.lower() for item in cold_items]
TYPE_EVENTS_LOWER = [item.lower() for item in type_events_items]


def _highlight_line(page, line, color):
    if not line["spans"]:
        return
    x0 = min(span["bbox"][0] for span in line["spans"])
    y0 = min(span["bbox"][1] for span in line["spans"])
    x1 = max(span["bbox"][2] for span in line["spans"])
    y1 = max(span["bbox"][3] for span in line["spans"])
    rect = fitz.Rect(x0, y0, x1, y1)
    annot = page.add_highlight_annot(rect)
    annot.set_colors(stroke=color)
    annot.update()


def subrayar_pdf_por_categoria(ruta_pdf_entrada, ruta_pdf_salida):
    doc = fitz.open(ruta_pdf_entrada)
    paginas_a_eliminar = []

    for page_index, page in enumerate(doc):
        pagina_tiene_evento = False
        pagina_tiene_funcion_valida = False
        pagina_tiene_comida = False
        eliminar_por_no_food = False

        page_text = page.get_text("text")

        match_event = event_order_regex.search(page_text)
        if match_event:
            numero = match_event.group(1)
            for rect in page.search_for(numero):
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=(0.7, 1, 0.7))
                annot.update()

        match_date = function_date_regex.search(page_text)
        if match_date:
            fecha = match_date.group(1).strip()
            for rect in page.search_for(fecha):
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=(0.7, 1, 0.7))
                annot.update()

        blocks = page.get_text("dict")["blocks"]
        buffer_lineas = []

        for block in blocks:
            if block["type"] != 0:
                continue

            for line in block["lines"]:
                texto_linea = " ".join(span["text"] for span in line["spans"]).strip()
                if not texto_linea:
                    continue

                texto_linea_lower = texto_linea.lower()
                buffer_lineas.append((texto_linea, line))
                if len(buffer_lineas) > 5:
                    buffer_lineas.pop(0)

                if any(func in texto_linea_lower for func in FUNCIONES_VALIDAS):
                    pagina_tiene_funcion_valida = True

                if any(item in texto_linea_lower for item in HOT_ITEMS_LOWER + COLD_ITEMS_LOWER + TYPE_EVENTS_LOWER):
                    pagina_tiene_comida = True

                if "no food or beverage required at this time" in texto_linea_lower:
                    eliminar_por_no_food = True

                for n in range(1, len(buffer_lineas) + 1):
                    texto_combinado = " ".join(t for t, _ in buffer_lineas[-n:])
                    if schedule_regex.match(texto_combinado):
                        pagina_tiene_evento = True
                        for _, buffered_line in buffer_lineas[-n:]:
                            _highlight_line(page, buffered_line, (0.7, 1, 0.7))
                        break

                color = None
                if any(item in texto_linea_lower for item in HOT_ITEMS_LOWER):
                    color = (1, 0.6, 0.6)
                elif any(item in texto_linea_lower for item in COLD_ITEMS_LOWER):
                    color = (0.6, 0.85, 1)
                elif any(item in texto_linea_lower for item in TYPE_EVENTS_LOWER):
                    color = (0.8, 0.6, 0.9)
                elif cabecera_evento_regex.match(texto_linea):
                    pagina_tiene_evento = True
                    pagina_tiene_funcion_valida = True
                    color = (0.7, 1, 0.7)

                if color:
                    _highlight_line(page, line, color)

        if not (pagina_tiene_evento or pagina_tiene_funcion_valida or pagina_tiene_comida) or eliminar_por_no_food:
            paginas_a_eliminar.append(page_index)

    for i in reversed(paginas_a_eliminar):
        doc.delete_page(i)

    doc.save(ruta_pdf_salida)
    doc.close()
