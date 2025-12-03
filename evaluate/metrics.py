"""
Metrics module for LLM Evaluation Framework

Calculates aggregate metrics for model evaluation:
- Average scores for each grading dimension
- Latency statistics (mean, median, p95, p99)
- Token usage statistics
- Cost analysis
"""

import statistics
from dataclasses import dataclass

from evaluate.grader import GradingResult
from evaluate.model_runner import ModelResponse


@dataclass
class DimensionStats:
    """Statistics for a single grading dimension."""

    dimension: str
    mean_score: float
    median_score: float
    min_score: int
    max_score: int
    std_dev: float
    score_distribution: dict[int, int]  # score -> count

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "mean_score": round(self.mean_score, 2),
            "median_score": self.median_score,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "std_dev": round(self.std_dev, 2),
            "score_distribution": self.score_distribution,
        }


@dataclass
class LatencyStats:
    """Latency statistics in milliseconds."""

    mean_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float

    def to_dict(self) -> dict:
        return {
            "mean_ms": round(self.mean_ms, 2),
            "median_ms": round(self.median_ms, 2),
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
            "std_dev_ms": round(self.std_dev_ms, 2),
        }


@dataclass
class TokenStats:
    """Token usage statistics."""

    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    mean_input_tokens: float
    mean_output_tokens: float
    mean_total_tokens: float

    def to_dict(self) -> dict:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "mean_input_tokens": round(self.mean_input_tokens, 2),
            "mean_output_tokens": round(self.mean_output_tokens, 2),
            "mean_total_tokens": round(self.mean_total_tokens, 2),
        }


@dataclass
class CostStats:
    """Cost statistics."""

    total_cost: float
    mean_cost_per_query: float
    cost_per_1000_queries: float

    def to_dict(self) -> dict:
        return {
            "total_cost": round(self.total_cost, 6),
            "mean_cost_per_query": round(self.mean_cost_per_query, 6),
            "cost_per_1000_queries": round(self.cost_per_1000_queries, 4),
        }


@dataclass
class ModelMetrics:
    """Complete metrics for a single model."""

    model_name: str
    model_id: str
    num_samples: int
    num_errors: int

    # Quality metrics
    on_topic_stats: DimensionStats
    grounded_stats: DimensionStats
    no_contradiction_stats: DimensionStats
    understandability_stats: DimensionStats
    overall_stats: DimensionStats
    average_score: float

    # Performance metrics
    latency_stats: LatencyStats
    token_stats: TokenStats
    cost_stats: CostStats

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "model_id": self.model_id,
            "num_samples": self.num_samples,
            "num_errors": self.num_errors,
            "quality_metrics": {
                "on_topic": self.on_topic_stats.to_dict(),
                "grounded": self.grounded_stats.to_dict(),
                "no_contradiction": self.no_contradiction_stats.to_dict(),
                "understandability": self.understandability_stats.to_dict(),
                "overall": self.overall_stats.to_dict(),
                "average_score": round(self.average_score, 2),
            },
            "latency": self.latency_stats.to_dict(),
            "tokens": self.token_stats.to_dict(),
            "cost": self.cost_stats.to_dict(),
        }


