from typing import List
from typing import Set
from adjacency_matrix import AdjacencyMatrix
from optimized_acceptance_variants import generate_optimized_acceptance_variants as generate_acceptance_variants
from variants_to_matrix import variants_to_matrix
from dependencies import TemporalType

def collapse_variant_level(matrix: AdjacencyMatrix, main_variants: List[List[str]], collapsed_activity: str, collapse_activities: List[str]) -> List[List[str]]:
    """
    Adds the variants of collapsed activities at the correct position in the main_variants
    
    Args:
        main_variants: List of variants in the main process (i.e., the process where the collapsed activity appears).
        collapsed_activity: The activity that will remain in the variants after collapsing.
        collapse_activities: activities which should be collapsed 
        
    Returns:
        New list of variants with specified activities collapsed and duplicates removed. 
    """
    modified_variants = []

    seen = set()
    variants_to_add = []

    # Check for existing activities y, which are in variants between elements of collapse_activities 
    activities_in_between = get_activities_happening_between(main_variants, collapse_activities, matrix)

    if not activities_in_between:
        # if activities in between are empty, we can directly collapse 
        return perform_collapse_variant(main_variants, collapsed_activity, collapse_activities)
    
    else: 
        for activity in activities_in_between:
            for collapse_activity in collapse_activities:
                # ensure that the intermediate variable y is temporally independent of all activities that are to be collapsed. 
                temporal_dep, existential_dep = matrix.get_dependency(activity, collapse_activity)
                # check for dependency type 
                if temporal_dep.type != TemporalType.INDEPENDENCE:
                    # then collapsing not possible, problem is that we have activities happening in between 
                    raise ValueError(f"Activities {activities_in_between} happen between the activities to be collapsed")
    
        # if we pass this check without raising an error, we can do the actual collapsing 
        return perform_collapse_variant(main_variants, collapsed_activity, collapse_activities)

def get_activities_happening_between(variants: List[List[str]], 
                                     collapse_activities: Set[str], 
                                     matrix: AdjacencyMatrix) -> List[str]:
    """
    Get the set of activities, which happen between (temporally dependent) the activities to be collapsed, by: 
    1. Getting the set of activities which are in the acceptance sequences between 
    2. Checking for each of the activities if it is temporally independent 
    3. Return the set of activities 

    Args:
        variants: A list of variants, each being a list of activity names.
        collapse_activities: A set of activity names considered for parallelizing.
        dependnecies: List of dependencies (adjacency matrix)
        
    Returns:
        A list of unique activity names that are strictly (temporally independent) between two consecutive parallelize activities.
    """

    elements_in_between = []

    for variant in variants:
        # Find indexes of collapse activities in this variant
        collapse_indexes = [i for i, activity in enumerate(variant) if activity in collapse_activities]
        collapse_indexes.sort()
        
        for i in range(len(collapse_indexes) - 1):
            start = collapse_indexes[i]
            end = collapse_indexes[i + 1]
            # Add elements between start and end
            for elem in variant[start + 1:end]:
                if elem not in collapse_activities and elem not in elements_in_between:
                    elements_in_between.append(elem)

    if not elements_in_between:
        # if activities in between are empty, we just return an empty list 
        return []
    else: 
        # define a list to store the activities which happen in between 
        activities_in_between = []

        for activity in elements_in_between:
            for collapse_activity in collapse_activities:
                # ensure that the intermediate variable y is temporally independent of all activities that are to be collapsed. 
                temporal_dep, _ = matrix.get_dependency(activity, collapse_activity)
                # check for dependency type 
                if temporal_dep.type != TemporalType.INDEPENDENCE and activity not in activities_in_between:
                    # then collapsing not possible, problem is that we have activities happening in between 
                    activities_in_between.append(activity)

        return activities_in_between

def perform_collapse_variant(variants: List[List[str]], collapsed_activity: str, collapse_activities: List[str]) -> List[List[str]]: 
    """
    Performs the actual collapsing on the level of variants, by replacing the first occurence of an activity of the collapsed set 
    with the collapsed_activity and deleting all other activities of collapse_activities 
    
    Args:
        variants: A list of variants, each being a list of activity names.
        collapsed_activity: Activity which should replace the collapsed_acivities after the prcess of collapsing 
        collapse_activities: A set of activity names considered for collapsing.
        
    Returns:
        A list of unique variants where the collapsing was performed
    """

    modified_variants = []
    seen = set()
    
    for variant in variants:
        # set initial conditions to be rest after each iteration 
        is_collapsed = False
        modified_variant = []
        # Remove activity from variant if present
        for act in variant:
            if act in collapse_activities: 
                if not is_collapsed: 
                    # for the first occurence of an activity from the set collapse_activities, we replace it with the collapsed_activity
                    modified_variant.append(collapsed_activity)
                    is_collapsed = True
            else:
                # if activity is not part of the collapse_activities but just a "normal" activity from the process 
                modified_variant.append(act)
        
        # Only add non-empty variants which are unique; add to overall set of collapsed variants  
        if modified_variant:
            variant_tuple = tuple(modified_variant)
            if variant_tuple not in seen:
                seen.add(variant_tuple)
                modified_variants.append(modified_variant)
            
                
    return modified_variants


def collapse_operation(main_matrix: AdjacencyMatrix, collapsed_activity: str, collapse_activities: List[str]) -> AdjacencyMatrix:
    """
    Collapse a set of activities 
    1. Checks
    2. Create all acceptance variants for matrix 
    3. Check validity for collpasing or if we can find activities in between 
    
    Args:
        main_matrix: The input adjacency matrix
        collapsed_activity: The name of the activity which should replace collapsed activities 
        collapse_activities: Set of activities which should be collapsed 
        
    Returns:
        A new adjacency matrix with the activities collapsed 
        
    Raises:
        ValueError: If activity not found
    """

    # check that new activity is not already in matrix 
    if collapsed_activity in main_matrix.activities:
        raise ValueError(f"Activity {collapsed_activity} already in matrix")
        
    # Generate variants from input matrix
    variants = generate_acceptance_variants(main_matrix)
    
    # Remove activity from variants
    modified_variants = collapse_variant_level(main_matrix, variants, collapsed_activity, collapse_activities)
    
    # Convert modified variants back to matrix
    new_matrix = variants_to_matrix(modified_variants, main_matrix.activities)
    
    return new_matrix