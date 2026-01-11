"""
WebSocket server for real-time communication with Electron frontend.
Handles transcript streaming and LLM response delivery.
"""

import asyncio
import json
import time
import os
from typing import Set
import logging
import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket server for frontend communication."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
    ):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        
    async def register(self, websocket: WebSocketServerProtocol) -> None:
        """Register a new client connection."""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
    
    async def unregister(self, websocket: WebSocketServerProtocol) -> None:
        """Unregister a client connection."""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def send_to_all(self, message: dict) -> None:
        """
        Send a message to all connected clients.
        
        Args:
            message: Dictionary to send as JSON
        """
        if not self.clients:
            return
        
        message_json = json.dumps(message)
        
        # Send to all clients concurrently
        await asyncio.gather(
            *[client.send(message_json) for client in self.clients],
            return_exceptions=True
        )
    
    async def send_transcript(
        self,
        text: str,
        is_final: bool,
        confidence: float = 0.0,
        timestamp: float = None,
    ) -> None:
        """
        Send a transcript update to all clients.
        
        Args:
            text: Transcribed text
            is_final: Whether this is a final transcript
            confidence: Confidence score (0-1)
            timestamp: Timestamp of the transcript
        """
        message = {
            "type": "transcript",
            "timestamp": timestamp or time.time(),
            "data": {
                "text": text,
                "is_final": is_final,
                "confidence": confidence,
            }
        }
        await self.send_to_all(message)
    
    async def send_response(
        self,
        text: str,
        context: str = "",
        latency_ms: int = 0,
    ) -> None:
        """
        Send an LLM response to all clients.
        
        Args:
            text: Generated response text
            context: Context/question that prompted the response
            latency_ms: End-to-end latency in milliseconds
        """
        message = {
            "type": "response",
            "timestamp": time.time(),
            "data": {
                "text": text,
                "context": context,
                "latency_ms": latency_ms,
            }
        }
        await self.send_to_all(message)
    
    async def send_status(
        self,
        status: str,
        details: dict = None,
    ) -> None:
        """
        Send a status update to all clients.
        
        Args:
            status: Status message (e.g., "connected", "error", "processing")
            details: Additional status details
        """
        message = {
            "type": "status",
            "timestamp": time.time(),
            "data": {
                "status": status,
                **(details or {})
            }
        }
        await self.send_to_all(message)
    
    async def handler(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """
        Handle WebSocket connections.
        
        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        await self.register(websocket)
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "status",
                "data": {"status": "connected", "message": "Welcome to Interview Sathi"}
            }))
            
            # Keep connection alive and handle incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed")
        finally:
            await self.unregister(websocket)
    
    async def handle_client_message(
        self,
        websocket: WebSocketServerProtocol,
        data: dict
    ) -> None:
        """
        Handle messages from clients.
        
        Args:
            websocket: Client websocket
            data: Message data
        """
        msg_type = data.get("type")
        
        if msg_type == "ping":
            # Respond to ping
            await websocket.send(json.dumps({"type": "pong"}))
        
        elif msg_type == "clear_context":
            # Signal to clear LLM context (handled by main.py)
            logger.info("Client requested context clear")
            await self.send_status("context_cleared")
        
        else:
            logger.warning(f"Unknown message type: {msg_type}")
    
    async def start(self) -> None:
        """Start the WebSocket server."""
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
        )
        logger.info(f"✓ WebSocket server started on ws://{self.host}:{self.port}")
    
    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")
    
    async def run_forever(self) -> None:
        """Run the server indefinitely."""
        await self.start()
        await asyncio.Future()  # Run forever


async def test_websocket_server():
    """Test WebSocket server."""
    print("Testing WebSocket server...")
    
    server = WebSocketServer()
    
    # Start server
    await server.start()
    
    print(f"✓ Server running on ws://{server.host}:{server.port}")
    print("Connect a WebSocket client to test")
    
    # Simulate sending messages
    await asyncio.sleep(2)
    await server.send_status("testing", {"message": "This is a test"})
    await server.send_transcript("Hello world", is_final=True, confidence=0.95)
    await server.send_response("This is a test response", latency_ms=1500)
    
    # Keep running for a bit
    await asyncio.sleep(5)
    
    await server.stop()
    print("✓ Server test complete")


if __name__ == "__main__":
    asyncio.run(test_websocket_server())
