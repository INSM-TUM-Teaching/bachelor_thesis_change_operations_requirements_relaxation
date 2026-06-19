from typing import List
from adjacency_matrix import AdjacencyMatrix
from optimized_acceptance_variants import generate_optimized_acceptance_variants as generate_acceptance_variants
from variants_to_matrix import variants_to_matrix

def condition_update_in_variants(variants: List[List[str]], condition_activity: str, depending_activity: str) -> List[List[str]]:
    """
    Makes an activity in variants depending on other activity
    
    Args:
        variants: List of variants to process
        condition_activity: Activity that determines if other activity occurs 
        depending_activity: Activity which depends on other activity
        
    Returns:
        New variants with the depending_activity now depending on condition_activity
    """
    modified_variants = []
    seen = set()
    
    for variant in variants:
        if condition_activity in variant:
            # The variant must not be changed, since the condition activity is present, so the depending activity may occur
            variants_to_add = [variant]
        else:
            # Condition activity not in variants, this means we must delete the occurence of the depending activity 
            modified_variant = [act for act in variant if act != depending_activity]
            variants_to_add = [modified_variant]

        for var in variants_to_add:
            if var:  # Only add non-empty variants
                variant_tuple = tuple(var)
                if variant_tuple not in seen:
                    seen.add(variant_tuple)
                    modified_variants.append(var)

    return modified_variants


def condition_update(matrix: AdjacencyMatrix, condition_activity: str, depending_activity: str) -> AdjacencyMatrix:
    """
    Makes an activity in the process dependending on another activity:
    1. Checking if the condition_activity is part of the variant 
    2. If it is part, the dependening activity may remain in the process, else it must be removed  
    
    Args:
        matrix: The input adjacency matrix
        condition_activity: The name of the activity which implices the other activity 
        depending_activity: The name of the activity which's occurence dependens on the condition activity 
        
    Returns:
        A new adjacency matrix with the activity skipped
        
    Raises:
        ValueError: If activity not found
    """
    if condition_activity not in matrix.activities:
        raise ValueError(f"Activity {condition_activity} not found in matrix")
    
    if depending_activity not in matrix.activities:
        raise ValueError(f"Activity {depending_activity} not found in matrix")
        
    # Generate variants from input matrix
    variants = generate_acceptance_variants(matrix)
    
    # Remove activity from variants
    modified_variants = condition_update_in_variants(variants, condition_activity, depending_activity)
    
    # Convert modified variants back to matrix
    new_matrix = variants_to_matrix(modified_variants, matrix.activities)
    
    return new_matrix

