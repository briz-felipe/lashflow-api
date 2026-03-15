import uuid


def _create_client(client_app, auth_headers, phone="11111111111"):
    resp = client_app.post(
        "/api/v1/clients/",
        json={"name": "Test Client", "phone": phone},
        headers=auth_headers,
    )
    return resp.json()["id"]


def _create_procedure(client_app, auth_headers):
    resp = client_app.post(
        "/api/v1/procedures/",
        json={
            "name": "Volume",
            "price_in_cents": 25000,
            "duration_minutes": 120,
        },
        headers=auth_headers,
    )
    return resp.json()["id"]


def _create_appointment(client_app, auth_headers, client_id=None, procedure_id=None, phone="11111111111"):
    if client_id is None:
        client_id = _create_client(client_app, auth_headers, phone=phone)
    if procedure_id is None:
        procedure_id = _create_procedure(client_app, auth_headers)
    resp = client_app.post(
        "/api/v1/appointments/",
        json={
            "client_id": client_id,
            "procedure_id": procedure_id,
            "scheduled_at": "2030-06-15T10:00:00",
            "price_charged": 25000,
        },
        headers=auth_headers,
    )
    return resp.json()


class TestAppointments:
    def test_create_appointment(self, client_app, auth_headers):
        appt = _create_appointment(client_app, auth_headers)
        assert appt["status"] == "pending_approval"
        assert "endsAt" in appt

    def test_status_transition_pending_to_confirmed(self, client_app, auth_headers):
        appt = _create_appointment(client_app, auth_headers)
        resp = client_app.patch(
            f"/api/v1/appointments/{appt['id']}/status",
            json={"status": "confirmed"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"

    def test_invalid_status_transition_returns_422(self, client_app, auth_headers):
        appt = _create_appointment(client_app, auth_headers)
        # pending_approval → completed is invalid
        resp = client_app.patch(
            f"/api/v1/appointments/{appt['id']}/status",
            json={"status": "completed"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_cancel_appointment(self, client_app, auth_headers):
        appt = _create_appointment(client_app, auth_headers)
        resp = client_app.patch(
            f"/api/v1/appointments/{appt['id']}/cancel",
            json={"reason": "Client request", "cancelled_by": "client"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelled"
        assert data["cancellationReason"] == "Client request"

    def test_list_appointments(self, client_app, auth_headers):
        _create_appointment(client_app, auth_headers, phone="22222222222")
        resp = client_app.get("/api/v1/appointments/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_pending_approvals(self, client_app, auth_headers):
        _create_appointment(client_app, auth_headers, phone="33333333333")
        resp = client_app.get("/api/v1/appointments/pending-approvals", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
