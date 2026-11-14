"""Histórico completo de transações (receitas e despesas)."""

from __future__ import annotations

from typing import Any

import gradio as gr

from frontend.api_client import (
    ApiError,
    create_transaction,
    delete_transaction,
    list_categories,
    list_transactions,
    update_transaction,
)
from frontend.formatting import format_brl, format_date_br, parse_date_input

TYPE_LABELS = {"income": "Receita", "expense": "Despesa"}
STATUS_LABELS = {"completed": "Concluída", "pending": "Pendente"}
TYPE_API = {v: k for k, v in TYPE_LABELS.items()}
STATUS_API = {v: k for k, v in STATUS_LABELS.items()}

FILTER_TYPE = ["Todas", "Receita", "Despesa"]
FILTER_STATUS = ["Todos", "Concluída", "Pendente"]
FORM_TYPES = ["Receita", "Despesa"]
FORM_STATUS = ["Concluída", "Pendente"]
TABLE_HEADERS = ["ID", "Descrição", "Valor", "Categoria", "Data", "Tipo", "Status"]


def _status_html(message: str, kind: str = "ok") -> str:
    css = {
        "ok": "sc-status-ok",
        "error": "sc-status-error",
        "loading": "sc-status-loading",
    }.get(kind, "sc-status-loading")
    return f'<p class="{css}">{message}</p>'


def _category_maps(
    categories: list[dict[str, Any]],
) -> tuple[dict[int, str], dict[str, int], dict[str, list[str]]]:
    id_to_name = {int(c["id"]): c["name"] for c in categories}
    name_to_id = {c["name"]: int(c["id"]) for c in categories}
    by_type = {
        "Receita": [c["name"] for c in categories if c["type"] == "income"],
        "Despesa": [c["name"] for c in categories if c["type"] == "expense"],
    }
    return id_to_name, name_to_id, by_type


def _rows_from_api(
    transactions: list[dict[str, Any]],
    id_to_name: dict[int, str],
) -> list[list[Any]]:
    rows = []
    for item in transactions:
        rows.append(
            [
                item["id"],
                item["description"],
                format_brl(item["amount"]),
                id_to_name.get(int(item["category_id"]), f"#{item['category_id']}"),
                format_date_br(item["date"]),
                TYPE_LABELS.get(item["type"], item["type"]),
                STATUS_LABELS.get(item["status"], item["status"]),
            ]
        )
    return rows


def _validate_form(
    description: str,
    amount: float | None,
    type_label: str,
    status_label: str,
    category_label: str,
    date_value: str,
    name_to_id: dict[str, int],
    by_type: dict[str, list[str]],
) -> tuple[dict[str, Any] | None, str | None]:
    description = (description or "").strip()
    if not description:
        return None, "Informe a descrição."
    if len(description) > 200:
        return None, "A descrição deve ter no máximo 200 caracteres."
    if amount is None:
        return None, "Informe o valor."
    try:
        amount_f = float(amount)
    except (TypeError, ValueError):
        return None, "Valor inválido."
    if amount_f <= 0:
        return None, "O valor deve ser maior que zero."
    if type_label not in TYPE_API:
        return None, "Selecione o tipo (Receita ou Despesa)."
    if status_label not in STATUS_API:
        return None, "Selecione o status."
    if not category_label:
        return None, "Selecione uma categoria."
    if category_label not in by_type.get(type_label, []):
        return None, "A categoria precisa ser compatível com o tipo da movimentação."
    date_iso = parse_date_input(date_value)
    if date_iso is None:
        return None, "Data inválida. Use AAAA-MM-DD ou DD/MM/AAAA."
    return (
        {
            "description": description,
            "amount": f"{amount_f:.2f}",
            "type": TYPE_API[type_label],
            "status": STATUS_API[status_label],
            "category_id": name_to_id[category_label],
            "date": date_iso,
        },
        None,
    )


def _blank_form(type_label: str = "Despesa") -> tuple[Any, ...]:
    try:
        categories = list_categories()
        _, _, by_type = _category_maps(categories)
        choices = by_type.get(type_label, [])
    except ApiError:
        choices = []
    return (
        None,
        "",
        None,
        type_label,
        "Concluída",
        gr.update(choices=choices, value=choices[0] if choices else None),
        "",
    )


