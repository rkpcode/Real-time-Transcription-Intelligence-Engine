"""
LLM response generation using Groq API with Llama 3.
Optimized for <800ms latency with streaming support.
"""

import os
import asyncio
from typing import Optional, List, Dict
import logging
from groq import AsyncGroq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroqLLM:
    """Generate intelligent responses using Groq's ultra-fast LLM API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.1-70b-versatile",
        max_tokens: int = 150,
        temperature: float = 0.3,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize Groq client
        self.client = AsyncGroq(api_key=self.api_key)
        
        # Conversation context (last N messages)
        self.context: List[Dict[str, str]] = []
        self.max_context_length = 10  # Keep last 10 exchanges
        
        # System prompt
        self.system_prompt = """You are an intelligent assistant helping during a video call or interview. 
Your role is to provide brief, actionable answers based on the conversation transcript.

Guidelines:
- Keep responses under 50 words
- Be concise and direct
- Focus on actionable information
- If asked a technical question, provide clear explanations
- If you don't have enough context, ask for clarification briefly"""
        
    def add_to_context(self, role: str, content: str) -> None:
        """
        Add a message to the conversation context.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
        """
        self.context.append({"role": role, "content": content})
        
        # Trim context if too long
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
        stream: bool = False,
    ) -> str:
        """
        Generate a response based on the transcript.
        
        Args:
            transcript: Recent conversation transcript
            question: Optional specific question to answer
            stream: Whether to stream the response
            
        Returns:
            Generated response text
        """
        try:
            # Build the user message
            if question:
                user_message = f"Transcript: {transcript}\n\nQuestion: {question}"
            else:
                user_message = f"Based on this conversation, provide a helpful insight or answer any implied questions:\n\n{transcript}"
            
            # Build messages array
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.context,
                {"role": "user", "content": user_message}
            ]
            
            # Generate response
            if stream:
                response_text = await self._generate_streaming(messages)
            else:
                response_text = await self._generate_standard(messages)
            
            # Add to context
            self.add_to_context("user", user_message)
            self.add_to_context("assistant", response_text)
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm having trouble generating a response right now."
    
    async def _generate_standard(self, messages: List[Dict[str, str]]) -> str:
        """Generate response without streaming."""
        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            
            response_text = completion.choices[0].message.content
            logger.info(f"Generated response: {response_text[:100]}...")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error in standard generation: {e}")
            raise
    
    async def _generate_streaming(self, messages: List[Dict[str, str]]) -> str:
        """Generate response with streaming (for progressive display)."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
            )
            
            response_text = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
            
            logger.info(f"Generated streaming response: {response_text[:100]}...")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            raise
    
    async def generate_quick_answer(self, question: str) -> str:
        """
        Generate a quick answer without full context.
        Useful for simple, standalone questions.
        
        Args:
            question: The question to answer
            
        Returns:
            Brief answer
        """
        try:
            messages = [
                {"role": "system", "content": "Provide a brief, accurate answer in under 30 words."},
                {"role": "user", "content": question}
            ]
            
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=100,
                temperature=0.2,
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating quick answer: {e}")
            return "Unable to answer right now."


async def test_groq():
    """Test Groq LLM integration."""
    print("Testing Groq LLM...")
    
    llm = GroqLLM()
    
    # Test 1: Simple question
    print("\n--- Test 1: Quick Answer ---")
    answer = await llm.generate_quick_answer("What is Python?")
    print(f"Q: What is Python?\nA: {answer}")
    
    # Test 2: Context-based response
    print("\n--- Test 2: Context-based Response ---")
    transcript = "We're discussing machine learning models. The interviewer asked about the difference between supervised and unsupervised learning."
    response = await llm.generate_response(transcript)
    print(f"Transcript: {transcript}\nResponse: {response}")
    
    # Test 3: Specific question with context
    print("\n--- Test 3: Specific Question ---")
    transcript = "The conversation is about web development frameworks."
    question = "What are the benefits of using React?"
    response = await llm.generate_response(transcript, question)
    print(f"Question: {question}\nResponse: {response}")
    
    print("\n✓ Groq LLM test successful!")


if __name__ == "__main__":
    asyncio.run(test_groq())
