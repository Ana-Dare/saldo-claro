import calendar
from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.schemas.dashboard import DashboardResponse, ExpenseByCategoryItem


def get_dashboard(db: Session, month: int, year: int) -> DashboardResponse:
    last_day = calendar.monthrange(year, month)[1]
    period_start = date(year, month, 1)
    period_end = date(year, month, last_day)

    base_filter = (
        Transaction.date >= period_start,
        Transaction.date <= period_end,
    )

    total_income = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            *base_filter,
            Transaction.type == TransactionType.income,
            Transaction.status == TransactionStatus.completed,
        )
        .scalar()
    )
    total_expenses = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            *base_filter,
            Transaction.type == TransactionType.expense,
            Transaction.status == TransactionStatus.completed,
        )
        .scalar()
    )
    pending_expenses = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            *base_filter,
            Transaction.type == TransactionType.expense,
            Transaction.status == TransactionStatus.pending,
        )
        .scalar()
    )

    total_income = Decimal(total_income)
    total_expenses = Decimal(total_expenses)
    pending_expenses = Decimal(pending_expenses)
    current_balance = total_income - total_expenses
    projected_balance = current_balance - pending_expenses

    rows = (
        db.query(
            Category.id,
            Category.name,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            *base_filter,
            Transaction.type == TransactionType.expense,
            Transaction.status == TransactionStatus.completed,
        )
        .group_by(Category.id, Category.name)
        .order_by(Category.name)
        .all()
    )

    expenses_by_category = [
        ExpenseByCategoryItem(
            category_id=row.id,
            category_name=row.name,
            total=Decimal(row.total),
        )
        for row in rows
    ]

    return DashboardResponse(
        month=month,
        year=year,
        total_income=total_income,
        total_expenses=total_expenses,
        current_balance=current_balance,
        pending_expenses=pending_expenses,
        projected_balance=projected_balance,
        expenses_by_category=expenses_by_category,
    )
