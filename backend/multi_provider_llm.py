"""
Multi-provider LLM with automatic failover.
Tries Groq → SambaNova → Together AI → Ollama
"""

import asyncio
import os
from typing import Optional, List, Dict
import logging
from groq import AsyncGroq
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiProviderLLM:
    """LLM with automatic failover across multiple providers."""
    
    def __init__(self):
        # API keys
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.sambanova_key = os.getenv("SAMBANOVA_API_KEY")
        self.together_key = os.getenv("TOGETHER_API_KEY")
        
        # Clients
        self.groq_client = AsyncGroq(api_key=self.groq_key) if self.groq_key else None
        
        # Context
        self.context: List[Dict[str, str]] = []
        self.max_context_length = 5
        
        # System prompt
        self.system_prompt = """You are an intelligent assistant helping during a video call. 
Provide brief, actionable answers in under 50 words.
Focus on key concepts and frameworks."""
        
        # Provider status tracking
        self.provider_failures = {"groq": 0, "sambanova": 0, "together": 0, "ollama": 0}
        
    def add_to_context(self, role: str, content: str):
        """Add to conversation context."""
        self.context.append({"role": role, "content": content})
        if len(self.context) > self.max_context_length:
            self.context = self.context[-self.max_context_length:]
    
    def clear_context(self):
        """Clear context."""
        self.context = []
    
    async def _try_groq(self, messages: List[Dict]) -> Optional[str]:
        """Try Groq API."""
        if not self.groq_client:
            return None
        
        try:
            completion = await self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=messages,
                max_tokens=150,
                temperature=0.3,
            )
            self.provider_failures["groq"] = 0  # Reset on success
            logger.info("✓ Groq response")
            return completion.choices[0].message.content
        except Exception as e:
            self.provider_failures["groq"] += 1
            logger.warning(f"Groq failed: {e}")
            return None
    
    async def _try_sambanova(self, messages: List[Dict]) -> Optional[str]:
        """Try SambaNova API."""
        if not self.sambanova_key:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.sambanova.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.sambanova_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "Meta-Llama-3.1-405B-Instruct",
                        "messages": messages,
                        "max_tokens": 150,
                        "temperature": 0.3,
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.provider_failures["sambanova"] = 0
                        logger.info("✓ SambaNova response")
                        return result["choices"][0]["message"]["content"]
        except Exception as e:
            self.provider_failures["sambanova"] += 1
            logger.warning(f"SambaNova failed: {e}")
        return None
    
    async def _try_together(self, messages: List[Dict]) -> Optional[str]:
        """Try Together AI."""
        if not self.together_key:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.together.xyz/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.together_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                        "messages": messages,
                        "max_tokens": 150,
                        "temperature": 0.3,
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.provider_failures["together"] = 0
                        logger.info("✓ Together AI response")
                        return result["choices"][0]["message"]["content"]
        except Exception as e:
            self.provider_failures["together"] += 1
            logger.warning(f"Together AI failed: {e}")
        return None
    
    async def _try_ollama(self, messages: List[Dict]) -> Optional[str]:
        """Try local Ollama."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": "llama3.2:3b",
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": 0.3, "num_predict": 150}
                    },
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.provider_failures["ollama"] = 0
                        logger.info("✓ Ollama response")
                        return result["message"]["content"]
        except Exception as e:
            self.provider_failures["ollama"] += 1
            logger.warning(f"Ollama failed: {e}")
        return None
    
    async def generate_response(self, transcript: str, question: Optional[str] = None) -> str:
        """Generate response with automatic failover."""
        user_message = f"Based on this conversation, provide a helpful insight:\n\n{transcript}"
        if question:
            user_message = f"Question: {question}\n\nContext: {transcript}"
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.context,
            {"role": "user", "content": user_message}
        ]
        
        # Try providers in order of speed/reliability
        providers = [
            ("Groq", self._try_groq),
            ("SambaNova", self._try_sambanova),
            ("Together AI", self._try_together),
            ("Ollama", self._try_ollama),
        ]
        
        for name, provider_func in providers:
            # Skip if failed too many times
            if self.provider_failures.get(name.lower().replace(" ", ""), 0) > 3:
                continue
            
            response = await provider_func(messages)
            if response:
                self.add_to_context("user", user_message)
                self.add_to_context("assistant", response)
                return response
        
        # All providers failed
        logger.error("All LLM providers failed!")
        return "Unable to generate response. Please check your API keys and internet connection."


async def test_multi_provider():
    """Test multi-provider LLM."""
    print("Testing Multi-Provider LLM with Failover...")
    print()
    
    llm = MultiProviderLLM()
    
    # Test
    response = await llm.generate_response("What is machine learning?")
    print(f"Response: {response}")
    print()
    print(f"Provider failures: {llm.provider_failures}")


if __name__ == "__main__":
    asyncio.run(test_multi_provider())
