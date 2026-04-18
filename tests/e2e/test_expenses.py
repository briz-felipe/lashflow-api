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

    def test_patch_expense_shifts_installment_date(self, client_app, auth_headers):
        """PATCH /expenses/{id} must accept reference_month and due_day updates
        so the UI can shift installment dates after a purchase was booked wrong."""
        create_resp = client_app.post(
            "/api/v1/expenses/",
            json={
                "name": "Parcelada",
                "category": "material",
                "amount_in_cents": 5000,
                "recurrence": "monthly",
                "reference_month": "2024-03",
                "dueDay": 10,
                "installments": 3,
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        expense_id = create_resp.json()["expense"]["id"]

        patch_resp = client_app.patch(
            f"/api/v1/expenses/{expense_id}",
            json={"referenceMonth": "2024-04", "dueDay": 15},
            headers=auth_headers,
        )
        assert patch_resp.status_code == 200
        body = patch_resp.json()
        assert body["referenceMonth"] == "2024-04"
        assert body["dueDay"] == 15

    def test_put_expense_backward_compat(self, client_app, auth_headers):
        """Existing clients using PUT must continue to work."""
        create_resp = client_app.post(
            "/api/v1/expenses/",
            json={
                "name": "Um item",
                "category": "material",
                "amount_in_cents": 3000,
                "recurrence": "one_time",
                "reference_month": "2024-05",
            },
            headers=auth_headers,
        )
        expense_id = create_resp.json()["expense"]["id"]

        put_resp = client_app.put(
            f"/api/v1/expenses/{expense_id}",
            json={"name": "Renomeado"},
            headers=auth_headers,
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["name"] == "Renomeado"

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
