import pytest 

# ── Core imports ────────────────────────────────────────────────────────────
from adjacency_matrix import AdjacencyMatrix, parse_yaml_to_adjacency_matrix
from dependencies import (
    TemporalDependency, ExistentialDependency,
    TemporalType, ExistentialType, Direction,
)
from variants_to_matrix import variants_to_matrix
from acceptance_variants import generate_acceptance_variants

from acceptance_skeleton import generate_skeleton

def temp_dep(typ: TemporalType, direction: Direction = Direction.FORWARD) -> TemporalDependency:
    return TemporalDependency(type=typ, direction=direction)
 
 
def exist_dep(typ: ExistentialType, direction: Direction = Direction.BOTH) -> ExistentialDependency:
    return ExistentialDependency(type=typ, direction=direction)
 
 
# --- define the dependnecies 
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


@pytest.fixture
def matrix_abc_seq(sample_activities):
    matrix = AdjacencyMatrix(activities=sample_activities)
    matrix.add_dependency(
        "A",
        "B",
        TemporalDependency(TemporalType.DIRECT, Direction.FORWARD),
        ExistentialDependency(ExistentialType.IMPLICATION, Direction.FORWARD),
    )
    matrix.add_dependency(
        "B",
        "C",
        TemporalDependency(TemporalType.EVENTUAL, Direction.FORWARD),
        ExistentialDependency(ExistentialType.EQUIVALENCE, Direction.BOTH),
    )
    matrix.add_dependency(
        "A",
        "C",
        TemporalDependency(TemporalType.INDEPENDENCE, Direction.BOTH),
        ExistentialDependency(ExistentialType.OR, Direction.BOTH),
    )
    return matrix