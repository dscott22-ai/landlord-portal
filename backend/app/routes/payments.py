from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.database import get_connection
import os
import shutil
from uuid import uuid4

router = APIRouter()

UPLOAD_DIR = "app/uploads/payment_proofs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/payments/pay-rent")
def pay_rent_json(payload: dict):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO payments
        (tenant_name, property_name, unit_label, amount, method, status, proof_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        payload["tenant_name"],
        payload["property_name"],
        payload["unit_label"],
        payload["amount"],
        payload["method"],
        payload.get("status", "Paid"),
        None
    ))

    conn.commit()
    payment_id = cursor.lastrowid
    conn.close()

    return {
        "message": "Payment recorded successfully",
        "payment_id": payment_id
    }


@router.post("/payments/zelle-submit")
async def zelle_submit(
    tenant_name: str = Form(...),
    property_name: str = Form(...),
    unit_label: str = Form(...),
    amount: float = Form(...),
    method: str = Form("Zelle"),
    proof: UploadFile = File(...)
):
    if not proof.filename:
        raise HTTPException(status_code=400, detail="Payment proof is required.")

    ext = os.path.splitext(proof.filename)[1]
    unique_name = f"{uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(proof.file, buffer)

    proof_path = f"/uploads/payment_proofs/{unique_name}"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO payments
        (tenant_name, property_name, unit_label, amount, method, status, proof_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        tenant_name,
        property_name,
        unit_label,
        amount,
        method,
        "Pending Verification",
        proof_path
    ))

    conn.commit()
    payment_id = cursor.lastrowid
    conn.close()

    return {
        "message": "Zelle payment submitted for verification",
        "payment_id": payment_id,
        "proof_path": proof_path
    }


@router.get("/owner/payments")
def get_payments():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM payments ORDER BY id DESC")
    payments = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "count": len(payments),
        "payments": payments
    }


@router.put("/owner/payments/{payment_id}/verify")
def verify_payment(payment_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
    payment = cursor.fetchone()

    if not payment:
        conn.close()
        raise HTTPException(status_code=404, detail="Payment not found")

    cursor.execute("""
        UPDATE payments
        SET status = ?
        WHERE id = ?
    """, ("Paid", payment_id))

    conn.commit()
    conn.close()

    return {"message": "Payment verified successfully"}
