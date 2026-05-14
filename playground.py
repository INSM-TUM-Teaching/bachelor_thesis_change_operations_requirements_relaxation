from utils.similarity_score import similarity_calculation_occurence
from utils.similarity_score import similarity_calculation_ordering
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

from variants_to_matrix import variants_to_matrix

from acceptance_skeleton import generate_skeleton

from solution_strategies.preservation_strategies import adapt_process

####################################################
# Testing 
def build_test_locked_dep() -> AdjacencyMatrix:
    """
    Three activities: X, A, B
    Existential constraints:
      - X ⟺ A  (equivalence: both occur or neither)
      - X ⊼ B  (NAND: cannot co-occur, but both may be absent)
    No temporal constraints.
    """
    matrix = AdjacencyMatrix(activities=["A", "B", "C", "X", "Y", "G", "H"])

    temp_indep  = TemporalDependency(type=TemporalType.INDEPENDENCE, direction=Direction.BOTH)
    temp_evt_forw  = TemporalDependency(type=TemporalType.EVENTUAL, direction=Direction.FORWARD)
    temp_evt_back  = TemporalDependency(type=TemporalType.EVENTUAL, direction=Direction.BACKWARD)
    exist_equiv = ExistentialDependency(type=ExistentialType.EQUIVALENCE, direction=Direction.BOTH)
    exist_nand  = ExistentialDependency(type=ExistentialType.NAND,        direction=Direction.BOTH)
    exist_indep = ExistentialDependency(type=ExistentialType.INDEPENDENCE, direction=Direction.BOTH)
    exist_n_equiv = ExistentialDependency(type=ExistentialType.NEGATED_EQUIVALENCE, direction=Direction.BOTH)
    exist_imp = ExistentialDependency(type=ExistentialType.IMPLICATION, direction=Direction.FORWARD)

    matrix.add_dependency("A", "B", None, exist_n_equiv)
    matrix.add_dependency("B", "C", None, exist_imp)

    matrix.add_dependency("X", "Y", None, exist_equiv)

    matrix.add_dependency("G", "H", None, exist_equiv)

    # A <-> B — no constraint between them directly
    # matrix.add_dependency("A", "B", temp_indep, exist_indep)
    # matrix.add_dependency("B", "A", temp_indep, exist_indep)

    return matrix

dependencies = build_test_locked_dep()
matrix = variants_to_matrix([[], ["A", "B", "C", "X", "Y", "G", "H"], ["A", "C", "X", "Y", "G"], ["A", "B", "C", "X", "Y", "H"]])

print(adapt_process(matrix, dependencies))

# print(generate_skeleton(dependencies))



# insert_variant([['A', 'B', 'C', 'D', 'E'], ['B', 'A', 'C']], 'X', dependencies)

from solution_strategies.skeleton_strategies import adapt_anchor_sort_reinsert

# result = adapt_anchor_sort_reinsert(['A', 'C', 'B', 'D', 'E'], ['_', 'B', '_', 'X', '_', 'A', '_'], ['A', 'B', 'X', 'E'])

# print(result)


