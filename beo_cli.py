from __future__ import annotations

import argparse
import tkinter as tk
from tkinter import filedialog

from beo_pipeline import extract_events_from_pdf
from beo_pipeline.beo_parser import infer_beo_type
from revision_artifacts import build_revision_artifacts, load_events_json, resolve_events_output_path
from save_json import save_json


def _pick_file(title: str, *, filetypes: list[tuple[str, str]]) -> str | None:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected = filedialog.askopenfilename(title=title, filetypes=filetypes)
    finally:
        root.destroy()
    return selected or None


def _ask_document_metadata(pdf_path: str) -> tuple[str | None, int | None]:
    detected_type, detected_revision_number = infer_beo_type(pdf_path)
    options = {
        "1": "original",
        "2": "revision",
        "3": "popup",
    }
    detected_option = next((key for key, value in options.items() if value == detected_type), "1")
    print("Selecciona el tipo de documento:")
    print(f"  1. original{' [detectado]' if detected_option == '1' else ''}")
    print(f"  2. revision{' [detectado]' if detected_option == '2' else ''}")
    print(f"  3. popup{' [detectado]' if detected_option == '3' else ''}")
    type_choice = input(f"Opcion [{detected_option}]: ").strip()
    if not type_choice:
        type_choice = detected_option
    type_value = options.get(type_choice)
    if not type_value:
        raise SystemExit(f"Opcion de tipo no valida: {type_choice}")

    default_revision = "" if type_value == "original" and detected_revision_number == 0 else str(detected_revision_number)
    revision_prompt = "Numero de revision"
    if default_revision:
        revision_prompt += f" [{default_revision}]"
    revision_prompt += ": "
    revision_raw = input(revision_prompt).strip()
    if revision_raw:
        try:
            revision_number = int(revision_raw)
        except ValueError as exc:
            raise SystemExit(f"Numero de revision no valido: {revision_raw}") from exc
    else:
        revision_number = detected_revision_number

    if type_value == "original":
        revision_number = 0
    return type_value, revision_number


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract standardized food-service events from hotel BEO PDFs.")
    parser.add_argument("pdf_path", nargs="?", help="Path to the BEO PDF")
    parser.add_argument("-o", "--output", help="Optional JSON output path")
    parser.add_argument("--baseline", help="Optional baseline events JSON used to build revision diff artifacts")
    parser.add_argument(
        "--pick-file",
        action="store_true",
        help="Open a file picker to select the BEO PDF instead of typing the path",
    )
    parser.add_argument(
        "--pick-baseline",
        action="store_true",
        help="Open a file picker to select the baseline JSON",
    )
    parser.add_argument(
        "--ask-metadata",
        action="store_true",
        help="Ask interactively for document type and revision number",
    )
    parser.add_argument(
        "--beo-type",
        choices=["original", "revision", "popup"],
        help="Override detected document type",
    )
    parser.add_argument(
        "--revision-number",
        type=int,
        help="Override detected revision number",
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip upload to OPS API after generating files",
    )
    args = parser.parse_args()

    pdf_path = args.pdf_path
    if args.pick_file or not pdf_path:
        pdf_path = _pick_file(
            "Select BEO PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if not pdf_path:
            raise SystemExit("No PDF selected.")

    baseline_path = args.baseline
    if args.pick_baseline:
        baseline_path = _pick_file(
            "Select baseline events JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not baseline_path:
            raise SystemExit("No baseline JSON selected.")

    beo_type_override = args.beo_type
    revision_number_override = args.revision_number
    if args.ask_metadata or (args.pick_file and args.beo_type is None and args.revision_number is None):
        beo_type_override, revision_number_override = _ask_document_metadata(pdf_path)

    events = extract_events_from_pdf(
        pdf_path,
        beo_type_override=beo_type_override,
        revision_number_override=revision_number_override,
    )
    resolved_output = resolve_events_output_path(pdf_path, args.output, beo_type_override=beo_type_override)
    baseline_events = load_events_json(baseline_path) if baseline_path else []
    revision_artifacts = None
    if baseline_path:
        revision_artifacts = build_revision_artifacts(
            events,
            source_file=pdf_path,
            baseline_events=baseline_events,
            baseline_source_file=baseline_path,
            beo_type_override=beo_type_override,
        )

    save_json(
        events,
        resolved_output,
        source_file=pdf_path,
        upload_to_ops=not args.no_upload,
        revision_artifacts=revision_artifacts,
    )


if __name__ == "__main__":
    main()
