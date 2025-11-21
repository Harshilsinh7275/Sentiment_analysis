from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List, Dict, Any
import csv
import io
import json
from uuid import uuid4
from fastapi.responses import StreamingResponse
import json
from datetime import datetime

def datetime_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()
    return str(o)


from ..services import db_service, azure_blob_service
from ..sentiment_analysis import analyze_many, analyze_text, build_summary
from .auth_routes import get_current_user
from ..services.results_db_service import save_result_metadata


print(">>> LOADING analysis_routes (Azure Blob Result Storage Enabled) <<<")

router = APIRouter(prefix="/analysis", tags=["Analysis"])


# INTERNAL HELPERS
async def _get_file_and_blob_bytes(file_id: str, current_user):
    file_doc = await db_service.get_file_by_id(file_id)
    if not file_doc or file_doc.get("user_email") != current_user["email"]:
        raise HTTPException(status_code=404, detail="File not found or unauthorized.")

    blob_name = file_doc["blob_name"]

    try:
        content_bytes = await azure_blob_service.download_blob_bytes(blob_name)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download blob '{blob_name}': {exc}",
        )

    return file_doc, content_bytes


def _detect_file_type(file_name: str) -> str:
    if "." in file_name:
        ext = file_name.rsplit(".", 1)[1].lower()
        if ext == "csv":
            return "csv"
    return "txt"



# 1) LINE-BY-LINE SENTIMENT ANALYSIS
@router.post("/linebyline/{file_id}")
async def start_linebyline_analysis(file_id: str, current_user=Depends(get_current_user)):

    file_doc, content_bytes = await _get_file_and_blob_bytes(file_id, current_user)

    file_name = file_doc.get("file_name") or file_doc.get("blob_name")
    file_type = _detect_file_type(file_name)

    rows = []
    results = []

    # ---------- TEXT FILE ----------
    if file_type == "txt":
        text = content_bytes.decode("utf-8", errors="ignore")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        results = analyze_many(lines)

        for idx, (line, res) in enumerate(zip(lines, results), start=1):
            rows.append({
                "index": idx,
                "text": line,
                "label": res["label"],
                "score": res["score"],
            })

    # ---------- CSV FILE ----------
    else:
        csv_text = content_bytes.decode("utf-8", errors="ignore")
        reader = csv.DictReader(io.StringIO(csv_text))

        texts = []
        original_rows = []

        for idx, row in enumerate(reader, start=1):
            # auto-detect column
            text_col = "text" if "text" in row else None
            if not text_col:
                for k, v in row.items():
                    if v and v.strip():
                        text_col = k
                        break

            if not text_col:
                continue

            text_val = (row[text_col] or "").strip()
            if not text_val:
                continue

            texts.append(text_val)
            original_rows.append({"index": idx, "row": row, "text_column": text_col})

        results = analyze_many(texts)

        for base, res in zip(original_rows, results):
            rows.append({
                "index": base["index"],
                "row": base["row"],
                "text_column": base["text_column"],
                "label": res["label"],
                "score": res["score"],
            })

    summary = build_summary(results)


    # SAVE RESULT FILE → AZURE BLOB STORAGE
    result_content = json.dumps({
        "file_id": file_id,
        "file_name": file_name,
        "analysis_type": "linebyline",
        "summary": summary,
        "rows": rows,
        "created_at": str(datetime.utcnow())
    }, indent=4)

    save_filename = f"{uuid4()}_{current_user['email']}_linebyline.json"

    upload_resp = await azure_blob_service.upload_file_to_blob(
        result_content.encode("utf-8"),
        save_filename
    )

    blob_url = upload_resp["url"]

  
    # SAVE METADATA → MONGODB
    await save_result_metadata(
        user_email=current_user["email"],
        analysis_type="linebyline",
        file_name=file_name,
        result_url=blob_url
    )

    return {
        "message": "Line-by-line sentiment analysis completed.",
        "result_url": blob_url,
        "summary": summary,
        "rows": rows,
    }



