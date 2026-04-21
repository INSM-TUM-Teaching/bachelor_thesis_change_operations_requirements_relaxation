from typing import List
from adjacency_matrix import AdjacencyMatrix
from optimized_acceptance_variants import generate_optimized_acceptance_variants as generate_acceptance_variants
from variants_to_matrix import variants_to_matrix

def delete_activity_from_variants(variants: List[List[str]], activity: str, remove_duplicates: bool = False) -> List[List[str]]:
    """
    Removes the specified activity from all acceptance variants.
    
    Args:
        variants: List of variants to process
        activity: Activity to remove from all variants
        remove_duplicates: If True, removes duplicate variants after removing the activity
        
    Returns:
        New variants with the activity removed, with or without duplicates based on remove_duplicates
    """
    modified_variants = []
    seen = set()
    
    for variant in variants:
        # Remove activity from variant if present
        modified_variant = [act for act in variant if act != activity]
        # Only add non-empty variants
        if modified_variant:
            if remove_duplicates:
                variant_tuple = tuple(modified_variant)
                if variant_tuple not in seen:
                    seen.add(variant_tuple)
                    modified_variants.append(modified_variant)
            else:
                modified_variants.append(modified_variant)
                
    return modified_variants

def delete_activity(matrix: AdjacencyMatrix, activity: str) -> AdjacencyMatrix:
    """
    Deletes an activity from the process by:
    1. Checking if deletion would result in an empty process due to equivalence relationships
    2. Generating acceptance variants from the input matrix
    3. Removing the activity from all variants
    4. Converting modified variants back to a matrix
    
    Args:
        matrix: The input adjacency matrix
        activity: The name of the activity to delete
        
    Returns:
        A new adjacency matrix with the activity removed
        
    Raises:
        ValueError: If activity not found or deletion would result in empty process
    """
    if activity not in matrix.activities:
        raise ValueError(f"Activity {activity} not found in matrix")
        
    # Generate variants from input matrix
    variants = generate_acceptance_variants(matrix)

    # Remove activity from variants
    modified_variants = delete_activity_from_variants(variants, activity)
    
    if not modified_variants:
        raise ValueError("Deletion would result in empty process")
        
    # Convert modified variants back to matrix
    # Remove the activity from the list first to ensure it's not included
    new_activities = [act for act in matrix.activities if act != activity]
    new_matrix = variants_to_matrix(modified_variants, matrix.activities)

    return new_matrix
