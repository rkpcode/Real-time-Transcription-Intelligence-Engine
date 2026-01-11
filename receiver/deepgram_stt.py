"""
Deepgram STT module for receiver (same as backend).
"""

# Copy from backend/deepgram_stt.py
import asyncio
import os
from typing import AsyncGenerator, Callable, Optional
import logging
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepgramSTT:
    """Real-time speech-to-text using Deepgram streaming API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "nova-2",
        language: str = "en-US",
        sample_rate: int = 16000,
    ):
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not found in environment")
        
        self.model = model
        self.language = language
        self.sample_rate = sample_rate
        
        # Initialize Deepgram client
        self.client = DeepgramClient(self.api_key)
        self.connection = None
        self.on_transcript: Optional[Callable] = None
        
    async def connect(self) -> None:
        """Establish WebSocket connection to Deepgram."""
        try:
            # Updated for Deepgram SDK 3.x
            self.connection = self.client.listen.asynclive.v("1")
            
            options = LiveOptions(
                model=self.model,
                language=self.language,
                encoding="linear16",
                sample_rate=self.sample_rate,
                channels=1,
                punctuate=True,
                smart_format=True,
                interim_results=True,
                utterance_end_ms=1000,
                vad_events=True,
            )
            
            self.connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
            self.connection.on(LiveTranscriptionEvents.Error, self._on_error)
            self.connection.on(LiveTranscriptionEvents.Close, self._on_close)
            
            if await self.connection.start(options):
                logger.info("✓ Connected to Deepgram")
            else:
                raise RuntimeError("Failed to start Deepgram connection")
                
        except Exception as e:
            logger.error(f"Failed to connect to Deepgram: {e}")
            raise
    
    async def _on_message(self, *args, **kwargs) -> None:
        """Handle incoming transcription results."""
        try:
            result = kwargs.get("result")
            if not result:
                return
            
            transcript = result.channel.alternatives[0].transcript
            
            if not transcript:
                return
            
            is_final = result.is_final
            confidence = result.channel.alternatives[0].confidence
            
            transcript_data = {
                "text": transcript,
                "is_final": is_final,
                "confidence": confidence,
                "timestamp": result.start if hasattr(result, 'start') else None,
            }
            
            if self.on_transcript:
                await self.on_transcript(transcript_data)
            
            if is_final:
                logger.info(f"Final: {transcript} ({confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Error processing transcript: {e}")
    
    async def _on_error(self, *args, **kwargs) -> None:
        """Handle errors."""
        error = kwargs.get("error")
        logger.error(f"Deepgram error: {error}")
    
    async def _on_close(self, *args, **kwargs) -> None:
        """Handle connection close."""
        logger.info("Deepgram connection closed")
    
    async def send_audio(self, audio_data: bytes) -> None:
        """Send audio data to Deepgram."""
        if not self.connection:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            await self.connection.send(audio_data)
        except Exception as e:
            logger.error(f"Error sending audio: {e}")
            raise
    
    async def close(self) -> None:
        """Close the connection."""
        if self.connection:
            await self.connection.finish()
            logger.info("Deepgram connection closed")
