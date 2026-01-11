"""
Simple test server to verify API keys and LLM functionality.
Run this to test if everything is working.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Load environment
load_dotenv()

app = FastAPI(title="Interview Sathi - Test Server")


@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "running",
        "message": "Interview Sathi Test Server",
        "version": "2.0"
    }


@app.get("/test-keys")
async def test_keys():
    """Test if API keys are loaded."""
    deepgram_key = os.getenv("DEEPGRAM_API_KEY")
    sambanova_key = os.getenv("SAMBANOVA_API_KEY")
    
    return {
        "deepgram": "✓ SET" if deepgram_key else "✗ NOT SET",
        "sambanova": "✓ SET" if sambanova_key else "✗ NOT SET",
        "deepgram_preview": deepgram_key[:20] + "..." if deepgram_key else None,
        "sambanova_preview": sambanova_key[:20] + "..." if sambanova_key else None,
    }


@app.get("/test-llm")
async def test_llm():
    """Test LLM with a simple question."""
    try:
        # Try importing multi-provider LLM
        import sys
        sys.path.append("../backend")
        from multi_provider_llm import MultiProviderLLM
        
        llm = MultiProviderLLM()
        response = await llm.generate_response("What is Python?")
        
        return {
            "status": "success",
            "question": "What is Python?",
            "answer": response,
            "provider_failures": llm.provider_failures
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


if __name__ == "__main__":
    print("=" * 50)
    print("Interview Sathi - Test Server")
    print("=" * 50)
    print("\nStarting server on http://localhost:8000")
    print("\nEndpoints:")
    print("  GET  /           - Health check")
    print("  GET  /test-keys  - Test API keys")
    print("  GET  /test-llm   - Test LLM")
    print("\n" + "=" * 50)
    
    uvicorn.run(
        "test_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
