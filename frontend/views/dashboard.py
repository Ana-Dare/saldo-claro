"""Helpers do resumo financeiro (dashboard único)."""

from __future__ import annotations

from typing import Any

from frontend.api_client import ApiError, get_dashboard
from frontend.config import MONTH_CHOICES
from frontend.formatting import format_brl, parse_api_amount

MONTH_LABELS = [label for label, _ in MONTH_CHOICES]
MONTH_VALUES = {label: value for label, value in MONTH_CHOICES}
VALUE_TO_MONTH = {value: label for label, value in MONTH_CHOICES}


def header_html() -> str:
    return """
    <div class="sc-header">
      <p class="sc-app-name">SaldoClaro</p>
      <h1 class="sc-title">Você no controle!</h1>
      <p class="sc-subtitle">Organize suas despesas e equilibre sua vida financeira.</p>
    </div>
    """


def summary_title_html(month: int, year: int) -> str:
    name = VALUE_TO_MONTH.get(month, "")
    return f'<h2 class="sc-summary-title">Resumo {name}</h2>'


def metric_card(label: str, value: str, extra_class: str = "") -> str:
    value_class = f"sc-metric-value {extra_class}".strip()
    return f"""
    <div class="sc-card sc-card-metric">
      <p class="sc-metric-label">{label}</p>
      <p class="{value_class}">{value}</p>
    </div>
    """


def metrics_row_html(data: dict[str, Any]) -> str:
    cards = [
        metric_card("Receitas recebidas", format_brl(data["total_income"]), "sc-value-income"),
        metric_card("Despesas pagas", format_brl(data["total_expenses"])),
        metric_card(
            "Despesas pendentes",
            format_brl(data["pending_expenses"]),
            "sc-value-pending",
        ),
        metric_card(
            "Saldo atual",
            format_brl(data["current_balance"]),
            "sc-value-balance",
        ),
    ]
    return f'<div class="sc-metrics-wrap">{"".join(cards)}</div>'


def projected_block(value: str) -> str:
    return f"""
    <div class="sc-projected">
      <p class="sc-projected-title">Saldo previsto</p>
      <p class="sc-projected-value">{value}</p>
      <p class="sc-projected-help">Saldo atual menos despesas pendentes.</p>
    </div>
    """


def is_empty_month(data: dict[str, Any]) -> bool:
    fields = ("total_income", "total_expenses", "pending_expenses")
    amounts = [parse_api_amount(data.get(key, 0)) for key in fields]
    return not any(amount > 0 for amount in amounts)


def fetch_summary(month: int, year: int) -> tuple[str, str, str, str]:
    """Retorna: título, métricas, saldo previsto, status."""
    try:
        data = get_dashboard(int(month), int(year))
    except ApiError as exc:
        return (
            summary_title_html(int(month), int(year)),
            '<div class="sc-empty">Não foi possível carregar os indicadores.</div>',
            projected_block(format_brl("0")),
            f'<p class="sc-status-error">⚠ {exc.message}</p>',
        )

    empty_note = ""
    if is_empty_month(data):
        empty_note = '<div class="sc-empty sc-empty-tight">Nenhuma movimentação neste mês.</div>'

    metrics = metrics_row_html(data) + empty_note
    return (
        summary_title_html(data["month"], data["year"]),
        metrics,
        projected_block(format_brl(data["projected_balance"])),
        f'<p class="sc-status-ok">Indicadores atualizados.</p>',
    )
