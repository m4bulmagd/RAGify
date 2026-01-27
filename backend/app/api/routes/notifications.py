from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.core.notifications import manager
from app.api import deps
from jose import jwt, JWTError
from app.core.config import settings
from app.schemas.token import TokenPayload
from uuid import UUID
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time notifications.
    Token is passed as query parameter for convenience with browser WS clients.
    """
    try:
        # Validate token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        user_id = UUID(token_data.sub)
    except (JWTError, Exception) as e:
        logger.error(f"WebSocket auth failed: {e}")
        await websocket.close(code=1008)  # Policy Violation
        return

    await manager.connect(user_id, websocket)
    try:
        while True:
            # Keep connection alive and wait for client to close
            data = await websocket.receive_text()
            # We don't expect much from client here, but could handle heartbeats
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id, websocket)
