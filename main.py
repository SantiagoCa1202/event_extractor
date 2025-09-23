import pdfplumber
import re
import os
import tkinter as tk
from tkinter import filedialog
from pprint import pprint
from PIL import Image
from pdf2image import convert_from_path
from datetime import datetime, timedelta
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

##//** CATEGORIZACIÓN 
from food_dictionary import cold_items, hot_items, irrelevant_items, type_events_items 

##//** Ruta al archivo donde se guardarán ítems no categorizados
uncategorized_path = "uncategorized.txt"
uncategorized_global_set = set()  # Para evitar duplicados en archivo


# Inicializar tkinter
root = tk.Tk()
root.withdraw()

# Diálogo para seleccionar archivo PDF
pdf_path = filedialog.askopenfilename(
    title="Selecciona el archivo PDF",
    filetypes=[("Archivos PDF", "*.pdf")]
)

if not pdf_path:
    print("❌ No se seleccionó ningún archivo.")
    exit()

print(f"Archivo PDF que se va a abrir: {pdf_path}")

eventos = []
en_attendance = False

# Funciones que nos interesan
funciones_deseadas = [
    "Reception", "Breakfast","Breakfast Buffet", "Lunch", "Lunch Buffet", "Dinner", "Coffee Break", "Cocktail Reception", "Menu Tasting"
]
funciones_regex = re.compile(rf"({'|'.join(re.escape(f) for f in funciones_deseadas)})", re.IGNORECASE)
cabecera_evento_regex = re.compile(
    r'(?P<time>\d{1,2}:\d{2}\s*[AP]M)\s+'
    r'(?P<function>Reception|Breakfast|Breakfast Buffet|Continental Breakfast|Lunch|Lunch Buffet|Dinner|Coffee Break|Continuous Break|Cocktail Reception|Menu Tasting)'
    r'(?:\s+(?P<room>.+))?$',
    re.IGNORECASE
)


def clasificar_food(detalles):
    food = {
        "hot": [],
        "cold": [],
        "uncategorized": []
    }

    for linea in detalles.split('\n'):
        if not linea.strip():
            continue

        # Dividir la línea por coma o punto y coma
        items = re.split(r'[;,&]', linea.strip())

        for raw_item in items:
            item = raw_item.strip().lower()

            if not item or any(ir in item for ir in irrelevant_items):
                continue

            matched = False
            for keyword in hot_items:
                if keyword.lower() in item:
                    food["hot"].append(raw_item.strip())
                    matched = True
                    break

            if not matched:
                for keyword in cold_items:
                    if keyword.lower() in item:
                        food["cold"].append(raw_item.strip())
                        matched = True
                        break

            if not matched:
                if item not in uncategorized_global_set:
                    food["uncategorized"].append(raw_item.strip())
                    with open(uncategorized_path, 'a', encoding='utf-8') as f:
                        f.write(raw_item.strip() + '\n')
                    uncategorized_global_set.add(item)

    return food

##//** LIMPIAR DETALLES
def limpiar_detalles(texto: str) -> str:
    lineas = texto.split('\n')
    lineas_limpias = []

    patrones_irrelevantes = [
        r"(?i)sheraton charlotte hotel",
        r"(?i)marriott proprietary and confidential",
        r"(?i)^phone.*",
        r"(?i)^quote.*",
        r"(?i)^folio.*",
        r"(?i)^organization.*",
        r"(?i)guarantees are required.*",
        r"(?i)absolutely no outside food.*",
        r"(?i)a service charge.*",
        r"(?i)administrative fee.*",
        r"(?i)conference",
        r"(?i)special",
        r"^\s*$"  # líneas vacías
    ]

    for linea in lineas:
        linea_limpia = linea.strip()
        if not linea_limpia:
            continue
        if any(re.search(pat, linea_limpia) for pat in patrones_irrelevantes):
            continue
        lineas_limpias.append(linea_limpia)

    return '\n'.join(lineas_limpias)

