#!/usr/bin/env python3
"""
LLM Model Evaluation Script for BYU Pathway Chatbot

This script evaluates multiple LLM models by:
1. Loading Q/A samples from Langfuse traces
2. Running each question through all configured models
3. Grading responses using GPT-5.1 with reasoning_effort=high
4. Generating comparison reports (markdown, CSV, JSON)

Usage:
    python evaluate_models.py [--samples N] [--seed S] [--csv PATH]

Examples:
    # Run with default settings (100 samples, seed=42)
    python evaluate_models.py

    # Run with 50 samples and random seed
    python evaluate_models.py --samples 50 --seed 12345

    # Use sequential selection (no randomization)
    python evaluate_models.py --samples 100 --seed 0

    # Use a different CSV file
    python evaluate_models.py --csv /path/to/traces.csv
"""

import argparse
import csv
import json
import logging
import random
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from evaluate.compare import ModelComparator
from evaluate.config import EvaluationConfig
from evaluate.grader import Grader, GradingResult
from evaluate.metrics import MetricsCalculator, ModelMetrics
from evaluate.model_runner import ModelResponse, ModelRunner

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_samples(csv_path: Path, num_samples: int, random_seed: int) -> list[dict]:
    """
    Load Q/A samples from Langfuse CSV.

    Args:
        csv_path: Path to the Langfuse traces CSV
        num_samples: Number of samples to select
        random_seed: Random seed (0 = sequential, non-zero = random)

    Returns:
        List of sample dictionaries with 'input', 'output', 'metadata' keys
    """
    logger.info(f"Loading samples from {csv_path}")

    samples = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip rows without questions or answers
            if not row.get("input") or not row.get("output"):
                continue

            # Parse metadata if present
            metadata = {}
            if row.get("metadata"):
                try:
                    metadata = json.loads(row["metadata"].replace("'", '"'))
                except (json.JSONDecodeError, ValueError):
                    # Try to extract retrieved_docs from the raw string
                    if "retrieved_docs" in row.get("metadata", ""):
                        metadata = {"retrieved_docs": row["metadata"]}

            samples.append({
                "input": row["input"],
                "output": row["output"],
                "metadata": metadata,
                "trace_id": row.get("id", ""),
                "timestamp": row.get("timestamp", ""),
                "original_latency": float(row.get("latency", 0) or 0),
                "original_cost": float(row.get("total_cost", 0) or 0),
            })

    logger.info(f"Loaded {len(samples)} total samples from CSV")

    # Select samples
    if random_seed == 0:
        # Sequential selection
        selected = samples[:num_samples]
        logger.info(f"Selected first {len(selected)} samples (sequential)")
    else:
        # Random selection with seed
        random.seed(random_seed)
        selected = random.sample(samples, min(num_samples, len(samples)))
        logger.info(f"Selected {len(selected)} random samples (seed={random_seed})")

    return selected


def extract_retrieved_docs(metadata: dict) -> str:
    """Extract retrieved documents from metadata."""
    # Try to get from metadata dict
    if isinstance(metadata, dict):
        if "retrieved_docs" in metadata:
            return metadata["retrieved_docs"]

    # If metadata is a string, return as-is
    if isinstance(metadata, str):
        return metadata

    return ""


