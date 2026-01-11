"""
Audio Sender - Stream audio from Interview Laptop to Receiver via WiFi
Run this on Laptop 1 (Interview laptop)
"""
import asyncio
import pyaudio
import websockets
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_audio():
    """Stream audio from microphone to receiver server via WebSocket."""
    server_url = os.getenv("WEBSOCKET_SERVER_URL", "ws://localhost:8000/ws/audio")
    sample_rate = int(os.getenv("AUDIO_SAMPLE_RATE", 16000))
    chunk_size = int(os.getenv("AUDIO_CHUNK_SIZE", 1600))
    
    logger.info(f"Connecting to receiver: {server_url}")
    
    # Initialize PyAudio
    audio = pyaudio.PyAudio()
    
    # List available audio devices
    logger.info("Available audio devices:")
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        logger.info(f"  [{i}] {info['name']}")
    
    # Open microphone stream
    device_index = int(os.getenv("AUDIO_DEVICE_INDEX", 0))
    logger.info(f"Using device index: {device_index}")
    
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=chunk_size,
    )
    
    try:
        async with websockets.connect(server_url) as websocket:
            logger.info("✓ Connected to receiver! Streaming audio...")
            logger.info("Speak into microphone - transcription will appear on receiver")
            
            while True:
                # Read audio from microphone
                audio_data = stream.read(chunk_size, exception_on_overflow=False)
                
                # Send to receiver
                await websocket.send(audio_data)
                
    except KeyboardInterrupt:
        logger.info("\nStopped streaming")
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error("Make sure receiver server is running on Laptop 2")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


if __name__ == "__main__":
    print("=" * 60)
    print("Interview Sathi - Audio Sender")
    print("=" * 60)
    print("\nStreaming audio to receiver laptop via WiFi...")
    print("Press Ctrl+C to stop\n")
    
    asyncio.run(send_audio())
