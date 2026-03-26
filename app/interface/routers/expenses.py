import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.infrastructure.database import get_session
from app.infrastructure.repositories.expense_repository import ExpenseRepository
from app.domain.entities.expense import Expense
from app.domain.services.expense_service import generate_installments
from app.interface.dependencies import get_professional_id
from app.interface.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    ExpenseInstallmentResponse,
    ExpenseSummaryResponse,
    MaterialPurchaseResponse,
    LinkedMaterialItem,
)

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("/summary", response_model=ExpenseSummaryResponse)
def expense_summary(
    month: str = Query(..., description="YYYY-MM"),
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ExpenseRepository(session)
    return repo.get_summary(professional_id, month)


@router.get("/monthly-totals")
def monthly_totals(
    months: int = Query(6, ge=1, le=24),
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ExpenseRepository(session)
    return repo.get_monthly_totals(professional_id, months)


@router.get("/material-purchases", response_model=List[MaterialPurchaseResponse])
def material_purchases(
    month: Optional[str] = None,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    """List material expenses with linked stock movements."""
    from app.infrastructure.repositories.stock_movement_repository import StockMovementRepository

    repo = ExpenseRepository(session)
    expenses = repo.list(professional_id, month=month, category="material")

    movement_repo = StockMovementRepository(session)

    # Pre-compute: for installment groups, collect all expense IDs in the group
    # so movements linked to ANY parcela show up on ALL parcelas
    group_expense_ids: dict[uuid.UUID, list[uuid.UUID]] = {}
    for exp in expenses:
        if exp.installment_group_id:
            group_expense_ids.setdefault(exp.installment_group_id, []).append(exp.id)

    # Also collect IDs from other months in the same group (not in current filter)
    seen_groups = set(group_expense_ids.keys())
    if seen_groups:
        all_material = repo.list(professional_id, category="material")
        for exp in all_material:
            if exp.installment_group_id in seen_groups and exp.id not in [
                eid for ids in group_expense_ids.values() for eid in ids
            ]:
                group_expense_ids[exp.installment_group_id].append(exp.id)

    # Cache movements per group to avoid repeated queries
    group_movements_cache: dict[uuid.UUID, list] = {}

    result = []
    for expense in expenses:
        if expense.installment_group_id and expense.installment_group_id in group_expense_ids:
            # Fetch movements for the whole installment group (cached)
            gid = expense.installment_group_id
            if gid not in group_movements_cache:
                all_rows = []
                for eid in group_expense_ids[gid]:
                    all_rows.extend(movement_repo.list_with_material_name(
                        professional_id, expense_id=eid,
                    ))
                # Deduplicate by movement id
                seen_ids = set()
                deduped = []
                for row in all_rows:
                    if row[0].id not in seen_ids:
                        seen_ids.add(row[0].id)
                        deduped.append(row)
                group_movements_cache[gid] = deduped
            rows = group_movements_cache[gid]
        else:
            rows = movement_repo.list_with_material_name(
                professional_id, expense_id=expense.id,
            )

        linked = [
            LinkedMaterialItem(
                material_name=material_name or "—",
                quantity=mov.quantity,
                unit_cost_in_cents=mov.unit_cost_in_cents,
                total_cost_in_cents=mov.total_cost_in_cents,
                date=mov.date,
            )
            for mov, material_name in rows
        ]
        result.append(MaterialPurchaseResponse(
            expense=ExpenseResponse.model_validate(expense),
            linked_materials=linked,
        ))
    return result


@router.get("/", response_model=List[ExpenseResponse])
def list_expenses(
    month: Optional[str] = None,
    category: Optional[str] = None,
    is_paid: Optional[bool] = None,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ExpenseRepository(session)
    return repo.list(professional_id, month=month, category=category, is_paid=is_paid)


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ExpenseRepository(session)
    expense = repo.get_by_id(professional_id, expense_id)
    if not expense:
        raise HTTPException(404, "Expense not found")
    return expense


@router.post("/", response_model=ExpenseInstallmentResponse, status_code=201)
def create_expense(
    body: ExpenseCreate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ExpenseRepository(session)

    if body.installments and body.installments > 1:
        records = generate_installments(
            name=body.name,
            category=body.category,
            amount_in_cents=body.amount_in_cents,
            due_day=body.due_day,
            reference_month=body.reference_month,
            notes=body.notes,
            installments=body.installments,
        )
        expenses = [
            Expense(**r, professional_id=professional_id) for r in records
        ]
        created = repo.create_many(expenses)
        return ExpenseInstallmentResponse(
            expense=ExpenseResponse.model_validate(created[0]),
            installments_created=len(created),
            installment_group_id=created[0].installment_group_id,
        )

    expense = Expense(
        professional_id=professional_id,
        name=body.name,
        category=body.category,
        amount_in_cents=body.amount_in_cents,
        recurrence=body.recurrence,
        due_day=body.due_day,
        reference_month=body.reference_month,
        notes=body.notes,
    )
    created = repo.create(expense)
    return ExpenseInstallmentResponse(
        expense=ExpenseResponse.model_validate(created),
        installments_created=1,
    )


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: uuid.UUID,
    body: ExpenseUpdate,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ExpenseRepository(session)
    expense = repo.get_by_id(professional_id, expense_id)
    if not expense:
        raise HTTPException(404, "Expense not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)
    return repo.update(expense)


@router.delete("/{expense_id}", status_code=204)
def delete_expense(
    expense_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ExpenseRepository(session)
    expense = repo.get_by_id(professional_id, expense_id)
    if not expense:
        raise HTTPException(404, "Expense not found")
    repo.delete(expense)


@router.patch("/{expense_id}/pay", response_model=ExpenseResponse)
def pay_expense(
    expense_id: uuid.UUID,
    professional_id: uuid.UUID = Depends(get_professional_id),
    session: Session = Depends(get_session),
):
    repo = ExpenseRepository(session)
    expense = repo.get_by_id(professional_id, expense_id)
    if not expense:
        raise HTTPException(404, "Expense not found")
    return repo.mark_paid(expense)
