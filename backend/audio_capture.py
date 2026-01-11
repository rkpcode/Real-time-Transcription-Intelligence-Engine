"""
Cross-platform system audio capture module.
Supports Windows (PyAudioWPatch) and macOS (PyAudio + BlackHole).
"""

import asyncio
import platform
import pyaudio
from typing import AsyncGenerator, Optional
import logging

# Platform-specific imports
if platform.system() == "Windows":
    try:
        import pyaudiowpatch as pa
    except ImportError:
        import pyaudio as pa
        logging.warning("PyAudioWPatch not found, falling back to PyAudio")
else:
    import pyaudio as pa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioCapture:
    """Captures system audio output for real-time processing."""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1600,  # 100ms at 16kHz
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.audio = pa.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        
    def _get_default_output_device(self) -> dict:
        """Get the default system output device (speakers/headphones)."""
        try:
            if platform.system() == "Windows":
                # On Windows, get WASAPI loopback device
                wasapi_info = self.audio.get_host_api_info_by_type(pyaudio.paWASAPI)
                default_device = self.audio.get_default_output_device_info()
                
                # Find loopback device
                for i in range(self.audio.get_device_count()):
                    device_info = self.audio.get_device_info_by_index(i)
                    if (device_info['hostApi'] == wasapi_info['index'] and
                        'loopback' in device_info['name'].lower()):
                        logger.info(f"Found loopback device: {device_info['name']}")
                        return device_info
                
                # Fallback to default output
                logger.warning("Loopback device not found, using default output")
                return default_device
            else:
                # On macOS, use BlackHole or default input (which should be BlackHole)
                default_device = self.audio.get_default_input_device_info()
                logger.info(f"Using device: {default_device['name']}")
                return default_device
                
        except Exception as e:
            logger.error(f"Error getting audio device: {e}")
            raise
    
    def start(self) -> None:
        """Start capturing audio."""
        device_info = self._get_default_output_device()
        
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_info['index'],
                frames_per_buffer=self.chunk_size,
                stream_callback=None,  # We'll use blocking mode for simplicity
            )
            logger.info("Audio capture started successfully")
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            raise
    
    def stop(self) -> None:
        """Stop capturing audio."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            logger.info("Audio capture stopped")
    
    def close(self) -> None:
        """Clean up resources."""
        self.stop()
        self.audio.terminate()
        logger.info("Audio capture closed")
    
    async def stream_audio(self) -> AsyncGenerator[bytes, None]:
        """
        Async generator that yields audio chunks.
        
        Yields:
            bytes: Raw audio data (16-bit PCM, mono, 16kHz)
        """
        if not self.stream:
            raise RuntimeError("Audio stream not started. Call start() first.")
        
        loop = asyncio.get_event_loop()
        
        try:
            while True:
                # Read audio in a non-blocking way
                audio_data = await loop.run_in_executor(
                    None,
                    self.stream.read,
                    self.chunk_size,
                    False  # Don't raise exception on overflow
                )
                yield audio_data
                
        except Exception as e:
            logger.error(f"Error streaming audio: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


async def test_audio_capture():
    """Test function to verify audio capture works."""
    print("Testing audio capture...")
    print(f"Platform: {platform.system()}")
    
    capture = AudioCapture()
    capture.start()
    
    try:
        chunk_count = 0
        async for audio_chunk in capture.stream_audio():
            chunk_count += 1
            print(f"Captured chunk {chunk_count}: {len(audio_chunk)} bytes")
            
            if chunk_count >= 10:  # Capture 1 second of audio
                break
        
        print("✓ Audio capture test successful!")
        
    finally:
        capture.close()


if __name__ == "__main__":
    asyncio.run(test_audio_capture())
