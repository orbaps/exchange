import unittest
from fastapi.testclient import TestClient
from dashboard.app import app

class TestDashboardAuth(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_token_exchange_valid_admin(self):
        response = self.client.post(
            "/api/auth/token",
            data={"username": "admin", "password": "adminpassword"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["role"], "admin")
        self.assertEqual(data["token_type"], "bearer")

    def test_token_exchange_valid_public(self):
        response = self.client.post(
            "/api/auth/token",
            data={"username": "public", "password": "publicpassword"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["role"], "public")

    def test_token_exchange_invalid(self):
        response = self.client.post(
            "/api/auth/token",
            data={"username": "admin", "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Incorrect username or password")

    def test_admin_route_protection(self):
        # 1. Unauthenticated request
        response = self.client.post("/api/admin/tournament/stop")
        self.assertEqual(response.status_code, 401)

        # 2. Public user request (Should be 403 Forbidden)
        pub_login = self.client.post(
            "/api/auth/token",
            data={"username": "public", "password": "publicpassword"}
        )
        pub_token = pub_login.json()["access_token"]
        
        response = self.client.post(
            "/api/admin/tournament/stop",
            headers={"Authorization": f"Bearer {pub_token}"}
        )
        self.assertEqual(response.status_code, 403)

        # 3. Admin user request (Should fail with 400 Bad Request because no tournament is running, but NOT 403)
        admin_login = self.client.post(
            "/api/auth/token",
            data={"username": "admin", "password": "adminpassword"}
        )
        admin_token = admin_login.json()["access_token"]
        
        response = self.client.post(
            "/api/admin/tournament/stop",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "No tournament is currently running.")
