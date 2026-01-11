"""
FastAPI Audio Receiver Server
Receives audio stream from main laptop and processes it for transcription.
"""

import asyncio
import os
from typing import Optional
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import pyaudio

from deepgram_stt import DeepgramSTT
try:
    from groq_llm import GroqLLM
except ImportError:
    GroqLLM = None

# Load environment
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Interview Sathi - Audio Receiver")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
deepgram_stt: Optional[DeepgramSTT] = None
groq_llm: Optional[GroqLLM] = None
connected_clients = set()

# Audio buffer for hardware input
audio_buffer = asyncio.Queue()


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global deepgram_stt, groq_llm
    
    logger.info("Starting Interview Sathi Receiver...")
    
    # Initialize Deepgram
    deepgram_stt = DeepgramSTT(
        model=os.getenv("DEEPGRAM_MODEL", "nova-2"),
        language=os.getenv("DEEPGRAM_LANGUAGE", "en-US"),
        sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", 16000)),
    )
    
    # Initialize LLM (try Groq, SambaNova, or skip if not available)
    groq_api_key = os.getenv("GROQ_API_KEY")
    sambanova_api_key = os.getenv("SAMBANOVA_API_KEY")
    
    if groq_api_key and GroqLLM:
        groq_llm = GroqLLM(
            model=os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
            max_tokens=int(os.getenv("GROQ_MAX_TOKENS", 100)),
            temperature=float(os.getenv("GROQ_TEMPERATURE", 0.2)),
        )
        logger.info("✓ Using Groq LLM")
    elif sambanova_api_key:
        # Use SambaNova via simple HTTP client
        groq_llm = None  # Will use SambaNova in generate_hint
        logger.info("✓ Using SambaNova LLM")
    else:
        groq_llm = None
        logger.warning("⚠ No LLM API key found - hints disabled")
    
    # Set custom system prompt for interview hints
    if groq_llm:
        groq_llm.system_prompt = """You are a stealth interview assistant. 
Analyze the interview question and provide a SINGLE SENTENCE hint or key point.
Be extremely concise - maximum 15 words.
Focus on the core concept or framework to mention.
Do not write full answers, just hints."""
    
    logger.info("✓ Components initialized")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Interview Sathi Receiver",
        "version": "2.0-stealth"
    }


@app.get("/status")
async def status():
    """Detailed status endpoint."""
    return {
        "deepgram": "connected" if deepgram_stt else "not initialized",
        "groq": "connected" if groq_llm else "not initialized",
        "connected_clients": len(connected_clients),
        "input_mode": os.getenv("INPUT_MODE", "hardware")
    }


@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for receiving audio stream from main laptop.
    Use this for network-based audio streaming.
    """
    await websocket.accept()
    logger.info("Audio WebSocket client connected")
    
    try:
        # Connect to Deepgram
        await deepgram_stt.connect()
        
        # Set up transcript callback
        async def handle_transcript(data):
            # Send transcript to all UI clients
            await broadcast_to_clients({
                "type": "transcript",
                "data": data
            })
            
            # Generate hint if final transcript
            if data["is_final"] and data["text"].strip():
                await generate_hint(data["text"])
        
        deepgram_stt.on_transcript = handle_transcript
        
        # Receive and process audio
        while True:
            # Receive audio chunk
            audio_data = await websocket.receive_bytes()
            
            # Send to Deepgram
            await deepgram_stt.send_audio(audio_data)
            
    except WebSocketDisconnect:
        logger.info("Audio WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Error in audio WebSocket: {e}")
    finally:
        await deepgram_stt.close()


@app.post("/audio/stream")
async def stream_audio_chunk(file: UploadFile = File(...)):
    """
    HTTP endpoint for receiving audio chunks.
    Alternative to WebSocket for simpler clients.
    """
    try:
        audio_data = await file.read()
        
        # Add to buffer for processing
        await audio_buffer.put(audio_data)
        
        return {"status": "received", "bytes": len(audio_data)}
        
    except Exception as e:
        logger.error(f"Error receiving audio chunk: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.websocket("/ws/ui")
async def websocket_ui_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for React UI clients.
    Sends transcripts and AI hints to the prompter interface.
    """
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"UI client connected. Total: {len(connected_clients)}")
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "status",
            "data": {
                "status": "connected",
                "message": "Stealth Prompter Ready"
            }
        })
        
        # Keep connection alive
        while True:
            # Receive messages from UI (e.g., clear context)
            message = await websocket.receive_json()
            
            if message.get("type") == "clear_context":
                groq_llm.clear_context()
                await websocket.send_json({
                    "type": "status",
                    "data": {"status": "context_cleared"}
                })
                
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
        logger.info(f"UI client disconnected. Total: {len(connected_clients)}")
    except Exception as e:
        logger.error(f"Error in UI WebSocket: {e}")
        connected_clients.discard(websocket)


