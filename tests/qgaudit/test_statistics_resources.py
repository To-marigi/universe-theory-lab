import numpy as np

from universe_lab.qgaudit.resources import estimate_resources
from universe_lab.qgaudit.statistics import finite_size_fit, summarize


def test_summary_uses_sample_uncertainty() -> None:
    result = summarize([1.0, 2.0, 3.0, 4.0])
    assert result.count == 4
    assert np.isclose(result.mean, 2.5)
    assert result.ci95_low < result.mean < result.ci95_high


def test_finite_size_fit_recovers_synthetic_parameters() -> None:
    rng = np.random.default_rng(11)
    counts = [225, 450, 900, 1800]
    observations = [
        (1.2 * count**-0.6 + 0.01 + rng.normal(0.0, 0.001, 30)).tolist()
        for count in counts
    ]
    result = finite_size_fit(counts, observations, bootstrap_samples=100, seed=12)
    assert 0.3 < result["parameters"]["p"]["estimate"] < 0.9
    assert 0.0 < result["parameters"]["b"]["estimate"] < 0.03


def test_resource_preflight_blocks_excessive_time() -> None:
    estimate = estimate_resources(
        18_000,
        seeds=30,
        measured_count=225,
        measured_seconds_per_seed=0.01,
        wall_time_budget_seconds=180.0,
    )
    assert not estimate.executable
    assert estimate.reason is not None
