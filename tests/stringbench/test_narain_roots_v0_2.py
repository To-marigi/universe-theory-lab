from universe_lab.stringbench.narain.branches import derive_branch_certificates
from universe_lab.stringbench.narain.roots import (
    d_roots,
    derive_root_system,
    e8_roots_exact,
)


def test_exact_parent_root_systems() -> None:
    e8 = derive_root_system(e8_roots_exact())
    d16 = derive_root_system(d_roots(16))
    assert e8.components == ("E8",)
    assert e8.root_count == 240
    assert e8.rank == 8
    assert d16.components == ("D16",)
    assert d16.root_count == 480
    assert d16.rank == 16


def test_bounded_search_derives_all_four_local_algebras() -> None:
    branches = {
        item.specification.branch.value: item for item in derive_branch_certificates()
    }
    assert branches["standard"].representative.analysis.components == ("E7", "E7")
    assert branches["base_fiber_dual"].representative.analysis.components == ("D6", "E8")
    assert branches["alternate"].representative.analysis.components == (
        "A1",
        "A1",
        "D12",
    )
    assert branches["maximal"].representative.analysis.components == ("D14",)
    assert {
        name: item.representative.analysis.root_count for name, item in branches.items()
    } == {
        "standard": 252,
        "base_fiber_dual": 300,
        "alternate": 268,
        "maximal": 364,
    }


def test_u1_rank_is_not_confused_with_nonabelian_rank() -> None:
    branches = derive_branch_certificates()
    assert all(item.representative.analysis.rank == 14 for item in branches)
    assert all(item.certificate.abelian_rank == 2 for item in branches)


def test_representatives_are_search_results_with_exact_cartan_data() -> None:
    for branch in derive_branch_certificates():
        representative = branch.representative
        assert "bounded rational search" in representative.search_certificate
        cartan = representative.analysis.cartan_matrix
        assert len(cartan) == 14
        assert all(row[index] == 2 for index, row in enumerate(cartan))