def load_transactions_screen(
    type_label: str,
    status_label: str,
) -> tuple[Any, Any, str]:
    try:
        categories = list_categories()
    except ApiError as exc:
        return [], gr.update(choices=[]), _status_html(f"⚠ {exc.message}", "error")

    id_to_name, _, by_type = _category_maps(categories)
    form_cats = by_type.get("Receita", []) + by_type.get("Despesa", [])

    type_ = TYPE_API.get(type_label) if type_label in TYPE_API else None
    status = STATUS_API.get(status_label) if status_label in STATUS_API else None

    try:
        transactions = list_transactions(type_=type_, status=status)
    except ApiError as exc:
        return (
            [],
            gr.update(choices=form_cats),
            _status_html(f"⚠ {exc.message}", "error"),
        )

    rows = _rows_from_api(transactions, id_to_name)
    if rows:
        status_msg = _status_html(f"{len(rows)} transação(ões).", "ok")
    else:
        status_msg = _status_html("Nenhuma transação para os filtros.", "loading")
    return rows, gr.update(choices=form_cats), status_msg


def on_type_change(type_label: str) -> Any:
    try:
        categories = list_categories()
    except ApiError:
        return gr.update(choices=[], value=None)
    _, _, by_type = _category_maps(categories)
    choices = by_type.get(type_label, [])
    return gr.update(choices=choices, value=choices[0] if choices else None)


def on_row_select(evt: gr.SelectData, table: Any) -> tuple[Any, ...]:
    noop = (gr.update(),) * 7
    if table is None or evt.index is None:
        return noop
    row_idx = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
    try:
        if hasattr(table, "iloc"):
            row = table.iloc[int(row_idx)].tolist()
        else:
            row = table[int(row_idx)]
    except (IndexError, TypeError, ValueError, KeyError):
        return noop

    tx_id, description, amount_brl, category, date_br, type_label, status_label = row
    amount_text = (
        str(amount_brl).replace("R$", "").replace(".", "").replace(",", ".").strip()
    )
    try:
        amount_val = float(amount_text)
    except ValueError:
        amount_val = None

    try:
        categories = list_categories()
        _, _, by_type = _category_maps(categories)
        cat_choices = by_type.get(type_label, [])
    except ApiError:
        cat_choices = [category]

    return (
        int(tx_id),
        description,
        amount_val,
        type_label,
        status_label,
        gr.update(choices=cat_choices, value=category),
        date_br,
    )


def clear_form() -> tuple[Any, ...]:
    return _blank_form("Despesa") + (
        gr.update(visible=False),
        _status_html("Formulário fechado.", "loading"),
    )


def open_add_form() -> tuple[Any, ...]:
    return _blank_form("Despesa") + (
        gr.update(visible=True),
        _status_html("Preencha os dados da nova transação.", "loading"),
    )


def open_edit_form(editing_id: float | int | None) -> tuple[Any, str]:
    if editing_id in (None, ""):
        return gr.update(visible=False), _status_html(
            "⚠ Clique em uma linha da tabela antes de editar.", "error"
        )
    return gr.update(visible=True), _status_html(
        "Edite os campos e clique em Salvar.", "ok"
    )


def save_transaction(
    editing_id: float | int | None,
    description: str,
    amount: float | None,
    type_label: str,
    status_label: str,
    category_label: str,
    date_value: str,
    filter_type: str,
    filter_status: str,
) -> tuple[Any, ...]:
    keep = (editing_id, description, amount, type_label, status_label, category_label, date_value)
    try:
        categories = list_categories()
    except ApiError as exc:
        listed = load_transactions_screen(filter_type, filter_status)
        return (listed[0], listed[1], _status_html(f"⚠ {exc.message}", "error")) + keep

    _, name_to_id, by_type = _category_maps(categories)
    payload, error = _validate_form(
        description,
        amount,
        type_label,
        status_label,
        category_label,
        date_value,
        name_to_id,
        by_type,
    )
    if error:
        listed = load_transactions_screen(filter_type, filter_status)
        return (listed[0], listed[1], _status_html(f"⚠ {error}", "error")) + keep

    try:
        if editing_id in (None, ""):
            create_transaction(payload)  # type: ignore[arg-type]
            msg = "Transação cadastrada."
        else:
            update_transaction(int(editing_id), payload)  # type: ignore[arg-type]
            msg = "Transação atualizada."
    except ApiError as exc:
        listed = load_transactions_screen(filter_type, filter_status)
        return (listed[0], listed[1], _status_html(f"⚠ {exc.message}", "error")) + keep

    listed = load_transactions_screen(filter_type, filter_status)
    return (
        listed[0],
        listed[1],
        _status_html(f"✓ {msg}", "ok"),
    ) + _blank_form(type_label)


