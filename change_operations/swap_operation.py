from typing import List
from adjacency_matrix import AdjacencyMatrix
from optimized_acceptance_variants import generate_optimized_acceptance_variants as generate_acceptance_variants
from variants_to_matrix import variants_to_matrix

def swap_activities_in_variants(variants: List[List[str]], activity1: str, activity2: str) -> List[List[str]]:
    """
    Swaps two activities in all variants.
    """
    swapped_variants = []
    for variant in variants:
        new_variant = []
        for activity in variant:
            if activity == activity1:
                new_variant.append(activity2)
            elif activity == activity2:
                new_variant.append(activity1)
            else:
                new_variant.append(activity)
        swapped_variants.append(new_variant)
    return swapped_variants

def swap_activities(matrix: AdjacencyMatrix, activity1: str, activity2: str) -> AdjacencyMatrix:
    """
    Swaps two activities in the process model by regenerating variants and then the matrix.
    
    Args:
        matrix: The input adjacency matrix.
        activity1: The first activity to swap.
        activity2: The second activity to swap.
        
    Returns:
        A new adjacency matrix with the activities swapped.
        
    Raises:
        ValueError: If either activity is not found in the matrix.
    """
    if activity1 not in matrix.activities or activity2 not in matrix.activities:
        raise ValueError("One or both activities not found in the matrix")

    # Generate acceptance variants from the original matrix
    variants = generate_acceptance_variants(matrix)
    
    # Swap the activities in each variant
    modified_variants = swap_activities_in_variants(variants, activity1, activity2)
    
    # Convert the modified variants back into a new adjacency matrix
    # The list of activities in the matrix remains the same.
    new_matrix = variants_to_matrix(modified_variants, matrix.activities)
    
    return new_matrix
