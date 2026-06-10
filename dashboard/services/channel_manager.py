import asyncio
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ChannelManager:
    """Manages WebSocket connections and channel-based pub/sub routing."""
    
    def __init__(self):
        # channel_name -> set of WebSockets
        self._channels: Dict[str, Set[WebSocket]] = {
            "leaderboard": set(),
            "analytics": set(),
            "tournament": set(),
            "health": set(),
            "federation": set()
        }
        # WebSocket -> set of channels subscribed
        self._client_subscriptions: Dict[WebSocket, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        async with self._lock:
            self._client_subscriptions[websocket] = set()

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            # Remove from all channels
            subscribed_channels = self._client_subscriptions.pop(websocket, set())
            for channel in subscribed_channels:
                if websocket in self._channels[channel]:
                    self._channels[channel].remove(websocket)
            logger.info(f"WebSocket client disconnected and cleaned up from channels: {subscribed_channels}")

    async def subscribe(self, websocket: WebSocket, channel: str) -> bool:
        if channel not in self._channels:
            logger.warning(f"Attempted subscription to invalid channel: {channel}")
            return False
        
        async with self._lock:
            self._channels[channel].add(websocket)
            if websocket in self._client_subscriptions:
                self._client_subscriptions[websocket].add(channel)
            else:
                self._client_subscriptions[websocket] = {channel}
            logger.info(f"WebSocket client subscribed to channel: {channel}")
            return True

    async def unsubscribe(self, websocket: WebSocket, channel: str) -> bool:
        if channel not in self._channels:
            return False
            
        async with self._lock:
            if websocket in self._channels[channel]:
                self._channels[channel].remove(websocket)
            if websocket in self._client_subscriptions:
                self._client_subscriptions[websocket].discard(channel)
            logger.info(f"WebSocket client unsubscribed from channel: {channel}")
            return True

    async def broadcast(self, channel: str, message: dict):
        if channel not in self._channels:
            return
            
        # Capture current set under lock, then send without lock to prevent blocking
        async with self._lock:
            targets = list(self._channels[channel])
            
        if not targets:
            return

        # Prepare send tasks
        tasks = []
        for ws in targets:
            tasks.append(self._send_safe(ws, message, channel))
        await asyncio.gather(*tasks)

    async def _send_safe(self, ws: WebSocket, message: dict, channel: str):
        try:
            await ws.send_json({
                "channel": channel,
                "data": message
            })
        except Exception as e:
            # Connection might be closed, disconnect will clean it up later
            logger.debug(f"Failed to send WS message on channel {channel}: {e}")
