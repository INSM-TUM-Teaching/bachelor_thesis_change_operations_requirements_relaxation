from acceptance_skeleton import generate_skeleton
from typing import List, Optional, Tuple, Dict, Set

import utils.similarity_score as similarity_score

from adjacency_matrix import AdjacencyMatrix, parse_yaml_to_adjacency_matrix

from utils.console_helpers import banner
from utils.console_helpers import choose

from variants_to_matrix import variants_to_matrix
from acceptance_variants import generate_acceptance_variants
from utils.console_helpers import deps_to_matrix

from dependencies import ExistentialDependency, TemporalDependency, ExistentialType

from acceptance_variants import satisfies_existential_constraints
from acceptance_variants import satisfies_temporal_constraints

from itertools import product as cartesian_product

from utils.similarity_score import similarity_calculation_occurence
from utils.similarity_score import similarity_calculation_ordering

from dependencies import TemporalType, Direction

# ── Debug mode ─────────────────────────────────────────────────
from utils.debug_mode import log


def perfom_skeleton_algorithm(matrix: AdjacencyMatrix, 
                              locked_dependencies: dict, 
                              new_activity: Optional[str] = None
                              ): 
    """
    Using the skeleton staretgy perfom the adaption of the matrix, including all the communication with the user 

    Args: 
        matrix: Adjacency matrix for midfication 
        locked_dependencies: Dict of locked dependencies 

    Return: 
        modified adjacency matrix 
    """


    # we offer the user the option to choose the method to calculate the similarity score
    options = ["Pure occurence similarity score - focus on preserving existential dependencies", 
            "Pure ordering similarity score - focus on preserving temporal dependencies",
            "Combined similarity score - allowing for a balanced consideration"]
    
    similarity_strategy = choose("Choose a method to calculate the similarity score between skeleton sequences and acceptance sequences: ", options)

    if "occurence" in similarity_strategy: 
        similarity_strategy = "occurence"
    elif "ordering" in similarity_strategy: 
        similarity_strategy = "ordering"
    else: 
        similarity_strategy = "combined"

    # if an error occurs, we use the new insert opportunity 
    modified_acceptance_sequences = adapt_process(matrix, locked_dependencies, similarity_strategy, new_activity)

    # get the result by translating the modified acceptance sequences in the matrix
    result = variants_to_matrix(modified_acceptance_sequences)

    return result


def adapt_process(matrix: AdjacencyMatrix, 
                  locked_dependencies: dict, 
                  similarity_strategy: str,
                  new_activity: Optional[str] = None
                ): 
