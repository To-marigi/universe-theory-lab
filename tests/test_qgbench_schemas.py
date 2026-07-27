import json
from pathlib import Path

from universe_lab.qgbench.cli import validate_knowledge_base
from universe_lab.qgbench.schemas import validate_claim_graph


def test_repository_knowledge_base_is_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    assert validate_knowledge_base(root) == []


def test_claim_graph_rejects_unknown_dependency(tmp_path: Path) -> None:
    path = tmp_path / "claims.jsonl"
    claim = {
        "id": "claim:test",
        "claim": "test",
        "kind": "definition",
        "status": "PROVEN",
        "assumptions": [],
        "scope": "test only",
        "sources": [{"id": "source:test"}],
        "depends_on": ["claim:missing"],
    }
    path.write_text(json.dumps(claim) + "\n", encoding="utf-8")
    errors = validate_claim_graph([path])
    assert any("unknown dependency" in error for error in errors)