# 2) WHOLE-FILE SUMMARY ANALYSIS
@router.post("/summary/{file_id}")
async def start_summary_analysis(file_id: str, current_user=Depends(get_current_user)):

    file_doc, content_bytes = await _get_file_and_blob_bytes(file_id, current_user)
    file_name = file_doc.get("file_name") or file_doc.get("blob_name")
    file_type = _detect_file_type(file_name)

    # construct full text
    if file_type == "txt":
        full_text = content_bytes.decode("utf-8", errors="ignore")

    else:
        csv_text = content_bytes.decode("utf-8", errors="ignore")
        reader = csv.DictReader(io.StringIO(csv_text))

        texts = []
        for row in reader:
            col = "text" if "text" in row else next(iter(row))
            val = (row[col] or "").strip()
            if val:
                texts.append(val)

        full_text = "\n".join(texts)

    if not full_text.strip():
        raise HTTPException(status_code=400, detail="File contains no text to analyze.")

    overall = analyze_text(full_text)

    # SAVE RESULT FILE → AZURE BLOB
    result_content = json.dumps({
        "file_id": file_id,
        "file_name": file_name,
        "analysis_type": "summary",
        "overall_result": overall,
        "created_at": str(datetime.utcnow())
    }, indent=4)

    save_filename = f"{uuid4()}_{current_user['email']}_summary.json"

    upload_resp = await azure_blob_service.upload_file_to_blob(
        result_content.encode("utf-8"),
        save_filename
    )

    blob_url = upload_resp["url"]

    # SAVE METADATA → MONGODB
    await save_result_metadata(
        user_email=current_user["email"],
        analysis_type="summary",
        file_name=file_name,
        result_url=blob_url
    )

    return {
        "message": "Summary analysis completed.",
        "result_url": blob_url,
        "overall_result": overall,
    }


# -------------------------------------------------------
# 3) LIST RESULTS
# -------------------------------------------------------
@router.get("/results")
async def list_analysis_results(current_user=Depends(get_current_user)):
    results = await db_service.get_user_results(current_user["email"])
    return {"results": results}


# Helper for JSON serialization
def datetime_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()
    return str(o)


# -------------------------------------------------------
# 4) DOWNLOAD RESULT (CSV or JSON)
# -------------------------------------------------------
@router.get("/download/{result_id}")
async def download_result(
    result_id: str, 
    format: str = "csv", 
    current_user=Depends(get_current_user)
):
    """
    Download a saved analysis result as CSV or JSON.
    """

    # Fetch result document
    result = await db_service.get_result_by_id(result_id)

    if not result or result.get("user_email") != current_user["email"]:
        raise HTTPException(status_code=404, detail="Result not found or unauthorized.")

    # Remove internal Mongo ID
    result.pop("_id", None)

    # -------------------------
    # JSON DOWNLOAD
    # -------------------------
    if format.lower() == "json":
        json_bytes = json.dumps(
            result,
            indent=4,
            default=datetime_converter   # <-- FIXED
        ).encode("utf-8")

        return StreamingResponse(
            io.BytesIO(json_bytes),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=analysis_{result_id}.json"
            }
        )

    # -------------------------
    # CSV DOWNLOAD
    # -------------------------
    if format.lower() == "csv":
        if "rows" not in result:
            raise HTTPException(status_code=400, detail="No rows available for CSV export.")

        output = io.StringIO()
        writer = None

        for row in result["rows"]:
            # Convert datetime fields inside rows if any
            clean_row = {
                k: (v.isoformat() if isinstance(v, datetime) else v)
                for k, v in row.items()
            }

            if writer is None:
                writer = csv.DictWriter(output, fieldnames=clean_row.keys())
                writer.writeheader()

            writer.writerow(clean_row)

        csv_bytes = output.getvalue().encode("utf-8")

        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=analysis_{result_id}.csv"
            }
        )

    # Invalid format
    raise HTTPException(status_code=400, detail="Invalid format. Use ?format=csv or ?format=json.")
