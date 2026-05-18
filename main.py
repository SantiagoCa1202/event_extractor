import pdfplumber
import re
import os
import tkinter as tk
from tkinter import filedialog
from datetime import datetime, timedelta
import pytesseract
from functions import clasificar_por_menu, clean_details
from functions import clasificar_waste_items
from config import TESSERACT_CMD, include_all_event_functions
from event_functions import (
    EVENT_FUNCTION_REGEX_FRAGMENT,
    normalize_function_name,
    same_event_function,
)
from text_extraction import safe_extract_text

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

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

events = []
en_attendance = False

funciones_regex = re.compile(EVENT_FUNCTION_REGEX_FRAGMENT, re.IGNORECASE)
cabecera_evento_regex = re.compile(
    r'(?P<time>\d{1,2}:\d{2}\s*[AP]M)\s+'
    rf'(?P<function>{EVENT_FUNCTION_REGEX_FRAGMENT})'
    r'(?:\s+(?P<room>.+))?$',
    re.IGNORECASE
)


def clasificar_food(detalles):
    food = {
        "hot_items": [],
        "cold_items": [],
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
                    food["hot_items"].append(raw_item.strip())
                    matched = True
                    break

            if not matched:
                for keyword in cold_items:
                    if keyword.lower() in item:
                        food["cold_items"].append(raw_item.strip())
                        matched = True
                        break

            if not matched:
                if item not in uncategorized_global_set:
                    food["uncategorized"].append(raw_item.strip())
                    with open(uncategorized_path, 'a', encoding='utf-8') as f:
                        f.write(raw_item.strip() + '\n')
                    uncategorized_global_set.add(item)

    return food


def has_food_evidence(event: dict) -> bool:
    menu_style = (event.get("menu_style") or "").strip()
    if menu_style:
        return True

    food = event.get("details", {}).get("food", {}) or {}
    if not isinstance(food, dict):
        return bool(food)

    waste_items = food.get("waste_items") or []
    if waste_items:
        return True

    matched = food.get("matched")
    if isinstance(matched, dict):
        if any(matched.get(section) for section in matched):
            return True
    elif matched:
        return True

    for key in ("hot_items", "cold_items", "extra"):
        values = food.get(key) or []
        if values:
            return True

    raw = (event.get("details", {}).get("raw") or "").lower()
    if not raw:
        return False
    food_signals = hot_items + cold_items + type_events_items
    return any(signal.lower() in raw for signal in food_signals)


def should_keep_event(event: dict) -> bool:
    if event.get("ignore_event"):
        return False
    if include_all_event_functions():
        return True
    return has_food_evidence(event)

# Detecta si una página pertenece a un bloque Page # 1 of x
def extraer_num_pagina(texto):
    match = re.search(r"Page\s+#\s*(\d+)\s+of\s+(\d+)", texto, re.IGNORECASE)
    return (int(match.group(1)), int(match.group(2))) if match else None


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


                # --- PRIMERA PASADA: events principales
                eventos_pagina = []
                for linea in lineas:

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
                            rf"(?P<function>{EVENT_FUNCTION_REGEX_FRAGMENT})\s+"
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
                                'function': normalize_function_name(match_linea.group('function')),
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
                        function_event = normalize_function_name(match_cabecera.group('function'))

                        evento_encontrado = False
                        for evento in eventos_pagina:
                            if same_event_function(function_event, evento['function']) and evento['time'].startswith(time_inicio):
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

                                detalle_limpio = clean_details(detalle_crudo)

                                adicionales = []
                                for item in type_events_items:
                                    if re.search(re.escape(item), detalle_limpio, re.IGNORECASE):
                                        adicionales.append(item.title())
                                    
                                evento['menu_style'] = ", ".join(adicionales)

                                menu_name = evento.get('menu_style')
                                if not menu_name:
                                    # No se encontró menú explícito
                                    menu_name = "unknown_menu"
                                try:
                                    clasificado = clasificar_por_menu(menu_name, detalle_limpio.splitlines())
                                except ValueError:
                                    clasificado = clasificar_food(detalle_limpio)
                                # Añadir waste_items dentro de food
                                clasificado['waste_items'] = clasificar_waste_items(detalle_limpio.splitlines())
                                evento['details'] = {
                                    'raw': detalle_limpio,
                                    'food': clasificado
                                }
                                evento['organization'] = organization
                                if not include_all_event_functions() and not has_food_evidence(evento):
                                    evento["ignore_event"] = True
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
                            detalle_limpio = clean_details(detalle_crudo)

                            adicionales = []

                            for item in type_events_items:
                                if re.search(re.escape(item), detalle_limpio, re.IGNORECASE):
                                    adicionales.append(item.title())
                            clasificado = clasificar_food(detalle_limpio)
                            clasificado["waste_items"] = clasificar_waste_items(detalle_limpio.splitlines())    

                            nuevo_evento = {
                                'day': day,
                                "date": date,
                                "time": time_inicio,
                                "pickup_food": calcular_pickup_food(time_inicio),
                                "lift_time": calcular_lift_time(time_inicio),
                                "function": function_event,
                                "menu_style": ", ".join(adicionales),
                                "room": sala,
                                "event_order": event_order,
                                'gtd': 0,
                                "organization": organization,
                                "details": {
                                    "raw": detalle_limpio,
                                    "food": clasificado,
                                },
                                "sub_event": True  # para saber que se generó desde cabecera
                            }
                            if should_keep_event(nuevo_evento):
                                eventos_pagina.append(nuevo_evento)


                    else:
                        j += 1

                eventos_filtrados = [
                    event
                    for event in eventos_pagina
                    if should_keep_event(event)
                ]
                events.extend(eventos_filtrados)

            else:
                i += 1
        else:
            i += 1

#Mostrar resultados
#pprint(events)
#pprint(len(events))
###############################################################################
nombre_sin_ext = os.path.splitext(os.path.basename(pdf_path))[0]
# ##//** ALL EVENTS 
from all_events import save_events_to_excel
save_events_to_excel(events, pdf_path, open_file=False)


##//** RESUMENES  
from resumenes import save_resumenes
save_resumenes(events, pdf_path, open_file=False)


# ##//** WASTE FOOD SHEET
from generate_waste_food_sheet import generate_waste_food_sheet
from save_json import save_json
generate_waste_food_sheet(events, filename=f"ready_to_print/waste_food/{nombre_sin_ext}_WASTE_FOOD_SHEET.xlsx")
 
## CREATE JSON
output_json_path = f"ready_to_print/json/{nombre_sin_ext}_events.json"
save_json(events, output_json_path, source_file=pdf_path)
print("✅ JSON guardado en:", output_json_path)

# ##//** SUBRAYAR Y GUARDAR NUEVO PDF 
from highlighter import subrayar_pdf_por_categoria

ruta_pdf_original = pdf_path
ruta_pdf_con_marcas = f"ready_to_print/highlighter/{nombre_sin_ext}_HIGHLIGHTER.PDF"

subrayar_pdf_por_categoria(ruta_pdf_original, ruta_pdf_con_marcas)
print("✅ PDF resaltado guardado en:", ruta_pdf_con_marcas)



