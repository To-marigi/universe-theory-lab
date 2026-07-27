from universe_lab.validation import environment_report, run_validation_suite


def test_all_required_backends_import() -> None:
    report = environment_report()
    failures = [backend for backend in report["backends"] if not backend["available"]]
    assert failures == []


def test_independent_validation_suite() -> None:
    result = run_validation_suite()
    assert result["passed"], result["checks"]
