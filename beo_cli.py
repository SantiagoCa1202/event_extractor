from __future__ import annotations

import argparse
import json
from pathlib import Path

from beo_pipeline import extract_events_from_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract standardized food-service events from hotel BEO PDFs.")
    parser.add_argument("pdf_path", help="Path to the BEO PDF")
    parser.add_argument("-o", "--output", help="Optional JSON output path")
    args = parser.parse_args()

    events = extract_events_from_pdf(args.pdf_path)
    payload = json.dumps(events, indent=2, ensure_ascii=False)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