def run_evaluation(config: EvaluationConfig) -> None:
    """
    Run the full evaluation pipeline.

    Args:
        config: Evaluation configuration
    """
    logger.info("=" * 60)
    logger.info("Starting LLM Model Evaluation")
    logger.info("=" * 60)
    logger.info(f"Models to evaluate: {[m.name for m in config.models_to_evaluate]}")
    logger.info(f"Grader: {config.grader_model.model_id} (reasoning_effort={config.grader_model.reasoning_effort})")
    logger.info(f"Samples: {config.num_samples}")
    logger.info(f"Random seed: {config.random_seed}")
    logger.info(f"Output directory: {config.output_dir}")
    logger.info("")

    # Load samples
    samples = load_samples(
        config.langfuse_csv_path,
        config.num_samples,
        config.random_seed,
    )

    if not samples:
        logger.error("No samples loaded. Check CSV path and format.")
        return

    # Initialize components
    model_runner = ModelRunner(
        models=config.models_to_evaluate,
        max_retries=config.max_retries,
        retry_delay=config.retry_delay,
    )
    grader = Grader(
        grader_config=config.grader_model,
        max_retries=config.max_retries,
        retry_delay=config.retry_delay,
    )

    # Store results: model_name -> list of (sample, response, grade) tuples
    results: dict[str, list[tuple[dict, ModelResponse, GradingResult]]] = {
        m.name: [] for m in config.models_to_evaluate
    }

    # Process each sample
    total_samples = len(samples)
    for i, sample in enumerate(samples, 1):
        logger.info(f"\n{'=' * 40}")
        logger.info(f"Sample {i}/{total_samples}")
        logger.info(f"Question: {sample['input'][:100]}...")

        # Extract retrieved documents
        retrieved_docs = extract_retrieved_docs(sample.get("metadata", {}))

        if not retrieved_docs:
            logger.warning(f"No retrieved docs for sample {i}, using empty context")
            retrieved_docs = "No context documents available."

        # Run through each model
        for model_config in config.models_to_evaluate:
            logger.info(f"  Running {model_config.name}...")

            # Get model response
            response = model_runner.run_question(
                question=sample["input"],
                retrieved_docs=retrieved_docs,
                model_config=model_config,
            )

            if response.error:
                logger.warning(f"  Error from {model_config.name}: {response.error}")
            else:
                logger.info(f"  Response received ({response.latency_ms:.0f}ms, {response.total_tokens} tokens)")

            # Grade the response
            logger.info("  Grading response...")
            grade = grader.grade(
                question=sample["input"],
                response=response.response_text,
                retrieved_docs=retrieved_docs,
            )

            if grade.error:
                logger.warning(f"  Grading error: {grade.error}")
            else:
                logger.info(
                    f"  Grades: on_topic={grade.on_topic_score}, grounded={grade.grounded_score}, "
                    f"no_contradiction={grade.no_contradiction_score}, "
                    f"understandability={grade.understandability_score}, overall={grade.overall_score}"
                )

            # Store result
            results[model_config.name].append((sample, response, grade))

            # Rate limiting
            time.sleep(config.delay_between_requests)

    # Calculate metrics
    logger.info("\n" + "=" * 60)
    logger.info("Calculating metrics...")

    metrics: dict[str, ModelMetrics] = {}
    for model_config in config.models_to_evaluate:
        model_results = results[model_config.name]
        responses = [r for _, r, _ in model_results]
        grades = [g for _, _, g in model_results]

        model_metrics = MetricsCalculator.calculate_model_metrics(
            model_name=model_config.name,
            model_id=model_config.model_id,
            responses=responses,
            grades=grades,
        )
        metrics[model_config.name] = model_metrics

    # Generate reports
    logger.info("Generating reports...")
    comparator = ModelComparator(config)
    output_files = comparator.generate_reports(results, metrics)

    # Print summary
    comparator.print_summary(metrics)

    # Print output file paths
    logger.info("\nOutput files:")
    for report_type, path in output_files.items():
        logger.info(f"  {report_type}: {path}")

    logger.info("\n" + "=" * 60)
    logger.info("Evaluation complete!")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate LLM models for BYU Pathway Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--samples",
        "-n",
        type=int,
        default=100,
        help="Number of samples to evaluate (default: 100)",
    )
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=42,
        help="Random seed for sample selection (0 = sequential, default: 42)",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Path to Langfuse traces CSV (default: /home/chris/byu-pathway/langfuse_traces_11_26_25.csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output directory (default: /home/chris/byu-pathway/pathway-indexer/data/evaluations)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between API requests in seconds (default: 1.0)",
    )

    args = parser.parse_args()

    # Create configuration
    config = EvaluationConfig(
        num_samples=args.samples,
        random_seed=args.seed,
        delay_between_requests=args.delay,
    )

    if args.csv:
        config.langfuse_csv_path = Path(args.csv)

    if args.output:
        config.output_dir = Path(args.output)
        config.output_dir.mkdir(parents=True, exist_ok=True)

    # Run evaluation
    try:
        run_evaluation(config)
    except KeyboardInterrupt:
        logger.info("\nEvaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Evaluation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
