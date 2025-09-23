import fitz  # PyMuPDF
import re
from food_dictionary import hot_items, cold_items, type_events_items

# Regex para encabezados
cabecera_evento_regex = re.compile(
    r'(?P<time>\d{1,2}:\d{2}\s*[AP]M)\s+'
    r'(?P<function>Reception|Breakfast|Breakfast Buffet|Continental Breakfast|Lunch|Lunch Buffet|Dinner|Coffee Break|Continuous Break|Cocktail Reception|Menu Tasting)\b',
    re.IGNORECASE
)

# Regex para EO y fecha
event_order_regex = re.compile(r"Event Order\s*#\s*[:#]?\s*(\d+)", re.IGNORECASE)
function_date_regex = re.compile(r"FUNCTION DAY/DATE:\s*(.+)", re.IGNORECASE)


# Funciones válidas
FUNCIONES_VALIDAS = [
    "Reception", "Breakfast", "Breakfast Buffet", "Lunch", "Lunch Buffet",
    "Dinner", "Coffee Break", "Cocktail Reception", "Menu Tasting"
]

def subrayar_pdf_por_categoria(ruta_pdf_entrada, ruta_pdf_salida):
    doc = fitz.open(ruta_pdf_entrada)
    paginas_a_eliminar = []

    for page_index, page in enumerate(doc):
        pagina_tiene_evento = False
        pagina_tiene_funcion_valida = False
        pagina_tiene_comida = False
        eliminar_por_no_food = False

        blocks = page.get_text("dict")["blocks"]
        buffer_lineas = []

        for block in blocks:
            if block["type"] != 0:
                continue

            for line in block["lines"]:
                texto_linea = " ".join(span["text"] for span in line["spans"]).strip()
                if not texto_linea:
                    continue

                buffer_lineas.append((texto_linea, line))
                if len(buffer_lineas) > 5:
                    buffer_lineas.pop(0)

                # Detectar funciones válidas
                if any(func.lower() in texto_linea.lower() for func in FUNCIONES_VALIDAS):
                    pagina_tiene_funcion_valida = True

                # Detectar comida
                if any(item.lower() in texto_linea.lower() for item in hot_items + cold_items + type_events_items):
                    pagina_tiene_comida = True

                # Detectar la frase "No Food or Beverage Required at this Time"
                if "no food or beverage required at this time" in texto_linea.lower():
                    eliminar_por_no_food = True

                # Detectar horarios con Function
                for n in range(1, len(buffer_lineas)+1):
                    texto_combinado = " ".join(t for t, _ in buffer_lineas[-n:])
                    match_schedule = re.match(
                        r"(?P<time>\d{1,2}:\d{2}\s*[AP]M\s*[-–—]\s*\d{1,2}:\d{2}\s*[AP]M)\s+"
                        r"(?P<function>Reception|Breakfast|Breakfast Buffet|Continental Breakfast|Lunch|Lunch Buffet|Dinner|Coffee Break|Continuous Break|Cocktail Reception|Menu Tasting)\s+"
                        r"(?P<room>.+?)\s+"
                        r"(?P<gtd>\d+)\s*;?\s*$",
                        texto_combinado,
                        re.IGNORECASE
                    )
                    if match_schedule:
                        pagina_tiene_evento = True
                        color = (0.7, 1, 0.7)
                        for _, l in buffer_lineas[-n:]:
                            if l["spans"]:
                                x0 = min(span["bbox"][0] for span in l["spans"])
                                y0 = min(span["bbox"][1] for span in l["spans"])
                                x1 = max(span["bbox"][2] for span in l["spans"])
                                y1 = max(span["bbox"][3] for span in l["spans"])
                                rect = fitz.Rect(x0, y0, x1, y1)
                                annot = page.add_highlight_annot(rect)
                                annot.set_colors(stroke=color)
                                annot.update()
                        break

                # Subrayado de comida, eventos o cabeceras
                color = None
                if any(item.lower() in texto_linea.lower() for item in hot_items):
                    color = (1, 0.6, 0.6)      # rojo suave
                elif any(item.lower() in texto_linea.lower() for item in cold_items):
                    color = (0.6, 0.85, 1)     # azul claro
                elif any(item.lower() in texto_linea.lower() for item in type_events_items):
                    color = (0.8, 0.6, 0.9)    # morado claro
                elif cabecera_evento_regex.match(texto_linea):
                    pagina_tiene_evento = True
                    pagina_tiene_funcion_valida = True
                    color = (0.7, 1, 0.7)      # verde claro

                if color and line["spans"]:
                    x0 = min(span["bbox"][0] for span in line["spans"])
                    y0 = min(span["bbox"][1] for span in line["spans"])
                    x1 = max(span["bbox"][2] for span in line["spans"])
                    y1 = max(span["bbox"][3] for span in line["spans"])
                    rect = fitz.Rect(x0, y0, x1, y1)
                    annot = page.add_highlight_annot(rect)
                    annot.set_colors(stroke=color)
                    annot.update()

                # ======================
                # Subrayar solo EO y Fecha
                # ======================
                # Buscar EO
                page_text = page.get_text("text")
                match_event = event_order_regex.search(page_text)
                if match_event:
                    numero = match_event.group(1)
                    rects = page.search_for(numero)
                    for rect in rects:
                        annot = page.add_highlight_annot(rect)
                        annot.set_colors(stroke=(0.7, 1, 0.7))  # verde claro
                        annot.update()

                # Buscar Fecha
                match_date = function_date_regex.search(page_text)
                if match_date:
                    fecha = match_date.group(1).strip()
                    rects = page.search_for(fecha)
                    for rect in rects:
                        annot = page.add_highlight_annot(rect)
                        annot.set_colors(stroke=(0.7, 1, 0.7))  # verde claro
                        annot.update()
        # 🚨 Regla: eliminar página si:
        # 1) No tiene evento, función válida ni comida
        # 2) Contiene "No Food or Beverage Required at this Time"
        if not (pagina_tiene_evento or pagina_tiene_funcion_valida or pagina_tiene_comida) or eliminar_por_no_food:
            paginas_a_eliminar.append(page_index)

    # Eliminar páginas sin interés
    for i in reversed(paginas_a_eliminar):
        doc.delete_page(i)

    doc.save(ruta_pdf_salida)
    doc.close()
