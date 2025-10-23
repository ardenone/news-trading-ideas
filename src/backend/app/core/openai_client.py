"""OpenAI Responses API client with error handling and cost tracking"""

import asyncio
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime
import structlog
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from app.config import settings

logger = structlog.get_logger()


class OpenAIClient:
    """Wrapper for OpenAI Responses API with retry logic and cost tracking"""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
        self.max_retries = 3
        self.backoff_base = 2
        self.total_cost_today = 0.0

        # Pricing (as of Oct 2025)
        self.pricing = {
            "gpt-4o-mini": {"input": 0.150 / 1_000_000, "output": 0.600 / 1_000_000},
            "gpt-4-turbo": {"input": 10.0 / 1_000_000, "output": 30.0 / 1_000_000},
            "gpt-4": {"input": 30.0 / 1_000_000, "output": 60.0 / 1_000_000},
            "text-embedding-3-small": {"input": 0.020 / 1_000_000, "output": 0.0},
        }

    async def create_response(
        self,
        input_text: str,
        model: str,
        instructions: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Call OpenAI Responses API with retry logic

        Args:
            input_text: The input prompt
            model: Model name (gpt-4o-mini, gpt-4-turbo, etc.)
            instructions: System instructions
            temperature: Sampling temperature (0-2)
            max_output_tokens: Max tokens in response
            response_format: {"type": "json_object"} for JSON mode

        Returns:
            Response dictionary with text, usage, and cost
        """
        for attempt in range(self.max_retries):
            try:
                # Build request payload
                payload = {
                    "model": model,
                    "input": input_text,
                    "temperature": temperature,
                }

                if instructions:
                    payload["instructions"] = instructions

                if max_output_tokens:
                    payload["max_output_tokens"] = max_output_tokens

                if response_format:
                    payload["text"] = {"format": response_format}

                # Make API call
                response = await self.client.post(
                    "/responses",
                    cast_to=object,
                    body=payload,
                )

                # Parse response
                result = self._parse_response(response, model)

                # Track cost
                self.total_cost_today += result["cost"]
                if self.total_cost_today > settings.MAX_DAILY_OPENAI_COST:
                    logger.warning(
                        "daily_cost_limit_exceeded",
                        total_cost=self.total_cost_today,
                        limit=settings.MAX_DAILY_OPENAI_COST,
                    )

                logger.info(
                    "openai_api_success",
                    model=model,
                    input_tokens=result["usage"]["input_tokens"],
                    output_tokens=result["usage"]["output_tokens"],
                    cost=result["cost"],
                    attempt=attempt + 1,
                )

                return result

            except RateLimitError as e:
                wait_time = self.backoff_base**attempt
                logger.warning(
                    "openai_rate_limit",
                    attempt=attempt + 1,
                    wait_time=wait_time,
                    error=str(e),
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    raise

            except APITimeoutError as e:
                wait_time = self.backoff_base**attempt
                logger.warning(
                    "openai_timeout",
                    attempt=attempt + 1,
                    wait_time=wait_time,
                    error=str(e),
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    raise

            except APIError as e:
                logger.error("openai_api_error", attempt=attempt + 1, error=str(e))
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise

            except Exception as e:
                logger.error("unexpected_openai_error", error=str(e), type=type(e).__name__)
                raise

    def _parse_response(self, response: Any, model: str) -> Dict[str, Any]:
        """Parse OpenAI Responses API response"""
        # Extract output text
        output_items = response.get("output", [])
        text_content = ""

        for item in output_items:
            if item.get("type") == "message":
                content = item.get("content", [])
                for content_item in content:
                    if content_item.get("type") == "output_text":
                        text_content += content_item.get("text", "")

        # Extract usage
        usage = response.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        # Calculate cost
        model_pricing = self.pricing.get(model, {"input": 0, "output": 0})
        cost = (input_tokens * model_pricing["input"]) + (output_tokens * model_pricing["output"])

        return {
            "text": text_content,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
            "cost": cost,
            "model": model,
            "response_id": response.get("id"),
        }

    async def create_embedding(self, text: str, model: str = None) -> list[float]:
        """
        Create embedding for text using OpenAI Embeddings API

        Args:
            text: Text to embed
            model: Embedding model (defaults to text-embedding-3-small)

        Returns:
            List of floats representing the embedding vector
        """
        if model is None:
            model = settings.OPENAI_EMBEDDING_MODEL

        try:
            response = await self.client.embeddings.create(input=text, model=model)

            # Track cost
            input_tokens = response.usage.input_tokens
            model_pricing = self.pricing.get(model, {"input": 0, "output": 0})
            cost = input_tokens * model_pricing["input"]
            self.total_cost_today += cost

            logger.debug(
                "embedding_created",
                model=model,
                input_tokens=input_tokens,
                cost=cost,
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error("embedding_error", error=str(e))
            raise

    def calculate_cost(
        self, input_tokens: int, output_tokens: int, model: str
    ) -> float:
        """Calculate cost for a given token usage"""
        model_pricing = self.pricing.get(model, {"input": 0, "output": 0})
        return (input_tokens * model_pricing["input"]) + (
            output_tokens * model_pricing["output"]
        )

    def get_daily_cost(self) -> float:
        """Get total cost accumulated today"""
        return self.total_cost_today

    def reset_daily_cost(self):
        """Reset daily cost counter (call at midnight)"""
        self.total_cost_today = 0.0


# Global client instance
openai_client = OpenAIClient()
