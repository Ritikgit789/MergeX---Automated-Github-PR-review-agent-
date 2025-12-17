"""Centralized LLM Gateway for all PR review agents.

This gateway provides a single point of access to the Groq API,
with quality validation, smart retry logic, and performance tracking.
"""
from typing import Dict, Any, Optional, List
import asyncio
import json
import logging
import time
from groq import AsyncGroq
from app.config.settings import settings

logger = logging.getLogger(__name__)


class LLMGateway:
    """Central gateway for all LLM calls with quality validation and retry logic."""
    
    def __init__(self):
        """Initialize the Groq client."""
        self._client = None
        self._call_count = 0
        self._total_tokens = 0
        self._total_time = 0.0
        
    @property
    def client(self) -> AsyncGroq:
        """Lazy initialization of Groq client."""
        if not self._client:
            if not settings.groq_api_key:
                raise ValueError(
                    "GROQ_API_KEY not found in environment variables. "
                    "Get one at: https://console.groq.com/keys"
                )
            self._client = AsyncGroq(api_key=settings.groq_api_key)
        return self._client
    
    async def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        agent_name: str = "unknown",
        timeout: Optional[int] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Call LLM with quality validation and smart retry logic.
        
        Args:
            system_prompt: System instruction for the LLM
            user_prompt: User query/content to analyze
            agent_name: Name of the calling agent (for logging)
            timeout: Override default timeout (defaults to settings.groq_timeout)
            max_tokens: Override max tokens
            temperature: Override temperature
            
        Returns:
            Dict with 'success', 'content', 'error', 'tokens', 'duration'
        """
        timeout = timeout or settings.groq_timeout
        max_tokens = max_tokens or settings.groq_max_tokens
        temperature = temperature if temperature is not None else settings.groq_temperature
        
        start_time = time.time()
        
        try:
            # First attempt with quality timeout
            result = await self._make_call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                agent_name=agent_name,
                timeout=timeout,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            duration = time.time() - start_time
            
            # Validate response quality
            if result["success"]:
                validation = self._validate_response(result["content"], agent_name)
                if not validation["valid"]:
                    logger.warning(
                        f"[{agent_name}] Response validation failed: {validation['reason']}. "
                        f"Attempting retry..."
                    )
                    # Retry with faster timeout if validation fails
                    result = await self._make_call(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        agent_name=agent_name,
                        timeout=settings.groq_retry_timeout,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    duration = time.time() - start_time
            
            # Update metrics
            self._call_count += 1
            self._total_tokens += result.get("tokens", 0)
            self._total_time += duration
            
            result["duration"] = round(duration, 2)
            logger.info(
                f"[{agent_name}] LLM call completed in {duration:.2f}s "
                f"(tokens: {result.get('tokens', 0)})"
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[{agent_name}] LLM call failed after {duration:.2f}s: {str(e)}")
            return {
                "success": False,
                "content": "",
                "error": str(e),
                "tokens": 0,
                "duration": round(duration, 2)
            }
    
    async def _make_call(
        self,
        system_prompt: str,
        user_prompt: str,
        agent_name: str,
        timeout: int,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Make the actual LLM API call with timeout."""
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=settings.groq_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}
                ),
                timeout=timeout
            )
            
            content = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            
            return {
                "success": True,
                "content": content,
                "error": None,
                "tokens": tokens
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "content": "",
                "error": f"LLM call timed out after {timeout}s",
                "tokens": 0
            }
        except Exception as e:
            return {
                "success": False,
                "content": "",
                "error": str(e),
                "tokens": 0
            }
    
    def _validate_response(self, content: str, agent_name: str) -> Dict[str, Any]:
        """
        Validate LLM response quality.
        
        Args:
            content: Response content from LLM
            agent_name: Name of the agent for context
            
        Returns:
            Dict with 'valid' boolean and 'reason' string
        """
        if not content or not content.strip():
            return {"valid": False, "reason": "Empty response"}
        
        # Try to parse JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return {"valid": False, "reason": f"Invalid JSON: {str(e)}"}
        
        # Check if it's a list or has expected structure
        if isinstance(data, list):
            # Valid - this is the expected format
            return {"valid": True, "reason": "Valid JSON array"}
        elif isinstance(data, dict):
            # Check if it has expected keys (some LLMs wrap in object)
            if "issues" in data or "findings" in data or "comments" in data:
                return {"valid": True, "reason": "Valid JSON object with expected keys"}
            else:
                logger.warning(f"[{agent_name}] Unexpected JSON structure: {list(data.keys())}")
                return {"valid": True, "reason": "Valid JSON (unexpected structure)"}
        else:
            return {"valid": False, "reason": f"Unexpected JSON type: {type(data)}"}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        avg_time = self._total_time / self._call_count if self._call_count > 0 else 0
        return {
            "total_calls": self._call_count,
            "total_tokens": self._total_tokens,
            "total_time": round(self._total_time, 2),
            "avg_time_per_call": round(avg_time, 2)
        }


# Singleton instance
_gateway_instance = None

def get_llm_gateway() -> LLMGateway:
    """Get or create the singleton LLM gateway instance."""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = LLMGateway()
    return _gateway_instance
