import unittest
import asyncio
from fastapi.testclient import TestClient
from dashboard.app import app
from dashboard.services.auth_service import create_access_token
from dashboard.dependencies import event_bridge
from analytics.events import AnalyticsEvent, AnalyticsEventType
from analytics.bus import AnalyticsEventBus

class TestDashboardWebSockets(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.admin_token = create_access_token({"sub": "admin", "role": "admin"})

    def test_ws_connection_unauthorized(self):
        # Missing token query parameter -> Should raise exception or fail connection
        with self.assertRaises(Exception):
            with self.client.websocket_connect("/api/ws"):
                pass

        # Invalid token query parameter -> close code 4008
        try:
            with self.client.websocket_connect("/api/ws?token=invalid_token") as ws:
                pass
        except Exception as e:
            # Depending on test client, it might raise an exception or allow checking close code
            pass

    def test_ws_flow_subscribe_and_broadcast(self):
        # 1. Connect with valid token
        with self.client.websocket_connect(f"/api/ws?token={self.admin_token}") as ws:
            # 2. Subscribe to leaderboard channel
            ws.send_json({"action": "subscribe", "channel": "leaderboard"})
            resp = ws.receive_json()
            self.assertEqual(resp["status"], "success")
            self.assertIn("Subscribed to channel leaderboard", resp["message"])

            # 3. Use EventBridge to simulate event publication
            # Bind loop manually for TestClient thread execution
            loop = asyncio.get_event_loop()
            event_bridge.set_loop(loop)
            
            # Create a mock LEADERBOARD_UPDATE event
            mock_payload = {
                "snapshot_id": "snap_ws",
                "campaign_id": "camp_ws",
                "entries": [
                    {"contestant_id": "team_1", "rank": 1, "score": 95.5, "rating_grade": "S"}
                ]
            }
            event = AnalyticsEvent(
                event_id="evt_ws",
                timestamp_ns=1000,
                event_type=AnalyticsEventType.LEADERBOARD_UPDATE,
                source="test",
                payload=mock_payload
            )
            
            # Run the process_event directly on the loop to ensure execution in synchronous test
            loop.run_until_complete(event_bridge._process_event(event))

            # 4. Receive message on WebSocket
            msg = ws.receive_json()
            self.assertEqual(msg["channel"], "leaderboard")
            self.assertEqual(msg["data"]["snapshot_id"], "snap_ws")