#-> AdjacencyMatrix: 
    """
    For a provided process adapt it to the locked dependencies and ensure they hold. 

    1) Build chain sets 
    2) 

    Args: 
        matrix: the adjacency matrix of the process 
        locked_dependencies: a dict of locked dependencies which must hold 
        similarity_strategy: str of the selected similarity strategy 
        new_activity: if a new activity is inserted, provide it as optional, to ensure it is used even if only temporal dependencies are provided 

    Returns: 
        adapted_matrix 
    """

    # ════════════════════════════════════════════════════════════════════════════
    #  Build chain sets 
    # ════════════════════════════════════════════════════════════════════════════

    chain_sets: List[Set[str]] = []

    # create a list of all activities with locked existential dependencies 
    all_occurence_activities = []

    # list to store all orderings 
    all_ordering_pairs = []

    # define dictionaries to store the dependencies seperatly 
    temporal_deps: Dict[Tuple[str, str], TemporalDependency] = {}
    existential_deps: Dict[Tuple[str, str], ExistentialDependency] = {}     

    # iterate through all the locked dependencies 
    for (from_act, to_act), (temp_dep, exist_dep) in locked_dependencies.items():

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

        # -------------------------
        # build chain sets 

        # only consider the activity for the chain sets, if they have an existential dependency 
        if exist_dep: 
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

        
        # -----------------------------------
        # build the ordering tuples 
        if temp_dep: 
            if temp_dep.direction == Direction.FORWARD: 
                all_ordering_pairs.append((from_act, to_act))
            elif temp_dep.direction == Direction.BACKWARD:
                all_ordering_pairs.append((to_act, from_act))
            else: 
                all_ordering_pairs.append((to_act, from_act))
                all_ordering_pairs.append((from_act, to_act))

    # deduplicate the ordering pairs while preserving order
    all_ordering_pairs = list(dict.fromkeys(all_ordering_pairs))
        
        
    log("Build the chain sets")
    log(f"Chain sets: {chain_sets} \n")

    log("Build the ordering tuples")
    log(f"Ordering tuples: {all_ordering_pairs} \n")

    # ════════════════════════════════════════════════════════════════════════════
    #  Form all possible occurence sets based on chain sets 
    # ════════════════════════════════════════════════════════════════════════════

    # define a list to store all possible occurence combinations per chain set for all chain sets 
    # defines the set of combinations which are valid (does not mean, that we need all of them)
    occurence_combinations_per_chain_set = []

    # iterate through all the chain sets 
    for chain_set in chain_sets:

        # define a list, to store for this chain set the occurence combinations
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

        for i in range(0, 1 << n):  
            current_subset_indices = []
            for j in range(n):
                if (i >> j) & 1:  
                    current_subset_indices.append(j)

            # create the subset 
            current_subset_activities = {chain_set[k] for k in current_subset_indices}

            # check if the existential constraints hold for the given subset 
            if satisfies_existential_constraints(current_subset_activities, chain_set, relevant_existential_deps):
                occurence_combinations_chain_set.append(list(current_subset_activities))

        occurence_combinations_per_chain_set.append(occurence_combinations_chain_set)

    # ════════════════════════════════════════════════════════════════════════════
    #  Mark the chain sets with IDs to keep track of them (used for empyt sets)
    #  Filter the occurences which are required and which are optional  
    #  Generate the needed acceptance sequences 
    # ════════════════════════════════════════════════════════════════════════════

    # based on the matrix generate the acceptance sequences 
    acceptance_sequences = generate_acceptance_variants(matrix)

    # create a list of all chain sets, and mark each with a unique ID
    # allows to distinguish between empty sets 
    chain_sets_combined = []
    for cs_idx, chain_set_occs in enumerate(occurence_combinations_per_chain_set):
        for occurence_chain_set in chain_set_occs:
            entry = (cs_idx, tuple(occurence_chain_set))   # tagged with cs_idx
            if entry not in chain_sets_combined:
                chain_sets_combined.append(entry)

    # ------------------------------
    # FILTER 

    # After building chain_sets_combined, before copying to unused_chain_sets:
    filtered = []
    for (cs_idx, occ_tuple) in chain_sets_combined:
        occ_list  = list(occ_tuple)
        occ_set   = set(occ_list)
        forbidden = False
        required  = False

        # iterate over all locked existential dependencies 
        for (act_a, act_b), exist_dep in existential_deps.items():
            cs_all = {a for occ in occurence_combinations_per_chain_set[cs_idx] for a in occ}
            
            # only consider existential dependencies if both activities are part of the chain set 
            if act_a not in cs_all or act_b not in cs_all:
                continue

            # get an overview of the occurence combinations in the current chain occurence 
            has_a = act_a in occ_set
            has_b = act_b in occ_set

            if has_a and has_b:
                flag = "exists_both"
            elif has_a:
                flag = "exists_only_a"
            elif has_b:
                flag = "exists_only_b"
            else:
                flag = "exists_neither"

            # from the dict of required truth values, use the falg to get if the tuple is needed 
            tv = required_truth_values(exist_dep.type)[flag]

            # forbidden by the dependency type — drop immediately
            if tv is False:    
                forbidden = True
                break
            
            # required by the dependency type — must be kept
            if tv is True:     
                required = True

            # if tv is None, we don't care, since they do not have to occur, but can occur 

        # if the occurence is forbidden, we continue 
        if forbidden:
            continue

        # if the occurence is required, we add it to set of occurence combinations which must be used 
        if required:
            filtered.append((cs_idx, occ_tuple))

        # if not required, we only keep the instances which 
        """
        elif any(
            (act_a in seq) == (act_a in occ_set) and (act_b in seq) == (act_b in occ_set)
            for (act_a, act_b) in existential_deps
            for seq in acceptance_sequences
        ):
            filtered.append((cs_idx, occ_tuple))
        """

    chain_sets_combined = filtered
    unused_chain_sets = list(chain_sets_combined)

    log(f"Chain occurence combinations which must be used: {unused_chain_sets} \n The rest is optional \n")

    # define a list to keep track of the unused ordering pairs 
    unused_ordering_pairs = all_ordering_pairs

    # copy in a list to keep track of the chain sets which were not yet used 
    unused_chain_sets = list(chain_sets_combined)

    # ════════════════════════════════════════════════════════════════════════════
    #  For each acceptance sequence find the best occurnce set & adapt & keep track of used chain sets 
    # ════════════════════════════════════════════════════════════════════════════

    # start by generating the skeleton sequences 
    # generate the skeleton sequences 
    # we use the skeleton sequences, since they present all cases
    # we do not have to use all skeleton sequences, but use chain occurneces for filtering 
    locked_deps_matrix = deps_to_matrix(locked_dependencies)
    skeleton_sequences = generate_skeleton(locked_deps_matrix)

    # check that the provided input does not have a contradiction in itself, preventing the creation of the skeleton sequences 
    if skeleton_sequences == [[]] or skeleton_sequences is None: 
        raise ValueError("There is a contradiction in the input and no skeleton can be built, please ensure the input does not contain contradictions in itself")

    # get the list of all activities of the skeleton 
    activities_in_skeleton = []

    for skeleton_sequence in skeleton_sequences: 
        for act in skeleton_sequence: 
            if act not in activities_in_skeleton and act != "_": 
                activities_in_skeleton.append(act)

    # define a list to store the new acceptance sequences 
    acceptance_sequences_new = []

    log("Phase 1 of skeleton algorithm: for each acceptance sequence find best fitting skeleton sequence")
    # iterate thorugh all acceptance sequences 
    for acceptance_sequence in acceptance_sequences: 

        # initialize the max score 
        max_sim_score_occurence = -10
        max_sim_score_ordering = -10

        max_sim_score_combined = -10

        selected_skeleton_sequence = []

        # this part needs to be converted for the acceptance sequences 
        # ----------------------------
        # iterate over all the possible skeleton sequences and select the sequence with the highest sim_score
        for skeleton_sequence in skeleton_sequences:

            # calculate the similarity score of occurence and ordering  
            sim_score_occurence = similarity_score.similarity_calculation_occurence(acceptance_sequence, skeleton_sequence, activities_in_skeleton)
            sim_score_ordering = similarity_score.similarity_calculation_ordering(acceptance_sequence, skeleton_sequence)

            # based on the selected similarity startegy, select the skeleton sequence 
            if similarity_strategy == "occurence": 
                # we search for the highest occurence sim score, if found also update the ordering 
                if sim_score_occurence > max_sim_score_occurence: 
                    max_sim_score_occurence = sim_score_occurence
                    selected_skeleton_sequence = skeleton_sequence
                    max_sim_score_ordering = sim_score_ordering
                
                # if the same sim_score for occurence, use the sim_score of ordering for detrmination 
                elif sim_score_occurence == max_sim_score_occurence:  

                    if sim_score_ordering > max_sim_score_ordering: 
                        max_sim_score_ordering = sim_score_ordering
                        selected_skeleton_sequence = skeleton_sequence
            
            elif similarity_strategy == "ordering": 
                # for the similarity score of ordering, select the skeleton sequence 
                if sim_score_ordering > max_sim_score_ordering: 
                    max_sim_score_ordering = sim_score_ordering
                    selected_skeleton_sequence = skeleton_sequence
                    max_sim_score_occurence = sim_score_occurence
                
                # if the same sim_score for occurence, use the sim_score of ordering for detrmination 
                elif sim_score_ordering == max_sim_score_ordering:  

                    if sim_score_occurence > max_sim_score_occurence: 
                        max_sim_score_occurence = sim_score_occurence
                        selected_skeleton_sequence = skeleton_sequence

            else: 
                # combined
                sim_score_combined = (sim_score_occurence + sim_score_ordering) / 2

                if sim_score_combined > max_sim_score_combined: 
                    max_sim_score_combined = sim_score_combined
                    selected_skeleton_sequence = skeleton_sequence

        # ----------------------------

        # get the contained chain sets per combined occurence set  
        contained_chain_occurence_sets = contained_occurence_chain_sets(selected_skeleton_sequence, occurence_combinations_per_chain_set)

        for contained_chain_occuence_set in contained_chain_occurence_sets: 
            if contained_chain_occuence_set in unused_chain_sets: 
                unused_chain_sets.remove(contained_chain_occuence_set)
        

        # get the contained ordering pairs per skeleton sequence 
        contained_pairs = contained_ordering_pairs(selected_skeleton_sequence, all_ordering_pairs)

        # remove all the used pairs to get an overview of the unused pairs 
        for pair in contained_pairs: 
            if pair in unused_ordering_pairs: 
                unused_ordering_pairs.remove(pair)

        if similarity_strategy == "occurence":
            used_score = max_sim_score_occurence
        elif similarity_strategy == "ordering":
            used_score = max_sim_score_ordering
        else:
            used_score = max_sim_score_combined

        log(f"Skeleton sequence: {selected_skeleton_sequence}, Acceptance sequence: {acceptance_sequence}, {similarity_strategy} similarity score: {used_score}")
        log(f"Contained chain occurence sets: {contained_chain_occurence_sets} \n")
        
        # perfom the adaption of the acceptance sequence 
        modified_variants = adapt_acceptance_sequence(acceptance_sequence, selected_skeleton_sequence, activities_in_skeleton, matrix)

        # ensure that we do not add duplicates 
        for v in modified_variants: 
            if v not in acceptance_sequences_new: 
                acceptance_sequences_new.append(v)

    log(f"Unused chain occurence sets after phase 1: {unused_chain_sets} \n")
    log(f"Unused ordering pairs after phase 1: {unused_ordering_pairs} \n")


    # ════════════════════════════════════════════════════════════════════════════
    #  For unused chain sets, find acceptance sequences 
    # ════════════════════════════════════════════════════════════════════════════

    log("Phase 2: for unused chain occurnece sets find pair of acceptance and skeleton sequence")

    for unused_chain_occurrence in list(unused_chain_sets):  # create a copy, since the list is modified mid-loop

        # already covered by a previously processed combined occurrence, we can skip it
        if unused_chain_occurrence not in unused_chain_sets:
            continue

        # find all combined occurrences that contain the unused chain occurrence
        candidate_skeleton_sequences = combined_occurrences_containing(
            unused_chain_occurrence, skeleton_sequences, occurence_combinations_per_chain_set
        )

        best_acceptance_sequence = []
        best_skel_seq = []
        max_sim_score_occurence = -10.0
        max_sim_score_ordering = -10.0
        max_sim_score_combined = -10.0

        for candidate_skel_seq in candidate_skeleton_sequences:

            # ── Select the best fitting acceptance sequence ───────────────────
            for acceptance_sequence in acceptance_sequences:

                # calculate the similarity score of occurence and ordering  
                sim_score_occurence = similarity_score.similarity_calculation_occurence(acceptance_sequence, candidate_skel_seq, activities_in_skeleton)
                sim_score_ordering = similarity_score.similarity_calculation_ordering(acceptance_sequence, candidate_skel_seq)
             
                # based on the selected similarity startegy, select the skeleton sequence 
                if similarity_strategy == "occurence": 
                    # we search for the highest occurence sim score, if found also update the ordering 
                    if sim_score_occurence > max_sim_score_occurence: 
                        max_sim_score_occurence = sim_score_occurence
                        best_acceptance_sequence = acceptance_sequence
                        best_skel_seq = candidate_skel_seq
                        max_sim_score_ordering = sim_score_ordering
                    
                    # if the same sim_score for occurence, use the sim_score of ordering for detrmination 
                    elif sim_score_occurence == max_sim_score_occurence:  

                        if sim_score_ordering > max_sim_score_ordering: 
                            max_sim_score_ordering = sim_score_ordering
                            best_acceptance_sequence = acceptance_sequence
                            best_skel_seq = candidate_skel_seq
                
                elif similarity_strategy == "ordering": 
                    # for the similarity score of ordering, select the skeleton sequence 
                    if sim_score_ordering > max_sim_score_ordering: 
                        max_sim_score_ordering = sim_score_ordering
                        best_acceptance_sequence = acceptance_sequence
                        best_skel_seq = candidate_skel_seq
                        max_sim_score_occurence = sim_score_occurence
                    
                    # if the same sim_score for occurence, use the sim_score of ordering for detrmination 
                    elif sim_score_ordering == max_sim_score_ordering:  

                        if sim_score_occurence > max_sim_score_occurence: 
                            max_sim_score_occurence = sim_score_occurence
                            best_acceptance_sequence = acceptance_sequence
                            best_skel_seq = candidate_skel_seq

                else: 
                    # combined
                    sim_score_combined = (sim_score_occurence + sim_score_ordering) / 2

                    if sim_score_combined > max_sim_score_combined: 
                        max_sim_score_combined = sim_score_combined
                        best_acceptance_sequence = acceptance_sequence
                        best_skel_seq = candidate_skel_seq
                

        contained_chain_occurence_sets = contained_occurence_chain_sets(best_skel_seq, occurence_combinations_per_chain_set)

        for contained_chain_occuence_set in contained_chain_occurence_sets: 
            if contained_chain_occuence_set in unused_chain_sets: 
                unused_chain_sets.remove(contained_chain_occuence_set)

        # get the contained ordering pairs per skeleton sequence 
        contained_pairs = contained_ordering_pairs(selected_skeleton_sequence, all_ordering_pairs)

        # remove all the used pairs to get an overview of the unused pairs 
        for pair in contained_pairs: 
            if pair in unused_ordering_pairs: 
                unused_ordering_pairs.remove(pair)

        if similarity_strategy == "occurence":
                used_score = max_sim_score_occurence
        elif similarity_strategy == "ordering":
            used_score = max_sim_score_ordering
        else:
            used_score = max_sim_score_combined

        log(f"Occurence set: {best_skel_seq}, Acceptance sequence: {best_acceptance_sequence}, {similarity_strategy} similarity score: {used_score}")
        log(f"Contained chain occurence sets: {contained_chain_occurence_sets} \n")

        # perfom the adaption of the acceptance sequence 
        modified_variants = adapt_acceptance_sequence(best_acceptance_sequence, best_skel_seq, activities_in_skeleton, matrix)

        # ensure that we do not add duplicates 
        for v in modified_variants: 
            if v not in acceptance_sequences_new: 
                acceptance_sequences_new.append(v)
    
    # ════════════════════════════════════════════════════════════════════════════
    #  For unused ordering pairs, find acceptance sequences 
    # ════════════════════════════════════════════════════════════════════════════

    log("Phase 4: for unused ordering pairs find pair of acceptance and skeleton sequence")

    for unused_ordering_pair in list(unused_ordering_pairs):  # create a copy, since the list is modified mid-loop

        # already covered by a previously processed combined occurrence, we can skip it
        if unused_ordering_pair not in unused_ordering_pairs:
            continue

        # find all combined occurrences that contain the unused chain occurrence
        candidate_skeleton_sequences = sequences_containing_pairs(skeleton_sequences, unused_ordering_pair)

        best_acceptance_sequence = []
        best_skel_seq = []
        max_sim_score_occurence = -10.0
        max_sim_score_ordering = -10.0
        max_sim_score_combined = -10.0

        for candidate_skel_seq in candidate_skeleton_sequences:

            # ── Select the best fitting acceptance sequence ───────────────────
            for acceptance_sequence in acceptance_sequences:

                # calculate the similarity score of occurence and ordering  
                sim_score_occurence = similarity_score.similarity_calculation_occurence(acceptance_sequence, candidate_skel_seq, activities_in_skeleton)
                sim_score_ordering = similarity_score.similarity_calculation_ordering(acceptance_sequence, candidate_skel_seq)
             
                # based on the selected similarity startegy, select the skeleton sequence 
                if similarity_strategy == "occurence": 
                    # we search for the highest occurence sim score, if found also update the ordering 
                    if sim_score_occurence > max_sim_score_occurence: 
                        max_sim_score_occurence = sim_score_occurence
                        best_acceptance_sequence = acceptance_sequence
                        best_skel_seq = candidate_skel_seq
                        max_sim_score_ordering = sim_score_ordering
                    
                    # if the same sim_score for occurence, use the sim_score of ordering for detrmination 
                    elif sim_score_occurence == max_sim_score_occurence:  

                        if sim_score_ordering > max_sim_score_ordering: 
                            max_sim_score_ordering = sim_score_ordering
                            best_acceptance_sequence = acceptance_sequence
                            best_skel_seq = candidate_skel_seq
                
                elif similarity_strategy == "ordering": 
                    # for the similarity score of ordering, select the skeleton sequence 
                    if sim_score_ordering > max_sim_score_ordering: 
                        max_sim_score_ordering = sim_score_ordering
                        best_acceptance_sequence = acceptance_sequence
                        best_skel_seq = candidate_skel_seq
                        max_sim_score_occurence = sim_score_occurence
                    
                    # if the same sim_score for occurence, use the sim_score of ordering for detrmination 
                    elif sim_score_ordering == max_sim_score_ordering:  

                        if sim_score_occurence > max_sim_score_occurence: 
                            max_sim_score_occurence = sim_score_occurence
                            best_acceptance_sequence = acceptance_sequence
                            best_skel_seq = candidate_skel_seq

                else: 
                    # combined
                    sim_score_combined = (sim_score_occurence + sim_score_ordering) / 2

                    if sim_score_combined > max_sim_score_combined: 
                        max_sim_score_combined = sim_score_combined
                        best_acceptance_sequence = acceptance_sequence
                        best_skel_seq = candidate_skel_seq
                

        # get the contained ordering pairs per skeleton sequence 
        contained_pairs = contained_ordering_pairs(selected_skeleton_sequence, all_ordering_pairs)

        # remove all the used pairs to get an overview of the unused pairs 
        for pair in contained_pairs: 
            if pair in unused_ordering_pairs: 
                unused_ordering_pairs.remove(pair)

        if similarity_strategy == "occurence":
                used_score = max_sim_score_occurence
        elif similarity_strategy == "ordering":
            used_score = max_sim_score_ordering
        else:
            used_score = max_sim_score_combined

        log(f"Skeleton sequence: {best_skel_seq}, Acceptance sequence: {best_acceptance_sequence}, {similarity_strategy} similarity score: {used_score}")

        # perfom the adaption of the acceptance sequence 
        modified_variants = adapt_acceptance_sequence(best_acceptance_sequence, best_skel_seq, activities_in_skeleton, matrix)

        # ensure that we do not add duplicates 
        for v in modified_variants: 
            if v not in acceptance_sequences_new: 
                acceptance_sequences_new.append(v)


    log(f"Unused ordering pairs after phase 1: {unused_ordering_pairs} \n")

    log(f"\nAcceptance sequences after skeleton algorithm: {acceptance_sequences_new}")
    # return the final result 
    return acceptance_sequences_new


