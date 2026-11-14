import pytest


@pytest.fixture
def income_category(client):
    return client.post(
        "/categories",
        json={"name": "Salário", "type": "income"},
    ).json()


@pytest.fixture
def expense_category(client):
    return client.post(
        "/categories",
        json={"name": "Contas", "type": "expense"},
    ).json()


def test_create_income_and_expense(client, income_category, expense_category):
    income = client.post(
        "/transactions",
        json={
            "description": "Pagamento",
            "amount": "3000",
            "type": "income",
            "date": "2026-11-01",
            "status": "completed",
            "category_id": income_category["id"],
        },
    )
    assert income.status_code == 201

    expense = client.post(
        "/transactions",
        json={
            "description": "Luz",
            "amount": "120.50",
            "type": "expense",
            "date": "2026-11-03",
            "status": "pending",
            "category_id": expense_category["id"],
        },
    )
    assert expense.status_code == 201


def test_reject_zero_or_negative_amount(client, expense_category):
    response = client.post(
        "/transactions",
        json={
            "description": "Teste",
            "amount": "0",
            "type": "expense",
            "date": "2026-11-01",
            "status": "completed",
            "category_id": expense_category["id"],
        },
    )
    assert response.status_code == 422


def test_reject_incompatible_category(client, income_category):
    response = client.post(
        "/transactions",
        json={
            "description": "Errado",
            "amount": "10",
            "type": "expense",
            "date": "2026-11-01",
            "status": "completed",
            "category_id": income_category["id"],
        },
    )
    assert response.status_code == 409


def test_list_with_filters(client, income_category, expense_category):
    client.post(
        "/transactions",
        json={
            "description": "A",
            "amount": "100",
            "type": "income",
            "date": "2026-11-10",
            "status": "completed",
            "category_id": income_category["id"],
        },
    )
    client.post(
        "/transactions",
        json={
            "description": "B",
            "amount": "50",
            "type": "expense",
            "date": "2026-11-15",
            "status": "pending",
            "category_id": expense_category["id"],
        },
    )

    by_type = client.get("/transactions", params={"type": "expense"})
    assert len(by_type.json()) == 1

    by_period = client.get(
        "/transactions",
        params={"start_date": "2026-11-01", "end_date": "2026-11-30"},
    )
    assert len(by_period.json()) == 2


def test_update_and_delete_transaction(client, expense_category):
    created = client.post(
        "/transactions",
        json={
            "description": "Internet",
            "amount": "99.90",
            "type": "expense",
            "date": "2026-11-02",
            "status": "completed",
            "category_id": expense_category["id"],
        },
    ).json()

    updated = client.put(
        f"/transactions/{created['id']}",
        json={"description": "Internet fibra", "status": "pending"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "pending"

    deleted = client.delete(f"/transactions/{created['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/transactions/{created['id']}").status_code == 404
