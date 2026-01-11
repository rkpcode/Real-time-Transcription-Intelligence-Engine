"""
Groq LLM module for receiver (same as backend).
"""

import os
import asyncio
from typing import Optional, List, Dict
import logging
from groq import AsyncGroq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroqLLM:
    """Generate intelligent hints using Groq's ultra-fast LLM API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.1-70b-versatile",
        max_tokens: int = 100,
        temperature: float = 0.2,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        self.client = AsyncGroq(api_key=self.api_key)
        self.context: List[Dict[str, str]] = []
        self.max_context_length = 5  # Shorter for faster responses
        
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
            
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            
            hint = completion.choices[0].message.content
            
            self.add_to_context("user", user_message)
            self.add_to_context("assistant", hint)
            
            logger.info(f"Generated hint: {hint}")
            
            return hint
            
        except Exception as e:
            logger.error(f"Error generating hint: {e}")
            return "Unable to generate hint right now."
