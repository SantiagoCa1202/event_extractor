import pdfplumber
import re

import os

import tkinter as tk
from tkinter import filedialog

# Inicializar tkinter
root = tk.Tk()
root.withdraw()  # Oculta la ventana principal

# Abrir diálogo para seleccionar archivo PDF
pdf_path = filedialog.askopenfilename(
    title="Selecciona el archivo PDF",
    filetypes=[("Archivos PDF", "*.pdf")]
)

if not pdf_path:
    print("❌ No se seleccionó ningún archivo.")
    exit()

print(f"Archivo PDF que se va a abrir: {pdf_path}")

texto_buscado = "Page # 1"
palabras_clave = ["reception", "breakfast", "lunch", "dinner", "coffee break", " cocktail reception"]
eventos = []

# Lista de descripciones válidas para el campo 'type'
tipos_validos = [
    "Modified Breakfast Buffet",
    "Custom Lunch Menu",
    "Custom Dinner Buffet",
    "Charlotte Lunch Table",
    "Piedmont Cured Lunch Table",
    "Imported Cheese Reception Table",
    "Charcuterie Table Reception Table",
    "Boxed Lunch",
    "Custom Plated Lunch",
    "All Star Breakfast",
    "Green's Lunch Table",
    "Antipasto Reception Table",
    "Custom Plated Dinner",
]

type_to_function_map = {
    "custom lunch menu": "Lunch Buffet",
    "custom plated lunch": "Plated Lunch",
    "custom plated dinner": "Plated Dinner",
    "modified breakfast buffet": "Breakfast Buffet",
    "modified breakfast buffet": "Breakfast Buffet",
    "custom lunch menu": "Lunch Buffet",
    "custom dinner buffet": "Dinner Buffet",
    "charlotte lunch table": "Lunch Buffet",
    "piedmont cured lunch table": "Lunch Buffet",
    "imported cheese reception table": "Reception",
    "charcuterie table reception table": "Reception",
    "boxed lunch": "Boxed Lunch",
    "custom plated lunch": "Plated Lunch",
    "all star breakfast": "Breakfast Buffet",
    "green's lunch table": "Lunch Buffet",
    "antipasto reception table": "Reception",
}

exclusiones = [
    "POST AS: CASH BAR - Welcome Reception"
]


from cold_hot_dictionary import cold_items, hot_items

