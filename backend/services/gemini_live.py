"""Gemini Live service."""
import asyncio
import inspect
import logging
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiLive:
    """
    Handles the interaction with the Gemini Live API.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        input_sample_rate: int,
        tools: Optional[List] = None,
        tool_mapping: Optional[Dict[str, Callable]] = None,
    ):
        """
        Initializes the GeminiLive client.

        Args:
            api_key: The Gemini API Key.
            model: The model name to use.
            input_sample_rate: The sample rate for audio input.
            tools: List of tools to enable.
            tool_mapping: Mapping of tool names to functions.
        """
        self.api_key = api_key
        self.model = model
        self.input_sample_rate = input_sample_rate
        self.client = genai.Client(api_key=api_key)
        self.tools = tools or []
        self.tool_mapping = tool_mapping or {}

        # Session state management
        self.session_state = "active"
        self.transcript_buffer: List[Dict[str, Any]] = []
        self.last_checkpoint_time: Optional[float] = None
        self.checkpoint_interval = 15
        self.session_id: Optional[str] = None
        self.transcript_callback: Optional[Callable] = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()

    def set_transcript_callback(self, callback: Callable):
        """Set callback for saving transcripts to session store."""
        self.transcript_callback = callback

    def pause_session(self) -> Dict[str, Any]:
        """Pause the session."""
        self.session_state = "paused"
        self._pause_event.clear()
        transcript_snapshot = self.transcript_buffer.copy()
        self._flush_transcript_buffer()
        return {"state": "paused", "transcript_snapshot": transcript_snapshot}

    def resume_session(self) -> Dict[str, Any]:
        """Resume the session."""
        self.session_state = "active"
        self._pause_event.set()
        return {"state": "active"}

    def end_session(self) -> Dict[str, Any]:
        """End the session."""
        self.session_state = "ended"
        self._pause_event.set()
        self._flush_transcript_buffer()
        return {"state": "ended", "final_transcript": self.transcript_buffer.copy()}

    def _flush_transcript_buffer(self):
        """Flush accumulated transcript buffer to session store."""
        if self.transcript_buffer and self.transcript_callback:
            self.transcript_callback(self.transcript_buffer.copy())
            self.transcript_buffer = []

    def _add_to_transcript_buffer(self, speaker: str, text: str):
        """Add transcript entry to buffer."""
        entry = {
            "speaker": speaker,
            "text": text,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self.transcript_buffer.append(entry)
        self._check_checkpoint()

    def _check_checkpoint(self):
        """Check if checkpoint interval has elapsed and flush if needed."""
        now = time.time()
        if self.last_checkpoint_time is None or (now - self.last_checkpoint_time) >= self.checkpoint_interval:
            self._flush_transcript_buffer()
            self.last_checkpoint_time = now

    async def start_session(
        self,
        audio_input_queue: asyncio.Queue,
        video_input_queue: asyncio.Queue,
        text_input_queue: asyncio.Queue,
        audio_output_callback: Callable,
        audio_interrupt_callback: Optional[Callable] = None,
        session_id: Optional[str] = None,
    ):
        """Start a Gemini Live session."""
        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
                )
            ),
            system_instruction=types.Content(
                parts=[
                    types.Part(
                        text="You are a helpful AI assistant. Keep your responses concise. "
                        "Speak in a friendly Irish accent. "
                        "You can see the user's camera or screen which is shared as realtime input images with you."
                    )
                ]
            ),
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
            realtime_input_config=types.RealtimeInputConfig(
                turn_coverage="TURN_INCLUDES_ONLY_ACTIVITY",
            ),
            tools=self.tools,
        )

        logger.info(f"Connecting to Gemini Live with model={self.model}")
        try:
            self.session_id = session_id
            self.last_checkpoint_time = time.time()
            self.session_state = "active"

            async with self.client.aio.live.connect(model=self.model, config=config) as session:
                logger.info("Gemini Live session opened successfully")

                async def send_audio():
                    try:
                        while True:
                            chunk = await audio_input_queue.get()
                            while self.session_state == "paused":
                                await self._pause_event.wait()
                                if self.session_state == "ended":
                                    return
                            if self.session_state == "active":
                                await session.send_realtime_input(
                                    audio=types.Blob(
                                        data=chunk, mime_type=f"audio/pcm;rate={self.input_sample_rate}"
                                    )
                                )
                    except asyncio.CancelledError:
                        logger.debug("send_audio task cancelled")
                    except Exception as e:
                        logger.error(f"send_audio error: {e}\n{traceback.format_exc()}")

                async def send_video():
                    try:
                        while True:
                            chunk = await video_input_queue.get()
                            logger.info(f"Sending video frame to Gemini: {len(chunk)} bytes")
                            await session.send_realtime_input(
                                video=types.Blob(data=chunk, mime_type="image/jpeg")
                            )
                    except asyncio.CancelledError:
                        logger.debug("send_video task cancelled")
                    except Exception as e:
                        logger.error(f"send_video error: {e}\n{traceback.format_exc()}")

                async def send_text():
                    try:
                        while True:
                            text = await text_input_queue.get()
                            logger.info(f"Sending text to Gemini: {text}")
                            await session.send_realtime_input(text=text)
                    except asyncio.CancelledError:
                        logger.debug("send_text task cancelled")
                    except Exception as e:
                        logger.error(f"send_text error: {e}\n{traceback.format_exc()}")

                event_queue = asyncio.Queue()

                async def receive_loop():
                    try:
                        while True:
                            async for response in session.receive():
                                logger.debug(f"Received response from Gemini: {response}")

                                if response.go_away:
                                    logger.warning(f"Received GoAway from Gemini: {response.go_away}")
                                if response.session_resumption_update:
                                    logger.info(f"Session resumption update: {response.session_resumption_update}")

                                server_content = response.server_content
                                tool_call = response.tool_call

                                if server_content:
                                    if server_content.model_turn:
                                        for part in server_content.model_turn.parts:
                                            if part.inline_data:
                                                if inspect.iscoroutinefunction(audio_output_callback):
                                                    await audio_output_callback(part.inline_data.data)
                                                else:
                                                    audio_output_callback(part.inline_data.data)

                                    if (
                                        server_content.input_transcription
                                        and server_content.input_transcription.text
                                    ):
                                        self._add_to_transcript_buffer(
                                            "user", server_content.input_transcription.text
                                        )
                                        await event_queue.put(
                                            {"type": "user", "text": server_content.input_transcription.text}
                                        )

                                    if (
                                        server_content.output_transcription
                                        and server_content.output_transcription.text
                                    ):
                                        self._add_to_transcript_buffer(
                                            "gemini", server_content.output_transcription.text
                                        )
                                        await event_queue.put(
                                            {"type": "gemini", "text": server_content.output_transcription.text}
                                        )

                                    if server_content.turn_complete:
                                        await event_queue.put({"type": "turn_complete"})

                                    if server_content.interrupted:
                                        if audio_interrupt_callback:
                                            if inspect.iscoroutinefunction(audio_interrupt_callback):
                                                await audio_interrupt_callback()
                                            else:
                                                audio_interrupt_callback()
                                        await event_queue.put({"type": "interrupted"})

                                if tool_call:
                                    function_responses = []
                                    for fc in tool_call.function_calls:
                                        func_name = fc.name
                                        args = fc.args or {}

                                        if func_name in self.tool_mapping:
                                            try:
                                                tool_func = self.tool_mapping[func_name]
                                                if inspect.iscoroutinefunction(tool_func):
                                                    result = await tool_func(**args)
                                                else:
                                                    loop = asyncio.get_running_loop()
                                                    result = await loop.run_in_executor(
                                                        None, lambda: tool_func(**args)
                                                    )
                                            except Exception as e:
                                                result = f"Error: {e}"

                                            function_responses.append(
                                                types.FunctionResponse(
                                                    name=func_name,
                                                    id=fc.id,
                                                    response={"result": result},
                                                )
                                            )
                                            await event_queue.put(
                                                {"type": "tool_call", "name": func_name, "args": args, "result": result}
                                            )

                                    await session.send_tool_response(function_responses=function_responses)

                            logger.debug("Gemini receive iterator completed, re-entering receive loop")

                    except asyncio.CancelledError:
                        logger.debug("receive_loop task cancelled")
                    except Exception as e:
                        logger.error(
                            f"receive_loop error: {type(e).__name__}: {e}\n{traceback.format_exc()}"
                        )
                        await event_queue.put({"type": "error", "error": f"{type(e).__name__}: {e}"})
                    finally:
                        logger.info("receive_loop exiting")
                        await event_queue.put(None)

                send_audio_task = asyncio.create_task(send_audio())
                send_video_task = asyncio.create_task(send_video())
                send_text_task = asyncio.create_task(send_text())
                receive_task = asyncio.create_task(receive_loop())

                try:
                    while True:
                        event = await event_queue.get()
                        if event is None:
                            break
                        if isinstance(event, dict) and event.get("type") == "error":
                            yield event
                            break
                        yield event
                finally:
                    logger.info("Cleaning up Gemini Live session tasks")
                    send_audio_task.cancel()
                    send_video_task.cancel()
                    send_text_task.cancel()
                    receive_task.cancel()

        except Exception as e:
            logger.error(f"Gemini Live session error: {type(e).__name__}: {e}\n{traceback.format_exc()}")
            raise
        finally:
            logger.info("Gemini Live session closed")