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