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

# import acceptance variants, since we can reuse most of the functions
from acceptance_variants import satisfies_existential_constraints
from acceptance_variants import satisfies_temporal_constraints
from acceptance_variants import build_permutations
from acceptance_variants import generate_acceptance_variants


def add_placeholder_activities(acceptance_skeleton: List[List[str]],
    temporal_dependencies: Dict[Tuple[str, str], TemporalDependency],
) -> List[str]:
    """
    Add placeholder activities (_) for all the positions, which could be replaced by multiple activities 
    """
    # define a list to store the mofified acceptance sequences 
    expanded_acceptance_skeleton = []

    # iterate over all the variants which were previously calculated 
    for variant in acceptance_skeleton: 

        # Guard: a single activity has no pairs to check — just wrap it in placeholders
        if len(variant) == 1:
            expanded_variant = ["_", variant[0], "_"]
            if expanded_variant not in expanded_acceptance_skeleton:
                expanded_acceptance_skeleton.append(expanded_variant)
            continue

        # define a list for the expanded variant 
        expanded_variant = ["_"]

        # for each of the variants go over all the activities 
        for i in range(len(variant) - 1): 
            # for each pair of activities located back to back, add the dependency type, if it is not direct temporal dependency, add a placeholder 
            # get the names of the activities 
            ai = variant[i]
            aj = variant[i + 1]

            # append the current activity to the expanded variant
            expanded_variant.append(ai)

            # get the dependency type between the activities, if they are temporally direct dependent, skip
            dependency = temporal_dependencies.get((ai, aj))
            if dependency.type != TemporalType.DIRECT: 
                # add a placeholder activity 
                expanded_variant.append("_")
        
        # append the last activity and a final placeholder 
        expanded_variant = expanded_variant + [aj, "_"]

        # add the modified variant to the other modified variants 
        if expanded_variant not in expanded_acceptance_skeleton: 
            expanded_acceptance_skeleton.append(expanded_variant)
    
    return expanded_acceptance_skeleton




def generate_skeleton(adj_matrix: AdjacencyMatrix) -> List[List[str]]:
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

        # create the subset 
        current_subset_activities = {activities[k] for k in current_subset_indices}

        # check if the existential constraints hold for the given subset 
        if satisfies_existential_constraints(current_subset_activities, activities, existential_deps):
            # build all permutations of the subset 
            permutations_of_subset = build_permutations(current_subset_activities)
            for seq in permutations_of_subset:
                if satisfies_temporal_constraints(seq, temporal_deps):
                    acceptance_variants.append(seq)

    # modify the acceptance sequences by adding placeholder activities 
    skeleton = add_placeholder_activities(acceptance_variants, temporal_deps)

    # add the empty acceptnace sequence 
    skeleton = skeleton + [[]]
    return skeleton   