def contained_ordering_pairs(sequence: List[str], 
                             all_ordering_pairs: List
                            ) -> List[(str)]: 
    """
    For a given sequence of activities, return the ordering pairs which are contained in it

    Args: 
        sequence: sequence of activities (ordered)
        all_ordering_pairs: list of the possible pairs for the ordering
    """

    # define list to store the contained pairs 
    contained_pairs = []

    # iterate over all pairs and check which of these are contained in the correct ordering 
    for (act_a, act_b) in all_ordering_pairs: 
        if act_a in sequence and act_b in sequence: 
            if sequence.index(act_a) < sequence.index(act_b): 
                contained_pairs.append((act_a, act_b))

    # return the result 
    return contained_pairs


def sequences_containing_pairs(all_sequences: List, 
                               ordering_pair: (str)
                               ) -> List[List[str]]: 
    """
    For a set of sequences find all sequences which contain a sepcific ordering pair. 

    Args: 
        all_seqeunces: list of all sequences, from which the sequences containing the pair should be selected 
        ordering_pair: tuple of ordered activities 

    Returns: 
        list of sequences containing the ordering pair 
    """
    # define a list to store the sequences containing the pair
    sequences_containing_pair = []

    # extract the activities from the ordering pair 
    (act_a, act_b) = ordering_pair

    # iterate over all sequences and get the set of sequences which contain the ordering pair 
    for sequence in all_sequences: 
        if act_a in sequence and act_b in sequence: 
            if sequence.index(act_a) < sequence.index(act_b): 
                sequences_containing_pair.append(sequence)
    
    # return the result 
    return sequences_containing_pair



