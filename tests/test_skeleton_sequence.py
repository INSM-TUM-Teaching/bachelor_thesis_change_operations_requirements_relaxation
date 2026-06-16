import pytest

from acceptance_skeleton import generate_skeleton


from adjacency_matrix import AdjacencyMatrix
from dependencies import (
    TemporalDependency,
    ExistentialDependency,
    TemporalType,
    ExistentialType,
    Direction,
)

from utils.console_helpers import deps_to_matrix


# define shorthand constructors for the dependnecy types 
DIRECT     = TemporalType.DIRECT
EVENTUAL   = TemporalType.EVENTUAL
INDEP      = TemporalType.INDEPENDENCE
EQUIV      = ExistentialType.EQUIVALENCE
IMPL       = ExistentialType.IMPLICATION
NEG_EQUIV  = ExistentialType.NEGATED_EQUIVALENCE
OR         = ExistentialType.OR
NAND       = ExistentialType.NAND
FWD        = Direction.FORWARD
BWD        = Direction.BACKWARD
BOTH       = Direction.BOTH


def test_direct_temp_sequence(): 
    # test direct temporal dependnecies, ensuring that no placeholder is positioned between the activities 

    # define a dict with required dependencies 
    dependencies = {
        ("A", "D"): (TemporalDependency(type=DIRECT, direction=FWD), None), 
        ("D", "A"): (TemporalDependency(type=DIRECT, direction=BWD), None), 
    }

    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))

    assert ["_", "A", "D", "_"] in skeleton_sequences 


def test_direct_temp_sequence_two(): 
    # ensure with direct temporal deps, no activity happens in between 

    # define a dict with required dependencies 
    dependencies = {
        ("A", "D"): (TemporalDependency(type=DIRECT, direction=FWD), None), 
        ("D", "A"): (TemporalDependency(type=DIRECT, direction=BWD), None), 

        ("A", "B"): (None, ExistentialDependency(type=EQUIV, direction=BOTH)), 
        ("B", "A"): (None, ExistentialDependency(type=EQUIV, direction=BOTH)), 
    }

    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))

    assert ["_", "A", "D", "_", "B", "_"] in skeleton_sequences 
    assert ["_", "B", "_", "A", "D", "_"] in skeleton_sequences 


def test_temp_transitive_closure(): 
    # ensure that we filter the skeleton sequences correctly using transitive closure of temporal dependencies 

    # define a dict with required dependencies 
    dependencies = {
        ("A", "B"): (TemporalDependency(type=DIRECT, direction=FWD), None), 
        ("B", "A"): (TemporalDependency(type=DIRECT, direction=BWD), None), 

        ("B", "C"): (TemporalDependency(type=DIRECT, direction=FWD), None), 
        ("C", "B"): (TemporalDependency(type=DIRECT, direction=BWD), None), 
    }

    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))

    # check no ordering which violates the trsnaitive closure 
    assert ["_", "C", "_", "A", "_"] not in skeleton_sequences
    assert ["_", "C", "A", "_"] not in skeleton_sequences


