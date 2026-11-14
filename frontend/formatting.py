from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def parse_api_amount(value: str | float | int | Decimal) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def format_brl(value: str | float | int | Decimal) -> str:
    amount = parse_api_amount(value)
    negative = amount < 0
    amount = abs(amount)
    text = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if negative:
        return f"- R$ {text}"
    return f"R$ {text}"


def format_date_br(value: str | date | None) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    text = str(value)[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return text


def parse_date_input(value: str | None) -> str | None:
    """Aceita AAAA-MM-DD ou DD/MM/AAAA e devolve AAAA-MM-DD."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None