def contained_occurence_chain_sets(
    occurence_combination: List[str],
    occurence_combinations_per_chain_set: List[List[List[str]]]
) -> List[Tuple[int, tuple]]:
    
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

    for cs_idx, chain_set_occs in enumerate(occurence_combinations_per_chain_set):
        fitting = [
            occ for occ in chain_set_occs
            if all(a in occurence_combination for a in occ)
        ]
        if fitting:
            largest = max(fitting, key=len)
            contained_occurences.append((cs_idx, tuple(largest)))  # tagged

    return contained_occurences

    

def combined_occurrences_containing(
    chain_occurrence_indexed: Tuple[int, tuple],   # (cs_idx, activities)
    all_combined_occurrences: List[List[str]],
    occurence_combinations_per_chain_set: List[List[List[str]]]
) -> List[List[str]]:
    """
    Return all combined occurrences where the slice belonging to the same
    chain set as chain_occurrence is *exactly* chain_occurrence — not a superset.

    Args:
        chain_occurrence_indexed:                     the unused chain set occurrence to match
        all_combined_occurrences:             every possible combined occurrence
        occurence_combinations_per_chain_set: valid occurrences grouped by chain set,
                                              used to identify which chain set the
                                              occurrence belongs to and which activities
                                              that chain set owns

    Returns:
        combined occurrences whose chain-set slice equals chain_occurrence exactly
    """

    cs_idx, chain_occurrence_tuple = chain_occurrence_indexed
    chain_occurrence_set = frozenset(chain_occurrence_tuple)

    # All activities owned by this chain set (union of all its valid occurrences)
    cs_activities: Set[str] = set()
    for occ in occurence_combinations_per_chain_set[cs_idx]:
        cs_activities.update(occ)

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
    matrix: AdjacencyMatrix
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
        matrix: Adjacency matrix of the process, to get temporal dependencies to preserve the structure for insertion 

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


    # ── Step 2a: Sort present anchors into skeleton order, by switching positions ──────────
    # define the list of anchors in the correct order, which are currently in the acceptance sequence  
    present_anchors_skeleton_order = [anchor for anchor in skeleton_sequence if anchor in filtered_sequence]

    # create a list with the positions where anchors are stored 
    anchor_positions = [i for i, a in enumerate(filtered_sequence) if a in present_anchors_skeleton_order]

    # caluclte an adapted list, where anchors are placed in the correct order 
    adapted: List[str] = list(filtered_sequence)
    for position, anchor in zip(anchor_positions, present_anchors_skeleton_order):
        adapted[position] = anchor

    # ── Step 2b: For anchors with direct temporal dependencies insert them correctly ──────────
    direct_pairs = []
    for i in range(len(skeleton_sequence) - 1):
        a = skeleton_sequence[i]
        b = skeleton_sequence[i + 1]
        if a != '_' and b != '_':          # adjacent anchors → DIRECT constraint
            direct_pairs.append((a, b))
    
    # for all the direct pairs, ensure they have the direct ordering 
    for (anchor_a, anchor_b) in direct_pairs: 

        # if one of the activities not in the adapted sequence, continue (will be added in the next step)
        if anchor_a not in adapted or anchor_b not in adapted: 
            continue

        # get the idx of the activities in the adapted sequence 
        idx_a = adapted.index(anchor_a)
        idx_b = adapted.index(anchor_b)

        lower_idx, upper_idx = min(idx_a, idx_b), max(idx_a, idx_b)

        # check if they already have the direct ordering 
        if upper_idx - lower_idx == 1: 
            # the activities have a distance of 1, so direct ordering 
            continue

        else: 
            # the activities do not yet have a direct ordering, need to change the positioning 
            # move upper activity directly after lower activity 

            # get the upper activity 
            upper_activity = adapted[upper_idx]

            # remove the upper activity from the process 
            adapted.remove(upper_activity)

            # insert it after the lower activity 
            adapted = adapted[:(lower_idx + 1)] + [upper_activity] + adapted[(lower_idx + 1):]


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

                # initialize the list to store the modification of the current iteration; used to see if we were able to perfom the insert 
                acceptance_sequence_current = []

                # given that both anchors are present 
                if next_anchor and prev_anchor: 
                    # check for direct dependencies to previous 
                    if missing_idx - prev_anchor_idx == 1: 
                        # direct temporal dependency, so add the missing_anchor directly after the activity 
                        acceptance_sequence_current = acceptance_sequence[:(prev_anchor_idx_acc+1)] + [missing_anchor] + acceptance_sequence[(prev_anchor_idx_acc+1):]
                        current_acceptance_sequences.append(acceptance_sequence_current)

                    elif next_anchor_idx - missing_idx == 1:
                        # direct temoporal dependency, so add the missing_anchor directly before the activity   
                        acceptance_sequence_current = acceptance_sequence[:next_anchor_idx_acc] + [missing_anchor] + acceptance_sequence[next_anchor_idx_acc:]
                        current_acceptance_sequences.append(acceptance_sequence_current)
                    
                    else: 
                        # all different positions to be inserted 
                        for i in range (prev_anchor_idx_acc + 1, next_anchor_idx_acc + 1): 
                            if _valid_insertion_position(acceptance_sequence, missing_anchor, i, matrix):
                                acceptance_sequence_current = acceptance_sequence[:i] + [missing_anchor] + acceptance_sequence[i:]
                                current_acceptance_sequences.append(acceptance_sequence_current)
                        
                        # if none of the insertion positions was valid, insert at all of them 
                        if acceptance_sequence_current == []: 
                            for i in range (prev_anchor_idx_acc + 1, next_anchor_idx_acc + 1): 
                                acceptance_sequence_current = acceptance_sequence[:i] + [missing_anchor] + acceptance_sequence[i:]
                                current_acceptance_sequences.append(acceptance_sequence_current)

                elif next_anchor and not prev_anchor: 
                    # beginning of the acceptance sequence 

                    # check for a direct temporal dependency 
                    if next_anchor_idx - missing_idx == 1:
                        # direct temoporal dependency, so add the missing_anchor directly before the activity   
                        acceptance_sequence_current = acceptance_sequence[:next_anchor_idx_acc] + [missing_anchor] + acceptance_sequence[next_anchor_idx_acc:]
                        current_acceptance_sequences.append(acceptance_sequence_current)
                    else: 
                        # no direct temporal dependency but only eventual, all positions before are possible 
                        for i in range (0, next_anchor_idx_acc + 1): 
                            if _valid_insertion_position(acceptance_sequence, missing_anchor, i, matrix):
                                acceptance_sequence_current = acceptance_sequence[:i] + [missing_anchor] + acceptance_sequence[i:]
                                current_acceptance_sequences.append(acceptance_sequence_current)

                        # if no insertion position was valid, use all the insertion positions 
                        if acceptance_sequence_current == []: 
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
                            if _valid_insertion_position(acceptance_sequence, missing_anchor, i, matrix):
                                acceptance_sequence_current = acceptance_sequence[:i] + [missing_anchor] + acceptance_sequence[i:]
                                current_acceptance_sequences.append(acceptance_sequence_current)

                            # if no of the insertion positions was valid, use all of them 
                            if acceptance_sequence_current == []:
                                for i in range (prev_anchor_idx_acc + 1, len(acceptance_sequence) + 1): 
                                    acceptance_sequence_current = acceptance_sequence[:i] + [missing_anchor] + acceptance_sequence[i:]
                                    current_acceptance_sequences.append(acceptance_sequence_current)

                else: 
                    # no anchors present, so wen insert at all possible positions 
                    for i in range (0, len(acceptance_sequence) + 1): 
                        if _valid_insertion_position(acceptance_sequence, missing_anchor, i, matrix):
                            acceptance_sequence_current = acceptance_sequence[:i] + [missing_anchor] + acceptance_sequence[i:]
                            current_acceptance_sequences.append(acceptance_sequence_current)

                    # if no of the insertion positions was valid with regard to the process, use all of the positions
                    if acceptance_sequence_current == []: 
                        for i in range (0, len(acceptance_sequence) + 1): 
                            acceptance_sequence_current = acceptance_sequence[:i] + [missing_anchor] + acceptance_sequence[i:]
                            current_acceptance_sequences.append(acceptance_sequence_current)





            # add the added anchor to the list of activities present in the process 
            present_anchors_skeleton_order.append(missing_anchor)

            # overwrite the lists, so that we get the correct list to be used with each iteration 
            acceptance_sequences_new = current_acceptance_sequences

    # return the final set of obtained acceptance sequences 
    return acceptance_sequences_new