# Detecta si una página pertenece a un bloque Page # 1 of x
def extraer_num_pagina(texto):
    match = re.search(r"Page\s+#\s*(\d+)\s+of\s+(\d+)", texto, re.IGNORECASE)
    return (int(match.group(1)), int(match.group(2))) if match else None


# Extrae la organización de las líneas
import re
def extract_organization(lines: list[str], event: dict) -> None:
    for line in lines:
        match = re.match(r'^ORGANIZATION:\s*(.+)$', line.strip())
        if match:
            organization = match.group(1).strip()
            event.setdefault("details", {})["organization"] = organization
            break  # opcional: si solo quieres tomar la primera aparición

def safe_extract_text(pdf_path, page_index):
    try:
        # Try to extract text using pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[page_index].extract_text()
            if text and text.strip():
                return text
    except Exception as e:
        print(f"pdfplumber failed for page {page_index + 1}: {e}. Falling back to OCR.")

    # Fallback to OCR if pdfplumber fails
    try:
        images = convert_from_path(pdf_path, first_page=page_index+1, last_page=page_index+1)
        if images:
            text = pytesseract.image_to_string(images[0])
            return text
    except Exception as e:
        print(f"OCR failed for page {page_index + 1}: {e}.")

    return ""

def calcular_pickup_food(time_str: str) -> str:
    """
    Recibe un rango de tiempo como '12:00 PM-1:00 PM' y devuelve la hora 40 minutos
    antes del inicio, formato '12:00 PM'.
    """
    hora_inicio = time_str.split('-')[0].strip().upper().replace(".", "")
    if hora_inicio[-2:] in ["AM", "PM"] and not hora_inicio[-3].isspace():
        hora_inicio = hora_inicio[:-2] + " " + hora_inicio[-2:]
    dt_inicio = datetime.strptime(hora_inicio, "%I:%M %p")
    pickup_dt = dt_inicio - timedelta(minutes=40)
    return pickup_dt.strftime("%I:%M %p")

def calcular_lift_time(time_str: str) -> str:
    """
    Recibe un rango de tiempo como '12:00 PM-1:00 PM' y devuelve la hora 30 minutos
    después del fin del evento, formato '12:00 PM'.
    """
    partes = time_str.split('-')
    
    if len(partes) > 1:
        hora_fin = partes[1].strip().upper().replace(".", "")
    else:
        # Si no hay rango, usar la misma hora como fin
        hora_fin = partes[0].strip().upper().replace(".", "")

    # Asegurar espacio antes de AM/PM
    if hora_fin[-2:] in ["AM", "PM"] and not hora_fin[-3].isspace():
        hora_fin = hora_fin[:-2] + " " + hora_fin[-2:]

    dt_fin = datetime.strptime(hora_fin, "%I:%M %p")
    lift_dt = dt_fin + timedelta(minutes=30)
    return lift_dt.strftime("%I:%M %p")

