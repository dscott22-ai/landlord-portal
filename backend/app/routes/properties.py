from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_connection

router = APIRouter()


class PropertyCreate(BaseModel):
    name: str
    owner_id: int


class UnitCreate(BaseModel):
    property_id: int
    unit_label: str
    rent_amount: float = 0


@router.post("/properties")
def create_property(property_data: PropertyCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO properties (name, owner_id) VALUES (?, ?)",
        (property_data.name, property_data.owner_id)
    )

    conn.commit()
    property_id = cursor.lastrowid
    conn.close()

    return {
        "message": "Property created successfully",
        "property_id": property_id,
        "name": property_data.name
    }


@router.get("/properties")
def get_properties():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM properties")
    properties = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "count": len(properties),
        "properties": properties
    }


@router.post("/units")
def create_unit(unit_data: UnitCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO units (property_id, unit_label, rent_amount) VALUES (?, ?, ?)",
        (unit_data.property_id, unit_data.unit_label, unit_data.rent_amount)
    )

    conn.commit()
    unit_id = cursor.lastrowid
    conn.close()

    return {
        "message": "Unit created successfully",
        "unit_id": unit_id,
        "unit_label": unit_data.unit_label
    }


@router.get("/units")
def get_units():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT units.id, units.property_id, units.unit_label, units.rent_amount, properties.name AS property_name
        FROM units
        JOIN properties ON units.property_id = properties.id
    """)
    units = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "count": len(units),
        "units": units
    }
class TenantAssign(BaseModel):
    user_id: int
    property_id: int
    unit_id: int


@router.post("/assign-tenant")
def assign_tenant(data: TenantAssign):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tenants (user_id, property_id, unit_id) VALUES (?, ?, ?)",
        (data.user_id, data.property_id, data.unit_id)
    )

    conn.commit()
    conn.close()

    return {"message": "Tenant assigned successfully"}
@router.get("/tenant/{user_id}/unit")
def get_tenant_unit(user_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT properties.name AS property_name,
           units.unit_label,
           units.rent_amount
    FROM tenants
    JOIN properties ON tenants.property_id = properties.id
    JOIN units ON tenants.unit_id = units.id
    WHERE tenants.user_id = ?
    """, (user_id,))

    row = cursor.fetchone()

    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Tenant assignment not found")

    return dict(row)
