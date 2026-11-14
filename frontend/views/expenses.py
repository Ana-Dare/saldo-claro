"""Visão resumida de despesas do mês (acompanhamento rápido)."""

from __future__ import annotations

import calendar
from datetime import date
from typing import Any

import gradio as gr

from frontend.api_client import (
    ApiError,
    create_transaction,
    list_categories,
    list_transactions,
    update_transaction,
)
from frontend.formatting import format_brl, format_date_br, parse_api_amount
from frontend.views.transactions import _category_maps, _status_html, _validate_form


def _period_iso(month: int, year: int) -> tuple[str, str]:
    last = calendar.monthrange(int(year), int(month))[1]
    return (
        date(int(year), int(month), 1).isoformat(),
        date(int(year), int(month), last).isoformat(),
    )


def expenses_list_html(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<div class="sc-empty sc-empty-tight">Nenhuma despesa neste mês.</div>'

    items = []
    for row in rows:
        paid = row["status"] == "completed"
        status_class = "sc-dot-paid" if paid else "sc-dot-pending"
        status_label = "Paga" if paid else "Pendente"
        items.append(
            f"""
            <div class="sc-expense-row">
              <div class="sc-expense-main">
                <span class="sc-expense-name">{row['description']}</span>
                <span class="sc-expense-cat">{row['category']}</span>
              </div>
              <span class="sc-expense-amount">{format_brl(row['amount'])}</span>
              <span class="{status_class}"><span aria-hidden="true">●</span> {status_label}</span>
            </div>
            """
        )
    return f'<div class="sc-expense-list">{"".join(items)}</div>'


def _expense_category_choices() -> list[str]:
    try:
        categories = list_categories()
        _, _, by_type = _category_maps(categories)
        return by_type.get("Despesa", [])
    except ApiError:
        return []


def _load_expense_rows(month: int, year: int) -> tuple[list[dict[str, Any]], str]:
    start, end = _period_iso(month, year)
    try:
        categories = list_categories()
        expenses = list_transactions(
            type_="expense",
            start_date=start,
            end_date=end,
        )
    except ApiError as exc:
        return [], _status_html(f"⚠ {exc.message}", "error")

    id_to_name, _, _ = _category_maps(categories)
    rows = [
        {
            "id": item["id"],
            "description": item["description"],
            "category": id_to_name.get(int(item["category_id"]), f"#{item['category_id']}"),
            "amount": item["amount"],
            "date": item["date"],
            "status": item["status"],
        }
        for item in expenses
    ]
    if rows:
        msg = _status_html(f"{len(rows)} despesa(s) no período.", "ok")
    else:
        msg = _status_html("Nenhuma despesa neste mês.", "loading")
    return rows, msg


def _dropdown_choices(rows: list[dict[str, Any]]) -> list[str]:
    return [
        f"{row['id']} — {row['description']} "
        f"({'Pendente' if row['status'] == 'pending' else 'Paga'})"
        for row in rows
    ]


def _parse_selected_id(selected: str | None) -> int | None:
    if not selected:
        return None
    try:
        return int(str(selected).split("—", 1)[0].strip())
    except ValueError:
        return None


def load_expenses(month: int, year: int) -> tuple[Any, ...]:
    """html, select, id, desc, amount, cat, date, status, confirm, form, msg"""
    rows, status = _load_expense_rows(month, year)
    return (
        expenses_list_html(rows),
        gr.update(choices=_dropdown_choices(rows), value=None),
        None,
        "",
        None,
        gr.update(choices=_expense_category_choices(), value=None),
        "",
        "Pendente",
        gr.update(visible=False),
        gr.update(visible=False),
        status,
    )


def on_expense_select(selected: str | None, month: int, year: int) -> tuple[Any, ...]:
    expense_id = _parse_selected_id(selected)
    empty = (
        None,
        "",
        None,
        gr.update(choices=_expense_category_choices()),
        "",
        "Pendente",
        gr.update(visible=False),
    )
    if expense_id is None:
        return empty + (
            _status_html("Selecione uma despesa para editar ou marcar como paga.", "loading"),
        )

    rows, _ = _load_expense_rows(month, year)
    match = next((r for r in rows if r["id"] == expense_id), None)
    if match is None:
        return empty + (_status_html("Despesa não encontrada no período.", "error"),)

    pending = match["status"] == "pending"
    return (
        match["id"],
        match["description"],
        float(parse_api_amount(match["amount"])),
        gr.update(choices=_expense_category_choices(), value=match["category"]),
        format_date_br(match["date"]),
        "Pendente" if pending else "Paga",
        gr.update(visible=pending),
        _status_html(
            "Despesa pendente selecionada. Confirme o pagamento ou edite os dados."
            if pending
            else "Despesa paga selecionada. Você pode editar os dados.",
            "ok",
        ),
    )


def request_mark_paid(editing_id: float | int | None) -> tuple[Any, str]:
    if editing_id in (None, ""):
        return gr.update(visible=False), _status_html(
            "⚠ Selecione uma despesa pendente.", "error"
        )
    return gr.update(visible=True), _status_html(
        "Confirma marcar esta despesa como paga?", "loading"
    )


def confirm_mark_paid(
    editing_id: float | int | None,
    month: int,
    year: int,
) -> tuple[Any, ...]:
    if editing_id in (None, ""):
        loaded = load_expenses(month, year)
        return loaded[:-1] + (_status_html("⚠ Nenhuma despesa selecionada.", "error"),)

    try:
        update_transaction(int(editing_id), {"status": "completed"})
    except ApiError as exc:
        loaded = load_expenses(month, year)
        return loaded[:-1] + (_status_html(f"⚠ {exc.message}", "error"),)

    loaded = load_expenses(month, year)
    return loaded[:-1] + (_status_html("✓ Despesa marcada como paga.", "ok"),)


def cancel_mark_paid() -> tuple[Any, str]:
    return gr.update(visible=False), _status_html("Confirmação cancelada.", "loading")


def clear_expense_form() -> tuple[Any, ...]:
    """Limpa campos, esconde confirmação e o formulário."""
    return (
        None,
        "",
        None,
        gr.update(choices=_expense_category_choices(), value=None),
        "",
        "Pendente",
        gr.update(visible=False),
        gr.update(visible=False),
        _status_html("Formulário fechado.", "loading"),
    )


def open_add_expense_form() -> tuple[Any, ...]:
    return (
        None,
        "",
        None,
        gr.update(choices=_expense_category_choices(), value=None),
        "",
        "Pendente",
        gr.update(visible=False),
        gr.update(visible=True),
        _status_html("Preencha os dados da nova despesa.", "loading"),
    )


def open_edit_expense_form(editing_id: float | int | None) -> tuple[Any, str]:
    if editing_id in (None, ""):
        return gr.update(visible=False), _status_html(
            "⚠ Selecione uma despesa antes de editar.", "error"
        )
    return gr.update(visible=True), _status_html(
        "Edite os campos e clique em Salvar.", "ok"
    )


def save_expense(
    editing_id: float | int | None,
    description: str,
    amount: float | None,
    category_label: str,
    date_value: str,
    status_label: str,
    month: int,
    year: int,
) -> tuple[Any, ...]:
    status_api = "pending" if status_label == "Pendente" else "completed"
    if not (date_value or "").strip():
        date_value = date(int(year), int(month), 1).strftime("%d/%m/%Y")

    # Em erro: mantém o formulário aberto para correção
    keep = (
        editing_id,
        description,
        amount,
        category_label,
        date_value,
        status_label,
        gr.update(visible=False),
        gr.update(visible=True),
    )

    try:
        categories = list_categories()
    except ApiError as exc:
        loaded = load_expenses(month, year)
        return loaded[:2] + keep + (_status_html(f"⚠ {exc.message}", "error"),)

    _, name_to_id, by_type = _category_maps(categories)
    payload, error = _validate_form(
        description,
        amount,
        "Despesa",
        "Pendente" if status_api == "pending" else "Concluída",
        category_label,
        date_value,
        name_to_id,
        by_type,
    )
    if error:
        loaded = load_expenses(month, year)
        return loaded[:2] + keep + (_status_html(f"⚠ {error}", "error"),)

    assert payload is not None
    payload["status"] = status_api
    payload["type"] = "expense"

    try:
        if editing_id in (None, ""):
            create_transaction(payload)
            msg = "Despesa adicionada."
        else:
            update_transaction(int(editing_id), payload)
            msg = "Despesa atualizada."
    except ApiError as exc:
        loaded = load_expenses(month, year)
        return loaded[:2] + keep + (_status_html(f"⚠ {exc.message}", "error"),)

    loaded = load_expenses(month, year)
    # html, select + form limpo (esconde formulário)
    return (
        loaded[0],
        loaded[1],
        None,
        "",
        None,
        gr.update(choices=_expense_category_choices(), value=None),
        "",
        "Pendente",
        gr.update(visible=False),  # confirm
        gr.update(visible=False),  # form
        _status_html(f"✓ {msg}", "ok"),
    )


def build_expenses_section() -> dict[str, Any]:
    gr.HTML('<p class="sc-section-title sc-section-compact">Despesas por categoria</p>')
    gr.HTML(
        '<p class="sc-section-help">Visão rápida das despesas do mês. '
        "Selecione um item e use os botões abaixo.</p>"
    )

    expense_html = gr.HTML()
    expense_select = gr.Dropdown(
        choices=[],
        label="Selecionar despesa",
        value=None,
        allow_custom_value=False,
    )
    status_html = gr.HTML(_status_html("Carregando despesas…", "loading"))

    with gr.Row():
        add_btn = gr.Button("Adicionar", variant="primary")
        edit_btn = gr.Button("Editar")
        mark_btn = gr.Button("Marcar como paga")

    with gr.Group(visible=False) as confirm_group:
        gr.Markdown("**Confirmar pagamento desta despesa?**")
        with gr.Row():
            confirm_btn = gr.Button("Confirmar pagamento", variant="primary")
            cancel_confirm_btn = gr.Button("Cancelar")

    with gr.Group(visible=False) as form_group:
        gr.HTML('<p class="sc-form-title">Formulário de despesa</p>')
        editing_id = gr.Number(visible=False, precision=0)
        with gr.Row():
            description = gr.Textbox(label="Nome da despesa", scale=2, min_width=140)
            amount = gr.Number(label="Valor (R$)", precision=2, minimum=0, scale=1, min_width=100)
            category = gr.Dropdown(label="Categoria", choices=[], scale=1, min_width=120)
        with gr.Row():
            date_input = gr.Textbox(label="Data", placeholder="DD/MM/AAAA", scale=1, min_width=110)
            status_input = gr.Dropdown(
                ["Pendente", "Paga"],
                value="Pendente",
                label="Status",
                scale=1,
                min_width=110,
            )
        with gr.Row():
            save_btn = gr.Button("Salvar", variant="primary")
            clear_btn = gr.Button("Cancelar")

    return {
        "html": expense_html,
        "select": expense_select,
        "status": status_html,
        "confirm_group": confirm_group,
        "confirm_btn": confirm_btn,
        "cancel_confirm_btn": cancel_confirm_btn,
        "form_group": form_group,
        "add_btn": add_btn,
        "edit_btn": edit_btn,
        "editing_id": editing_id,
        "description": description,
        "amount": amount,
        "category": category,
        "date_input": date_input,
        "status_input": status_input,
        "save_btn": save_btn,
        "clear_btn": clear_btn,
        "mark_btn": mark_btn,
    }
