"""Dashboard único do SaldoClaro."""

from __future__ import annotations

from datetime import date
from typing import Any

import gradio as gr

from frontend.views.categories import build_categories, load_categories_screen
from frontend.views.dashboard import (
    VALUE_TO_MONTH,
    fetch_summary,
    header_html,
)
from frontend.views.expenses import (
    build_expenses_section,
    cancel_mark_paid,
    clear_expense_form,
    confirm_mark_paid,
    load_expenses,
    on_expense_select,
    open_add_expense_form,
    open_edit_expense_form,
    request_mark_paid,
    save_expense,
)
from frontend.views.transactions import build_transactions, load_transactions_screen


def _shift_month(month: int, year: int, delta: int) -> tuple[int, int]:
    month = int(month) + delta
    year = int(year)
    if month < 1:
        return 12, year - 1
    if month > 12:
        return 1, year + 1
    return month, year


def refresh_dashboard(month: int, year: int) -> tuple[Any, ...]:
    """Atualiza resumo + despesas do mês."""
    summary = fetch_summary(month, year)
    expenses = load_expenses(month, year)
    return summary + expenses


def go_prev_month(month: int, year: int) -> tuple[Any, ...]:
    month, year = _shift_month(month, year, -1)
    return (month, year) + refresh_dashboard(month, year)


def go_next_month(month: int, year: int) -> tuple[Any, ...]:
    month, year = _shift_month(month, year, 1)
    return (month, year) + refresh_dashboard(month, year)


def after_expense_mutation(*args: Any) -> tuple[Any, ...]:
    """Salva despesa e atualiza resumo + lista."""
    result = save_expense(*args)
    # args: editing_id, desc, amount, cat, date, status, month, year
    month, year = args[-2], args[-1]
    summary = fetch_summary(month, year)
    # result already has expenses outputs; prepend summary
    return summary + result


def after_confirm_paid(editing_id: Any, month: int, year: int) -> tuple[Any, ...]:
    result = confirm_mark_paid(editing_id, month, year)
    summary = fetch_summary(month, year)
    return summary + result


def build_home() -> dict[str, Any]:
    today = date.today()

    gr.HTML(header_html())

    month_state = gr.State(today.month)
    year_state = gr.State(today.year)

    with gr.Row(elem_classes=["sc-month-nav"]):
        prev_btn = gr.Button("←", scale=0, min_width=48)
        summary_title = gr.HTML(
            f'<h2 class="sc-summary-title">Resumo {VALUE_TO_MONTH[today.month]}</h2>'
        )
        next_btn = gr.Button("→", scale=0, min_width=48)

    summary_status = gr.HTML('<p class="sc-status-loading">Carregando indicadores…</p>')
    metrics_html = gr.HTML()
    projected_html = gr.HTML()

    summary_outputs = [summary_title, metrics_html, projected_html, summary_status]

    exp = build_expenses_section()
    expense_outputs = [
        exp["html"],
        exp["select"],
        exp["editing_id"],
        exp["description"],
        exp["amount"],
        exp["category"],
        exp["date_input"],
        exp["status_input"],
        exp["confirm_group"],
        exp["form_group"],
        exp["status"],
    ]

    dash_outputs = summary_outputs + expense_outputs

    tx = build_transactions(embedded=True)
    cat = build_categories(embedded=True)

    # Navegação de mês
    prev_btn.click(
        go_prev_month,
        inputs=[month_state, year_state],
        outputs=[month_state, year_state] + dash_outputs,
    )
    next_btn.click(
        go_next_month,
        inputs=[month_state, year_state],
        outputs=[month_state, year_state] + dash_outputs,
    )

    # Despesas
    exp["select"].change(
        on_expense_select,
        inputs=[exp["select"], month_state, year_state],
        outputs=[
            exp["editing_id"],
            exp["description"],
            exp["amount"],
            exp["category"],
            exp["date_input"],
            exp["status_input"],
            exp["confirm_group"],
            exp["status"],
        ],
    )
    exp["add_btn"].click(
        open_add_expense_form,
        outputs=[
            exp["editing_id"],
            exp["description"],
            exp["amount"],
            exp["category"],
            exp["date_input"],
            exp["status_input"],
            exp["confirm_group"],
            exp["form_group"],
            exp["status"],
        ],
    )
    exp["edit_btn"].click(
        open_edit_expense_form,
        inputs=[exp["editing_id"]],
        outputs=[exp["form_group"], exp["status"]],
    )
    exp["mark_btn"].click(
        request_mark_paid,
        inputs=[exp["editing_id"]],
        outputs=[exp["confirm_group"], exp["status"]],
    )
    exp["confirm_btn"].click(
        after_confirm_paid,
        inputs=[exp["editing_id"], month_state, year_state],
        outputs=dash_outputs,
    )
    exp["cancel_confirm_btn"].click(
        cancel_mark_paid,
        outputs=[exp["confirm_group"], exp["status"]],
    )
    exp["save_btn"].click(
        after_expense_mutation,
        inputs=[
            exp["editing_id"],
            exp["description"],
            exp["amount"],
            exp["category"],
            exp["date_input"],
            exp["status_input"],
            month_state,
            year_state,
        ],
        outputs=dash_outputs,
    )
    exp["clear_btn"].click(
        clear_expense_form,
        outputs=[
            exp["editing_id"],
            exp["description"],
            exp["amount"],
            exp["category"],
            exp["date_input"],
            exp["status_input"],
            exp["confirm_group"],
            exp["form_group"],
            exp["status"],
        ],
    )

    return {
        "month_state": month_state,
        "year_state": year_state,
        "dash_outputs": dash_outputs,
        "tx_filters": tx["filters"],
        "tx_outputs": tx["outputs"],
        "cat_filters": cat["filters"],
        "cat_outputs": cat["outputs"],
    }
