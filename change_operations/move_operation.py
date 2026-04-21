from typing import Tuple, Optional, Dict, List
from dependencies import (
    TemporalDependency,
    ExistentialDependency,
    Direction,
)
from adjacency_matrix import AdjacencyMatrix
from optimized_acceptance_variants import generate_optimized_acceptance_variants as generate_acceptance_variants
from variants_to_matrix import variants_to_matrix
from change_operations.delete_operation import delete_activity_from_variants
from change_operations.insert_operation import insert_into_variants

def move_activity(
        matrix: AdjacencyMatrix,
        activity: str,
        dependencies: Dict[
            Tuple[str, str],
            Tuple[Optional[TemporalDependency], Optional[ExistentialDependency]],
        ],
    ) -> AdjacencyMatrix:
    """
    Removes activity from original position and moves it to new position.

    Args:
        matrix: The input adjacency matrix
        activity: The name of the activity which should be moved
        dependencies: The dependencies defining the new position of the activity to be moved

    Returns:
        A new adjacency matrix with the activity moved

    Raises:
        ValueError: If input produces contradiction
    """
    variants = generate_acceptance_variants(matrix)
    try:
        new_variants = move_activity_in_variants(activity, dependencies, variants)
    except ValueError as e:
        raise ValueError(f"The input is invalid: {str(e)}") from e
    
    result_matrix = variants_to_matrix(new_variants, matrix.activities)
    
    # Override any inferred dependencies with the explicitly specified dependencies
    for (source, target), (temp_dep, exist_dep) in dependencies.items():
        if temp_dep is not None or exist_dep is not None:
            if source in result_matrix.activities and target in result_matrix.activities:
                current_temp, current_exist = result_matrix.dependencies.get((source, target), (None, None))
                
                final_temp = temp_dep if temp_dep is not None else current_temp
                final_exist = exist_dep if exist_dep is not None else current_exist
                
                result_matrix.add_dependency(source, target, final_temp, final_exist)
                
                # Also update the reverse dependency
                # This ensures that if (d,a) = (EVENTUAL FORWARD, IMPLICATION FORWARD)
                # then (a,d) = (EVENTUAL BACKWARD, IMPLICATION BACKWARD)
                if target in result_matrix.activities and source in result_matrix.activities:
                    # Create the reverse temporal dependency
                    reverse_temp = None
                    if final_temp is not None:
                        if final_temp.direction == Direction.FORWARD:
                            reverse_temp = TemporalDependency(final_temp.type, Direction.BACKWARD)
                        elif final_temp.direction == Direction.BACKWARD:
                            reverse_temp = TemporalDependency(final_temp.type, Direction.FORWARD)
                        else:  # Direction.BOTH
                            reverse_temp = TemporalDependency(final_temp.type, Direction.BOTH)
                    
                    # Create the reverse existential dependency
                    reverse_exist = None
                    if final_exist is not None:
                        if final_exist.direction == Direction.FORWARD:
                            reverse_exist = ExistentialDependency(final_exist.type, Direction.BACKWARD)
                        elif final_exist.direction == Direction.BACKWARD:
                            reverse_exist = ExistentialDependency(final_exist.type, Direction.FORWARD)
                        else:  # Direction.BOTH
                            reverse_exist = ExistentialDependency(final_exist.type, Direction.BOTH)
                    
                    result_matrix.add_dependency(target, source, reverse_temp, reverse_exist)
    
    return result_matrix

def move_activity_in_variants(
        activity: str,
        dependencies: Dict[
            Tuple[str, str],
            Tuple[Optional[TemporalDependency], Optional[ExistentialDependency]],
        ],
        variants: List[List[str]],
    ) -> List[List[str]]:
    """
    Removes activity from original position and moves it to new position.

    Args:
        activity: The name of the activity which should be moved
        dependencies: The dependencies defining the new position of the activity to be moved
        variants: The variants of the original matrix

    Returns:
        A new adjacency matrix with the activity moved

    Raises:
        ValueError: If input produces contradiction
    """
    variants_after_delete = delete_activity_from_variants(variants, activity)
    matrix_after_delete = variants_to_matrix(variants_after_delete)

    total_dependencies = matrix_after_delete.get_dependencies() | dependencies
    try:
        new_variants = insert_into_variants(activity, dependencies, total_dependencies , matrix_after_delete.activities, variants_after_delete)
    except ValueError as e:
        raise ValueError(f"The input is invalid: {e}")

    return new_variants