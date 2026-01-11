"""
Real-time Speech-to-Text using Deepgram WebSocket API.
Optimized for <300ms latency.
"""

import asyncio
import os
from typing import AsyncGenerator, Callable, Optional
import logging
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
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
        config = DeepgramClientOptions(
            options={"keepalive": "true"}
        )
        self.client = DeepgramClient(self.api_key, config)
        self.connection = None
        
        # Callback for transcription results
        self.on_transcript: Optional[Callable] = None
        
    async def connect(self) -> None:
        """Establish WebSocket connection to Deepgram."""
        try:
            self.connection = self.client.listen.asyncwebsocket.v("1")
            
            # Configure live transcription options
            options = LiveOptions(
                model=self.model,
                language=self.language,
                encoding="linear16",
                sample_rate=self.sample_rate,
                channels=1,
                punctuate=True,
                smart_format=True,
                interim_results=True,  # Get partial results for lower latency
                utterance_end_ms=1000,  # End utterance after 1s of silence
                vad_events=True,  # Voice activity detection
            )
            
            # Set up event handlers
            self.connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
            self.connection.on(LiveTranscriptionEvents.Error, self._on_error)
            self.connection.on(LiveTranscriptionEvents.Close, self._on_close)
            
            # Start connection
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
            
            # Extract transcript
            transcript = result.channel.alternatives[0].transcript
            
            if not transcript:
                return
            
            # Check if this is a final result
            is_final = result.is_final
            confidence = result.channel.alternatives[0].confidence
            
            # Create transcript data
            transcript_data = {
                "text": transcript,
                "is_final": is_final,
                "confidence": confidence,
                "timestamp": result.start if hasattr(result, 'start') else None,
            }
            
            # Call the callback if set
            if self.on_transcript:
                await self.on_transcript(transcript_data)
            
            # Log final transcripts
            if is_final:
                logger.info(f"Final transcript: {transcript} (confidence: {confidence:.2f})")
            
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
        """
        Send audio data to Deepgram for transcription.
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM, mono, 16kHz)
        """
        if not self.connection:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            self.connection.send(audio_data)
        except Exception as e:
            logger.error(f"Error sending audio: {e}")
            raise
    
    async def close(self) -> None:
        """Close the connection."""
        if self.connection:
            await self.connection.finish()
            logger.info("Deepgram connection closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


async def test_deepgram():
    """Test Deepgram connection and transcription."""
    print("Testing Deepgram STT...")
    
    # Create a simple callback
    async def print_transcript(data):
        status = "FINAL" if data["is_final"] else "interim"
        print(f"[{status}] {data['text']} (confidence: {data.get('confidence', 0):.2f})")
    
    async with DeepgramSTT() as stt:
        stt.on_transcript = print_transcript
        
        print("✓ Deepgram connection successful!")
        print("Note: Send actual audio data using send_audio() to get transcriptions")
        
        # Keep connection alive for a bit
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(test_deepgram())