with pdfplumber.open(pdf_path) as pdf:
    i = 0
    while i < len(pdf.pages):
        page = pdf.pages[i]
        texto = safe_extract_text(pdf_path, i)
        if not texto:
            i += 1
            continue

        if "Event Order" in texto and "FUNCTION DAY/DATE" in texto:
            match_order = re.search(r"Event Order\s*#\s*[:#]?\s*(\d+)", texto)
            match_fecha = re.search(r"FUNCTION DAY/DATE\s*[:#]?\s*([A-Za-z]+),\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", texto)

            if match_order and match_fecha:
                day = match_fecha.group(1)
                date = match_fecha.group(2)
                event_order = int(match_order.group(1))
                
                # Detectar si esta página forma parte de un bloque multipágina
                num_pagina = extraer_num_pagina(texto)
                paginas_conjuntas = []

                if num_pagina:
                    pagina_actual, total_paginas = num_pagina
                    # Agrupar todas las páginas de este bloque
                    while i < len(pdf.pages):
                        sub_texto = pdf.pages[i].extract_text()
                        if not sub_texto:
                            i += 1
                            continue
                        if re.search(rf"Page\s*#\s*{pagina_actual}\b", sub_texto, re.IGNORECASE):
                            paginas_conjuntas.append(sub_texto)
                            pagina_actual += 1
                            i += 1
                            if pagina_actual > total_paginas:
                                break
                        else:
                            break
                else:
                    paginas_conjuntas = [texto]
                    i += 1
                # Juntar todas las líneas del bloque multi página
                bloque_texto = "\n".join(paginas_conjuntas)
                
                lineas = bloque_texto.split('\n')

                # Extraer ORGANIZATION si existe
                for linea in lineas:
                    match_org = re.match(r"ORGANIZATION:\s*(.+)", linea.strip(), re.IGNORECASE)
                    if match_org:
                        organization = match_org.group(1).strip()
                        break
                else:
                    organization = None


                # --- PRIMERA PASADA: eventos principales
                eventos_pagina = []
                for linea in lineas:
                    linea = linea.strip()
                    # Marcar inicio y fin de la sección ATTENDANCE
                    if "ATTENDANCE" in linea.upper():
                        en_attendance = True
                        continue
                    if any(seccion in linea.upper() for seccion in ["ROOM SETUP", "FUNCTION SETUP", "AUDIO VISUAL", "SIGNAGE", "ORDER OF EVENTS"]):
                        en_attendance = False
                        continue
                    
                    if not en_attendance or not linea:
                        continue

                    if funciones_regex.search(linea):
                        match_linea = re.match(
                            r"(?P<time>\d{1,2}:\d{2}\s*[AP]M\s*-\s*\d{1,2}:\d{2}\s*[AP]M)\s+"
                            r"(?P<function>Reception|Breakfast|Breakfast Buffet|Continental Breakfast|Lunch|Lunch Buffet|Dinner|Coffee Break|Continuous Break|Cocktail Reception|Menu Tasting)\s+"
                            r"(?P<room>.+?)\s+"
                            r"(?:(\d+\s+)*?)?"            # posibles números intermedios (Rental, EXP)
                            r"(?P<gtd>\d+)\s*;?\s*$",     # GTD final, opcionalmente seguido de punto y coma
                            linea.strip(),
                            re.IGNORECASE
                        )
                        if match_linea:
                            eventos_pagina.append({
                                'day': day,
                                'date': date,
                                'event_order': event_order,
                                'time': match_linea.group('time'),
                                'pickup_food': calcular_pickup_food(match_linea.group('time')),
                                'lift_time': calcular_lift_time(match_linea.group('time')),
                                'function': match_linea.group('function'),
                                'menu_style': "",
                                'room': match_linea.group('room').strip(),
                                'gtd': int(match_linea.group('gtd')),
                                'organization': organization,
                                'details': {
                                    'raw': '',
                                    'food': {
                                        'hot': [],
                                        'cold': [],
                                        'uncategorized': []
                                    },
                                }
                            })

                # --- SEGUNDA PASADA: extraer detalles desde cabeceras
                j = 0
                while j < len(lineas):
                    match_cabecera = cabecera_evento_regex.match(lineas[j].strip())
                    if match_cabecera:
                        time_inicio = match_cabecera.group('time')
                        funcion = match_cabecera.group('function')

                        evento_encontrado = False
                        for evento in eventos_pagina:
                            if funcion.lower() in evento['function'].lower() and evento['time'].startswith(time_inicio):
                                evento_encontrado = True
                                print(f"Evento encontrado: {evento['function']} a las {evento['time']}")
                                detalles = []
                                omitir = False
                                j += 1  # avanzamos para empezar a leer detalles justo después de la cabecera

                                while j < len(lineas):
                                    siguiente = lineas[j].strip()
                                    # Detectar inicio del bloque a omitir
                                    if re.match(r"^EVENT ORDER Page #\s*\d+\s+of\s+\d+", siguiente, re.IGNORECASE):
                                        omitir = True

                                    # Detectar final del bloque a omitir
                                    if omitir and siguiente.upper().startswith("ORGANIZATION:"):
                                        omitir = False
                                        j += 1  # opcional: avanzar para no incluir esta línea tampoco
                                        continue
                                    
                                    if not omitir:
                                        if cabecera_evento_regex.match(siguiente):
                                            break
                                        detalles.append(siguiente)
                                    j += 1

                                detalle_crudo = "\n".join(detalles).strip()

                                detalle_limpio = limpiar_detalles(detalle_crudo)

                                adicionales = []
                                for item in type_events_items:
                                    if re.search(re.escape(item), detalle_limpio, re.IGNORECASE):
                                        adicionales.append(item.title())
                                    
                                evento['menu_style'] = ", ".join(adicionales)
                                evento['details'] = {
                                    'raw': detalle_limpio,
                                    'food': clasificar_food(detalle_limpio)
                                }
                                evento['organization'] = organization 
                                break
                            
                        # Solo avanzamos en j si no entramos al bloque anterior (no procesamos detalles)
                        if not evento_encontrado:
                            # Crear nuevo evento desde cabecera
                            sala = match_cabecera.group('room')

                            detalles = []
                            omitir = False
                            j += 1
                            while j < len(lineas):
                                siguiente = lineas[j].strip()
                                # Detectar inicio del bloque a omitir
                                if re.match(r"^EVENT ORDER Page #\s*\d+\s+of\s+\d+", siguiente, re.IGNORECASE):
                                    omitir = True

                                # Detectar final del bloque a omitir
                                if omitir and siguiente.upper().startswith("ORGANIZATION:"):
                                    omitir = False
                                    j += 1  # opcional: avanzar para no incluir esta línea tampoco
                                    continue
                                
                                if not omitir:
                                    if cabecera_evento_regex.match(siguiente):
                                        break
                                    detalles.append(siguiente)
                                j += 1

                            detalle_crudo = "\n".join(detalles).strip()
                            detalle_limpio = limpiar_detalles(detalle_crudo)

                            adicionales = []

                            for item in type_events_items:
                                if re.search(re.escape(item), detalle_limpio, re.IGNORECASE):
                                    adicionales.append(item.title())
                                
                            nuevo_evento = {
                                'day': day,
                                "date": date,
                                "time": time_inicio,
                                "pickup_food": calcular_pickup_food(time_inicio),
                                "lift_time": calcular_lift_time(time_inicio),
                                "function": funcion,
                                "menu_style": ", ".join(adicionales),
                                "room": sala,
                                "event_order": event_order,
                                'gtd': 0,
                                "organization": organization,
                                "details": {
                                    "raw": detalle_limpio,
                                    "food": clasificar_food(detalle_limpio),
                                },
                                "sub_event": True  # para saber que se generó desde cabecera
                            }

                            eventos_pagina.append(nuevo_evento)


                    else:
                        j += 1


                eventos.extend(eventos_pagina)

            else:
                i += 1
        else:
            i += 1

