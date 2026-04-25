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


def satisfies_existential_constraints(
    subset: Set[str],
    activities: List[str],
    existential_dependencies: Dict[Tuple[str, str], ExistentialDependency],
) -> bool:
    """
    Checks if a subset of activities satisfies all existential constraints.
    """
    for (ai, aj), dependency in existential_dependencies.items():
        if dependency.type == ExistentialType.INDEPENDENCE:
            continue

        in_subset_ai = ai in subset
        in_subset_aj = aj in subset
        dep_type = dependency.type

        if not check_existential_relationship(
            in_subset_ai, in_subset_aj, dep_type, dependency.direction
        ):
            return False

    return True


def build_permutations(subset: Set[str]) -> List[List[str]]:
    """
    Generates all possible orderings (permutations) of activities in a subset.
    """
    if not subset:
        return [[]]
    return [list(p) for p in permutations(subset)]


def satisfies_temporal_constraints(
    variant: List[str],
    temporal_dependencies: Dict[Tuple[str, str], TemporalDependency],
) -> bool:
    """
    Checks if a variant of activities satisfies all temporal constraints.
    """
    if not variant:  # An empty variant has no temporal constraints to violate
        return True

    activity_to_pos = {activity: i for i, activity in enumerate(variant)}

    for i in range(len(variant)):
        for j in range(len(variant)):
            if i == j:
                continue

            ai = variant[i]
            aj = variant[j]

            dependency = temporal_dependencies.get((ai, aj))
            if not dependency or dependency.type == TemporalType.INDEPENDENCE:
                continue  # No constraint or independence means satisfied

            pos_ai = activity_to_pos[ai]
            pos_aj = activity_to_pos[aj]
            dep_type = dependency.type

            if not check_temporal_relationship(
                pos_ai, pos_aj, dep_type, dependency.direction
            ):
                return False

    return True


def generate_acceptance_variants(adj_matrix: AdjacencyMatrix) -> List[List[str]]:
    """
    Generates all valid acceptance variants from an adjacency matrix.
    """
    activities = adj_matrix.activities
    temporal_deps: Dict[Tuple[str, str], TemporalDependency] = {}
    existential_deps: Dict[Tuple[str, str], ExistentialDependency] = {}

    for (source, target), (temp_dep, exist_dep) in adj_matrix.dependencies.items():
        if temp_dep:
            temporal_deps[(source, target)] = temp_dep
        if exist_dep:
            existential_deps[(source, target)] = exist_dep

    acceptance_variants = []
    n = len(activities)

    for i in range(1, 1 << n):  # 2^n subsets, skip empty set
        current_subset_indices = []
        for j in range(n):
            if (i >> j) & 1:  # Check if j-th bit is set
                current_subset_indices.append(j)

        current_subset_activities = {activities[k] for k in current_subset_indices}

        if satisfies_existential_constraints(
            current_subset_activities, activities, existential_deps
        ):
            permutations_of_subset = build_permutations(current_subset_activities)
            for seq in permutations_of_subset:
                if satisfies_temporal_constraints(seq, temporal_deps):
                    acceptance_variants.append(seq)

    return acceptance_variants

