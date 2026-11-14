"""Gerenciamento de categorias no dashboard."""

from __future__ import annotations

from typing import Any

import gradio as gr

from frontend.api_client import (
    ApiError,
    create_category,
    delete_category,
    list_categories,
    update_category,
)

TYPE_LABELS = {"income": "Receita", "expense": "Despesa"}
TYPE_API = {v: k for k, v in TYPE_LABELS.items()}
FILTER_TYPES = ["Todas", "Receita", "Despesa"]
FORM_TYPES = ["Receita", "Despesa"]
TABLE_HEADERS = ["ID", "Nome", "Tipo"]


def _status_html(message: str, kind: str = "ok") -> str:
    css = {
        "ok": "sc-status-ok",
        "error": "sc-status-error",
        "loading": "sc-status-loading",
    }.get(kind, "sc-status-loading")
    return f'<p class="{css}">{message}</p>'


def _rows_from_api(
    categories: list[dict[str, Any]],
    type_filter: str,
) -> list[list[Any]]:
    rows = []
    for item in categories:
        type_label = TYPE_LABELS.get(item["type"], item["type"])
        if type_filter in TYPE_API and type_label != type_filter:
            continue
        rows.append([item["id"], item["name"], type_label])
    return rows


def _validate_form(name: str, type_label: str) -> tuple[dict[str, Any] | None, str | None]:
    name = (name or "").strip()
    if not name:
        return None, "Informe o nome da categoria."
    if len(name) > 80:
        return None, "O nome deve ter no máximo 80 caracteres."
    if type_label not in TYPE_API:
        return None, "Selecione o tipo (Receita ou Despesa)."
    return {"name": name, "type": TYPE_API[type_label]}, None


def _blank_form(type_label: str = "Despesa") -> tuple[Any, ...]:
    return None, "", type_label


def load_categories_screen(type_filter: str) -> tuple[Any, str]:
    try:
        categories = list_categories()
    except ApiError as exc:
        return [], _status_html(f"⚠ {exc.message}", "error")

    rows = _rows_from_api(categories, type_filter)
    if rows:
        status = _status_html(f"{len(rows)} categoria(s).", "ok")
    else:
        status = _status_html("Nenhuma categoria encontrada.", "loading")
    return rows, status


def on_row_select(evt: gr.SelectData, table: Any) -> tuple[Any, ...]:
    noop = (gr.update(), gr.update(), gr.update())
    if table is None or evt.index is None:
        return noop
    row_idx = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
    try:
        if hasattr(table, "iloc"):
            row = table.iloc[int(row_idx)].tolist()
        else:
            row = table[int(row_idx)]
        cat_id, name, type_label = row
        return int(cat_id), str(name), str(type_label)
    except (IndexError, TypeError, ValueError, KeyError):
        return noop


def clear_form() -> tuple[Any, ...]:
    return _blank_form() + (
        gr.update(visible=False),
        _status_html("Formulário fechado.", "loading"),
    )


def open_add_form() -> tuple[Any, ...]:
    return _blank_form() + (
        gr.update(visible=True),
        _status_html("Preencha os dados da nova categoria.", "loading"),
    )


def open_edit_form(editing_id: float | int | None) -> tuple[Any, str]:
    if editing_id in (None, ""):
        return gr.update(visible=False), _status_html(
            "⚠ Clique em uma linha da tabela antes de editar.", "error"
        )
    return gr.update(visible=True), _status_html(
        "Edite os campos e clique em Salvar.", "ok"
    )


def save_category(
    editing_id: float | int | None,
    name: str,
    type_label: str,
    type_filter: str,
) -> tuple[Any, ...]:
    keep = (editing_id, name, type_label)
    payload, error = _validate_form(name, type_label)
    if error:
        listed = load_categories_screen(type_filter)
        return (listed[0], _status_html(f"⚠ {error}", "error")) + keep

    try:
        if editing_id in (None, ""):
            create_category(payload)  # type: ignore[arg-type]
            msg = "Categoria cadastrada."
        else:
            update_category(int(editing_id), payload)  # type: ignore[arg-type]
            msg = "Categoria atualizada."
    except ApiError as exc:
        listed = load_categories_screen(type_filter)
        return (listed[0], _status_html(f"⚠ {exc.message}", "error")) + keep

    listed = load_categories_screen(type_filter)
    return (listed[0], _status_html(f"✓ {msg}", "ok")) + _blank_form(type_label)