#Mostrar resultados
#pprint(eventos)
#pprint(len(eventos))
###############################################################################
    ##//* PROCESO DE GUARDADO LISTA DE EVENTOS EN EXCEL *//##
nombre_sin_ext = os.path.splitext(os.path.basename(pdf_path))[0]

import pandas as pd
from collections import defaultdict
from datetime import datetime

# Agrupar eventos por fecha
eventos_por_dia = defaultdict(list)
for evento in eventos:
    eventos_por_dia[evento["date"]].append(evento)

# ORDENAR EVENTOS 
def extraer_hora_inicio(hora_str: str) -> datetime:
    # Limpieza y separación del rango
    hora_str = hora_str.strip().upper().replace(".", "")
    
    # Si es un rango, tomar solo la hora de inicio
    if '-' in hora_str:
        hora_inicio = hora_str.split('-')[0].strip()
    else:
        hora_inicio = hora_str.strip()
    
    # Asegura que tenga espacio antes de AM/PM
    if hora_inicio[-2:] in ["AM", "PM"] and not hora_inicio[-3].isspace():
        hora_inicio = hora_inicio[:-2] + " " + hora_inicio[-2:]
    
    return datetime.strptime(hora_inicio, "%I:%M %p")

for fecha, eventos_dia in eventos_por_dia.items():
    eventos_dia.sort(key=lambda e: extraer_hora_inicio(e["time"]))
