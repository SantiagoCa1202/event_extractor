from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side

def prep_list(events, filename="events.xlsx"):
    wb = Workbook()
    wb.remove(wb.active)  # quitar hoja por defecto

    # Definir borde fino
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    headers = ["Initials", "Menu Item", "Prep Amount", "Unit"]

    for event in events:
        sheet_name = f"Event {event.get('event_order', '')}"
        ws = wb.create_sheet(title=sheet_name[:31])  # máximo 31 caracteres

        row = 1

        # ====== SECCIÓN COLD FOOD ======
        for label, key in [
            ("Event Order:", "event_order"),
            ("Time:", "time"),
            ("Room:", "room"),
            ("Function:", "function"),
            ("Menu Style:", "menu_style"),
            ("Date:", "date"),
            ("Day:", "day"),
            ("GTD:", "gtd"),
        ]:
            ws[f"B{row}"] = label
            ws[f"C{row}"] = event.get(key, "")
            # Negrita y bordes
            ws[f"B{row}"].font = Font(bold=True)
            ws[f"B{row}"].border = thin_border
            ws[f"C{row}"].border = thin_border
            row += 1

        # Encabezados tabla cold (desde columna 2)
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.border = thin_border

        cold_items = event.get("details", {}).get("food", {}).get("matched", {}).get("cold_items", [])
        for item in cold_items:
            row += 1
            for col in range(1, 5):  # columnas B-E
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
            ws.cell(row=row, column=2, value=item.get("name", "") )  # columna C = "Menu Item"

        row += 3  # espacio entre secciones

        # ====== SECCIÓN HOT FOOD ======
        for label, key in [
            ("Event Order:", "event_order"),
            ("Time:", "time"),
            ("Room:", "room"),
            ("Function:", "function"),
            ("Menu Style:", "menu_style"),
            ("Date:", "date"),
            ("Day:", "day"),
            ("GTD:", "gtd"),
        ]:
            ws[f"B{row}"] = label
            ws[f"C{row}"] = event.get(key, "")
            ws[f"B{row}"].font = Font(bold=True)
            ws[f"B{row}"].border = thin_border
            ws[f"C{row}"].border = thin_border
            row += 1

        # Encabezados tabla hot (desde columna 2)
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.border = thin_border

        hot_items = event.get("details", {}).get("food", {}).get("matched", {}).get("hot_items", [])
        for item in hot_items:
            row += 1
            for col in range(1, 5):  # columnas B-E
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
            ws.cell(row=row, column=2, value=item.get("name", "") )

        # Ajustar ancho de columnas B-E
        for col in range(1, 5):
            ws.column_dimensions[chr(64 + col)].width = 25

        # Missing Items
        row += 3
        ws[f"A{row}"] = "Missing Items"
        ws[f"A{row}"].font = Font(bold=True)
        ws[f"A{row}"].border = thin_border
        row += 1
        # --- Missing Cold Items ---
        cold_missing = event.get("details", {}).get("food", {}).get("missing", {}).get("cold_items", [])
        for item in cold_missing:
            row += 1
            for col in range(1, 5):  # columnas B-E
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
            ws.cell(row=row, column=2, value=item)

        # --- Missing Hot Items ---
        hot_missing = event.get("details", {}).get("food", {}).get("missing", {}).get("hot_items", [])
        for item in hot_missing:
            row += 1
            for col in range(1, 5):  # columnas B-E
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
            ws.cell(row=row, column=2, value=item)

        # Ajustar ancho de columnas B-E
        for col in range(1, 5):
            ws.column_dimensions[chr(64 + col)].width = 25
        
       
            

    # Guardar archivo
    wb.save(filename)
    print(f"Archivo Excel creado: {filename}")
