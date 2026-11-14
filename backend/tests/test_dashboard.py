def test_dashboard_calculations(client):
    income_cat = client.post(
        "/categories",
        json={"name": "Salário", "type": "income"},
    ).json()
    expense_cat = client.post(
        "/categories",
        json={"name": "Mercado", "type": "expense"},
    ).json()

    client.post(
        "/transactions",
        json={
            "description": "Salário",
            "amount": "5000",
            "type": "income",
            "date": "2026-11-05",
            "status": "completed",
            "category_id": income_cat["id"],
        },
    )
    client.post(
        "/transactions",
        json={
            "description": "Mercado",
            "amount": "800",
            "type": "expense",
            "date": "2026-11-06",
            "status": "completed",
            "category_id": expense_cat["id"],
        },
    )
    client.post(
        "/transactions",
        json={
            "description": "Aluguel",
            "amount": "1500",
            "type": "expense",
            "date": "2026-11-10",
            "status": "pending",
            "category_id": expense_cat["id"],
        },
    )

    response = client.get("/dashboard", params={"month": 11, "year": 2026})
    assert response.status_code == 200
    data = response.json()

    assert data["total_income"] == "5000.00"
    assert data["total_expenses"] == "800.00"
    assert data["current_balance"] == "4200.00"
    assert data["pending_expenses"] == "1500.00"
    assert data["projected_balance"] == "2700.00"
    assert len(data["expenses_by_category"]) == 1
    assert data["expenses_by_category"][0]["total"] == "800.00"

    other_month = client.get("/dashboard", params={"month": 10, "year": 2026})
    zeros = other_month.json()
    assert zeros["total_income"] == "0.00"
    assert zeros["current_balance"] == "0.00"
