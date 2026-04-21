from typing import List
from adjacency_matrix import AdjacencyMatrix
from optimized_acceptance_variants import generate_optimized_acceptance_variants as generate_acceptance_variants
from variants_to_matrix import variants_to_matrix

def skip_activity_in_variants(variants: List[List[str]], optional_activity: str) -> List[List[str]]:
    """
    Removes the specified activity from all acceptance variants.
    
    Args:
        variants: List of variants to process
        optional_activity: Activity which becomes optional in the process 
    Returns:
        New variants with the activity now being optional
    """
    modified_variants = []
    seen = set()
    
    for variant in variants:
        if optional_activity in variant:
            # Create one version without the activity
            modified_variant = [act for act in variant if act != optional_activity]

            # Create two versions: one with and one without the activity
            variants_to_add = [variant, modified_variant]
        else:
            # Activity not in variant, keep as is
            variants_to_add = [variant]

        for var in variants_to_add:
            if var:  # Only add non-empty variants
                variant_tuple = tuple(var)
                if variant_tuple not in seen:
                    seen.add(variant_tuple)
                    modified_variants.append(var)
                       
    return modified_variants


def skip_activity(matrix: AdjacencyMatrix, optional_activity: str) -> AdjacencyMatrix:
    """
    Makes an activity in the process optional:
    1. Checking if the named activity is part ov the variant 
    2. If it is part of the variant, for each variant with the activity create one wthout it 
    
    Args:
        matrix: The input adjacency matrix
        activity: The name of the activity to become optional
        
    Returns:
        A new adjacency matrix with the activity skipped
        
    Raises:
        ValueError: If activity not found
    """
    if optional_activity not in matrix.activities:
        raise ValueError(f"Activity {optional_activity} not found in matrix")
        
    # Generate variants from input matrix
    variants = generate_acceptance_variants(matrix)
    
    # Remove activity from variants
    modified_variants = skip_activity_in_variants(variants, optional_activity)
    
        
    # Convert modified variants back to matrix
    new_matrix = variants_to_matrix(modified_variants, matrix.activities)
    
    return new_matrix

