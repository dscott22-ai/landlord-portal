from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

payments = []


class PaymentRequest(BaseModel):
    tenant_name: str
    property_name: str
    unit_label: str
    amount: float
    method: str
    status: str = "Paid"


@router.post("/payments/pay-rent")
def pay_rent(payment: PaymentRequest):
    payment_data = payment.model_dump()
    payment_data["id"] = len(payments) + 1
    payments.append(payment_data)

    return {
        "message": "Rent payment recorded successfully",
        "payment": payment_data
    }


@router.get("/owner/payments")
def get_all_payments():
    return {
        "count": len(payments),
        "payments": payments
    }