def test_eventual_temp_allows_intermediary():
    # test eventual ordering, leaving space and not allowing other cases 

    dependencies = {
        ("A", "B"): (TemporalDependency(type=EVENTUAL, direction=FWD), None),
        ("B", "A"): (TemporalDependency(type=EVENTUAL, direction=BWD), None),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    # A placeholder must separate A and B (eventual, not direct)
    assert ["_", "A", "_", "B", "_"] in skeleton_sequences
    # The reverse order must not appear — A still precedes B
    assert ["_", "B", "_", "A", "_"] not in skeleton_sequences
 
 
 
def test_mixed_direct_eventual_chain():
    # test mixed combinations of temporal dependnecies, ensuring correct disticntion between types 
    # and considers stransitive closure 

    dependencies = {
        ("A", "B"): (TemporalDependency(type=DIRECT, direction=FWD), None),
        ("B", "A"): (TemporalDependency(type=DIRECT, direction=BWD), None),
        ("B", "C"): (TemporalDependency(type=EVENTUAL, direction=FWD), None),
        ("C", "B"): (TemporalDependency(type=EVENTUAL, direction=BWD), None),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    # A and B directly adjacent, then placeholder before C
    assert ["_", "A", "B", "_", "C", "_"] in skeleton_sequences
    # No placeholder allowed between A and B
    assert ["_", "A", "_", "B", "_", "C", "_"] not in skeleton_sequences
    # C must not precede A
    assert ["_", "C", "_", "A", "B", "_"] not in skeleton_sequences
 
 
# ---------------------------------------------------------------------------
# Existential dependency tests
# ---------------------------------------------------------------------------
 
def test_implication_fwd_optional_activity():
    # test if implication reflected correctly 

    dependencies = {
        ("A", "B"): (None, ExistentialDependency(type=IMPL, direction=FWD)),
        ("B", "A"): (None, ExistentialDependency(type=IMPL, direction=BWD)),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    # B alone is valid (B may exist without A)
    assert any(
        "B" in seq and "A" not in seq
        for seq in skeleton_sequences
    ), "Expected a skeleton with B but not A"
 
    # A and B together is valid
    assert any(
        "A" in seq and "B" in seq
        for seq in skeleton_sequences
    ), "Expected a skeleton with both A and B"
 
    # A alone must not appear 
    assert not any(
        "A" in seq and "B" not in seq
        for seq in skeleton_sequences
    ), "Found forbidden skeleton with A but not B"
 
 

 
def test_negated_equivalence_mutual_exclusion():
    """
    A ⊕ B (NEGATED EQUIVALENCE / XOR): exactly one of A or B must occur in
    every valid sequence. The skeleton must contain sequences with only A and
    sequences with only B, but never both together and never neither.
    """
    dependencies = {
        ("A", "B"): (None, ExistentialDependency(type=NEG_EQUIV, direction=BOTH)),
        ("B", "A"): (None, ExistentialDependency(type=NEG_EQUIV, direction=BOTH)),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    # A alone is valid
    assert any(
        "A" in seq and "B" not in seq
        for seq in skeleton_sequences
    ), "Expected a skeleton with A but not B"
 
    # B alone is valid
    assert any(
        "B" in seq and "A" not in seq
        for seq in skeleton_sequences
    ), "Expected a skeleton with B but not A"
 
    # Both together must not appear
    assert not any(
        "A" in seq and "B" in seq
        for seq in skeleton_sequences
    ), "Found forbidden skeleton with both A and B"
 
    # Neither must not appear (for non-empty sequences)
    non_empty = [s for s in skeleton_sequences if s != [] and s != ["_"]]
    assert not any(
        "A" not in seq and "B" not in seq
        for seq in non_empty
    ), "Found non-empty skeleton with neither A nor B"
 
 
def test_nand_allows_neither_or_one():
    """
    A | B (NAND): A and B must not both occur. Valid subsets: {}, {A}, {B}.
    The skeleton must NOT contain any sequence where both A and B are present.
    """
    dependencies = {
        ("A", "B"): (None, ExistentialDependency(type=NAND, direction=BOTH)),
        ("B", "A"): (None, ExistentialDependency(type=NAND, direction=BOTH)),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    # A alone is valid
    assert any(
        "A" in seq and "B" not in seq
        for seq in skeleton_sequences
    ), "Expected a skeleton with A but not B"
 
    # B alone is valid
    assert any(
        "B" in seq and "A" not in seq
        for seq in skeleton_sequences
    ), "Expected a skeleton with B but not A"
 
    # Both together must not appear
    assert not any(
        "A" in seq and "B" in seq
        for seq in skeleton_sequences
    ), "Found forbidden skeleton with both A and B"
 
 
def test_or_requires_at_least_one():
    """
    A ∨ B (OR): at least one of A or B must occur. The skeleton must contain
    sequences with A, sequences with B, and sequences with both, but never a
    non-empty sequence containing neither.
    """
    dependencies = {
        ("A", "B"): (None, ExistentialDependency(type=OR, direction=BOTH)),
        ("B", "A"): (None, ExistentialDependency(type=OR, direction=BOTH)),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    # A alone is valid
    assert any(
        "A" in seq and "B" not in seq
        for seq in skeleton_sequences
    ), "Expected a skeleton with A but not B"
 
    # B alone is valid
    assert any(
        "B" in seq and "A" not in seq
        for seq in skeleton_sequences
    ), "Expected a skeleton with B but not A"
 
    # Both together is valid
    assert any(
        "A" in seq and "B" in seq
        for seq in skeleton_sequences
    ), "Expected a skeleton with both A and B"
 
    # A non-empty sequence with neither must not appear
    non_empty = [s for s in skeleton_sequences if s != [] and set(s) != {"_"}]
    assert not any(
        "A" not in seq and "B" not in seq
        for seq in non_empty
    ), "Found non-empty skeleton with neither A nor B"
 
 
def test_equiv_both_or_neither():
    """
    A ⟺ B (EQUIVALENCE): A and B always co-occur or both are absent.
    """
    dependencies = {
        ("A", "B"): (None, ExistentialDependency(type=EQUIV, direction=BOTH)),
        ("B", "A"): (None, ExistentialDependency(type=EQUIV, direction=BOTH)),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    # A without B is forbidden
    assert not any(
        "A" in seq and "B" not in seq
        for seq in skeleton_sequences
    ), "Found forbidden skeleton with A but not B"
 
    # B without A is forbidden
    assert not any(
        "B" in seq and "A" not in seq
        for seq in skeleton_sequences
    ), "Found forbidden skeleton with B but not A"
 
    # Both together is valid
    assert any(
        "A" in seq and "B" in seq
        for seq in skeleton_sequences
    ), "Expected a skeleton with both A and B"
 
 
# ---------------------------------------------------------------------------
# Combined temporal + existential tests
# ---------------------------------------------------------------------------
 
def test_direct_temp_with_implication():
    """
    A ≺_d B (direct) and A ⇒ B (FORWARD IMPLICATION): when A occurs B must
    follow directly. B may also occur alone (without A).
    """
    dependencies = {
        ("A", "B"): (
            TemporalDependency(type=DIRECT, direction=FWD),
            ExistentialDependency(type=IMPL, direction=FWD),
        ),
        ("B", "A"): (
            TemporalDependency(type=DIRECT, direction=BWD),
            ExistentialDependency(type=IMPL, direction=BWD),
        ),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    # When both present, A must immediately precede B
    assert ["_", "A", "B", "_"] in skeleton_sequences
 
    # B alone is valid (implication is one-way)
    assert any(
        "B" in seq and "A" not in seq
        for seq in skeleton_sequences
    ), "Expected a skeleton with B but not A"
 
    # A alone must be absent
    assert not any(
        "A" in seq and "B" not in seq
        for seq in skeleton_sequences
    ), "Found forbidden skeleton with A but not B"
 
 
def test_eventual_temp_with_nand():
    """
    A ≺ B (eventual) and A | B (NAND): these are contradictory — if NAND
    holds neither A nor B may both appear, yet the temporal dependency
    requires an ordering between them when both are present.  With NAND the
    valid subsets containing both are suppressed, so the skeleton must only
    contain sequences with at most one of A or B (plus empty).
    """
    dependencies = {
        ("A", "B"): (
            TemporalDependency(type=EVENTUAL, direction=FWD),
            ExistentialDependency(type=NAND, direction=BOTH),
        ),
        ("B", "A"): (
            TemporalDependency(type=EVENTUAL, direction=BWD),
            ExistentialDependency(type=NAND, direction=BOTH),
        ),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    # Both A and B together must not appear
    assert not any(
        "A" in seq and "B" in seq
        for seq in skeleton_sequences
    ), "Found forbidden skeleton with both A and B under NAND"
 
 
def test_equiv_with_eventual_ordering():
    """
    A ⟺ B (EQUIVALENCE) and A ≺ B (eventual): A and B always co-occur and
    A always precedes B. The skeleton must reflect this joint constraint.
    """
    dependencies = {
        ("A", "B"): (
            TemporalDependency(type=EVENTUAL, direction=FWD),
            ExistentialDependency(type=EQUIV, direction=BOTH),
        ),
        ("B", "A"): (
            TemporalDependency(type=EVENTUAL, direction=BWD),
            ExistentialDependency(type=EQUIV, direction=BOTH),
        ),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    # A before B with placeholder allowed
    assert ["_", "A", "_", "B", "_"] in skeleton_sequences
 
    # B before A violates the temporal constraint
    assert ["_", "B", "_", "A", "_"] not in skeleton_sequences
 
    # Neither A alone nor B alone may appear
    assert not any(
        "A" in seq and "B" not in seq
        for seq in skeleton_sequences
    )
    assert not any(
        "B" in seq and "A" not in seq
        for seq in skeleton_sequences
    )
 
 
# ---------------------------------------------------------------------------
# Contradiction / empty-skeleton detection tests
# ---------------------------------------------------------------------------
 
def test_contradiction_circular_direct_dependency():
    """
    A ≺_d B and B ≺_d A simultaneously create a cycle: A must directly
    precede B and B must directly precede A. No valid acceptance sequence can
    satisfy both constraints, so generate_skeleton must return [[]] or [] to
    signal a contradiction.
    """
    dependencies = {
        ("A", "B"): (TemporalDependency(type=DIRECT, direction=FWD), None),
        ("B", "A"): (TemporalDependency(type=DIRECT, direction=FWD), None),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    assert skeleton_sequences == [[]] or skeleton_sequences == []
 
 
def test_contradiction_implication_and_nand():
    """
    A ⇒ B (FORWARD IMPLICATION) and A | B (NAND): if A occurs then B must
    occur (implication), but A and B must not both occur (NAND). Any sequence
    containing A leads to a contradiction. The only valid non-empty sequences
    are those containing B alone (if NAND permits it), but the implication
    forces B whenever A appears — meaning A can never appear. The skeleton
    must reflect that A is absent from all sequences, or produce a
    contradiction signal.
    """
    dependencies = {
        ("A", "B"): (
            None,
            ExistentialDependency(type=IMPL, direction=FWD),
        ),
        ("B", "A"): (
            None,
            ExistentialDependency(type=NAND, direction=BOTH),
        ),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    # A must never appear in any skeleton sequence
    assert not any(
        "A" in seq
        for seq in skeleton_sequences
    ), "Found skeleton with A, violating NAND + IMPLICATION contradiction"
 
 
def test_negated_equivalence_and_equivalence_contradiction():
    """
    A ⟺ B (EQUIVALENCE) and A ⊕ B (NEGATED EQUIVALENCE) simultaneously:
    equivalence requires both to co-occur while negated equivalence forbids
    them from co-occurring. No valid subset exists, so generate_skeleton must
    return [[]] or [].
    """
    dependencies = {
        ("A", "B"): (None, ExistentialDependency(type=EQUIV, direction=BOTH)),
        ("B", "A"): (None, ExistentialDependency(type=NEG_EQUIV, direction=BOTH)),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    assert skeleton_sequences == [[]] or skeleton_sequences == []
 
 
# ---------------------------------------------------------------------------
# Multi-activity interaction tests
# ---------------------------------------------------------------------------
 
def test_three_activities_two_branches_nand():
    """
    A | B (NAND) with a third activity C that is temporally independent.
    The skeleton must offer branches with {A, C} and {B, C} but never {A, B, C}
    or {A, B}.
    """
    dependencies = {
        ("A", "B"): (None, ExistentialDependency(type=NAND, direction=BOTH)),
        ("B", "A"): (None, ExistentialDependency(type=NAND, direction=BOTH)),
        ("A", "C"): (TemporalDependency(type=EVENTUAL, direction=FWD), None),
        ("C", "A"): (TemporalDependency(type=EVENTUAL, direction=BWD), None),
    }
 
    skeleton_sequences = generate_skeleton(deps_to_matrix(dependencies))
 
    # A and B must never co-occur
    assert not any(
        "A" in seq and "B" in seq
        for seq in skeleton_sequences
    ), "Found forbidden skeleton with both A and B under NAND"
 
    # C may appear alongside A
    assert any("A" in seq and "C" in seq for seq in skeleton_sequences), \
        "Expected a skeleton with A and C"
 
    # C may appear alongside B
    assert any("B" in seq and "C" in seq for seq in skeleton_sequences), \
        "Expected a skeleton with B and C"
 