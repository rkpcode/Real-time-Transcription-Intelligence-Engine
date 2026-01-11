"""
Main orchestration module for Interview Sathi backend.
Coordinates audio capture, STT, LLM, and WebSocket server.
"""

import asyncio
import os
import time
import logging
from dotenv import load_dotenv

from audio_capture import AudioCapture
from deepgram_stt import DeepgramSTT
from groq_llm import GroqLLM
from websocket_server import WebSocketServer

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InterviewSathi:
    """Main application orchestrator."""
    
    def __init__(self):
        # Initialize components
        self.audio_capture = None
        self.deepgram_stt = None
        self.groq_llm = None
        self.websocket_server = None
        
        # Transcript buffer for LLM context
        self.transcript_buffer = []
        self.buffer_max_length = 10  # Keep last 10 final transcripts
        
        # Latency tracking
        self.last_audio_timestamp = None
        
    async def initialize(self) -> None:
        """Initialize all components."""
        logger.info("Initializing Interview Sathi...")
        
        # Initialize audio capture
        sample_rate = int(os.getenv("AUDIO_SAMPLE_RATE", 16000))
        chunk_size = int(os.getenv("AUDIO_CHUNK_SIZE", 1600))
        
        self.audio_capture = AudioCapture(
            sample_rate=sample_rate,
            channels=1,
            chunk_size=chunk_size,
        )
        
        # Initialize Deepgram STT
        self.deepgram_stt = DeepgramSTT(
            model=os.getenv("DEEPGRAM_MODEL", "nova-2"),
            language=os.getenv("DEEPGRAM_LANGUAGE", "en-US"),
            sample_rate=sample_rate,
        )
        
        # Set up transcript callback
        self.deepgram_stt.on_transcript = self.handle_transcript
        
        # Initialize Groq LLM
        self.groq_llm = GroqLLM(
            model=os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
            max_tokens=int(os.getenv("GROQ_MAX_TOKENS", 150)),
            temperature=float(os.getenv("GROQ_TEMPERATURE", 0.3)),
        )
        
        # Initialize WebSocket server
        ws_host = os.getenv("WEBSOCKET_HOST", "localhost")
        ws_port = int(os.getenv("WEBSOCKET_PORT", 8765))
        
        self.websocket_server = WebSocketServer(
            host=ws_host,
            port=ws_port,
        )
        
        logger.info("✓ All components initialized")
    
    async def handle_transcript(self, transcript_data: dict) -> None:
        """
        Handle incoming transcripts from Deepgram.
        
        Args:
            transcript_data: Transcript data from Deepgram
        """
        text = transcript_data["text"]
        is_final = transcript_data["is_final"]
        confidence = transcript_data.get("confidence", 0.0)
        
        # Send transcript to frontend
        await self.websocket_server.send_transcript(
            text=text,
            is_final=is_final,
            confidence=confidence,
        )
        
        # If final transcript, add to buffer and potentially generate response
        if is_final and text.strip():
            self.transcript_buffer.append(text)
            
            # Trim buffer
            if len(self.transcript_buffer) > self.buffer_max_length:
                self.transcript_buffer = self.transcript_buffer[-self.buffer_max_length:]
            
            # Check if we should generate a response
            await self.maybe_generate_response(text)
    
    async def maybe_generate_response(self, latest_transcript: str) -> None:
        """
        Decide whether to generate an LLM response based on the transcript.
        
        Args:
            latest_transcript: The most recent final transcript
        """
        # Simple heuristic: Generate response if transcript ends with '?'
        # or contains question words
        question_indicators = ['?', 'what', 'how', 'why', 'when', 'where', 'who', 'can you', 'could you']
        
        should_respond = any(
            indicator in latest_transcript.lower()
            for indicator in question_indicators
        )
        
        if should_respond:
            await self.generate_response()
    
    async def generate_response(self) -> None:
        """Generate and send an LLM response based on recent transcripts."""
        try:
            start_time = time.time()
            
            # Combine recent transcripts for context
            context = " ".join(self.transcript_buffer[-5:])  # Last 5 transcripts
            
            # Generate response
            response = await self.groq_llm.generate_response(context)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Send response to frontend
            await self.websocket_server.send_response(
                text=response,
                context=context[-100:],  # Last 100 chars of context
                latency_ms=latency_ms,
            )
            
            logger.info(f"Generated response in {latency_ms}ms: {response[:50]}...")
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await self.websocket_server.send_status("error", {
                "message": "Failed to generate response"
            })
    
    async def audio_pipeline(self) -> None:
        """Main audio processing pipeline."""
        logger.info("Starting audio pipeline...")
        
        try:
            # Start audio capture
            self.audio_capture.start()
            
            # Connect to Deepgram
            await self.deepgram_stt.connect()
            
            # Send status update
            await self.websocket_server.send_status("listening", {
                "message": "Audio capture active"
            })
            
            # Stream audio to Deepgram
            async for audio_chunk in self.audio_capture.stream_audio():
                await self.deepgram_stt.send_audio(audio_chunk)
                
        except Exception as e:
            logger.error(f"Error in audio pipeline: {e}")
            await self.websocket_server.send_status("error", {
                "message": f"Audio pipeline error: {str(e)}"
            })
        finally:
            # Cleanup
            self.audio_capture.close()
            await self.deepgram_stt.close()
    
    async def run(self) -> None:
        """Run the main application."""
        try:
            # Initialize components
            await self.initialize()
            
            # Start WebSocket server
            await self.websocket_server.start()
            
            # Run audio pipeline
            await self.audio_pipeline()
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up...")
        
        if self.audio_capture:
            self.audio_capture.close()
        
        if self.deepgram_stt:
            await self.deepgram_stt.close()
        
        if self.websocket_server:
            await self.websocket_server.stop()
        
        logger.info("✓ Cleanup complete")


async def main():
    """Entry point."""
    print("=" * 60)
    print("Interview Sathi - Real-time Audio Transcription & LLM Assistant")
    print("=" * 60)
    print()
    
    # Check for API keys
    if not os.getenv("DEEPGRAM_API_KEY"):
        print("❌ DEEPGRAM_API_KEY not found in environment")
        print("Please set it in .env file or environment variables")
        return
    
    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not found in environment")
        print("Please set it in .env file or environment variables")
        return
    
    print("✓ API keys found")
    print()
    
    # Create and run application
    app = InterviewSathi()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