def remove_category(
    editing_id: float | int | None,
    type_filter: str,
) -> tuple[Any, ...]:
    listed = load_categories_screen(type_filter)
    if editing_id in (None, ""):
        return (
            listed[0],
            _status_html("⚠ Selecione uma categoria na tabela.", "error"),
        ) + _blank_form()

    try:
        delete_category(int(editing_id))
    except ApiError as exc:
        return (
            listed[0],
            _status_html(f"⚠ {exc.message}", "error"),
            editing_id,
            gr.update(),
            gr.update(),
        )

    listed = load_categories_screen(type_filter)
    return (listed[0], _status_html("✓ Categoria excluída.", "ok")) + _blank_form()


def build_categories(*, embedded: bool = True) -> dict[str, Any]:
    gr.HTML('<p class="sc-section-title sc-section-compact">Categorias</p>')
    gr.HTML(
        '<p class="sc-section-help">Organize receitas e despesas. '
        "Categorias com transações vinculadas não podem ser excluídas.</p>"
    )

    with gr.Row(elem_classes=["sc-filters"]):
        type_filter = gr.Dropdown(
            FILTER_TYPES, value="Todas", label="Filtrar por tipo", scale=1, min_width=140
        )
        filter_btn = gr.Button("Filtrar", variant="secondary", scale=0, min_width=90)

    status_html = gr.HTML(_status_html("Carregando…", "loading"))
    table = gr.Dataframe(
        headers=TABLE_HEADERS,
        datatype=["number", "str", "str"],
        interactive=False,
        wrap=True,
        label="Categorias",
        elem_classes=["sc-table", "sc-table-compact"],
    )

    with gr.Row():
        add_btn = gr.Button("Adicionar", variant="primary")
        edit_btn = gr.Button("Editar")
        delete_btn = gr.Button("Excluir", variant="stop")

    with gr.Group(visible=False) as form_group:
        gr.HTML('<p class="sc-form-title">Formulário de categoria</p>')
        editing_id = gr.Number(visible=False, precision=0)
        with gr.Row():
            name_input = gr.Textbox(label="Nome", scale=2, min_width=140)
            type_input = gr.Dropdown(FORM_TYPES, value="Despesa", label="Tipo", scale=1)
        with gr.Row():
            save_btn = gr.Button("Salvar", variant="primary")
            clear_btn = gr.Button("Cancelar")

    filter_inputs = [type_filter]
    list_outputs = [table, status_html]
    form_fields = [editing_id, name_input, type_input]

    filter_btn.click(load_categories_screen, inputs=filter_inputs, outputs=list_outputs)
    type_filter.change(load_categories_screen, inputs=filter_inputs, outputs=list_outputs)
    table.select(on_row_select, inputs=[table], outputs=form_fields)

    add_btn.click(open_add_form, outputs=form_fields + [form_group, status_html])
    edit_btn.click(
        open_edit_form,
        inputs=[editing_id],
        outputs=[form_group, status_html],
    )
    save_btn.click(
        save_category,
        inputs=form_fields + filter_inputs,
        outputs=list_outputs + form_fields,
    ).then(
        lambda: gr.update(visible=False),
        outputs=[form_group],
    )
    clear_btn.click(clear_form, outputs=form_fields + [form_group, status_html])
    delete_btn.click(
        remove_category,
        inputs=[editing_id] + filter_inputs,
        outputs=list_outputs + form_fields,
    ).then(
        lambda: gr.update(visible=False),
        outputs=[form_group],
    )

    return {"filters": filter_inputs, "outputs": list_outputs}