def _valid_insertion_position(
    acceptance_sequence: List[str],
    activity: str,
    index: int,
    matrix: AdjacencyMatrix,
) -> bool:
    """
    For a provided insertion position, check if it is valid regarding the temporal dependencies provided from the process 

    Args: 
        acceptance_sequence: acceptance sequence, in which the activity should be inserted 
        activity: activity for insertion 
        index: integer of the position for insertion 
        matrix: adjacency matrix to get the temporal dependencies 

    Returns: 
        True if the insertion is valid, False when the insertion is not valid 
    """

    # extract the sequence of activities happening before and the sequence of activities happening after 
    before_sequence = acceptance_sequence[:index]
    after_sequence = acceptance_sequence[index:] 

    # check for each activity of the before sequence, if it happens before the activity or is temporally independent 
    for before_act in before_sequence: 

        # get the dependency between the activities 
        dep = matrix.get_dependency(before_act, activity)

        if dep is None: 
            continue
        else: 
            temp_dep, _ = dep

        # if no dependency provided, skip 
        if temp_dep is None: 
            continue

        # check for the valid dependency types eventual dependecy forward, direct forwrad, independence 
        is_eventual_forward = (
            temp_dep.type      == TemporalType.EVENTUAL
            and temp_dep.direction == Direction.FORWARD
        )

        is_direct_forward = (
            temp_dep.type      == TemporalType.DIRECT
            and temp_dep.direction == Direction.FORWARD
        )

        is_independent = temp_dep.type == TemporalType.INDEPENDENCE

        # check if it is one of these types, if that is the case: continue
        # otherwise return False since insertion does not match the process structure 
        if is_eventual_forward or is_direct_forward or is_independent: 
            continue
        else: 
            return False
        
    # check for each activity of the after sequence, if it happens after the activity or is temporally independent 
    for after_activity in after_sequence: 

        # get the dependency between the activities 
        dep = matrix.get_dependency(activity, after_activity)

        if dep is None: 
            continue
        else: 
            temp_dep, _ = dep

        # if no dependency provided, skip 
        if temp_dep is None: 
            continue

        # check for the valid dependency types eventual dependecy forward, direct forwrad, independence 
        is_eventual_forward = (
            temp_dep.type      == TemporalType.EVENTUAL
            and temp_dep.direction == Direction.FORWARD
        )

        is_direct_forward = (
            temp_dep.type      == TemporalType.DIRECT
            and temp_dep.direction == Direction.FORWARD
        )

        is_independent = temp_dep.type == TemporalType.INDEPENDENCE

        # check if it is one of these types, if that is the case: continue
        # otherwise return False since insertion does not match the process structure 
        if is_eventual_forward or is_direct_forward or is_independent: 
            continue
        else: 
            return False
        
    # if all the checks passed, the position is possible regarding the process structure 
    return True


