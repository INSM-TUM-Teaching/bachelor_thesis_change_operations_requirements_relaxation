from similarity_score import similarity_calculation_occurence
from similarity_score import similarity_calculation_ordering
import acceptance_skeleton

from itertools import permutations
from typing import List, Tuple, Dict, Set
from dependencies import (
    TemporalType,
    ExistentialType,
    TemporalDependency,
    ExistentialDependency,
    Direction,
)
from adjacency_matrix import AdjacencyMatrix
from constraint_logic import check_temporal_relationship, check_existential_relationship

# import acceptance variants, since we can reuse most of the functions
from acceptance_variants import satisfies_existential_constraints
from acceptance_variants import satisfies_temporal_constraints
from acceptance_variants import build_permutations
from acceptance_variants import generate_acceptance_variants

####################################################
# Testing 
def build_test_matrix() -> AdjacencyMatrix:
    """
    Three activities: X, A, B
    Existential constraints:
      - X ⟺ A  (equivalence: both occur or neither)
      - X ⊼ B  (NAND: cannot co-occur, but both may be absent)
    No temporal constraints.
    """
    matrix = AdjacencyMatrix(activities=["X", "A", "B"])

    temp_indep  = TemporalDependency(type=TemporalType.INDEPENDENCE, direction=Direction.BOTH)
    temp_evt_forw  = TemporalDependency(type=TemporalType.EVENTUAL, direction=Direction.FORWARD)
    temp_evt_back  = TemporalDependency(type=TemporalType.EVENTUAL, direction=Direction.BACKWARD)
    exist_equiv = ExistentialDependency(type=ExistentialType.EQUIVALENCE, direction=Direction.BOTH)
    exist_nand  = ExistentialDependency(type=ExistentialType.NAND,        direction=Direction.BOTH)
    exist_indep = ExistentialDependency(type=ExistentialType.INDEPENDENCE, direction=Direction.BOTH)

    matrix.add_dependency("X", "B", temp_evt_back, exist_equiv)
    matrix.add_dependency("B", "X", temp_evt_forw, exist_equiv)

    matrix.add_dependency("X", "A", temp_evt_forw, exist_equiv)
    matrix.add_dependency("A", "X", temp_evt_back, exist_equiv)

    # A <-> B — no constraint between them directly
    # matrix.add_dependency("A", "B", temp_indep, exist_indep)
    # matrix.add_dependency("B", "A", temp_indep, exist_indep)

    return matrix

skeleton = acceptance_skeleton.generate_skeleton(build_test_matrix())

sim_score = similarity_calculation_ordering(['B', 'A', 'C', 'D', 'E'], skeleton[0], ['A', 'B', 'X'])
print(sim_score)
