"""
Local LLM module using Ollama (FREE alternative to Groq).
No API keys needed - runs completely locally.
"""

import asyncio
import os
from typing import Optional, List, Dict
import logging
import json
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaLLM:
    """Generate intelligent hints using Ollama (local LLM)."""
    
    def __init__(
        self,
        model: str = "llama3.2:3b",  # Fast, lightweight model
        host: str = "http://localhost:11434",
        max_tokens: int = 100,
        temperature: float = 0.2,
    ):
        self.model = model
        self.host = host
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        self.context: List[Dict[str, str]] = []
        self.max_context_length = 5
        
        self.system_prompt = """You are a stealth interview assistant. 
Provide ONLY a brief hint or key concept in ONE sentence (max 15 words).
Focus on frameworks, key terms, or approach - not full answers."""
        
    def add_to_context(self, role: str, content: str) -> None:
        """Add message to context."""
        self.context.append({"role": role, "content": content})
        
        if len(self.context) > self.max_context_length:
            self.context = self.context[-self.max_context_length:]
    
    def clear_context(self) -> None:
        """Clear conversation context."""
        self.context = []
        logger.info("Context cleared")
    
    async def generate_response(
        self,
        transcript: str,
        question: Optional[str] = None,
    ) -> str:
        """Generate a hint based on the transcript."""
        try:
            user_message = f"Question: {transcript}\n\nProvide a brief hint."
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.context,
                {"role": "user", "content": user_message}
            ]
            
            # Call Ollama API
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    }
                }
                
                async with session.post(
                    f"{self.host}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        hint = result["message"]["content"]
                        
                        self.add_to_context("user", user_message)
                        self.add_to_context("assistant", hint)
                        
                        logger.info(f"Generated hint: {hint}")
                        return hint
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama error: {error_text}")
                        return "Unable to generate hint right now."
            
        except aiohttp.ClientConnectorError:
            logger.error("Cannot connect to Ollama. Is it running?")
            return "Ollama not running. Start it with: ollama serve"
        except Exception as e:
            logger.error(f"Error generating hint: {e}")
            return "Unable to generate hint right now."


async def test_ollama():
    """Test Ollama LLM integration."""
    print("Testing Ollama LLM...")
    print("Make sure Ollama is running: ollama serve")
    print()
    
    llm = OllamaLLM()
    
    # Test 1: Simple question
    print("--- Test 1: Quick Answer ---")
    answer = await llm.generate_response("What is Python?")
    print(f"Q: What is Python?\nA: {answer}\n")
    
    # Test 2: Context-based response
    print("--- Test 2: Context-based Response ---")
    transcript = "Explain the difference between supervised and unsupervised learning"
    response = await llm.generate_response(transcript)
    print(f"Q: {transcript}\nA: {response}\n")
    
    print("✓ Ollama LLM test successful!")


if __name__ == "__main__":
    asyncio.run(test_ollama())
