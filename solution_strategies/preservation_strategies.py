from acceptance_skeleton import generate_skeleton
from typing import List, Optional, Tuple, Dict, Set

import utils.similarity_score as similarity_score

from adjacency_matrix import AdjacencyMatrix, parse_yaml_to_adjacency_matrix

from utils.console_helpers import banner
from utils.console_helpers import choose

from variants_to_matrix import variants_to_matrix
from acceptance_variants import generate_acceptance_variants
from utils.console_helpers import deps_to_matrix

from dependencies import ExistentialDependency, TemporalDependency

from acceptance_variants import satisfies_existential_constraints
from acceptance_variants import satisfies_temporal_constraints

from itertools import product as cartesian_product

from utils.similarity_score import similarity_calculation_occurence
from utils.similarity_score import similarity_calculation_ordering



def adapt_process(matrix: AdjacencyMatrix, 
                  locked_dependencies:AdjacencyMatrix
                ): 
#-> AdjacencyMatrix: 
    """
    For a provided process adapt it to the locked dependencies and ensure they hold. 

    1) Build chain sets 
    2) 

    Args: 
        matrix: the adjacency matrix of the process 
        locked_dependencies: a dict of locked dependencies which must hold 

    Returns: 
        adapted_matrix 
    """

    # ════════════════════════════════════════════════════════════════════════════
    #  Build chain sets 
    # ════════════════════════════════════════════════════════════════════════════

    chain_sets: List[Set[str]] = []

    # create a list of all activities with locked existential dependencies 
    all_occurence_activities = []

    # define dictionaries to store the dependencies seperatly 
    temporal_deps: Dict[Tuple[str, str], TemporalDependency] = {}
    existential_deps: Dict[Tuple[str, str], ExistentialDependency] = {}     

    # iterate through all the locked dependencies 
    for (from_act, to_act), (temp_dep, exist_dep) in locked_dependencies.dependencies.items():

        # create the dicts of dependencies 
        if temp_dep:
            temporal_deps[(from_act, to_act)] = temp_dep
        if exist_dep:
            existential_deps[(from_act, to_act)] = exist_dep

        # create a list of all activities with locked existential dependencies 
        if from_act not in all_occurence_activities: 
            all_occurence_activities.append(from_act)
        
        if to_act not in all_occurence_activities: 
            all_occurence_activities.append(to_act)

        # We skip all the pairs of activities, where only the temporal dependency is locked 
        if exist_dep is None:
            continue

        # Find the indices of all chain sets that contain either activity
        containing_indices = [
            i for i, cs in enumerate(chain_sets)
            if from_act in cs or to_act in cs
        ]

        if not containing_indices:
            # Neither activity is known yet → open a new chain set
            chain_sets.append({from_act, to_act})

        elif len(containing_indices) == 1:
            # One chain set already contains one activity → add the other
            chain_sets[containing_indices[0]].update({from_act, to_act})

        else:
            # Activities sit in different chain sets → merge them all into one
            # Iterate in reverse so that popping by index does not shift
            # the positions of indices we have not yet removed
            merged: Set[str] = {from_act, to_act}
            for i in sorted(containing_indices, reverse=True):
                merged.update(chain_sets[i])
                chain_sets.pop(i)
            chain_sets.append(merged)

    # ════════════════════════════════════════════════════════════════════════════
    #  Form all possible occurence sets based on chain sets 
    # ════════════════════════════════════════════════════════════════════════════

    occurence_combinations_per_chain_set = []

    # iterate thorigh all the chain sets 
    for chain_set in chain_sets:

        occurence_combinations_chain_set = []

        # from the existential deps, filter the relevant ones 
        relevant_existential_deps = {
            (s, t): dep
            for (s, t), dep in existential_deps.items()
            if s in chain_set and t in chain_set
        }


        # build all possible permutations for each chain_set 
        chain_set = list(chain_set)

        n = len(chain_set)

        for i in range(0, 1 << n):  # 2^n subsets, skip empty set
            current_subset_indices = []
            for j in range(n):
                if (i >> j) & 1:  # Check if j-th bit is set
                    current_subset_indices.append(j)

            # create the subset 
            current_subset_activities = {chain_set[k] for k in current_subset_indices}

            # check if the existential constraints hold for the given subset 
            if satisfies_existential_constraints(current_subset_activities, chain_set, relevant_existential_deps):
                occurence_combinations_chain_set.append(list(current_subset_activities))

        occurence_combinations_per_chain_set.append(occurence_combinations_chain_set)

    # ════════════════════════════════════════════════════════════════════════════
    #  Generate the dictionary of chain sets to keep track 
    #  Generate all possible occurence combinations 
    # ════════════════════════════════════════════════════════════════════════════

    # list to store all the chain set occurence combinations which were already used 
    used_chain_set_occurence_combinations = []

    chain_sets_combined = []

    for chain_set in occurence_combinations_per_chain_set: 
        for occurence_chain_set in chain_set: 
            if occurence_chain_set not in chain_sets_combined: 
                chain_sets_combined.append(occurence_chain_set)
    
    print(chain_sets_combined)

    unused_chain_sets = chain_sets_combined
            

    # generate all the combined occurence combinations 
    all_combined_occurrences: List[List[str]] = [
        [act for occ_set in combination for act in occ_set]
        for combination in cartesian_product(*occurence_combinations_per_chain_set)
    ]

    print(all_combined_occurrences)

    # ════════════════════════════════════════════════════════════════════════════
    #  For each acceptance sequence find the best occurnce set & adapt & keep track of used chain sets 
    # ════════════════════════════════════════════════════════════════════════════

    # based on the matrix generate the acceptance sequences 
    acceptance_sequences = generate_acceptance_variants(matrix)

    # iterate thorugh all acceptance sequences 
    for acceptance_sequence in acceptance_sequences: 

        # initialize the max score 
        max_sim_score_occurence = -10
        max_sim_score_ordering = -10

        max_sim_score_combined = -10

        selected_occurence_set = []

        for occurence_set in all_combined_occurrences: 

            # perfom similarity calculation 
            sim_score_occurence = similarity_calculation_occurence(acceptance_sequence, occurence_set, all_occurence_activities)
            
            if sim_score_occurence > max_sim_score_occurence: 
                max_sim_score_occurence = sim_score_occurence
                selected_occurence_set = occurence_set

        # get the contained chain sets per combined occurence set  
        contained_chain_occurence_sets = contained_occurence_chain_sets(selected_occurence_set, occurence_combinations_per_chain_set)

        for contained_chain_occuence_set in contained_chain_occurence_sets: 
            if contained_chain_occuence_set in unused_chain_sets: 
                unused_chain_sets.remove(contained_chain_occuence_set)

        print(f"Occurence set: {selected_occurence_set}, Acceptance sequence: {acceptance_sequence}, sim score: {max_sim_score_occurence}")
        # TODO - perfom adaption 

    print(f"Unsused chain occurence sets: {unused_chain_sets}")


    # ════════════════════════════════════════════════════════════════════════════
    #  For unused chain sets, find acceptance sequences 
    # ════════════════════════════════════════════════════════════════════════════

    print("#################")

    adapted_sequences: List[List[str]] = []

    for unused_chain_occurrence in list(unused_chain_sets):  # create a copy, since the list is modified mid-loop

        # already covered by a previously processed combined occurrence, we can skip it
        if unused_chain_occurrence not in unused_chain_sets:
            continue

        # find all combined occurrences that contain the unused chain occurrence
        candidate_combined_occurrences = combined_occurrences_containing(
            unused_chain_occurrence, all_combined_occurrences, occurence_combinations_per_chain_set
        )

        print(f"candidates: {candidate_combined_occurrences}")

        for candidate_combined_occ in candidate_combined_occurrences:

            # ── Select the best fitting acceptance sequence ───────────────────
            best_acceptance_sequence = []
            best_combined_occ = []
            max_sim_score_occurence = -10.0
            max_sim_score_ordering = -10.0

            for acceptance_sequence in acceptance_sequences:

                sim_score_occurence = similarity_calculation_occurence(acceptance_sequence, candidate_combined_occ, all_occurence_activities)
                
                if sim_score_occurence > max_sim_score_occurence:
                    max_sim_score_occurence = sim_score_occurence
                    best_acceptance_sequence = acceptance_sequence
                    best_combined_occ = candidate_combined_occ

            
        contained_chain_occurence_sets = contained_occurence_chain_sets(best_combined_occ, occurence_combinations_per_chain_set)

        for contained_chain_occuence_set in contained_chain_occurence_sets: 
            if contained_chain_occuence_set in unused_chain_sets: 
                unused_chain_sets.remove(contained_chain_occuence_set)

        print(f"Occurence set: {best_combined_occ}, Acceptance sequence: {best_acceptance_sequence}, sim score: {max_sim_score_occurence}")
        # TODO - perform adaption 