def clasificar_comida(lineas_comida):
    cold_food = []
    hot_food = []
    unclassified = [] 

    for linea in lineas_comida:
        linea_lower = linea.lower()
        # Buscar palabras clave de frío o caliente dentro de la línea
        if any(item in linea_lower for item in cold_items):
            cold_food.append(linea)
        elif any(item in linea_lower for item in hot_items):
            hot_food.append(linea)
        else:
            # Si no se reconoce, por default lo ponemos en cold_food
            unclassified.append(linea)

    return cold_food, hot_food, unclassified

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue

        if texto_buscado in text:
            lower_text = text.lower()
            if any(palabra in lower_text for palabra in palabras_clave):
                print(f"\n✅ Página {i + 1} contiene función válida")

                # Extraer valores comunes una vez por página
                event_order = None
                date = None
                day = None

                # Dividir líneas de texto solo una vez para no repetirlo
                lines = text.splitlines()
                # Crear un diccionario para mapear función y hora a tipo
                funcion_tipo_map = {}

                # Leer claves de comida una vez
                with open("claves_comida.txt", "r", encoding="utf-8") as f:
                    claves_comida = [line.strip().lower() for line in f if line.strip()]
                
                # Extender las líneas si es necesario (añadir líneas de la página siguiente)
                pag_siguiente_lines = []
                if i + 1 < len(pdf.pages):
                    next_page_text = pdf.pages[i + 1].extract_text()
                    if next_page_text:
                        pag_siguiente_lines = next_page_text.splitlines()
                
                # Unir líneas actuales y siguientes para poder buscar comida extendida
                all_lines_ext = lines + pag_siguiente_lines

                # Primero buscamos las líneas con la descripción tipo para cada función como "7:00 AM - Breakfast"
                for idx, line in enumerate(lines):
                    alt_match = re.match(r'(\d{1,2}:\d{2}\s*[AP]M)\s+(Reception|Breakfast|Lunch|Dinner|Coffee Break| Cocktail Reception)', line, re.IGNORECASE)
                    if alt_match:
                        funcion = alt_match.group(2).capitalize()
                        next_idx = idx + 1

                        # Buscar el tipo válido dentro de las próximas 5 líneas (por si hay líneas intermedias)
                        posible_tipo = None
                        for offset in range(1, 6):  # hasta 5 líneas siguientes
                            idx_busqueda = idx + offset
                            if idx_busqueda < len(lines):
                                linea_siguiente = lines[idx_busqueda].strip()
                                for tipo_valido in tipos_validos:
                                    if tipo_valido.lower() == linea_siguiente.lower():
                                        posible_tipo = tipo_valido
                                        break
                            if posible_tipo:
                                break
                                
                        # Verificar si hay comida en las siguientes líneas (actuales + de la página siguiente)
                        tiene_comida = False
                        for offset in range(1, 30):  # buscar hasta 30 líneas después
                            siguiente_idx = idx + offset
                            if siguiente_idx < len(all_lines_ext):
                                siguiente_linea = all_lines_ext[siguiente_idx].lower()
                                if any(clave in siguiente_linea for clave in claves_comida):
                                    tiene_comida = True
                                    break
                                
                        # Si se encontró comida y un tipo válido, guardar el mapeo
                        if posible_tipo and tiene_comida:
                            funcion_tipo_map[funcion] = posible_tipo
                            

                # Ahora recorremos líneas para extraer eventos con sus datos
                for line in lines:
                    # Event Order
                    if not event_order:
                        match = re.search(r'Event Order\s*#\s*[:\-]?\s*(\d{6})', line)
                        if match:
                            event_order = match.group(1)

                    # Fecha y día
                    if not date:
                        match = re.search(r'([A-Za-z]+),\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})', line)
                        if match:
                            day = match.group(1)
                            date = match.group(2)

                    # Buscar líneas de función (time, function, room, gtd)
                    match = re.search(
                        r'(\d{1,2}:\d{2}\s*[AP]M\s*-\s*\d{1,2}:\d{2}\s*[AP]M)\s+'
                        r'(Reception|Breakfast|Lunch|Dinner|Coffee Break|Cocktail Reception)\s+'
                        r'(.+?)\s+(\d+)$',
                        line,
                        re.IGNORECASE
                    )
                    if match:
                        funcion = match.group(2).capitalize()
                        current_idx = lines.index(line)
                        print(f"linea: {line}")
                        # Buscar líneas siguientes al evento por palabras clave de comida
                        tiene_comida = False
                        with open("claves_comida.txt", "r", encoding="utf-8") as f:
                            claves_comida = [line.strip().lower() for line in f if line.strip()]
                        lineas_comida_evento = []
                        for offset in range(1, 30):  # revisar hasta 30 líneas siguientes
                            siguiente_idx = current_idx + offset
                            if siguiente_idx < len(lines):
                                siguiente_linea = lines[siguiente_idx].strip()
                                if any(clave in siguiente_linea.lower() for clave in claves_comida):
                                    tiene_comida = True
                                    lineas_comida_evento.append(siguiente_linea)


                        if tiene_comida:
                            # Revisar si alguna de las líneas cercanas contiene una frase excluida
                            lineas_cercanas = " ".join(lines[current_idx:current_idx+5]).upper()  # hasta 5 líneas siguientes
                            if any(exclusion.upper() in lineas_cercanas for exclusion in exclusiones):
                                continue  # Omitir este evento
                            
                            type_value = funcion_tipo_map.get(funcion, None)
                            type_lower = type_value.lower() if type_value else None

                            if type_lower and type_lower in type_to_function_map:
                                funcion_final = type_to_function_map[type_lower]
                            else:
                                funcion_final = funcion

                            cold_food, hot_food, unclassified = clasificar_comida(lineas_comida_evento)
                            evento = {
                                "event_order": event_order,
                                "function": funcion_final,
                                "time": match.group(1),
                                "room": match.group(3).strip(),
                                "date": date,
                                "day": day,
                                "gtd": match.group(4),
                                "food": {
                                    "hot_food": hot_food,
                                    "cold_food": cold_food,
                                }
                            }
                            eventos.append(evento)
                            # Guardar líneas no clasificadas en archivo externo para revisión
                            if unclassified:
                                with open("por_clasificar.txt", "a", encoding="utf-8") as archivo:
                                    for item in unclassified:
                                        archivo.write(f"{item}\n")



