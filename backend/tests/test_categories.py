def test_create_and_list_categories(client):
    response = client.post(
        "/categories",
        json={"name": "Salário", "type": "income"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Salário"
    assert body["type"] == "income"
    assert "id" in body

    list_response = client.get("/categories")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_get_update_and_delete_category(client):
    created = client.post(
        "/categories",
        json={"name": "Lazer", "type": "expense"},
    ).json()

    get_response = client.get(f"/categories/{created['id']}")
    assert get_response.status_code == 200

    updated = client.put(
        f"/categories/{created['id']}",
        json={"name": "Entretenimento"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Entretenimento"

    delete_response = client.delete(f"/categories/{created['id']}")
    assert delete_response.status_code == 204

    assert client.get(f"/categories/{created['id']}").status_code == 404


def test_delete_category_with_transactions_returns_409(client):
    category = client.post(
        "/categories",
        json={"name": "Mercado", "type": "expense"},
    ).json()
    client.post(
        "/transactions",
        json={
            "description": "Compras",
            "amount": "50.00",
            "type": "expense",
            "date": "2026-11-05",
            "status": "completed",
            "category_id": category["id"],
        },
    )

    response = client.delete(f"/categories/{category['id']}")
    assert response.status_code == 409
