from typing import List, Set, Tuple
from adjacency_matrix import AdjacencyMatrix
from dependencies import ExistentialDependency, ExistentialType, TemporalDependency, TemporalType, Direction

def get_existential_relation(a, b, combinations) -> Tuple[ExistentialType, Direction]:
    """
    Finds existential dependency type for dependency from activity a to b

    Args:
        a: First activity
        b: Second activity
        combinations: Combinations defining the relation
        
    Returns:
        The existential type for the relation
    """
    #Check which combinations of the two activities do exist in combinations
    exists_neither = False
    exists_both = False
    exists_only_a = False
    exists_only_b = False
    for combination in combinations:
        if (a in combination) and (b in combination):
            exists_both = True
        elif (a not in combination) and (b not in combination):
            exists_neither = True
        elif (a in combination) and (b not in combination):
            exists_only_a = True
        elif (a not in combination) and (b in combination):
            exists_only_b = True
    
    #Deduce dependency type from combinations
    if (not exists_only_a) and (not exists_only_b):
        return (ExistentialType.EQUIVALENCE, Direction.BOTH)
    if not exists_only_a:
        #Add direction a->b
        return (ExistentialType.IMPLICATION, Direction.FORWARD)
    if not exists_only_b:
        #change to other direction  a<-b
        return (ExistentialType.IMPLICATION, Direction.BACKWARD)
    if (not exists_neither) and (not exists_both):
        return (ExistentialType.NEGATED_EQUIVALENCE, Direction.BOTH)
    if not exists_both:
        return (ExistentialType.NAND, Direction.BOTH)
    if not exists_neither:
        return (ExistentialType.OR, Direction.BOTH)
    return (ExistentialType.INDEPENDENCE, Direction.BOTH)

def get_temporal_relation(a, b, variants: List[List[str]]) -> Tuple[TemporalType, Direction]:
    """
    Finds temporal dependency type from dependency for activity a to b

    Args:
        a: Fist activity
        b: Second activity
        variants: Variants defining the relation
        
    Returns:
        The temporal type for the relation
    """
    #Check which relations exist
    exists_a_before_b = False
    exists_b_before_a = False
    exists_a_not_direct_before_b = False
    exists_b_not_direct_before_a = False

    for variant in variants:
        if not((a in variant) and (b in variant)):
            continue
        pos_a = variant.index(a)
        pos_b = variant.index(b)
        if pos_a < pos_b:
            exists_a_before_b = True
            if pos_a + 1 != pos_b:
                exists_a_not_direct_before_b = True
        else:
            exists_b_before_a = True
            if pos_a != pos_b + 1:
                exists_b_not_direct_before_a = True
        if (exists_a_before_b and exists_b_before_a):
            break

    #Deduce relation type from existing relations
    if exists_a_before_b and not exists_b_before_a and not exists_a_not_direct_before_b:
        return (TemporalType.DIRECT, Direction.FORWARD) #a<_d b
    if exists_a_before_b and not exists_b_before_a:
        return (TemporalType.EVENTUAL, Direction.FORWARD) #a< b
    if exists_b_before_a and not exists_a_before_b and not exists_b_not_direct_before_a:
        #add a >_d b
        return (TemporalType.DIRECT, Direction.BACKWARD)
    if exists_b_before_a and not exists_a_before_b:
        #add a > b
        return (TemporalType.EVENTUAL, Direction.BACKWARD)
    if exists_a_before_b and exists_b_before_a:
        return (TemporalType.INDEPENDENCE, Direction.BOTH)
    return (None, None)

def variants_to_matrix(variants: List[List[str]], original_activities: List[str] = None) -> AdjacencyMatrix:
    """
    Converts a list of variants into an AdjacencyMatrix.
    """

    #Get the set of activities
    activities: Set[str] = set()
    for variant in variants:
        activities.update(variant)

    if original_activities:
        original_set = set(original_activities)

        # Items that are in the original order
        ordered = [a for a in original_activities if a in activities]

        # Additional items not found in original_activities, keep their relative order
        extras = [a for a in activities if a not in original_set]

        activities_list = ordered + extras
    else:
        activities_list = list(activities)
    matrix = AdjacencyMatrix(activities_list)

    combinations = set(frozenset(variant) for variant in variants)

    for activity_a in activities:
        for activity_b in activities:
            if activity_a == activity_b:
                continue
            existential_type, existential_direction = get_existential_relation(activity_a, activity_b, combinations)
            temporal_type, temporal_direction = get_temporal_relation(activity_a, activity_b, variants)


            exist_dep = ExistentialDependency(existential_type, existential_direction)
            temp_dep = TemporalDependency(temporal_type, temporal_direction) if temporal_type is not None else None

            matrix.add_dependency(activity_a, activity_b, temp_dep, exist_dep)
    
    return matrix