# Crear una lista de filas combinadas para el Excel
filas_excel = []
for fecha, eventos_dia in eventos_por_dia.items():
    day_name = eventos_dia[0]["day"]
    filas_excel.append({"": f"{day_name}, {fecha}"})  # Encabezado del día
    for evento in eventos_dia:
        food = evento["details"]["food"]
        if food["hot"] and food["cold"]:
            food_type = "Hot & Cold"
        elif food["hot"]:
            food_type = "Hot Only"
        elif food["cold"]:
            food_type = "Cold Only"
        else:
            food_type = "None"
        filas_excel.append({
            "Time": evento["time"],
            "Organization": evento['organization'],
            "Function": f"{evento['function']} {'(no food)' if not evento['details']['food']['hot'] and not evento['details']['food']['cold'] else ''}",
            "Menu Style": evento["menu_style"],
            "Room": evento["room"],
            "GTD": evento["gtd"],
            "Event #": evento["event_order"],
            "Food Type": food_type
        })
    filas_excel.append({})  # Fila vacía para separar días
# Crear DataFrame y guardar
df_final = pd.DataFrame(filas_excel)

nombre_sin_ext = os.path.splitext(os.path.basename(pdf_path))[0]

# Crear el nombre del archivo Excel cambiando la extensión
excel_path_all = f"ready_to_print/all/{nombre_sin_ext}_all.xlsx"

# Guardar el DataFrame con ese nombre
df_final.to_excel(excel_path_all, index=False)
from openpyxl import load_workbook
from openpyxl.styles import Border, Side, Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

archivo_excel = excel_path_all
wb = load_workbook(archivo_excel)
ws = wb.active

# Estilos
borde_fino = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)
negrita = Font(bold=True)
centrado = Alignment(horizontal="center", vertical="center")
relleno_gris = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

# Determinar número de columnas máximo
max_col = ws.max_column

# Ajustar ancho de columnas
for col in ws.columns:
    max_length = 0
    col_letter = get_column_letter(col[0].column)
    for cell in col:
        if cell.value:
            max_length = max(max_length, len(str(cell.value)))
    ws.column_dimensions[col_letter].width = max_length + 2

# Recorrer todas las filas
for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=max_col):
    fila = row[0].row
    for cell in row:
        cell.border = borde_fino

    # Revisar si es fila de día
    primer_valor = row[0].value
    import re
    if isinstance(primer_valor, str) and re.match(r"^[A-Za-z]+,\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}$", primer_valor.strip()):
        # Combinar celdas
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=max_col)
        cell = ws.cell(row=fila, column=1)
        cell.font = negrita
        cell.alignment = centrado
        cell.fill = relleno_gris

# Guardar archivo final
wb.save(archivo_excel)
os.startfile(os.path.abspath(excel_path_all))

print(f"\n✅ Archivo '{archivo_excel}' actualizado.")


