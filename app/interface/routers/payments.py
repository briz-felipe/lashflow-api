import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.infrastructure.database import get_session
from app.infrastructure.repositories.payment_repository import PaymentRepository
from app.domain.entities.payment import Payment, PartialPaymentRecord
from app.domain.services.payment_service import calculate_payment_status, sum_partial_payments
from app.interface.dependencies import get_professional_id
from app.interface.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    PaymentResponse,
    PaymentStatsResponse,
    MonthlyRevenueItem,
    MethodBreakdownResponse,
    PartialPaymentRecordResponse,
)

router = APIRouter(prefix="/payments", tags=["payments"])


def _to_response(payment: Payment, repo: PaymentRepository) -> PaymentResponse:
    partials = repo.get_partial_records(payment.id)
    data = PaymentResponse.model_validate(payment)
    data.partial_payments = [PartialPaymentRecordResponse.model_validate(p) for p in partials]
    return data


@router.get("/stats", response_model=PaymentStatsResponse)
def payment_stats(
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = PaymentRepository(session)
    stats = repo.get_stats(professional_id)
    return PaymentStatsResponse(**stats)


@router.get("/monthly-revenue", response_model=List[MonthlyRevenueItem])
def monthly_revenue(
    months: int = Query(6, ge=1, le=24),
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = PaymentRepository(session)
    return repo.get_monthly_revenue(professional_id, months)


@router.get("/method-breakdown", response_model=MethodBreakdownResponse)
def method_breakdown(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = PaymentRepository(session)
    breakdown = repo.get_method_breakdown(professional_id, from_date, to_date)
    return MethodBreakdownResponse(**breakdown)


@router.get("/by-appointment/{appointment_id}", response_model=PaymentResponse)
def get_by_appointment(
    appointment_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = PaymentRepository(session)
    payment = repo.get_by_appointment(professional_id, appointment_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    return _to_response(payment, repo)


@router.get("/cash-flow", response_model=List[PaymentResponse])
def cash_flow(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = PaymentRepository(session)
    payments = repo.list(professional_id, from_date=from_date, to_date=to_date)
    return [_to_response(p, repo) for p in payments]


@router.get("/", response_model=List[PaymentResponse])
def list_payments(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = PaymentRepository(session)
    payments = repo.list(professional_id, from_date=from_date, to_date=to_date)
    return [_to_response(p, repo) for p in payments]


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = PaymentRepository(session)
    payment = repo.get_by_id(professional_id, payment_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    return _to_response(payment, repo)


@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(
    body: PaymentCreate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = PaymentRepository(session)
    if repo.get_by_appointment(professional_id, body.appointment_id):
        raise HTTPException(409, "Payment already exists for this appointment")

    status = calculate_payment_status(body.paid_amount_in_cents, body.total_amount_in_cents)
    payment = Payment(
        professional_id=professional_id,
        appointment_id=body.appointment_id,
        client_id=body.client_id,
        total_amount_in_cents=body.total_amount_in_cents,
        paid_amount_in_cents=body.paid_amount_in_cents,
        status=status,
        method=body.method,
        paid_at=datetime.utcnow() if status.value == "paid" else None,
        notes=body.notes,
    )
    created = repo.create(payment)
    return _to_response(created, repo)


@router.patch("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: uuid.UUID,
    body: PaymentUpdate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = PaymentRepository(session)
    payment = repo.get_by_id(professional_id, payment_id)
    if not payment:
        raise HTTPException(404, "Payment not found")

    if body.partial_payment:
        partial = PartialPaymentRecord(
            payment_id=payment.id,
            amount_in_cents=body.partial_payment.amount_in_cents,
            method=body.partial_payment.method,
        )
        repo.add_partial(partial)
        # Recalculate paid amount from all partials
        all_partials = repo.get_partial_records(payment.id)
        payment.paid_amount_in_cents = sum_partial_payments(
            [p.amount_in_cents for p in all_partials]
        )

    if body.paid_amount_in_cents is not None:
        payment.paid_amount_in_cents = body.paid_amount_in_cents
    if body.method is not None:
        payment.method = body.method
    if body.notes is not None:
        payment.notes = body.notes

    payment.status = calculate_payment_status(
        payment.paid_amount_in_cents, payment.total_amount_in_cents
    )
    if payment.status.value == "paid" and not payment.paid_at:
        payment.paid_at = datetime.utcnow()

    updated = repo.update(payment)
    return _to_response(updated, repo)
