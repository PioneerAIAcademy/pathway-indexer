"""
Model Comparator module for LLM Evaluation Framework

Compares models and generates:
- Markdown summary reports
- CSV files with detailed results
- Explanatory text for interpretation
"""

import csv
import json
from datetime import datetime
from pathlib import Path

from evaluate.config import EvaluationConfig
from evaluate.grader import GradingResult
from evaluate.metrics import ModelMetrics
from evaluate.model_runner import ModelResponse


class ModelComparator:
    """
    Compares models and generates reports.

    Outputs:
    - Markdown summary with tables and explanations
    - CSV with detailed per-sample results
    - JSON with raw metrics
    """

    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def generate_reports(
        self,
        results: dict[str, list[tuple[dict, ModelResponse, GradingResult]]],
        metrics: dict[str, ModelMetrics],
    ) -> dict[str, Path]:
        """
        Generate all reports from evaluation results.

        Args:
            results: Dict of model_name -> list of (sample, response, grade) tuples
            metrics: Dict of model_name -> ModelMetrics

        Returns:
            Dict of report_type -> file path
        """
        output_files = {}

        # Generate markdown report
        md_path = self._generate_markdown_report(metrics)
        output_files["markdown"] = md_path

        # Generate CSV with detailed results
        csv_path = self._generate_csv_report(results)
        output_files["csv"] = csv_path

        # Generate JSON with raw metrics
        json_path = self._generate_json_report(metrics)
        output_files["json"] = json_path

        return output_files

    def _generate_markdown_report(self, metrics: dict[str, ModelMetrics]) -> Path:
        """Generate the main markdown summary report."""
        output_path = self.config.output_dir / f"evaluation_report_{self.timestamp}.md"

        lines = []

        # Header
        lines.append("# LLM Model Evaluation Report")
        lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Samples Evaluated:** {self.config.num_samples}")
        lines.append(f"**Random Seed:** {self.config.random_seed}")
        lines.append(
            f"**Grader Model:** {self.config.grader_model.model_id} (reasoning_effort={self.config.grader_model.reasoning_effort})"
        )
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append("This report compares multiple LLM models for the BYU Pathway Missionary Chatbot. ")
        lines.append("Each model was evaluated on the same set of questions using a consistent grading rubric.")
        lines.append("")

        # Find best model
        best_model = max(metrics.values(), key=lambda m: m.average_score)
        cheapest_model = min(metrics.values(), key=lambda m: m.cost_stats.mean_cost_per_query)
        fastest_model = min(
            metrics.values(), key=lambda m: m.latency_stats.mean_ms if m.latency_stats.mean_ms > 0 else float("inf")
        )

        lines.append(f"- **Highest Quality:** {best_model.model_name} (avg score: {best_model.average_score:.2f}/5.0)")
        lines.append(
            f"- **Lowest Cost:** {cheapest_model.model_name} (${cheapest_model.cost_stats.cost_per_1000_queries:.4f} per 1000 queries)"
        )
        lines.append(
            f"- **Fastest Response:** {fastest_model.model_name} (mean: {fastest_model.latency_stats.mean_ms:.0f}ms)"
        )
        lines.append("")

        # Quality Scores Table
        lines.append("## Quality Scores")
        lines.append("")
        lines.append("Scores are on a 1-5 scale (5 = excellent, 1 = poor). Higher is better.")
        lines.append("")

        # Table header
        lines.append("| Model | On-Topic | Grounded | No Contradiction | Understandability | Overall | **Average** |")
        lines.append("|-------|----------|----------|------------------|-------------------|---------|-------------|")

        # Sort by average score descending
        sorted_metrics = sorted(metrics.values(), key=lambda m: m.average_score, reverse=True)

        for m in sorted_metrics:
            lines.append(
                f"| {m.model_name} | "
                f"{m.on_topic_stats.mean_score:.2f} | "
                f"{m.grounded_stats.mean_score:.2f} | "
                f"{m.no_contradiction_stats.mean_score:.2f} | "
                f"{m.understandability_stats.mean_score:.2f} | "
                f"{m.overall_stats.mean_score:.2f} | "
                f"**{m.average_score:.2f}** |"
            )

        lines.append("")

        # Dimension Explanations
        lines.append("### Dimension Definitions")
        lines.append("")
        lines.append("- **On-Topic:** Does the response directly address the user's question?")
        lines.append("- **Grounded:** Is the response based on the provided context documents with proper citations?")
        lines.append("- **No Contradiction:** Does the response avoid contradicting the source material?")
        lines.append("- **Understandability:** Is the response clear, well-organized, and easy to understand?")
        lines.append("- **Overall:** Holistic assessment of response quality for helping BYU Pathway missionaries")
        lines.append("")

        # Performance Metrics Table
        lines.append("## Performance Metrics")
        lines.append("")
        lines.append("| Model | Mean Latency | P95 Latency | Mean Tokens | Mean Cost/Query | Cost/1000 Queries |")
        lines.append("|-------|--------------|-------------|-------------|-----------------|-------------------|")

        for m in sorted_metrics:
            lines.append(
                f"| {m.model_name} | "
                f"{m.latency_stats.mean_ms:.0f}ms | "
                f"{m.latency_stats.p95_ms:.0f}ms | "
                f"{m.token_stats.mean_total_tokens:.0f} | "
                f"${m.cost_stats.mean_cost_per_query:.6f} | "
                f"${m.cost_stats.cost_per_1000_queries:.4f} |"
            )

        lines.append("")

        # Cost Analysis
        lines.append("## Cost Analysis")
        lines.append("")

        # Calculate monthly cost estimates
        queries_per_month = [1000, 10000, 100000]
        lines.append("### Estimated Monthly Costs")
        lines.append("")

        header = "| Model |"
        for q in queries_per_month:
            header += f" {q:,} queries |"
        lines.append(header)

        divider = "|-------|"
        for _ in queries_per_month:
            divider += "---------------|"
        lines.append(divider)

        for m in sorted_metrics:
            row = f"| {m.model_name} |"
            for q in queries_per_month:
                monthly_cost = m.cost_stats.mean_cost_per_query * q
                row += f" ${monthly_cost:.2f} |"
            lines.append(row)

        lines.append("")

        # Detailed Model Analysis
        lines.append("## Detailed Model Analysis")
        lines.append("")

        for m in sorted_metrics:
            lines.append(f"### {m.model_name}")
            lines.append("")
            lines.append(f"**Model ID:** `{m.model_id}`")
            lines.append(f"**Samples:** {m.num_samples} ({m.num_errors} errors)")
            lines.append("")

            # Score distribution
            lines.append("**Score Distribution (Overall):**")
            if m.overall_stats.score_distribution:
                for score in sorted(m.overall_stats.score_distribution.keys(), reverse=True):
                    count = m.overall_stats.score_distribution[score]
                    pct = (count / m.num_samples) * 100
                    bars = "█" * int(pct / 5)
                    lines.append(f"- Score {score}: {count} ({pct:.1f}%) {bars}")
            lines.append("")

            # Performance summary
            lines.append("**Performance:**")
            lines.append(f"- Latency: {m.latency_stats.mean_ms:.0f}ms mean, {m.latency_stats.p95_ms:.0f}ms p95")
            lines.append(f"- Tokens: {m.token_stats.mean_total_tokens:.0f} mean per query")
            lines.append(f"- Cost: ${m.cost_stats.cost_per_1000_queries:.4f} per 1000 queries")
            lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        lines.append("")
        lines.append("Based on the evaluation results:")
        lines.append("")

        # Generate recommendations based on results
        quality_diff = best_model.average_score - min(m.average_score for m in metrics.values())

        if quality_diff < 0.3:
            lines.append("1. **Quality is similar across models.** Consider cost and latency as primary factors.")
        else:
            lines.append(
                f"1. **{best_model.model_name} shows notably higher quality.** Consider if the quality improvement justifies additional cost."
            )

        cost_ratio = best_model.cost_stats.mean_cost_per_query / cheapest_model.cost_stats.mean_cost_per_query
        if cost_ratio > 2:
            lines.append(
                f"2. **Cost difference is significant.** {best_model.model_name} costs {cost_ratio:.1f}x more than {cheapest_model.model_name}."
            )

        lines.append(
            "3. **Review low-scoring samples** in the detailed CSV to identify specific areas for improvement."
        )
        lines.append("")

        # Methodology
        lines.append("## Methodology")
        lines.append("")
        lines.append("### Evaluation Process")
        lines.append("1. Sample questions were selected from Langfuse traces")
        lines.append("2. Each question was run through all models with the same retrieved context")
        lines.append("3. Responses were graded by GPT-5.1 (reasoning_effort=high) on 5 dimensions")
        lines.append("4. Metrics were aggregated and compared")
        lines.append("")
        lines.append("### Grading Model")
        lines.append(f"- **Model:** {self.config.grader_model.model_id}")
        lines.append(f"- **Reasoning Effort:** {self.config.grader_model.reasoning_effort}")
        lines.append("- **API:** OpenAI Responses API")
        lines.append("")

        # Write file
        with open(output_path, "w") as f:
            f.write("\n".join(lines))

        return output_path

    def _generate_csv_report(
        self,
        results: dict[str, list[tuple[dict, ModelResponse, GradingResult]]],
    ) -> Path:
        """Generate CSV with detailed per-sample results."""
        output_path = self.config.output_dir / f"evaluation_details_{self.timestamp}.csv"

        # Prepare rows
        rows = []

        for model_name, samples in results.items():
            for sample, response, grade in samples:
                row = {
                    "model_name": model_name,
                    "model_id": response.model_id,
                    "question": sample.get("input", ""),
                    "original_answer": sample.get("output", ""),
                    "model_response": response.response_text[:1000]
                    if response.response_text
                    else "",  # Truncate for CSV
                    "on_topic_score": grade.on_topic_score,
                    "on_topic_explanation": grade.on_topic_explanation,
                    "grounded_score": grade.grounded_score,
                    "grounded_explanation": grade.grounded_explanation,
                    "no_contradiction_score": grade.no_contradiction_score,
                    "no_contradiction_explanation": grade.no_contradiction_explanation,
                    "understandability_score": grade.understandability_score,
                    "understandability_explanation": grade.understandability_explanation,
                    "overall_score": grade.overall_score,
                    "overall_explanation": grade.overall_explanation,
                    "average_score": grade.average_score,
                    "latency_ms": response.latency_ms,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost": response.cost,
                    "response_error": response.error,
                    "grading_error": grade.error,
                }
                rows.append(row)

        # Write CSV
        if rows:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        return output_path

    def _generate_json_report(self, metrics: dict[str, ModelMetrics]) -> Path:
        """Generate JSON with raw metrics."""
        output_path = self.config.output_dir / f"evaluation_metrics_{self.timestamp}.json"

        data = {
            "timestamp": self.timestamp,
            "config": {
                "num_samples": self.config.num_samples,
                "random_seed": self.config.random_seed,
                "grader_model": self.config.grader_model.model_id,
                "grader_reasoning_effort": self.config.grader_model.reasoning_effort,
            },
            "models": {name: m.to_dict() for name, m in metrics.items()},
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        return output_path

    def print_summary(self, metrics: dict[str, ModelMetrics]) -> None:
        """Print a quick summary to the terminal."""
        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)

        # Sort by average score
        sorted_metrics = sorted(metrics.values(), key=lambda m: m.average_score, reverse=True)

        print("\nQuality Ranking (by average score):")
        print("-" * 40)

        for i, m in enumerate(sorted_metrics, 1):
            print(f"{i}. {m.model_name}")
            print(f"   Score: {m.average_score:.2f}/5.0")
            print(f"   Cost: ${m.cost_stats.cost_per_1000_queries:.4f}/1000 queries")
            print(f"   Latency: {m.latency_stats.mean_ms:.0f}ms mean")
            print()

        print("=" * 60)
