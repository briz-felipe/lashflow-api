class TestExpenses:
    def test_create_single_expense(self, client_app, auth_headers):
        resp = client_app.post(
            "/api/v1/expenses/",
            json={
                "name": "Aluguel",
                "category": "aluguel",
                "amount_in_cents": 150000,
                "recurrence": "monthly",
                "reference_month": "2024-03",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["installmentsCreated"] == 1
        assert data["expense"]["name"] == "Aluguel"

    def test_create_installment_expense(self, client_app, auth_headers):
        resp = client_app.post(
            "/api/v1/expenses/",
            json={
                "name": "Cadeira",
                "category": "material",
                "amount_in_cents": 25000,
                "recurrence": "monthly",
                "reference_month": "2024-01",
                "installments": 6,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["installmentsCreated"] == 6
        assert data["installmentGroupId"] is not None
        assert data["expense"]["installmentCurrent"] == 1
        assert data["expense"]["installmentTotal"] == 6

    def test_list_expenses_by_month(self, client_app, auth_headers):
        client_app.post(
            "/api/v1/expenses/",
            json={
                "name": "Internet",
                "category": "internet",
                "amount_in_cents": 10000,
                "recurrence": "monthly",
                "reference_month": "2024-03",
            },
            headers=auth_headers,
        )
        resp = client_app.get("/api/v1/expenses/?month=2024-03", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_pay_expense(self, client_app, auth_headers):
        create_resp = client_app.post(
            "/api/v1/expenses/",
            json={
                "name": "Energia",
                "category": "energia",
                "amount_in_cents": 45000,
                "recurrence": "monthly",
                "reference_month": "2024-03",
            },
            headers=auth_headers,
        )
        expense_id = create_resp.json()["expense"]["id"]
        pay_resp = client_app.patch(f"/api/v1/expenses/{expense_id}/pay", headers=auth_headers)
        assert pay_resp.status_code == 200
        assert pay_resp.json()["isPaid"] is True

    def test_expense_summary(self, client_app, auth_headers):
        client_app.post(
            "/api/v1/expenses/",
            json={
                "name": "Aluguel",
                "category": "aluguel",
                "amount_in_cents": 100000,
                "recurrence": "monthly",
                "reference_month": "2024-05",
            },
            headers=auth_headers,
        )
        resp = client_app.get("/api/v1/expenses/summary?month=2024-05", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["totalInCents"] == 100000
        assert data["pendingInCents"] == 100000
        assert "aluguel" in data["byCategory"]
