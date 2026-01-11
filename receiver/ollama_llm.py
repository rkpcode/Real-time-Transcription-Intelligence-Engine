"""
Local LLM module using Ollama for receiver (FREE alternative).
"""

import os
import asyncio
from typing import Optional, List, Dict
import logging
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaLLM:
    """Generate intelligent hints using Ollama (local LLM)."""
    
    def __init__(
        self,
        model: str = "llama3.2:3b",
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
                        return "Unable to generate hint."
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return "Ollama not running. Start: ollama serve"
