import json
import os

def save_json(data, output_path: str):
    """Guarda un objeto Python como archivo JSON con formato legible."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅ JSON guardado en: {os.path.abspath(output_path)}")
    