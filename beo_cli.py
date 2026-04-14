from __future__ import annotations

import argparse
import json

from beo_pipeline import extract_events_from_pdf
from ops_events_api import upload_events_to_ops
from save_json import save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract standardized food-service events from hotel BEO PDFs.")
    parser.add_argument("pdf_path", help="Path to the BEO PDF")
    parser.add_argument("-o", "--output", help="Optional JSON output path")
    args = parser.parse_args()

    events = extract_events_from_pdf(args.pdf_path)
    payload = json.dumps(events, indent=2, ensure_ascii=False)

    if args.output:
        save_json(events, args.output, source_file=args.pdf_path)
    else:
        print(payload)
        result = upload_events_to_ops(events, source_file=args.pdf_path)
        if not result.attempted:
            print(f"OPS upload omitido. job_id={result.job_id} motivo={result.message}")
        elif result.success:
            print(f"OPS upload completado. job_id={result.job_id} status={result.status_code}")
        else:
            print(f"OPS upload fallo. job_id={result.job_id} detalle={result.message}")


if __name__ == "__main__":
    main()
