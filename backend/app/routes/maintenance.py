from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import os
import shutil
from uuid import uuid4

router = APIRouter()

maintenance_requests = []

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

    request_data = {
        "id": len(maintenance_requests) + 1,
        "tenant_name": tenant_name,
        "property_name": property_name,
        "unit_label": unit_label,
        "category": category,
        "priority": priority,
        "location": location,
        "description": description,
        "entry_permission": entry_permission,
        "photos": saved_photo_paths,
        "status": status
    }

    maintenance_requests.append(request_data)

    return {
        "message": "Maintenance request submitted successfully",
        "request": request_data
    }


@router.get("/owner/maintenance")
def get_all_maintenance_requests(property_name: Optional[str] = Query(default=None)):
    if property_name:
        filtered_requests = [
            request for request in maintenance_requests
            if request["property_name"].lower() == property_name.lower()
        ]
        return {
            "count": len(filtered_requests),
            "requests": filtered_requests
        }

    return {
        "count": len(maintenance_requests),
        "requests": maintenance_requests
    }


@router.put("/owner/maintenance/{request_id}")
def update_maintenance_status(request_id: int, update: StatusUpdate):
    valid_statuses = ["Submitted", "In Progress", "Completed"]

    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    for request in maintenance_requests:
        if request["id"] == request_id:
            request["status"] = update.status
            return {
                "message": "Maintenance request updated successfully",
                "request": request
            }

    raise HTTPException(status_code=404, detail="Maintenance request not found")