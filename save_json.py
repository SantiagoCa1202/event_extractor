import json
import os

from ops_events_api import upload_events_to_ops
from revision_artifacts import save_revision_artifacts


def save_json(
    data,
    output_path: str,
    source_file: str | None = None,
    upload_to_ops: bool = True,
    revision_artifacts: dict | None = None,
):
    """Guarda un objeto Python como archivo JSON con formato legible."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"JSON guardado en: {os.path.abspath(output_path)}")

    if revision_artifacts is not None:
        diff_path, upsert_path = save_revision_artifacts(revision_artifacts, output_events_path=output_path)
        print(f"Revision diff guardado en: {os.path.abspath(diff_path)}")
        print(f"Upsert payload guardado en: {os.path.abspath(upsert_path)}")

    if upload_to_ops and isinstance(data, list):
        result = upload_events_to_ops(data, source_file=source_file or output_path)
        if not result.attempted:
            print(f"OPS upload omitido. job_id={result.job_id} motivo={result.message}")
        elif result.success:
            print(f"OPS upload completado. job_id={result.job_id} status={result.status_code}")
        else:
            print(f"OPS upload fallo. job_id={result.job_id} detalle={result.message}")