# from pprint import pprint
# pprint(eventos)


###############################################################################
    ##//* PROCESO DE GUARDADO LISTA DE EVENTOS EN EXCEL *//##

import pandas as pd
from collections import defaultdict
# Agrupar eventos por fecha
eventos_por_dia = defaultdict(list)
for evento in eventos:
    eventos_por_dia[evento["date"]].append(evento)
# Crear una lista de filas combinadas para el Excel
filas_excel = []
for fecha, eventos_dia in eventos_por_dia.items():
    day_name = eventos_dia[0]["day"]
    filas_excel.append({"": f"{day_name}, {fecha}"})  # Encabezado del día
    for evento in eventos_dia:
        filas_excel.append({
            "Time": evento["time"],
            "Function": evento["function"],
            "Room": evento["room"],
            "GTD": evento["gtd"],
            "Event #": evento["event_order"]
        })
    filas_excel.append({})  # Fila vacía para separar días
# Crear DataFrame y guardar
df_final = pd.DataFrame(filas_excel)

nombre_sin_ext = os.path.splitext(os.path.basename(pdf_path))[0]

# Crear el nombre del archivo Excel cambiando la extensión
excel_path_all = f"ready_to_print/{nombre_sin_ext}_all.xlsx"

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

#######//***
from openpyxl import Workbook
from openpyxl.styles import Font

# Crear un nuevo archivo de Excel
wb = Workbook()
ws = wb.active
ws.title = "Eventos"

# Estilos
bold_font = Font(bold=True)

# Empezar en la primera fila
row = 1

for evento in eventos:
    ws.cell(row=row, column=1, value="Event Order:").font = bold_font
    ws.cell(row=row, column=2, value=evento["event_order"])
    row += 1

    ws.cell(row=row, column=1, value="Function:").font = bold_font
    ws.cell(row=row, column=2, value=evento["function"])
    row += 1

    ws.cell(row=row, column=1, value="Time:").font = bold_font
    ws.cell(row=row, column=2, value=evento["time"])
    row += 1

    ws.cell(row=row, column=1, value="Room:").font = bold_font
    ws.cell(row=row, column=2, value=evento["room"])
    row += 1

    ws.cell(row=row, column=1, value="Date:").font = bold_font
    ws.cell(row=row, column=2, value=evento["date"])
    row += 1

    ws.cell(row=row, column=1, value="Day:").font = bold_font
    ws.cell(row=row, column=2, value=evento["day"])
    row += 1

    ws.cell(row=row, column=1, value="GTD:").font = bold_font
    ws.cell(row=row, column=2, value=evento["gtd"])
    row += 2

    # Hot food
    ws.cell(row=row, column=1, value="Hot Food:").font = bold_font
    row += 1
    for item in evento["food"]["hot_food"]:
        ws.cell(row=row, column=2, value=item)
        row += 1

    # Cold food
    row += 1
    ws.cell(row=row, column=1, value="Cold Food:").font = bold_font
    row += 1
    for item in evento["food"]["cold_food"]:
        ws.cell(row=row, column=2, value=item)
        row += 1

    # Espacio entre eventos
    row += 2

# Guardar el archivo
excel_path_prep = f"ready_to_print/{nombre_sin_ext}_prep.xlsx"
wb.save(excel_path_prep)
print("✅ Archivo 'eventos.xlsx' creado exitosamente.")
