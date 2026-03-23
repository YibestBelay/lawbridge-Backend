# routers/payments.py

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

from database import get_db
from models import Payment, UserRole
from schemas import PaymentCreate, PaymentUpdate, PaymentResponse
from auth import get_current_user

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


# ── Helper: generate invoice number ───────────────────────────
def generate_invoice_number(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    # Count only payments created this year for a year-scoped, collision-safer number
    from sqlalchemy import extract
    count = db.execute(
        select(func.count(Payment.id)).where(
            extract("year", Payment.created_at) == year
        )
    ).scalar()
    number = str(count + 1).zfill(3)  # e.g. 001, 002, 003
    return f"#INV-{year}-{number}"


# ── Helper: ownership/access check ────────────────────────────
def assert_payment_access(payment: Payment, current_user: dict):
    """Raises 403 if the user is neither client, lawyer, nor admin for this payment."""
    user_role = current_user.get("role")
    user_id = uuid.UUID(current_user["user_id"])

    if user_role == UserRole.admin:
        return  # admins can access everything

    if payment.client_id != user_id and payment.lawyer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this payment"
        )


# ══════════════════════════════════════════
# CREATE PAYMENT — POST /payments
# ══════════════════════════════════════════
@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    new_payment = Payment(
        invoice_number=generate_invoice_number(db),
        client_id=uuid.UUID(current_user["user_id"]),
        lawyer_id=payment_data.lawyer_id,
        case_id=payment_data.case_id,
        amount=payment_data.amount,
        method=payment_data.method,
        due_date=payment_data.due_date,
        notes=payment_data.notes
    )

    try:
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid reference: case_id or lawyer_id does not exist"
        )

    return new_payment


# ══════════════════════════════════════════
# GET MY PAYMENTS — GET /payments
# ══════════════════════════════════════════
@router.get("/", response_model=list[PaymentResponse])
def get_my_payments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = uuid.UUID(current_user["user_id"])
    user_role = current_user.get("role")

    # Admins see all payments; clients & lawyers see only their own
    if user_role == UserRole.admin:
        payments = db.execute(select(Payment)).scalars().all()
    else:
        payments = db.execute(
            select(Payment).where(
                (Payment.client_id == user_id) | (Payment.lawyer_id == user_id)
            )
        ).scalars().all()

    return payments


# ══════════════════════════════════════════
# GET ONE PAYMENT — GET /payments/{payment_id}
# ══════════════════════════════════════════
@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    payment = db.get(Payment, payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    assert_payment_access(payment, current_user)

    return payment


# ══════════════════════════════════════════
# UPDATE PAYMENT STATUS — PATCH /payments/{payment_id}
# ══════════════════════════════════════════
@router.patch("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: uuid.UUID,
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    payment = db.get(Payment, payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Only the lawyer assigned to the payment (or admin) can update it
    user_role = current_user.get("role")
    user_id = uuid.UUID(current_user["user_id"])

    if user_role != UserRole.admin and payment.lawyer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned lawyer or an admin can update a payment"
        )

    update_data = payment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)

    # Auto-stamp paid_at when status is set to Completed
    from models import PaymentStatus
    if update_data.get("status") == PaymentStatus.completed and not payment.paid_at:
        payment.paid_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(payment)

    return payment


# ══════════════════════════════════════════
# DELETE PAYMENT — DELETE /payments/{payment_id}
# ══════════════════════════════════════════
@router.delete("/{payment_id}", status_code=204)
def delete_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    payment = db.get(Payment, payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Only the client who created it or an admin can delete a payment
    user_role = current_user.get("role")
    user_id = uuid.UUID(current_user["user_id"])

    if user_role != UserRole.admin and payment.client_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the client who created this payment or an admin can delete it"
        )

    db.delete(payment)
    db.commit()

    return None