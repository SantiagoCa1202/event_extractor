import json
import re
from pathlib import Path

from food_dictionary import hot_items


BASE_DIR = Path(__file__).resolve().parent
MENU_PATH = BASE_DIR / "assets" / "main_menu.json"

with MENU_PATH.open("r", encoding="utf-8") as menu_file:
    data = json.load(menu_file)

menus = {m["title"].lower(): m for m in data["menu"]}


def clean_details(text: str) -> str:
    lines = text.split("\n")
    cleaned_lines = []
    irrelevant_patterns = [
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
        r"^\s*$",
        r"(?i)based on 60 minutes of continuous service, price includes 10% upcharge for groups under \d+ppl",
        r"(?i)\$\d+(\.\d+)? per person",
        r"(?i)room setup \d{1,2}:\d{2} (AM|PM)-\d{1,2}:\d{2} (AM|PM).*",
        r"(?i)u-shape",
        r"(?i)any room set changes within 24 hours of the event will be charged \$\d+ per incident.*",
        r"(?i)employee, service employees and/or service bartenders.*",
        r"(?i)banquet function, the hotel will retain the portion of their service charge.*",
        r"(?i)staffing for the function, and the service charge is not the property of those third[-â€]party employees.*",
        r"(?i)property of the employee\(s\) providing service to you.*",
    ]

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        if any(re.search(pattern, line_clean) for pattern in irrelevant_patterns):
            continue
        cleaned_lines.append(line_clean)

    return "\n".join(cleaned_lines)


def clasificar_por_menu(menu_name: str, detalles: list[str]):
    resultado = {
        "matched": {},
        "extra": [],
        "missing": {},
        "waste_items": [],
    }

    if menu_name.lower() not in menus:
        raise ValueError(f"Menú '{menu_name}' no encontrado en main_menu.json")

    menu = menus[menu_name.lower()]

    for section, bloques in menu["sections"].items():
        resultado["matched"][section] = []
        resultado["missing"][section] = [
            item["name"].lower()
            for bloque in bloques
            for item in bloque["items"]
        ]

    for detalle in detalles:
        detalle_lower = detalle.lower()
        encontrado = False

        for section, bloques in menu["sections"].items():
            for bloque in bloques:
                for item in bloque["items"]:
                    item_name = item["name"].lower()
                    if item_name in detalle_lower:
                        resultado["matched"][section].append(item)
                        if item_name in resultado["missing"][section]:
                            resultado["missing"][section].remove(item_name)
                        encontrado = True

        if not encontrado:
            resultado["extra"].append(detalle)

    return resultado


def clasificar_waste_items(detalles: list[str]) -> list[str]:
    waste_encontrados = set()
    for detalle in detalles:
        detalle_lower = detalle.lower()
        for item in hot_items:
            if item.lower() in detalle_lower:
                waste_encontrados.add(item)
                break
    return list(waste_encontrados)
