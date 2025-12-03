"""
Model Runner module for LLM Evaluation Framework

Runs questions through different LLM models using the appropriate API:
- Chat Completions API for GPT-4 models
- Responses API for GPT-5 models

Tracks latency, token usage, and cost for each response.
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

from evaluate.config import (
    CONTEXT_PROMPT,
    MODELS_TO_EVALUATE,
    SYSTEM_CITATION_PROMPT,
    ModelConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class ModelResponse:
    """Response from a model including metadata."""

    model_name: str
    model_id: str
    response_text: str

    # Performance metrics
    latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float

    # Error tracking
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "model_name": self.model_name,
            "model_id": self.model_id,
            "response_text": self.response_text,
            "latency_ms": self.latency_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost": self.cost,
            "error": self.error,
        }


class ModelRunner:
    """
    Runs questions through different LLM models.

    Handles both Chat Completions API (GPT-4) and Responses API (GPT-5).
    """

    def __init__(
        self,
        models: list[ModelConfig] = None,
        max_retries: int = 3,
        retry_delay: float = 5.0,
    ):
        self.client = OpenAI()
        self.models = models or MODELS_TO_EVALUATE
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def run_question(
        self,
        question: str,
        retrieved_docs: str,
        model_config: ModelConfig,
    ) -> ModelResponse:
        """
        Run a single question through a specific model.

        Args:
            question: The user's question
            retrieved_docs: The context documents to provide
            model_config: Configuration for the model to use

        Returns:
            ModelResponse with the response and metadata
        """
        # Build the prompt with context
        context_prompt = CONTEXT_PROMPT.format(context_str=retrieved_docs)
        full_user_message = f"{context_prompt}\n\nQuestion: {question}"

        for attempt in range(self.max_retries):
            try:
                start_time = time.time()

                if model_config.api_type == "chat_completions":
                    response = self._call_chat_completions(model_config, full_user_message)
                else:  # responses API
                    response = self._call_responses_api(model_config, full_user_message)

                response.latency_ms = (time.time() - start_time) * 1000
                return response

            except Exception as e:
                logger.warning(f"Model {model_config.name} error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return self._error_response(model_config, f"API error: {e}")

        return self._error_response(model_config, "Max retries exceeded")

    def run_question_all_models(
        self,
        question: str,
        retrieved_docs: str,
    ) -> dict[str, ModelResponse]:
        """
        Run a question through all configured models.

        Args:
            question: The user's question
            retrieved_docs: The context documents to provide

        Returns:
            Dictionary mapping model names to their responses
        """
        responses = {}
        for model_config in self.models:
            logger.info(f"Running question through {model_config.name}...")
            response = self.run_question(question, retrieved_docs, model_config)
            responses[model_config.name] = response
        return responses

    def _call_chat_completions(
        self,
        model_config: ModelConfig,
        user_message: str,
    ) -> ModelResponse:
        """Call the Chat Completions API (for GPT-4 models)."""
        response = self.client.chat.completions.create(
            model=model_config.model_id,
            messages=[
                {"role": "system", "content": SYSTEM_CITATION_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=model_config.temperature or 0.7,
        )

        # Extract response
        response_text = response.choices[0].message.content

        # Extract token usage
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens

        # Calculate cost
        cost = (input_tokens / 1_000_000) * model_config.input_price_per_1m + (
            output_tokens / 1_000_000
        ) * model_config.output_price_per_1m

        return ModelResponse(
            model_name=model_config.name,
            model_id=model_config.model_id,
            response_text=response_text,
            latency_ms=0,  # Will be set by caller
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=cost,
        )

    def _call_responses_api(
        self,
        model_config: ModelConfig,
        user_message: str,
    ) -> ModelResponse:
        """Call the Responses API (for GPT-5 models)."""
        # Combine system prompt and user message for Responses API
        full_prompt = f"{SYSTEM_CITATION_PROMPT}\n\n{user_message}"

        response = self.client.responses.create(
            model=model_config.model_id,
            input=full_prompt,
            reasoning={"effort": model_config.reasoning_effort or "low"},
        )

        # Extract response
        response_text = response.output_text

        # Extract token usage
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = input_tokens + output_tokens

        # Calculate cost
        cost = (input_tokens / 1_000_000) * model_config.input_price_per_1m + (
            output_tokens / 1_000_000
        ) * model_config.output_price_per_1m

        return ModelResponse(
            model_name=model_config.name,
            model_id=model_config.model_id,
            response_text=response_text,
            latency_ms=0,  # Will be set by caller
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=cost,
        )

    def _error_response(
        self,
        model_config: ModelConfig,
        error: str,
    ) -> ModelResponse:
        """Create a ModelResponse indicating an error."""
        return ModelResponse(
            model_name=model_config.name,
            model_id=model_config.model_id,
            response_text="",
            latency_ms=0,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost=0,
            error=error,
        )