async def broadcast_to_clients(message: dict):
    """Broadcast message to all connected UI clients."""
    if not connected_clients:
        return
    
    disconnected = set()
    
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception as e:
            logger.error(f"Error broadcasting to client: {e}")
            disconnected.add(client)
    
    # Remove disconnected clients
    connected_clients.difference_update(disconnected)


async def generate_hint(transcript: str):
    """Generate AI hint based on transcript."""
    try:
        # Check if LLM is available
        if not groq_llm:
            logger.debug("LLM not available - skipping hint generation")
            return
        
        # Check if this looks like a question
        question_indicators = ['?', 'what', 'how', 'why', 'explain', 'describe', 'tell me']
        is_question = any(ind in transcript.lower() for ind in question_indicators)
        
        if not is_question:
            return
        
        # Generate hint
        hint = await groq_llm.generate_response(
            transcript=transcript,
            question="Provide a brief hint to answer this question"
        )
        
        # Broadcast hint to UI
        await broadcast_to_clients({
            "type": "hint",
            "data": {
                "text": hint,
                "question": transcript[-100:],  # Last 100 chars
                "timestamp": asyncio.get_event_loop().time()
            }
        })
        
        logger.info(f"Generated hint: {hint[:50]}...")
        
    except Exception as e:
        logger.error(f"Error generating hint: {e}")


async def hardware_audio_capture():
    """
    Capture audio from USB sound card (hardware input mode).
    Runs as background task.
    """
    logger.info("Starting hardware audio capture...")
    
    sample_rate = int(os.getenv("AUDIO_SAMPLE_RATE", 16000))
    chunk_size = int(os.getenv("AUDIO_CHUNK_SIZE", 1600))
    device_index = int(os.getenv("HARDWARE_DEVICE_INDEX", 0))
    
    audio = pyaudio.PyAudio()
    
    try:
        # Open audio stream from USB sound card
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk_size,
        )
        
        logger.info(f"✓ Capturing from device {device_index}")
        
        # Connect to Deepgram
        await deepgram_stt.connect()
        
        # Set up transcript callback
        async def handle_transcript(data):
            await broadcast_to_clients({
                "type": "transcript",
                "data": data
            })
            
            if data["is_final"] and data["text"].strip():
                await generate_hint(data["text"])
        
        deepgram_stt.on_transcript = handle_transcript
        
        # Capture and process audio
        while True:
            audio_data = stream.read(chunk_size, exception_on_overflow=False)
            await deepgram_stt.send_audio(audio_data)
            await asyncio.sleep(0.01)  # Small delay to prevent blocking
            
    except Exception as e:
        logger.error(f"Error in hardware audio capture: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        await deepgram_stt.close()


@app.on_event("startup")
async def start_hardware_capture():
    """Start hardware audio capture if in hardware mode."""
    input_mode = os.getenv("INPUT_MODE", "hardware")
    
    if input_mode == "hardware":
        asyncio.create_task(hardware_audio_capture())
        logger.info("Hardware audio capture task started")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 8000))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "audio_server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