def contained_occurence_chain_sets(
    occurence_combination: List[str],
    occurence_combinations_per_chain_set: List[List[List[str]]]
) -> List[List[str]]:
    """
    For a given occurrence combination, return for each chain set the largest
    occurrence that is fully contained in the combination.

    'Contained' means every activity in the occurrence appears in the combination.
    Per chain set only the largest fitting occurrence is returned, so if both
    [A, C] and [A] fit, only [A, C] is included in the result.

    Args:
        occurence_combination:              the selected combined occurrence
        occurence_combinations_per_chain_set: valid occurrences grouped by chain set

    Returns:
        list with one entry per chain set: the largest fitting occurrence,
        or nothing for that chain set if no occurrence fits.
    """
    contained_occurences = []

    for chain_set_occs in occurence_combinations_per_chain_set:

        # Find all occurrences from this chain set that fit in the combination.
        fitting = [
            occ for occ in chain_set_occs
            if all(a in occurence_combination for a in occ)
        ]

        if fitting:
            # Per chain set keep only the largest fitting occurrence.
            largest = max(fitting, key=len)
            contained_occurences.append(largest)

    return contained_occurences


def combined_occurrences_containing(
    chain_occurrence: List[str],
    all_combined_occurrences: List[List[str]],
    occurence_combinations_per_chain_set: List[List[List[str]]]
) -> List[List[str]]:
    """
    Return all combined occurrences where the slice belonging to the same
    chain set as chain_occurrence is *exactly* chain_occurrence — not a superset.

    Args:
        chain_occurrence:                     the unused chain set occurrence to match
        all_combined_occurrences:             every possible combined occurrence
        occurence_combinations_per_chain_set: valid occurrences grouped by chain set,
                                              used to identify which chain set the
                                              occurrence belongs to and which activities
                                              that chain set owns

    Returns:
        combined occurrences whose chain-set slice equals chain_occurrence exactly
    """

    chain_occurrence_set = frozenset(chain_occurrence)

    # Identify which chain set this occurrence belongs to, and collect all
    # activities owned by that chain set (union of all its valid occurrences).
    # Any activity in a non-empty occurrence uniquely pins the chain set,
    # since each activity belongs to exactly one chain set.
    cs_activities: Set[str] = set()
    found = False

    for chain_set_occs in occurence_combinations_per_chain_set:
        candidate_cs_activities = set()
        for occ in chain_set_occs:
            candidate_cs_activities.update(occ)

        if chain_occurrence_set <= candidate_cs_activities or chain_occurrence_set == frozenset():
            # Check if this chain set actually has this occurrence as a valid entry
            if any(frozenset(occ) == chain_occurrence_set for occ in chain_set_occs):
                cs_activities = candidate_cs_activities
                found = True
                break

    if not found:
        return []

    # For each combined occurrence, extract the slice that belongs to this chain
    # set and check whether it equals chain_occurrence exactly.
    result = []
    for combined_occ in all_combined_occurrences:
        cs_slice = frozenset(act for act in combined_occ if act in cs_activities)
        if cs_slice == chain_occurrence_set:
            result.append(combined_occ)

    return result


