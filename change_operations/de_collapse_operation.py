from typing import List
from adjacency_matrix import AdjacencyMatrix
from optimized_acceptance_variants import generate_optimized_acceptance_variants as generate_acceptance_variants
from variants_to_matrix import variants_to_matrix

def decollapse_variant_level(main_variants: List[List[str]], collapsed_activity: str, collapsed_variants: List[List[str]]) -> List[List[str]]:
    """
    Adds the variants of collapsed activities at the correct position in the main_variants
    
    Args:
        main_variants: List of variants to main process (process in which collapsed activity is)
        collapsed_activity: Activity which is currently collapsed and should now be de-collapsed
        collapsed_variants: variants of the currently collapsed activity 
        
    Returns:
        New variants with the activity de-collapsed, without duplicates 
    """
    modified_variants = []
    seen = set()
    variants_to_add = []
    
    for variant in main_variants:
        if collapsed_activity in variant:
            # The activity needs to be de-collapsed - insert all possible variants in the variant at the position of the collapsed activity 
            index = variant.index(collapsed_activity)
            for collapsed_variant in collapsed_variants:
                modified_variant = variant[:index] + collapsed_variant + variant[index+1:]
                variants_to_add.append(modified_variant)
        
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


def decollapse_operation(main_matrix: AdjacencyMatrix, collapsed_activity: str, collapsed_matrix: AdjacencyMatrix) -> AdjacencyMatrix:
    """
    Decollapses an activity which is currently collapsed 
    1. Checking that collapsed activity is part of the process 
    2. For collapsed activity create all possible acceptance seqeunces
    3. For each variant of main process in wich the activity to de-collapse is included, insert at the position 
        of the activity the acceptance sequence of the collapsed one 
    
    Args:
        main_matrix: The input adjacency matrix
        collapsed_activity: The name of the activity which is currently collapsed and should be de-collapsed 
        collapsed_matrix: The adjacency matrix of the activity which is currently collapsed 
        
    Returns:
        A new adjacency matrix with the activity decollapsed
        
    Raises:
        ValueError: If activity not found
    """

    if collapsed_activity not in main_matrix.activities:
        raise ValueError(f"Activity {collapsed_activity} not found in matrix")
    
    # test that none of the activities of the collapsed matrix are in the current matrix
    for activity in collapsed_matrix.get_activities():
        if activity in main_matrix.get_activities() and activity != collapsed_activity:
            raise ValueError(f"Activity {activity} is in matrix and collapsed matrix, activities would be defined ambigously after collapsing")
        
    # Generate variants from input matrix
    variants = generate_acceptance_variants(main_matrix)

    # generate variants of collapsed process 
    collapsed_variants = generate_acceptance_variants(collapsed_matrix)
    
    # Remove activity from variants
    modified_variants = decollapse_variant_level(variants, collapsed_activity, collapsed_variants)
    
    # Convert modified variants back to matrix
    new_matrix = variants_to_matrix(modified_variants, main_matrix.activities)
    
    return new_matrix