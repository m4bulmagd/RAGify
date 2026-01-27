import asyncio
import json
import logging
from typing import Dict, List, Set, Optional
from uuid import UUID

import redis.asyncio as redis
from fastapi import WebSocket
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and facilitates broadcasting via Redis Pub/Sub.
    """

    def __init__(self):
        # Maps user_id to a set of active WebSockets
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self._listen_task: Optional[asyncio.Task] = None

    async def connect(self, user_id: UUID, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected via WebSocket. Active connections: {len(self.active_connections[user_id])}")

    def disconnect(self, user_id: UUID, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected from WebSocket.")

    async def send_personal_message(self, message: dict, user_id: UUID):
        """Send message to all active connections of a user."""
        if user_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.add(websocket)
            
            for ws in disconnected:
                self.disconnect(user_id, ws)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected users (use sparingly)."""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)

    async def start_redis_listener(self):
        """Start listening to Redis Pub/Sub channel for notifications."""
        redis_url = settings.REDIS_URL or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
        self.redis_client = redis.from_url(redis_url)
        self.pubsub = self.redis_client.pubsub()
        await self.pubsub.subscribe("notifications")
        
        self._listen_task = asyncio.create_task(self._listen_to_redis())
        logger.info("Started Redis notification listener")

    async def stop_redis_listener(self):
        """Stop Redis listener and close client."""
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            await self.pubsub.unsubscribe("notifications")
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Stopped Redis notification listener")

    async def _listen_to_redis(self):
        """Continuously listen for messages on Redis Pub/Sub."""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        user_id_str = data.get("user_id")
                        if user_id_str:
                            user_id = UUID(user_id_str)
                            payload = data.get("payload")
                            if payload:
                                await self.send_personal_message(payload, user_id)
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
            # Potentially restart here
            await asyncio.sleep(5)
            await self.start_redis_listener()


# Global manager instance
manager = ConnectionManager()
