"""
LLM Evaluation Framework for BYU Pathway Chatbot

This module provides tools for evaluating and comparing different LLM models
for the BYU Pathway Missionary Chatbot, including:
- GPT-4o-mini (current production model)
- GPT-5-mini
- GPT-5-nano
- GPT-5.1

Grading is performed using GPT-5.1 with reasoning_effort=high via the Responses API.
"""

from evaluate.compare import ModelComparator
from evaluate.config import EvaluationConfig
from evaluate.grader import Grader
from evaluate.metrics import MetricsCalculator
from evaluate.model_runner import ModelRunner

__all__ = [
    "EvaluationConfig",
    "Grader",
    "ModelRunner",
    "MetricsCalculator",
    "ModelComparator",
]