# for a single acceptance sequence, adapt it to an occurenece set and in the second step ensure compliance with the temporal dependencies 
def adapt_acceptance_sequence(
    acceptance_sequence: List[str],
    skeleton_sequence: List[str],
    activities_in_skeleton: List[str],
) -> List[List[str]]:
    """
    Adapt an acceptance sequence to conform to the selected skeleton sequence.

    The algorithm proceeds in three steps:
      1. Remove anchor activities that belong to other skeleton sequences but
         not to the selected one.
      2. Sort the remaining selected anchors into the skeleton-prescribed order.
      3. Insert the for the skeleton sequence missing anchor activities 

    Args:
        acceptance_sequence:   The acceptance sequence to adapt.
        skeleton_sequence:     The selected skeleton sequence (anchors + placeholders).
        activities_in_skeleton: All anchor activities across all skeleton sequences, used to identify mismatched anchors in step 1.

    Returns:
        A list of adapted sequences. Contains exactly one sequence when no
        missing anchors exist, and multiple sequences otherwise.
    """

    # ── Step 1: Remove mismatched anchors ─────────────────────────────────
    # An activity is a mismatched anchor if it appears in any skeleton sequence
    # (anchor_set_all) but not in the selected skeleton sequence (anchor_set_selected).

    filtered_sequence = []

    # remove all the missmatched anchoring activities 
    for act in acceptance_sequence:
        if not (act in activities_in_skeleton and act not in skeleton_sequence):
            filtered_sequence.append(act)
    

    # ── Step 2: Sort present anchors into skeleton order ──────────
    # Only anchors that are actually present in the filtered sequence are
    # re-ordered. 
    #
    # Strategy: identify the index positions currently occupied by selected
    # anchors in the filtered sequence, then overwrite those positions with
    # the anchors in the order the skeleton prescribes.

    # define the list of anchors in the correct order, which are currently in the acceptance sequence  
    present_anchors_skeleton_order = [anchor for anchor in skeleton_sequence if anchor in filtered_sequence]

    # create a list with the positions where anchors are stored 
    anchor_positions = [i for i, a in enumerate(filtered_sequence) if a in present_anchors_skeleton_order]

    # caluclte an adapted list, where anchors are placed in the correct order 
    adapted: List[str] = list(filtered_sequence)
    for position, anchor in zip(anchor_positions, present_anchors_skeleton_order):
        adapted[position] = anchor

    # ── Step 3: Insert missing anchors ───────────────────────────
    # For each missing anchor activity (either because missing in general or because of insertion)
    # insert it at the correct position, by using other anchors as orientataion and insert in between 

    # calculate the set of missing anchors 
    missing_anchors = [a for a in skeleton_sequence if a != '_' and a not in adapted]

    acceptance_sequences_new = [adapted]
    
    # check if there are missing anchors, iff insert them 
    if missing_anchors: 

        # for each of the missing anchors, add it step by step to the acceptance sequences 
        for missing_anchor in missing_anchors: 
            
            # create a set to store the acceptance sequences of this iteration 
            current_acceptance_sequences = []

            # for each of the different variants of the acceptance sequences perform the adaption
            # we know that the anchor activities are always at the same index 
            for acceptance_sequence in acceptance_sequences_new: 

                # find neighboruing activities in skeleton sequence (if they exist), which are also in acceptanec sequence
                missing_idx = skeleton_sequence.index(missing_anchor)

                # search left in skeleton order for the nearest anchor already in adapted
                prev_anchor = next(
                    (skeleton_sequence[i] for i in range(missing_idx - 1, -1, -1)
                    if skeleton_sequence[i] in present_anchors_skeleton_order),
                    None
                )

                # search right in skeleton order for the nearest anchor already in adapted
                next_anchor = next(
                    (skeleton_sequence[i] for i in range(missing_idx + 1, len(skeleton_sequence))
                    if skeleton_sequence[i] in present_anchors_skeleton_order),
                    None
                )

                # for the neighboruing activities get the indexes
                if prev_anchor: 
                    prev_anchor_idx_acc = acceptance_sequence.index(prev_anchor)
                    prev_anchor_idx = skeleton_sequence.index(prev_anchor)

                if next_anchor: 
                    next_anchor_idx_acc = acceptance_sequence.index(next_anchor)
                    next_anchor_idx = skeleton_sequence.index(next_anchor)

                # TODO 08.05.2026
                # When inserting anchor activities, check if the original temporal dependencies can be used for insert 
                # in some cases this allows to preserve the original structure 

                # given that both anchors are present 
                if next_anchor and prev_anchor: 
                    # check for direct dependencies to previous 
                    if missing_idx - prev_anchor_idx == 1: 
                        # direct temporal dependency, so add the missing_anchor directly after the activity 
                        acceptance_sequence_current = acceptance_sequence[:(prev_anchor_idx_acc+1)] + [missing_anchor] + acceptance_sequence[(prev_anchor_idx_acc+1):]
                        current_acceptance_sequences.append(acceptance_sequence_current)

                    elif next_anchor_idx - missing_idx == 1:
                        # direct temoporal dependency, so add the missing_anchor directly before the activity   
                        acceptance_sequence_current = acceptance_sequence[:(next_anchor_idx_acc)] + [missing_anchor] + acceptance_sequence[(next_anchor_idx_acc):]
                        current_acceptance_sequences.append(acceptance_sequence_current)
                    
                    else: 
                        # all different positions to be inserted 
                        for i in range (prev_anchor_idx_acc + 1, next_anchor_idx_acc + 1): 
                            acceptance_sequence_current = acceptance_sequence[:i] + [missing_anchor] + acceptance_sequence[i:]
                            current_acceptance_sequences.append(acceptance_sequence_current)

                elif next_anchor and not prev_anchor: 
                    # beginning of the acceptance sequence 

                    # check for a direct temporal dependency 
                    if next_anchor_idx - missing_idx == 1:
                        # direct temoporal dependency, so add the missing_anchor directly before the activity   
                        acceptance_sequence_current = acceptance_sequence[:(next_anchor_idx_acc+1)] + [missing_anchor] + acceptance_sequence[(next_anchor_idx_acc+1):]
                        current_acceptance_sequences.append(acceptance_sequence_current)
                    else: 
                        # no direct temporal dependency but only eventual, all positions before are possible 
                        for i in range (0, next_anchor_idx_acc + 1): 
                            acceptance_sequence_current = acceptance_sequence[:i] + [missing_anchor] + acceptance_sequence[i:]
                            current_acceptance_sequences.append(acceptance_sequence_current)

                elif prev_anchor and not next_anchor: 
                    # end of the acceptance sequence 

                    # check for a direct temporal dependency 
                    if missing_idx - prev_anchor_idx == 1:
                        # direct temoporal dependency, so add the missing_anchor directly before the activity   
                        acceptance_sequence_current = acceptance_sequence[:(prev_anchor_idx_acc+1)] + [missing_anchor] + acceptance_sequence[(prev_anchor_idx_acc+1):]
                        current_acceptance_sequences.append(acceptance_sequence_current)
                    else: 
                        # no direct temporal dependency but only eventual, all positions before are possible 
                        for i in range (prev_anchor_idx_acc + 1, len(acceptance_sequence) + 1): 
                            acceptance_sequence_current = acceptance_sequence[:i] + [missing_anchor] + acceptance_sequence[i:]
                            current_acceptance_sequences.append(acceptance_sequence_current)

                else: 
                    # no anchors present, so wen insert at all possible positions 
                    for i in range (0, len(acceptance_sequence) + 1): 
                        acceptance_sequence_current = acceptance_sequence[:i] + [missing_anchor] + acceptance_sequence[i:]
                        current_acceptance_sequences.append(acceptance_sequence_current)


            # add the added anchor to the list of activities present in the process 
            present_anchors_skeleton_order.append(missing_anchor)

            # overwrite the lists, so that we get the correct list to be used with each iteration 
            acceptance_sequences_new = current_acceptance_sequences

    # return the final set of obtained acceptance sequences 
    return acceptance_sequences_new