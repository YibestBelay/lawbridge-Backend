# routers/cases.py

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from database import get_db
from models import Case
from schemas import CaseCreate, CaseResponse, CaseUpdate
from auth import get_current_user

router = APIRouter(
    prefix="/cases",
    tags=["Cases"]
)


# ══════════════════════════════════════════
# CREATE CASE — POST /cases
# ══════════════════════════════════════════
@router.post("/", response_model=CaseResponse, status_code=201)
def create_case(
    case_data: CaseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    new_case = Case(
        title=case_data.title,
        description=case_data.description,
        client_id=uuid.UUID(current_user["user_id"]),  # taken from JWT token
        lawyer_id=case_data.lawyer_id,
        category_id=case_data.category_id,
        fee_amount=case_data.fee_amount
    )

    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    return new_case


# ══════════════════════════════════════════
# GET ALL MY CASES — GET /cases
# ══════════════════════════════════════════
@router.get("/", response_model=list[CaseResponse])
def get_my_cases(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # returns only cases belonging to the logged in user
    cases = db.execute(
        select(Case).where(Case.client_id == uuid.UUID(current_user["user_id"]))
    ).scalars().all()

    return cases


# ══════════════════════════════════════════
# GET ONE CASE — GET /cases/{case_id}
# ══════════════════════════════════════════
@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    case = db.get(Case, case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return case


# ══════════════════════════════════════════
# UPDATE CASE — PATCH /cases/{case_id}
# ══════════════════════════════════════════
@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: uuid.UUID,
    case_data: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    case = db.get(Case, case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    for field, value in case_data.model_dump(exclude_unset=True).items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)

    return case


# ══════════════════════════════════════════
# DELETE CASE — DELETE /cases/{case_id}
# ══════════════════════════════════════════
@router.delete("/{case_id}", status_code=204)
def delete_case(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    case = db.get(Case, case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    db.delete(case)
    db.commit()

    return None