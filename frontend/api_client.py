"""Cliente HTTP da API usando apenas a biblioteca padrão."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from frontend.config import API_BASE_URL, REQUEST_TIMEOUT


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _extract_error_message(raw: bytes, fallback: str) -> str:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return fallback

    detail = payload.get("detail")
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list) and detail:
        first = detail[0]
        if isinstance(first, dict) and "msg" in first:
            loc = first.get("loc", [])
            msg = first.get("msg", "")
            if loc:
                return f"{loc[-1]}: {msg}"
            return str(msg)
    return fallback


def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    clean_params = {
        key: value
        for key, value in (params or {}).items()
        if value is not None and value != ""
    }
    query = f"?{urlencode(clean_params)}" if clean_params else ""
    url = f"{API_BASE_URL}{path}{query}"

    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, method=method, headers=headers)

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            raw = response.read()
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
    except HTTPError as exc:
        body_bytes = exc.read() if exc.fp else b""
        raise ApiError(
            _extract_error_message(body_bytes, "Erro ao consultar a API."),
            exc.code,
        ) from exc
    except URLError as exc:
        raise ApiError(
            "Não foi possível conectar à API. Verifique se o backend está em execução.",
        ) from exc
    except TimeoutError as exc:
        raise ApiError("A API demorou demais para responder.") from exc
    except json.JSONDecodeError as exc:
        raise ApiError("Resposta inválida da API.") from exc


def get_dashboard(month: int, year: int) -> dict[str, Any]:
    return _request("GET", "/dashboard", params={"month": month, "year": year})


def list_categories() -> list[dict[str, Any]]:
    result = _request("GET", "/categories")
    return result or []


def create_category(payload: dict[str, Any]) -> dict[str, Any]:
    return _request("POST", "/categories", body=payload)


def update_category(category_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return _request("PUT", f"/categories/{category_id}", body=payload)


def delete_category(category_id: int) -> None:
    _request("DELETE", f"/categories/{category_id}")


def list_transactions(
    *,
    type_: str | None = None,
    status: str | None = None,
    category_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    result = _request(
        "GET",
        "/transactions",
        params={
            "type": type_,
            "status": status,
            "category_id": category_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )
    return result or []


def create_transaction(payload: dict[str, Any]) -> dict[str, Any]:
    return _request("POST", "/transactions", body=payload)


def update_transaction(transaction_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return _request("PUT", f"/transactions/{transaction_id}", body=payload)


def delete_transaction(transaction_id: int) -> None:
    _request("DELETE", f"/transactions/{transaction_id}")
