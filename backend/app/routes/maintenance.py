from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from app.database import get_connection
import os
import shutil
from uuid import uuid4
import json

router = APIRouter()

UPLOAD_DIR = "app/uploads/maintenance"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class StatusUpdate(BaseModel):
    status: str


@router.post("/maintenance/request")
async def create_maintenance_request(
    tenant_name: str = Form(...),
    property_name: str = Form(...),
    unit_label: str = Form(...),
    category: str = Form(...),
    priority: str = Form(...),
    location: str = Form(...),
    description: str = Form(...),
    entry_permission: str = Form(...),
    status: str = Form("Submitted"),
    photos: list[UploadFile] = File(...)
):
    if not description.strip():
        raise HTTPException(
            status_code=400,
            detail="A description is required for maintenance requests."
        )

    if not photos or len(photos) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one photo is required for maintenance requests."
        )

    saved_photo_paths = []

    for photo in photos:
        if not photo.filename:
            continue

        ext = os.path.splitext(photo.filename)[1]
        unique_name = f"{uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

        saved_photo_paths.append(f"/uploads/maintenance/{unique_name}")

    if len(saved_photo_paths) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one valid photo is required."
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO maintenance_requests
        (tenant_name, property_name, unit_label, category, priority, location, description, entry_permission, status, photos)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tenant_name,
        property_name,
        unit_label,
        category,
        priority,
        location,
        description,
        entry_permission,
        status,
        json.dumps(saved_photo_paths)
    ))

    conn.commit()
    request_id = cursor.lastrowid
    conn.close()

    return {
        "message": "Maintenance request submitted successfully",
        "request_id": request_id
    }


@router.get("/owner/maintenance")
def get_all_maintenance_requests(property_name: Optional[str] = Query(default=None)):
    conn = get_connection()
    cursor = conn.cursor()

    if property_name:
        cursor.execute("""
            SELECT * FROM maintenance_requests
            WHERE LOWER(property_name) = LOWER(?)
            ORDER BY id DESC
        """, (property_name,))
    else:
        cursor.execute("SELECT * FROM maintenance_requests ORDER BY id DESC")

    rows = cursor.fetchall()
    conn.close()

    requests = []
    for row in rows:
        item = dict(row)
        item["photos"] = json.loads(item["photos"]) if item["photos"] else []
        requests.append(item)

    return {
        "count": len(requests),
        "requests": requests
    }


@router.put("/owner/maintenance/{request_id}")
def update_maintenance_status(request_id: int, update: StatusUpdate):
    valid_statuses = ["Submitted", "In Progress", "Completed"]

    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM maintenance_requests WHERE id = ?", (request_id,))
    existing = cursor.fetchone()

    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Maintenance request not found")

    cursor.execute("""
        UPDATE maintenance_requests
        SET status = ?
        WHERE id = ?
    """, (update.status, request_id))

    conn.commit()
    conn.close()

    return {"message": "Maintenance request updated successfully"}