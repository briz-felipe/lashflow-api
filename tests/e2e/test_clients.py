class TestClients:
    def test_create_client(self, client_app, auth_headers):
        resp = client_app.post(
            "/api/v1/clients/",
            json={"name": "Ana Silva", "phone": "(11) 99999-0000"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Ana Silva"
        assert data["phone"] == "11999990000"  # normalized

    def test_create_duplicate_phone_fails(self, client_app, auth_headers):
        client_app.post(
            "/api/v1/clients/",
            json={"name": "Ana Silva", "phone": "11999990000"},
            headers=auth_headers,
        )
        resp = client_app.post(
            "/api/v1/clients/",
            json={"name": "Other", "phone": "(11) 99999-0000"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    def test_list_clients(self, client_app, auth_headers):
        client_app.post(
            "/api/v1/clients/",
            json={"name": "Maria", "phone": "11111111111"},
            headers=auth_headers,
        )
        resp = client_app.get("/api/v1/clients/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert "data" in data

    def test_get_client(self, client_app, auth_headers):
        create_resp = client_app.post(
            "/api/v1/clients/",
            json={"name": "João", "phone": "22222222222"},
            headers=auth_headers,
        )
        client_id = create_resp.json()["id"]
        resp = client_app.get(f"/api/v1/clients/{client_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "João"

    def test_get_nonexistent_client(self, client_app, auth_headers):
        import uuid
        resp = client_app.get(f"/api/v1/clients/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_soft_delete_client(self, client_app, auth_headers):
        create_resp = client_app.post(
            "/api/v1/clients/",
            json={"name": "Delete Me", "phone": "33333333333"},
            headers=auth_headers,
        )
        client_id = create_resp.json()["id"]
        resp = client_app.delete(f"/api/v1/clients/{client_id}", headers=auth_headers)
        assert resp.status_code == 204
        get_resp = client_app.get(f"/api/v1/clients/{client_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_requires_auth(self, client_app):
        resp = client_app.get("/api/v1/clients/")
        assert resp.status_code == 401