class MetricsCalculator:
    """Calculates aggregate metrics from evaluation results."""

    @staticmethod
    def calculate_dimension_stats(
        scores: list[int],
        dimension: str,
    ) -> DimensionStats:
        """Calculate statistics for a single grading dimension."""
        if not scores or all(s == 0 for s in scores):
            return DimensionStats(
                dimension=dimension,
                mean_score=0,
                median_score=0,
                min_score=0,
                max_score=0,
                std_dev=0,
                score_distribution={},
            )

        # Filter out error scores (0)
        valid_scores = [s for s in scores if s > 0]

        if not valid_scores:
            return DimensionStats(
                dimension=dimension,
                mean_score=0,
                median_score=0,
                min_score=0,
                max_score=0,
                std_dev=0,
                score_distribution={},
            )

        # Calculate distribution
        distribution = {}
        for score in valid_scores:
            distribution[score] = distribution.get(score, 0) + 1

        return DimensionStats(
            dimension=dimension,
            mean_score=statistics.mean(valid_scores),
            median_score=statistics.median(valid_scores),
            min_score=min(valid_scores),
            max_score=max(valid_scores),
            std_dev=statistics.stdev(valid_scores) if len(valid_scores) > 1 else 0,
            score_distribution=distribution,
        )

    @staticmethod
    def calculate_latency_stats(latencies_ms: list[float]) -> LatencyStats:
        """Calculate latency statistics."""
        if not latencies_ms:
            return LatencyStats(
                mean_ms=0,
                median_ms=0,
                min_ms=0,
                max_ms=0,
                p95_ms=0,
                p99_ms=0,
                std_dev_ms=0,
            )

        # Filter out zero latencies (errors)
        valid_latencies = [l for l in latencies_ms if l > 0]

        if not valid_latencies:
            return LatencyStats(
                mean_ms=0,
                median_ms=0,
                min_ms=0,
                max_ms=0,
                p95_ms=0,
                p99_ms=0,
                std_dev_ms=0,
            )

        sorted_latencies = sorted(valid_latencies)
        n = len(sorted_latencies)

        # Calculate percentiles
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)

        return LatencyStats(
            mean_ms=statistics.mean(valid_latencies),
            median_ms=statistics.median(valid_latencies),
            min_ms=min(valid_latencies),
            max_ms=max(valid_latencies),
            p95_ms=sorted_latencies[min(p95_idx, n - 1)],
            p99_ms=sorted_latencies[min(p99_idx, n - 1)],
            std_dev_ms=statistics.stdev(valid_latencies) if len(valid_latencies) > 1 else 0,
        )

    @staticmethod
    def calculate_token_stats(
        input_tokens: list[int],
        output_tokens: list[int],
    ) -> TokenStats:
        """Calculate token usage statistics."""
        total_input = sum(input_tokens)
        total_output = sum(output_tokens)
        n = len(input_tokens) if input_tokens else 1

        return TokenStats(
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_input + total_output,
            mean_input_tokens=total_input / n if n > 0 else 0,
            mean_output_tokens=total_output / n if n > 0 else 0,
            mean_total_tokens=(total_input + total_output) / n if n > 0 else 0,
        )

    @staticmethod
    def calculate_cost_stats(costs: list[float]) -> CostStats:
        """Calculate cost statistics."""
        total = sum(costs)
        n = len(costs) if costs else 1
        mean = total / n if n > 0 else 0

        return CostStats(
            total_cost=total,
            mean_cost_per_query=mean,
            cost_per_1000_queries=mean * 1000,
        )

    @classmethod
    def calculate_model_metrics(
        cls,
        model_name: str,
        model_id: str,
        responses: list[ModelResponse],
        grades: list[GradingResult],
    ) -> ModelMetrics:
        """
        Calculate complete metrics for a single model.

        Args:
            model_name: Display name of the model
            model_id: Model ID
            responses: List of model responses
            grades: List of grading results for those responses

        Returns:
            ModelMetrics with all aggregate statistics
        """
        num_samples = len(responses)
        num_errors = sum(1 for r in responses if r.error is not None)

        # Extract scores for each dimension
        on_topic_scores = [g.on_topic_score for g in grades]
        grounded_scores = [g.grounded_score for g in grades]
        no_contradiction_scores = [g.no_contradiction_score for g in grades]
        understandability_scores = [g.understandability_score for g in grades]
        overall_scores = [g.overall_score for g in grades]

        # Calculate dimension stats
        on_topic_stats = cls.calculate_dimension_stats(on_topic_scores, "on_topic")
        grounded_stats = cls.calculate_dimension_stats(grounded_scores, "grounded")
        no_contradiction_stats = cls.calculate_dimension_stats(no_contradiction_scores, "no_contradiction")
        understandability_stats = cls.calculate_dimension_stats(understandability_scores, "understandability")
        overall_stats = cls.calculate_dimension_stats(overall_scores, "overall")

        # Calculate average score across all dimensions
        all_averages = [g.average_score for g in grades if g.error is None]
        average_score = statistics.mean(all_averages) if all_averages else 0

        # Extract performance metrics
        latencies = [r.latency_ms for r in responses]
        input_tokens = [r.input_tokens for r in responses]
        output_tokens = [r.output_tokens for r in responses]
        costs = [r.cost for r in responses]

        return ModelMetrics(
            model_name=model_name,
            model_id=model_id,
            num_samples=num_samples,
            num_errors=num_errors,
            on_topic_stats=on_topic_stats,
            grounded_stats=grounded_stats,
            no_contradiction_stats=no_contradiction_stats,
            understandability_stats=understandability_stats,
            overall_stats=overall_stats,
            average_score=average_score,
            latency_stats=cls.calculate_latency_stats(latencies),
            token_stats=cls.calculate_token_stats(input_tokens, output_tokens),
            cost_stats=cls.calculate_cost_stats(costs),
        )
