"""WebSocket handlers for Gemini Live."""
import asyncio
import base64
import json
import logging
import traceback
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from backend.config import settings
from backend.services.gemini_live import GeminiLive
from backend.websocket.manager import manager
from backend.api.sessions import service as session_service

logger = logging.getLogger(__name__)


async def handle_websocket(websocket: WebSocket, session_id: Optional[str] = None):
    """
    Handle WebSocket connection for Gemini Live.

    Validates session if session_id provided, then manages the Gemini Live connection.
    """
    try:
        logger.info(f"WebSocket request received, session_id={session_id}")

        # Validate session if provided
        if session_id:
            session = session_service.get_session(session_id)
            if not session:
                logger.warning(f"WebSocket connection rejected: session {session_id} not found")
                await websocket.close(code=4004, reason="Session not found")
                return

            if session["state"] != session_service.SESSION_STATE_ACTIVE:
                logger.warning(
                    f"WebSocket connection rejected: session {session_id} not active (state={session['state']})"
                )
                await websocket.close(code=4005, reason="Session not active")
                return

            logger.info(f"WebSocket connection accepted for session {session_id}")
        else:
            logger.info("WebSocket connection accepted (no session_id - demo mode)")

        await websocket.accept()
        logger.info("WebSocket accepted, now setting up Gemini...")

        # Create input queues for different input types
        audio_input_queue = asyncio.Queue()
        video_input_queue = asyncio.Queue()
        text_input_queue = asyncio.Queue()

        # Transcript persistence callback
        def save_transcript_to_session(transcript_entries):
            if session_id:
                session = session_service.get_session(session_id)
                if session:
                    if "transcript" not in session:
                        session["transcript"] = []
                    session["transcript"].extend(transcript_entries)
                    logger.debug(f"Saved {len(transcript_entries)} transcript entries to session {session_id}")

        # Audio output callback - send to WebSocket
        async def audio_output_callback(audio_data: bytes):
            await websocket.send_bytes(audio_data)

        # Audio interrupt callback
        async def audio_interrupt_callback():
            await websocket.send_json({"type": "interrupted"})

        # Create Gemini Live client
        gemini_client = GeminiLive(
            api_key=settings.GEMINI_API_KEY,
            model=settings.MODEL,
            input_sample_rate=16000,
            tool_mapping={},
        )
        gemini_client.set_transcript_callback(save_transcript_to_session)

        # Start receiving messages from client
        receive_task = asyncio.create_task(
            receive_messages(websocket, audio_input_queue, video_input_queue, text_input_queue)
        )

        # Start Gemini session and forward responses
        try:
            logger.info("Starting Gemini Live session...")
            async for event in gemini_client.start_session(
                audio_input_queue=audio_input_queue,
                video_input_queue=video_input_queue,
                text_input_queue=text_input_queue,
                audio_output_callback=audio_output_callback,
                audio_interrupt_callback=audio_interrupt_callback,
                session_id=session_id,
            ):
                if event is None:
                    break

                event_type = event.get("type") if isinstance(event, dict) else None

                # Handle state changes from Gemini
                if session_id and event_type == "interrupted":
                    session_service.update_session(session_id, user_id="", state=session_service.SESSION_STATE_PAUSED)

                if event_type in ["user", "gemini", "turn_complete", "interrupted", "tool_call"]:
                    await websocket.send_json(event)
                elif event_type == "error":
                    await websocket.send_json(event)
                    break

        except Exception as e:
            logger.error(f"Gemini Live session error: {e}")
            try:
                await websocket.send_json({"type": "error", "error": str(e)})
            except Exception:
                pass
        finally:
            # Proper task cleanup with timeout
            receive_task.cancel()
            try:
                await asyncio.wait_for(receive_task, timeout=1.0)
            except asyncio.CancelledError:
                pass
            except asyncio.TimeoutError:
                logger.warning("Receive task did not cancel within timeout")

            # End Gemini session properly
            try:
                gemini_client.end_session()
            except Exception as e:
                logger.debug(f"Error ending Gemini session: {e}")

            manager.disconnect(session_id or "demo")
            logger.info("WebSocket session ended")

    except Exception as e:
        logger.error(f"WebSocket handler error: {e}\n{traceback.format_exc()}")
        try:
            await websocket.close(code=4000, reason=str(e))
        except Exception:
            pass


async def receive_messages(
    websocket: WebSocket,
    audio_queue: asyncio.Queue,
    video_queue: asyncio.Queue,
    text_queue: asyncio.Queue,
):
    """Receive messages from WebSocket and route to appropriate queues."""
    try:
        while True:
            data = await websocket.receive()

            # Handle text messages
            if "text" in data:
                try:
                    message = json.loads(data["text"])
                    msg_type = message.get("type")

                    if msg_type == "text":
                        await text_queue.put(message.get("content", ""))
                    elif msg_type == "audio":
                        audio_bytes = base64.b64decode(message.get("data", ""))
                        await audio_queue.put(audio_bytes)
                    elif msg_type == "video":
                        video_bytes = base64.b64decode(message.get("data", ""))
                        await video_queue.put(video_bytes)

                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received")

            # Handle binary messages
            elif "bytes" in data:
                await audio_queue.put(data["bytes"])

    except asyncio.CancelledError:
        logger.debug("Receive task cancelled")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error receiving messages: {e}")
