import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError

from dashboard.dependencies import get_channel_manager
from dashboard.services.channel_manager import ChannelManager
from dashboard.services.auth_service import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["WebSockets"])

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    # Resolve manager manually inside websocket to handle dependencies smoothly
    from dashboard.dependencies import channel_manager
    
    # 1. Authenticate via token
    try:
        user_info = verify_token(token)
        logger.info(f"WebSocket client authenticated: {user_info['username']} ({user_info['role']})")
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=4008) # Policy Violation close code
        return

    # 2. Accept connection
    await websocket.accept()
    await channel_manager.connect(websocket)

    try:
        while True:
            # 3. Read subscription messages
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")
                channel = msg.get("channel")

                if action == "subscribe" and channel:
                    ok = await channel_manager.subscribe(websocket, channel)
                    if ok:
                        await websocket.send_json({
                            "status": "success",
                            "message": f"Subscribed to channel {channel}"
                        })
                    else:
                        await websocket.send_json({
                            "status": "error",
                            "message": f"Failed to subscribe. Invalid channel: {channel}"
                        })
                elif action == "unsubscribe" and channel:
                    await channel_manager.unsubscribe(websocket, channel)
                    await websocket.send_json({
                        "status": "success",
                        "message": f"Unsubscribed from channel {channel}"
                    })
                else:
                    await websocket.send_json({
                        "status": "error",
                        "message": "Invalid action or missing channel field"
                    })
            except json.JSONDecodeError:
                await websocket.send_json({
                    "status": "error",
                    "message": "JSON decoding failed. Expected subscription request."
                })
            except Exception as e:
                logger.error(f"Error handling socket frame: {e}", exc_info=True)

    except WebSocketDisconnect:
        await channel_manager.disconnect(websocket)
        logger.info("WebSocket connection closed by client.")
