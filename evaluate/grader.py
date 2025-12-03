"""
Grader module for LLM Evaluation Framework

Uses GPT-5.1 with reasoning_effort=high via the Responses API to grade
AI responses on 5 dimensions:
- on_topic: Does the response address the question?
- grounded: Is the response based on provided context?
- no_contradiction: Does the response avoid contradicting sources?
- understandability: Is the response clear and well-organized?
- overall: Overall quality rating
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

from evaluate.config import GRADER_MODEL, GRADING_PROMPT, ModelConfig

logger = logging.getLogger(__name__)


@dataclass
class GradingResult:
    """Result of grading a single Q/A pair."""

    on_topic_score: int
    on_topic_explanation: str
    grounded_score: int
    grounded_explanation: str
    no_contradiction_score: int
    no_contradiction_explanation: str
    understandability_score: int
    understandability_explanation: str
    overall_score: int
    overall_explanation: str

    # Grading metadata
    grading_latency_ms: float
    grading_input_tokens: int
    grading_output_tokens: int
    grading_cost: float

    # Raw response for debugging
    raw_response: Optional[str] = None
    error: Optional[str] = None

    @property
    def average_score(self) -> float:
        """Calculate average score across all dimensions."""
        return (
            self.on_topic_score
            + self.grounded_score
            + self.no_contradiction_score
            + self.understandability_score
            + self.overall_score
        ) / 5.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "on_topic": {
                "score": self.on_topic_score,
                "explanation": self.on_topic_explanation,
            },
            "grounded": {
                "score": self.grounded_score,
                "explanation": self.grounded_explanation,
            },
            "no_contradiction": {
                "score": self.no_contradiction_score,
                "explanation": self.no_contradiction_explanation,
            },
            "understandability": {
                "score": self.understandability_score,
                "explanation": self.understandability_explanation,
            },
            "overall": {
                "score": self.overall_score,
                "explanation": self.overall_explanation,
            },
            "average_score": self.average_score,
            "grading_latency_ms": self.grading_latency_ms,
            "grading_input_tokens": self.grading_input_tokens,
            "grading_output_tokens": self.grading_output_tokens,
            "grading_cost": self.grading_cost,
            "error": self.error,
        }


class Grader:
    """
    Grades AI responses using GPT-5.1 with reasoning_effort=high.

    Uses the Responses API for GPT-5 models.
    """

    def __init__(
        self,
        grader_config: ModelConfig = GRADER_MODEL,
        max_retries: int = 3,
        retry_delay: float = 5.0,
    ):
        self.client = OpenAI()
        self.grader_config = grader_config
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def grade(
        self,
        question: str,
        response: str,
        retrieved_docs: str,
    ) -> GradingResult:
        """
        Grade a single Q/A pair.

        Args:
            question: The user's question
            response: The AI's response to grade
            retrieved_docs: The context documents provided to the AI

        Returns:
            GradingResult with scores for each dimension
        """
        # Format the grading prompt
        prompt = GRADING_PROMPT.format(
            retrieved_docs=retrieved_docs,
            question=question,
            response=response,
        )

        # Call the grading model
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()

                # Use Responses API for GPT-5 models
                api_response = self.client.responses.create(
                    model=self.grader_config.model_id,
                    input=prompt,
                    reasoning={"effort": self.grader_config.reasoning_effort},
                )

                latency_ms = (time.time() - start_time) * 1000

                # Extract response text
                response_text = api_response.output_text

                # Extract token usage
                input_tokens = api_response.usage.input_tokens
                output_tokens = api_response.usage.output_tokens

                # Calculate cost
                cost = (input_tokens / 1_000_000) * self.grader_config.input_price_per_1m + (
                    output_tokens / 1_000_000
                ) * self.grader_config.output_price_per_1m

                # Parse JSON response
                grades = self._parse_grades(response_text)

                return GradingResult(
                    on_topic_score=grades["on_topic"]["score"],
                    on_topic_explanation=grades["on_topic"]["explanation"],
                    grounded_score=grades["grounded"]["score"],
                    grounded_explanation=grades["grounded"]["explanation"],
                    no_contradiction_score=grades["no_contradiction"]["score"],
                    no_contradiction_explanation=grades["no_contradiction"]["explanation"],
                    understandability_score=grades["understandability"]["score"],
                    understandability_explanation=grades["understandability"]["explanation"],
                    overall_score=grades["overall"]["score"],
                    overall_explanation=grades["overall"]["explanation"],
                    grading_latency_ms=latency_ms,
                    grading_input_tokens=input_tokens,
                    grading_output_tokens=output_tokens,
                    grading_cost=cost,
                    raw_response=response_text,
                )

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse grading response (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return self._error_result(
                        f"JSON parse error: {e}", response_text if "response_text" in locals() else None
                    )

            except Exception as e:
                logger.warning(f"Grading API error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return self._error_result(f"API error: {e}")

        return self._error_result("Max retries exceeded")

    def _parse_grades(self, response_text: str) -> dict:
        """Parse the JSON grades from the response text."""
        # Try to find JSON in the response
        text = response_text.strip()

        # If response starts with ``` (markdown code block), extract JSON
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (``` markers)
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```") and not in_json:
                    in_json = True
                    continue
                elif line.startswith("```") and in_json:
                    break
                elif in_json:
                    json_lines.append(line)
            text = "\n".join(json_lines)

        # Parse JSON
        return json.loads(text)

    def _error_result(self, error: str, raw_response: Optional[str] = None) -> GradingResult:
        """Create a GradingResult indicating an error."""
        return GradingResult(
            on_topic_score=0,
            on_topic_explanation="Error during grading",
            grounded_score=0,
            grounded_explanation="Error during grading",
            no_contradiction_score=0,
            no_contradiction_explanation="Error during grading",
            understandability_score=0,
            understandability_explanation="Error during grading",
            overall_score=0,
            overall_explanation="Error during grading",
            grading_latency_ms=0,
            grading_input_tokens=0,
            grading_output_tokens=0,
            grading_cost=0,
            raw_response=raw_response,
            error=error,
        )
