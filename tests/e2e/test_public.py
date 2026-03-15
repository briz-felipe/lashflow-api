class TestPublicRoutes:
    def test_public_procedures_no_auth(self, client_app):
        resp = client_app.get("/api/v1/public/procedures")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_public_available_slots_no_auth(self, client_app, auth_headers):
        # Create a procedure first (requires auth)
        proc_resp = client_app.post(
            "/api/v1/procedures/",
            json={
                "name": "Classic",
                "price_in_cents": 15000,
                "duration_minutes": 90,
            },
            headers=auth_headers,
        )
        procedure_id = proc_resp.json()["id"]

        # Set up a time slot (Monday)
        client_app.put(
            "/api/v1/settings/time-slots",
            json={"slots": [{"day_of_week": 1, "start_time": "09:00", "end_time": "18:00", "is_available": True}]},
            headers=auth_headers,
        )

        # Query slots as public (no auth)
        resp = client_app.get(
            "/api/v1/public/available-slots",
            params={"date": "2030-01-06", "procedure_id": procedure_id},
        )
        assert resp.status_code == 200
        assert "slots" in resp.json()

    def test_public_book_appointment(self, client_app, auth_headers):
        proc_resp = client_app.post(
            "/api/v1/procedures/",
            json={
                "name": "Hybrid",
                "price_in_cents": 20000,
                "duration_minutes": 60,
            },
            headers=auth_headers,
        )
        procedure_id = proc_resp.json()["id"]

        resp = client_app.post(
            "/api/v1/public/appointments",
            json={
                "procedure_id": procedure_id,
                "scheduled_at": "2030-06-20T10:00:00",
                "client": {"name": "Ana Pública", "phone": "(11) 98765-4321"},
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending_approval"

    def test_public_book_reuses_existing_client(self, client_app, auth_headers):
        # Create client via admin API first
        client_app.post(
            "/api/v1/clients/",
            json={"name": "Existing", "phone": "11987654321"},
            headers=auth_headers,
        )

        proc_resp = client_app.post(
            "/api/v1/procedures/",
            json={
                "name": "Removal",
                "price_in_cents": 5000,
                "duration_minutes": 30,
            },
            headers=auth_headers,
        )
        procedure_id = proc_resp.json()["id"]

        # Book with same phone — should reuse client, not create new
        resp = client_app.post(
            "/api/v1/public/appointments",
            json={
                "procedure_id": procedure_id,
                "scheduled_at": "2030-06-21T10:00:00",
                "client": {"name": "Any Name", "phone": "(11) 98765-4321"},
            },
        )
        assert resp.status_code == 201

        # Only 1 client should exist
        clients_resp = client_app.get("/api/v1/clients/", headers=auth_headers)
        assert clients_resp.json()["total"] == 1