##//** SETUP DE EVENTOS
filas_excel = []
for fecha, eventos_dia in eventos_por_dia.items():
    day_name = eventos_dia[0]["day"]
    filas_excel.append({"": f"{day_name}, {fecha}"})  # Encabezado del día
    for evento in eventos_dia:
        food = evento["details"]["food"]
        if food["hot"] and food["cold"]:
            food_type = "Hot & Cold"
        elif food["hot"]:
            food_type = "Hot Only"
        elif food["cold"]:
            food_type = "Cold Only"
        else:
            food_type = "None"

        # Fila principal del evento
        filas_excel.append({
            "Time": evento["time"],
            "Organization": evento['organization'],
            "Function": f"{evento['function']} {'(no food)' if not food['hot'] and not food['cold'] else ''}",
            "Room": evento["room"],
            "GTD": evento["gtd"],
            "Event #": evento["event_order"],
            "Food Type": food_type
        })

        # Fila extra: Menu Style
        filas_excel.append({
            "Time": "",
            "Organization": "Menu Style",
            "Function": evento.get('menu_style', ''),
            "Room": "",
            "GTD": "",
            "Event #": "",
            "Food Type": ""
        })

        # Fila extra: Pickup Food
        filas_excel.append({
            "Time": "",
            "Organization": "Pickup Food",
            "Function": evento.get('pickup_food', ''),
            "Room": "",
            "GTD": "",
            "Event #": "",
            "Food Type": ""
        })

        # Fila extra: Lift Time
        filas_excel.append({
            "Time": "",
            "Organization": "Lift Time",
            "Function": evento.get('lift_time', ''),
            "Room": "",
            "GTD": "",
            "Event #": "",
            "Food Type": ""
        })
        filas_excel.append({})

    filas_excel.append({})

# Crear DataFrame y guardar
df_final = pd.DataFrame(filas_excel)

# Guardar Excel como antes
excel_path_all = f"ready_to_print/setup/{nombre_sin_ext}_setup.xlsx"
df_final.to_excel(excel_path_all, index=False)

# Estilos con openpyxl
from openpyxl import load_workbook
from openpyxl.styles import Border, Side, Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

wb = load_workbook(excel_path_all)
ws = wb.active

# Estilos
borde_fino = Border(left=Side(style='thin'), right=Side(style='thin'),
                    top=Side(style='thin'), bottom=Side(style='thin'))
negrita = Font(bold=True)
centrado = Alignment(horizontal="center", vertical="center")
relleno_gris = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

# Ajustar ancho de columnas
max_col = ws.max_column
for col in ws.columns:
    max_length = 0
    col_letter = get_column_letter(col[0].column)
    for cell in col:
        if cell.value:
            max_length = max(max_length, len(str(cell.value)))
    ws.column_dimensions[col_letter].width = max_length + 2

# Aplicar borde y estilos a filas de día
for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=max_col):
    fila = row[0].row
    for cell in row:
        cell.border = borde_fino

    primer_valor = row[0].value
    import re
    if isinstance(primer_valor, str) and re.match(r"^[A-Za-z]+,\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}$", primer_valor.strip()):
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=max_col)
        cell = ws.cell(row=fila, column=1)
        cell.font = negrita
        cell.alignment = centrado
        cell.fill = relleno_gris

# Aplicar negrita al title de Pickup/Lift
for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=max_col):
    room_cell = row[4]  # columna Room (índice 3)
    if room_cell.value in ["Pickup Food", "Lift Time", "Menu Style"]:
        room_cell.font = Font(bold=True)
# Guardar archivo final
wb.save(excel_path_all)
os.startfile(os.path.abspath(excel_path_all))

print(f"\n✅ Archivo '{excel_path_all}' actualizado.")


##//** SUBRAYAR Y GUARDAR NUEVO PDF 

from highlighter import subrayar_pdf_por_categoria

ruta_pdf_original = pdf_path
ruta_pdf_con_marcas = f"ready_to_print/highlighter/{nombre_sin_ext}_HIGHLIGHTER.PDF"

subrayar_pdf_por_categoria(ruta_pdf_original, ruta_pdf_con_marcas)
print("✅ PDF resaltado guardado en:", ruta_pdf_con_marcas)