def remove_transaction(
    editing_id: float | int | None,
    filter_type: str,
    filter_status: str,
) -> tuple[Any, ...]:
    listed = load_transactions_screen(filter_type, filter_status)
    if editing_id in (None, ""):
        return (
            listed[0],
            listed[1],
            _status_html("⚠ Selecione uma transação na tabela.", "error"),
        ) + _blank_form()

    try:
        delete_transaction(int(editing_id))
    except ApiError as exc:
        return (
            listed[0],
            listed[1],
            _status_html(f"⚠ {exc.message}", "error"),
            editing_id,
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )

    listed = load_transactions_screen(filter_type, filter_status)
    return (
        listed[0],
        listed[1],
        _status_html("✓ Transação excluída.", "ok"),
    ) + _blank_form()


def build_transactions(*, embedded: bool = True) -> dict[str, Any]:
    gr.HTML('<p class="sc-section-title sc-section-compact">Transações</p>')
    gr.HTML(
        '<p class="sc-section-help">Histórico completo de receitas e despesas.</p>'
    )

    with gr.Row(elem_classes=["sc-filters"]):
        filter_type = gr.Dropdown(
            FILTER_TYPE, value="Todas", label="Tipo", scale=1, min_width=110
        )
        filter_status = gr.Dropdown(
            FILTER_STATUS, value="Todos", label="Status", scale=1, min_width=110
        )
        filter_btn = gr.Button("Filtrar", variant="secondary", scale=0, min_width=90)

    status_html = gr.HTML(_status_html("Carregando…", "loading"))
    table = gr.Dataframe(
        headers=TABLE_HEADERS,
        datatype=["number", "str", "str", "str", "str", "str", "str"],
        interactive=False,
        wrap=True,
        label="Histórico",
        elem_classes=["sc-table", "sc-table-compact"],
    )

    with gr.Row():
        add_btn = gr.Button("Adicionar", variant="primary")
        edit_btn = gr.Button("Editar")
        delete_btn = gr.Button("Excluir", variant="stop")

    with gr.Group(visible=False) as form_group:
        gr.HTML('<p class="sc-form-title">Formulário de transação</p>')
        editing_id = gr.Number(label="ID", precision=0, visible=False)
        with gr.Row():
            description = gr.Textbox(label="Descrição", scale=2, min_width=140)
            amount = gr.Number(label="Valor (R$)", precision=2, minimum=0, scale=1, min_width=100)
            date_input = gr.Textbox(label="Data", placeholder="DD/MM/AAAA", scale=1, min_width=100)
        with gr.Row():
            type_input = gr.Dropdown(FORM_TYPES, value="Despesa", label="Tipo", scale=1)
            status_input = gr.Dropdown(FORM_STATUS, value="Concluída", label="Status", scale=1)
            category_input = gr.Dropdown([], label="Categoria", scale=1)
        with gr.Row():
            save_btn = gr.Button("Salvar", variant="primary")
            clear_btn = gr.Button("Cancelar")

    filter_inputs = [filter_type, filter_status]
    list_outputs = [table, category_input, status_html]
    form_fields = [
        editing_id,
        description,
        amount,
        type_input,
        status_input,
        category_input,
        date_input,
    ]

    filter_btn.click(load_transactions_screen, inputs=filter_inputs, outputs=list_outputs)
    filter_type.change(load_transactions_screen, inputs=filter_inputs, outputs=list_outputs)
    filter_status.change(load_transactions_screen, inputs=filter_inputs, outputs=list_outputs)
    type_input.change(on_type_change, inputs=[type_input], outputs=[category_input])
    table.select(on_row_select, inputs=[table], outputs=form_fields)

    add_btn.click(open_add_form, outputs=form_fields + [form_group, status_html])
    edit_btn.click(
        open_edit_form,
        inputs=[editing_id],
        outputs=[form_group, status_html],
    )
    save_btn.click(
        save_transaction,
        inputs=form_fields + filter_inputs,
        outputs=list_outputs + form_fields,
    ).then(
        lambda: gr.update(visible=False),
        outputs=[form_group],
    )
    clear_btn.click(clear_form, outputs=form_fields + [form_group, status_html])
    delete_btn.click(
        remove_transaction,
        inputs=[editing_id] + filter_inputs,
        outputs=list_outputs + form_fields,
    ).then(
        lambda: gr.update(visible=False),
        outputs=[form_group],
    )

    return {
        "filters": filter_inputs,
        "outputs": list_outputs,
        "form_fields": form_fields,
    }
