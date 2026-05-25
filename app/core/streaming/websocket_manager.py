# app/core/streaming/websocket_manager.py

from fastapi import WebSocket

from app.config.logging import get_logger


logger = get_logger("ws-manager")


# =========================================================
# WEBSOCKET MANAGER
# =========================================================
class ConnectionManager:

    def __init__(self):

        self.active_connections = {}

    # =====================================================
    # CONNECT
    # =====================================================
    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
    ):

        await websocket.accept()

        self.active_connections[
            client_id
        ] = websocket

        logger.info(
            "WebSocket connected",
            client_id=client_id,
        )

    # =====================================================
    # DISCONNECT
    # =====================================================
    def disconnect(
        self,
        client_id: str,
    ):

        if client_id in self.active_connections:
            del self.active_connections[
                client_id
            ]

        logger.info(
            "WebSocket disconnected",
            client_id=client_id,
        )

    # =====================================================
    # SEND PERSONAL MESSAGE
    # =====================================================
    async def send_personal_message(
        self,
        message: str,
        client_id: str,
    ):

        websocket = self.active_connections.get(
            client_id
        )

        if websocket:
            await websocket.send_text(message)

    # =====================================================
    # SEND JSON EVENT
    # =====================================================
    async def send_json_event(
        self,
        client_id: str,
        event_type: str,
        payload: dict,
    ):
        """Send a structured JSON event to a specific client.
        Supports token streaming, execution progress, and tool status."""
        websocket = self.active_connections.get(client_id)
        if websocket:
            await websocket.send_json({
                "type": event_type,
                "data": payload
            })

    # =====================================================
    # BROADCAST
    # =====================================================
    async def broadcast(
        self,
        message: str,
    ):

        for connection in (
            self.active_connections.values()
        ):
            await connection.send_text(message)


manager = ConnectionManager()