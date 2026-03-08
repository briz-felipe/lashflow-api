class TestLogin:
    def test_login_returns_token(self, client_app, admin_user):
        resp = client_app.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client_app, admin_user):
        resp = client_app.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpass"},
        )
        assert resp.status_code == 401

    def test_login_unknown_user(self, client_app):
        resp = client_app.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "any"},
        )
        assert resp.status_code == 401


class TestMe:
    def test_me_returns_user(self, client_app, auth_headers, admin_user):
        resp = client_app.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
        assert data["is_superuser"] is True

    def test_me_unauthorized_without_token(self, client_app):
        resp = client_app.get("/api/v1/auth/me")
        assert resp.status_code == 401


class TestRegister:
    def test_register_requires_superuser(self, client_app, auth_headers):
        resp = client_app.post(
            "/api/v1/auth/register",
            json={"username": "newuser", "password": "pass123"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["username"] == "newuser"

    def test_register_without_auth_fails(self, client_app):
        resp = client_app.post(
            "/api/v1/auth/register",
            json={"username": "newuser", "password": "pass123"},
        )
        assert resp.status_code == 401

    def test_register_duplicate_username(self, client_app, auth_headers, admin_user):
        resp = client_app.post(
            "/api/v1/auth/register",
            json={"username": "admin", "password": "pass123"},
            headers=auth_headers,
        )
        assert resp.status_code == 409
