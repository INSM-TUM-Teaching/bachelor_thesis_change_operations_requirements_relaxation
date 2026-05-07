from typing import Tuple, Optional, Dict, List
from dependencies import (
    TemporalDependency,
    ExistentialDependency,
)
from adjacency_matrix import AdjacencyMatrix
from acceptance_variants import (
    generate_acceptance_variants,
    satisfies_existential_constraints,
    satisfies_temporal_constraints,
)
from optimized_acceptance_variants import generate_optimized_acceptance_variants as generate_acceptance_variants
from utils.split_dependencies import split_dependencies
from utils.check_valid_input import is_valid_input
from variants_to_matrix import variants_to_matrix

def search_valid_positions_to_insert(
    variant: List[str],
    activity: str,
    temporal_deps: Dict[Tuple[str, str], TemporalDependency],
) -> List[List[str]]:
    """
    Searches all options where activity can be inserted according to temporal dependencies.

    Args:
        variant: variant in which activity shall be inserted
        activity: The name of the activity to insert.
        temporal_dependencies: The temporal dependencies defining the position of the activity to be inserted.

    Returns:
        List of new variants according to temporal dependencies
    """
    new_variants: List[List[str]] = []

    for pos in range(len(variant) + 1):
        new_variant = variant.copy()
        new_variant.insert(pos, activity)
        if satisfies_temporal_constraints(new_variant, temporal_deps):
            new_variants.append(new_variant.copy())
    return new_variants

def insert_activity(
    matrix: AdjacencyMatrix,
    activity: str,
    dependencies: Dict[
        Tuple[str, str],
        Tuple[Optional[TemporalDependency], Optional[ExistentialDependency]],
    ],
) -> AdjacencyMatrix:
    """
    Adds a new acivity to the process by:
    1. Generating variants for the input matrix.
    2. Insert into variants.
    3. Convet variants to new matrix.

    Args:
        matrix: The input adjacency matrix
        activity: The name of the activity to insert
        dependencies: The dependencies defining the position of the activity to be inserted

    Returns:
        A new adjacency matrix with the activity inserted

    Raises:
        ValueError: If input produces contradiction
    """
    total_dependencies = matrix.get_dependencies() | dependencies
    variants = generate_acceptance_variants(matrix)
    try:
        new_variants =  insert_into_variants(activity, dependencies, total_dependencies, matrix.get_activities(), variants)
    except ValueError as e:
        raise ValueError(f"The input is invalid: {e}")
    return variants_to_matrix(new_variants, matrix.activities)

def insert_into_variants(
    activity: str,
    dependencies: Dict[
        Tuple[str, str],
        Tuple[Optional[TemporalDependency], Optional[ExistentialDependency]],
    ],
    total_dependencies: Dict[
        Tuple[str, str],
        Tuple[Optional[TemporalDependency], Optional[ExistentialDependency]],
    ],
    activities: List[str],
    variants: List[List[str]]
    )-> List[List[str]]:
    """
    Adds a new acivity to the process by:
    1. Checking if input is valid.
    2. Checking if for variant existential dependencies hold with and without activity to be inserted.
    3. Inserting according to direct or eventual temporal dependencies.

    Args:
        activity: The name of the activity to insert
        dependencies: The dependencies defining the position of the activity to be inserted
        total_dependencies: Dependencies which also include all the dependencies from the original matrix
        activities: The activities from the original matrix
        variants: Variants of the original matrix

    Returns:
        Variants of the process with activity inserted.

    Raises:
        ValueError: If input produces contradiction
    """
    new_activities = activities.copy()
    new_activities.append(activity)

    try:
        is_valid_input(activities, new_activities, activity, variants, total_dependencies)
    except ValueError as e:
        raise ValueError(str(e)) from e

    temporal_deps, existential_deps = split_dependencies(dependencies)
    total_temporal_deps, total_existential_deps = split_dependencies(total_dependencies)

    new_variants = []

    if satisfies_existential_constraints(
        {activity}, new_activities, total_existential_deps
    ):
        new_variants.append([activity])

    for variant in variants:
        if satisfies_existential_constraints(
            set(variant), new_activities, total_existential_deps
        ):
            new_variants.append(variant)
        variant_with_activity = variant.copy()
        variant_with_activity.append(activity)
        if not satisfies_existential_constraints(
            set(variant_with_activity), new_activities, total_existential_deps
        ):
            continue
        valid_variants = search_valid_positions_to_insert(
            variant, activity, temporal_deps
        )
        new_variants.extend(valid_variants)

    return new_variants