def required_truth_values(dep_type: ExistentialType) -> dict:
    """
    Returns which truth values MUST be True for the discovery algorithm
    to correctly identify the given dependency type.
    Maps directly to get_existential_relation() in variants_to_matrix.py.
    """
    # Key: flag name → True = must appear, False = must NOT appear, None = don't care
    return {
        ExistentialType.EQUIVALENCE: {
            "exists_both":    True,   # required
            "exists_only_a":  False,  # forbidden
            "exists_only_b":  False,  # forbidden
            "exists_neither": None,   # don't care — optional
        },
        ExistentialType.IMPLICATION: {  # direction FORWARD: a→b
            "exists_both":    True,   # required
            "exists_only_a":  False,  # forbidden
            "exists_only_b":  True,   # required
            "exists_neither": None,   # don't care
        },
        ExistentialType.NEGATED_EQUIVALENCE: {
            "exists_both":    False,  # forbidden
            "exists_only_a":  True,   # required
            "exists_only_b":  True,   # required
            "exists_neither": False,  # forbidden
        },
        ExistentialType.NAND: {
            "exists_both":    False,  # forbidden
            "exists_only_a":  True,   # don't care
            "exists_only_b":  True,   # don't care
            "exists_neither": True,   # don't care
        },
        ExistentialType.OR: {
            "exists_both":    True,   # don't care
            "exists_only_a":  True,   # don't care
            "exists_only_b":  True,   # don't care
            "exists_neither": False,  # forbidden — OR requires at least one always present
        },
        ExistentialType.INDEPENDENCE: {
            "exists_both":    True,  # None
            "exists_only_a":  True,  # None
            "exists_only_b":  True,  # None
            "exists_neither": True,   # all don't care
        },
    }[dep_type]


def occurrence_is_needed(
    occ: List[str],
    act_a: str,
    act_b: str,
    dep_type: ExistentialType,
    original_acceptance_sequences: List[List[str]],
) -> bool:
    """
    Using the discovery algorithm truth-value logic, decide whether
    an occurrence combination must be kept in the chain set.

    Rules:
      - FORBIDDEN  → always drop
      - REQUIRED   → always keep
      - DON'T CARE → keep only if reachable in the original process
    """
    occ_set = set(occ)
    has_a = act_a in occ_set
    has_b = act_b in occ_set

    # Map this occurrence to one of the four truth-value flags
    if has_a and has_b:
        flag = "exists_both"
    elif has_a:
        flag = "exists_only_a"
    elif has_b:
        flag = "exists_only_b"
    else:
        flag = "exists_neither"

    tv = required_truth_values(dep_type)[flag]

    if tv is False:   # forbidden by the dependency type
        return False
    if tv is True:    # required to identify the dependency type
        return True

    # tv is None → don't care: keep only if reachable in original process
    return any(
        (act_a in seq) == has_a and (act_b in seq) == has_b
        for seq in original_acceptance_sequences
    )