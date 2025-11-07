"""
WebSocket API routes for AI Tutor Proof of Concept.

Provides WebSocket endpoint for live updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json
import logging

from backend.api.facade import get_facade

router = APIRouter()
logger = logging.getLogger(__name__)

# Store active WebSocket connections
active_connections: list[WebSocket] = []


async def broadcast_message(message: Dict[str, Any]):
    """
    Broadcast a message to all active WebSocket connections.
    
    Args:
        message: Message dictionary to broadcast
    """
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send message to connection: {e}")
            disconnected.append(connection)
    
    # Remove disconnected connections
    for connection in disconnected:
        if connection in active_connections:
            active_connections.remove(connection)


@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for live updates.
    
    Supports message types:
    - graph_update: Graph structure has changed
    - summarization_progress: Summarization progress update
    - chat_message: New chat message
    - error: Error notification
    
    Example messages:
    - {"type": "graph_update", "data": {...}}
    - {"type": "summarization_progress", "data": {"topic_id": "...", "progress": 0.5}}
    - {"type": "chat_message", "data": {"session_id": "...", "message": "..."}}
    """
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket connection established. Total connections: {len(active_connections)}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await websocket.send_json({"type": "pong"})
                elif message_type == "subscribe":
                    # Client subscribes to specific update types
                    # For now, we just acknowledge
                    await websocket.send_json({"type": "subscribed", "data": message.get("data", {})})
                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": f"Unknown message type: {message_type}"}
                    })
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON message"}
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket connection disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Total connections: {len(active_connections)}")

