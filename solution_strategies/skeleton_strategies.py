from acceptance_skeleton import generate_skeleton
from typing import List, Optional, Tuple, Dict, Set

import utils.similarity_score as similarity_score

from adjacency_matrix import AdjacencyMatrix

from utils.console_helpers import choose

from variants_to_matrix import variants_to_matrix
from acceptance_variants import generate_acceptance_variants
from utils.console_helpers import deps_to_matrix

from dependencies import ExistentialDependency, TemporalDependency, ExistentialType

from acceptance_variants import satisfies_existential_constraints

from dependencies import TemporalType, Direction

# ── Debug mode ─────────────────────────────────────────────────
from utils.debug_mode import log


def perform_skeleton_algorithm(matrix: AdjacencyMatrix, 
                              locked_dependencies: dict, 
                              skip_activity: Optional[str] = None, 
                              insert_activity: Optional[str] = None
) -> AdjacencyMatrix: 
    """
    Handler for perfoming the skeleton solution staretgy. 

    1. Ask the user to select a similarity score 
    2. Adapt the process based on the selected similarity score 
    3. return the matrix  

    Args: 
        matrix: Adjacency matrix for midfication 
        locked_dependencies: Dict of locked dependencies 
        skip_activity: Activity to be skipped (optional)  

    Returns: 
        modified adjacency matrix 

    """

    # we offer the user the option to choose the method to calculate the similarity score
    options = ["Occurrence similarity score - focus on preserving existential dependencies", 
            "Ordering similarity score - focus on preserving temporal dependencies",
            "Combined similarity score - allowing for a balanced consideration"]
    
    similarity_strategy = choose("Choose a method to calculate the similarity score between skeleton sequences and acceptance sequences: ", options)

    if "occurrence" in similarity_strategy: 
        similarity_strategy = "occurrence"
    elif "ordering" in similarity_strategy: 
        similarity_strategy = "ordering"
    else: 
        similarity_strategy = "combined"

    # if an error occurs, we use the new insert opportunity 
    modified_acceptance_sequences = adapt_process(matrix, locked_dependencies, similarity_strategy, skip_activity, insert_activity)

    # get the result by translating the modified acceptance sequences in the matrix
    result = variants_to_matrix(modified_acceptance_sequences)

    return result


def adapt_process(matrix: AdjacencyMatrix, 
                  locked_dependencies: dict, 
                  similarity_strategy: str,
                  skip_activity: Optional[str] = None,
                  insert_activity: Optional[str] = None
                ) -> AdjacencyMatrix: 
    """
    For a provided process adapt it to the locked dependencies and ensure they hold. 

    1) Build occurrence combinations and ordering tuples
    2) If there is an activity to be skipped 
        2.1) If part of a locked existential dependency, ensure reflected in occurrence combinations 
    3) For each acceptance sequence find the most similar skeleton sequence and adapt it 
    4) For unused occurrence combinations, find acceptance sequences and adapt it
    5) For unused ordering pairs, find acceptance sequences and adapt it
    6) Translate the modified acceptance sequences to the matrix and return it 

    Args: 
        matrix: the adjacency matrix of the process 
        locked_dependencies: a dict of locked dependencies which must hold 
        similarity_strategy: str of the selected similarity strategy 
        skip_activity: str of an activity to be skipped (optional) 

    Returns: 
        modified acceptance sequences 
    """

    # ════════════════════════════════════════════════════════════════════════════
    #  Build occurrence combinations and ordering pairs
    # ════════════════════════════════════════════════════════════════════════════

    # create a list of all activities with locked existential dependencies 
    all_occurence_activities = []

    # list to store all orderings 
    all_ordering_pairs = []

    # defines the set of combinations which are valid (does not mean, that we need all of them)
    all_occurrence_combinations = []

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
        # build the occurrence combinations, if an existential depenency is provided 
        if exist_dep: 

            # get which truth values are required by the discovery algorithm 
            truth_values = required_truth_values(exist_dep)

            # define a dict for the mapping of occurrence combinations 
            flag_to_occ = {
                "exists_both":    [min(from_act, to_act), max(from_act, to_act)],
                "exists_only_a":  [from_act],
                "exists_only_b":  [to_act],
                "exists_neither": [],
            }

            # for each occurrence combination, check if it is required, if this is the case 
            for flag, occ in flag_to_occ.items():
                if truth_values[flag]:

                    # define the entry of required occurrence combinations and add it 
                    entry = ((min(from_act, to_act), max(from_act, to_act)), occ)

                    # ensure no duplicates are added 
                    if entry not in all_occurrence_combinations:
                        all_occurrence_combinations.append(entry)

        
        # -----------------------------------
        # build the ordering tuples, if a temporal dependency is provided  
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
        

    # log the occurrence combinations and ordering pairs (structures which must occur)
    log("Build the occurrence combinations")
    log("Each entry is (activity pair, occurrence combination): the first tuple names the activities, the second the occurrence combination")
    log(f"Occurrence combinations: {all_occurrence_combinations} \n")

    log("Build the ordering tuples")
    log(f"Ordering tuples: {all_ordering_pairs} \n")

    # ════════════════════════════════════════════════════════════════════════════
    #  Generate the needed acceptance sequences 
    # ════════════════════════════════════════════════════════════════════════════

    # based on the matrix generate the acceptance sequences 
    acceptance_sequences = generate_acceptance_variants(matrix)


    # ════════════════════════════════════════════════════════════════════════════
    #  Cover skipped activities
    # ════════════════════════════════════════════════════════════════════════════

    # if we have a skip_activity, we need adaptions 
    if skip_activity:

        # check if the skip activity has a locked existential dependnecy 
        if skip_activity in all_occurence_activities:  

            log("The activity to be skipped has locked existential dependencies")

            # iterate over all existential dependencies involving the skip_activity
            for (act_a, act_b), exist_dep in existential_deps.items():

                # only consider the canonical direction to avoid processing both directions 
                # and only consider pairs that involve the skip_activity
                if act_a > act_b or skip_activity not in (act_a, act_b):
                    continue

                # check if any required combination for this pair already excludes the skip_activity
                already_skippable = any(
                    pair == (act_a, act_b) and skip_activity not in occ_comb
                    for (pair, occ_comb) in all_occurrence_combinations
                )

                if not already_skippable:
                    # add the empty entry, which was optional beforehand 
                    empty_entry = ((act_a, act_b), [])

                    if empty_entry not in all_occurrence_combinations:
                        all_occurrence_combinations.append(empty_entry)

                        log(f"Inserted skip entry {empty_entry} for pair ({act_a}, {act_b})")


    # ---------------------------------------------------    

    # define a list to keep track of the unused ordering pairs 
    unused_ordering_pairs = list(all_ordering_pairs)

    # copy in a list to keep track of the occurrence combinations which were not yet used 
    unused_occurrence_combinations = list(all_occurrence_combinations)


    # ════════════════════════════════════════════════════════════════════════════
    #  For each acceptance sequence find the best occurnce set & adapt & keep track of used occurrence combinations 
    # ════════════════════════════════════════════════════════════════════════════
  
    # generate the skeleton sequences 
    skeleton_sequences = generate_skeleton(deps_to_matrix(locked_dependencies))

    log(f"Skeleton sequences: {skeleton_sequences}")

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

    # define occurrence activities for the similarity score, without the inserted activity, if it exists 
    # esnures that for the similarity calculation, the inserted new activity does not interfer
    sim_activities_in_skeleton = activities_in_skeleton.copy()

    if insert_activity and insert_activity in sim_activities_in_skeleton:
        sim_activities_in_skeleton.remove(insert_activity) 
        

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
            sim_score_occurence = similarity_score.similarity_calculation_occurence(acceptance_sequence, skeleton_sequence, sim_activities_in_skeleton)
            sim_score_ordering = similarity_score.similarity_calculation_ordering(acceptance_sequence, skeleton_sequence)

            # based on the selected similarity startegy, select the skeleton sequence 
            if similarity_strategy == "occurrence": 
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

        # get the contained occurrence combinations per combined occurence set  
        contained_occurence_combinations = get_contained_occurence_combinations(selected_skeleton_sequence, all_occurrence_combinations)

        for contained_occurence_combination in contained_occurence_combinations: 
            if contained_occurence_combination in unused_occurrence_combinations: 
                unused_occurrence_combinations.remove(contained_occurence_combination)
        

        # get the contained ordering pairs per skeleton sequence 
        contained_pairs = contained_ordering_pairs(selected_skeleton_sequence, all_ordering_pairs)

        # remove all the used pairs to get an overview of the unused pairs 
        for pair in contained_pairs: 
            if pair in unused_ordering_pairs: 
                unused_ordering_pairs.remove(pair)

        if similarity_strategy == "occurrence":
            used_score = max_sim_score_occurence
        elif similarity_strategy == "ordering":
            used_score = max_sim_score_ordering
        else:
            used_score = max_sim_score_combined

        log(f"Skeleton sequence: {selected_skeleton_sequence}, Acceptance sequence: {acceptance_sequence}, {similarity_strategy} similarity score: {used_score}")
        log(f"Contained occurrence combinations: {contained_occurence_combinations} \n")
        
        # perfom the adaption of the acceptance sequence 
        modified_variants = adapt_acceptance_sequence(acceptance_sequence, selected_skeleton_sequence, activities_in_skeleton, matrix)

        # ensure that we do not add duplicates 
        for v in modified_variants: 
            if v not in acceptance_sequences_new: 
                acceptance_sequences_new.append(v)

    log(f"Unused occurrence combinations after phase 1: {unused_occurrence_combinations} \n")
    log(f"Unused ordering pairs after phase 1: {unused_ordering_pairs} \n")


    # ════════════════════════════════════════════════════════════════════════════
    #  For unused occurrence combinations, find acceptance sequences 
    # ════════════════════════════════════════════════════════════════════════════

    if unused_occurrence_combinations: 
        log("Phase 2: for unused occurrence combinations find pair of acceptance and skeleton sequence")

    for unused_occurrence_combination in list(unused_occurrence_combinations):  # create a copy, since the list is modified mid-loop

        # already covered by a previously processed combined occurrence, we can skip it
        if unused_occurrence_combination not in unused_occurrence_combinations:
            continue

        # find all combined occurrences that contain the unused occurrence combinations
        candidate_skeleton_sequences = get_combined_occurrences_containing(
            unused_occurrence_combination, skeleton_sequences
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
                sim_score_occurence = similarity_score.similarity_calculation_occurence(acceptance_sequence, candidate_skel_seq, sim_activities_in_skeleton)
                sim_score_ordering = similarity_score.similarity_calculation_ordering(acceptance_sequence, candidate_skel_seq)
             
                # based on the selected similarity startegy, select the skeleton sequence 
                if similarity_strategy == "occurrence": 
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


        # get the contained occurrence combinations per combined occurence set  
        contained_occurence_combinations = get_contained_occurence_combinations(best_skel_seq, all_occurrence_combinations)

        for contained_occurence_combination in contained_occurence_combinations: 
            if contained_occurence_combination in unused_occurrence_combinations: 
                unused_occurrence_combinations.remove(contained_occurence_combination)

        # get the contained ordering pairs per skeleton sequence 
        contained_pairs = contained_ordering_pairs(best_skel_seq, all_ordering_pairs)

        # remove all the used pairs to get an overview of the unused pairs 
        for pair in contained_pairs: 
            if pair in unused_ordering_pairs: 
                unused_ordering_pairs.remove(pair)

        if similarity_strategy == "occurrence":
                used_score = max_sim_score_occurence
        elif similarity_strategy == "ordering":
            used_score = max_sim_score_ordering
        else:
            used_score = max_sim_score_combined

        log(f"Skeleton sequence: {best_skel_seq}, Acceptance sequence: {best_acceptance_sequence}, {similarity_strategy} similarity score: {used_score}")
        log(f"Contained occurrence combinations: {contained_occurence_combinations} \n")

        # perfom the adaption of the acceptance sequence 
        modified_variants = adapt_acceptance_sequence(best_acceptance_sequence, best_skel_seq, activities_in_skeleton, matrix)

        # ensure that we do not add duplicates 
        for v in modified_variants: 
            if v not in acceptance_sequences_new: 
                acceptance_sequences_new.append(v)
    
    # ════════════════════════════════════════════════════════════════════════════
    #  For unused ordering pairs, find acceptance sequences 
    # ════════════════════════════════════════════════════════════════════════════

    if unused_ordering_pairs: 
        log("Phase 3: for unused ordering pairs find pair of acceptance and skeleton sequence")

    for unused_ordering_pair in list(unused_ordering_pairs):  # create a copy, since the list is modified mid-loop

        # already covered by a previously processed combined occurrence, we can skip it
        if unused_ordering_pair not in unused_ordering_pairs:
            continue

        # find all combined occurrences that contain the unused occurrence combination
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
                sim_score_occurence = similarity_score.similarity_calculation_occurence(acceptance_sequence, candidate_skel_seq, sim_activities_in_skeleton)
                sim_score_ordering = similarity_score.similarity_calculation_ordering(acceptance_sequence, candidate_skel_seq)
             
                # based on the selected similarity startegy, select the skeleton sequence 
                if similarity_strategy == "occurrence": 
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
        contained_pairs = contained_ordering_pairs(best_skel_seq, all_ordering_pairs)

        # remove all the used pairs to get an overview of the unused pairs 
        for pair in contained_pairs: 
            if pair in unused_ordering_pairs: 
                unused_ordering_pairs.remove(pair)

        if similarity_strategy == "occurrence":
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


    log(f"Modified acceptance sequences after skeleton algorithm: {acceptance_sequences_new}")
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

    Returns: 
        List[(str)]: list with the contained ordering pairs 
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
        List[List[str]]: list of sequences containing the ordering pair 
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


def get_contained_occurence_combinations(
    sequence: List[str],
    all_occurrence_combinations: List[Tuple[Tuple[str, str], List[str]]]
) -> List[Tuple[Tuple[str, str], List[str]]]:
    
    """
    For a given sequence, return for each pair of activities, 
    the maximum contained occurrence combination.

    Args:
        sequence: the selected combined occurrence
        all_occurrence_combinations: all valid occurrences by pair of activities

    Returns:
        list with one entry per occurrence pair with the max contained occurrence combination
    """

    # initilaize list to collect all contained occurrence combinations 
    contained = []

    # collect all unique pairs
    all_pairs = list(dict.fromkeys(pair for (pair, _) in all_occurrence_combinations))

    # iterate all the pairs of activities (comparable to all required existential dependnecies)
    for pair in all_pairs:

        # get the activities from the pair 
        act1, act2 = pair 

        # get all valid occurrence combinations for the pair
        occurrence_combination_pair = [
            occ_comb for (p, occ_comb) in all_occurrence_combinations
            if p == pair
        ]

        # for each of the valid occurrence combination, identify the pair which is contained 
        for occ_comb in occurrence_combination_pair: 
            if (((act1 in occ_comb and act1 in sequence) 
                or (act1 not in occ_comb and act1 not in sequence)) 
            and ((act2 in occ_comb and act2 in sequence) 
                or (act2 not in occ_comb and act2 not in sequence))):

                # append the occurrence combination 
                contained.append((pair, occ_comb))

    return contained

    
def get_combined_occurrences_containing(
    unused_occurrence_combination: Tuple[Tuple[str, str], List[str]],  
    sequences: List[List[str]]
) -> List[List[str]]:
    """
    For an unused occurrence combination, from a list of sequences return all sequences which contain this occurrence combination 

    Args:
        unused_occurrence_combination: the unused occurrence combination to match
        sequences: the set of sequences to filter from the sequences containing the unused occurrence combination 

    Returns:
        list of sequences, which contain the unused occurrence combination exactly
    """

    # define a list for the candidate sequences 
    candidate_sequences = []

    # extract the values from the unused occurrence combination
    (act1, act2), occ_comb = unused_occurrence_combination

    # create the list of valid sequences and return it 
    return [
        sequence for sequence in sequences
        if (act1 in occ_comb) == (act1 in sequence)
        and (act2 in occ_comb) == (act2 in sequence)
    ]


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


def required_truth_values(exist_dep: ExistentialDependency) -> dict:
    """
    Returns which truth values MUST be True for the discovery algorithm to correctly identify the given dependency type.
    Maps directly to get_existential_relation() in variants_to_matrix.py.

    Args: 
        exist_dep: existential dependency consisting of a type and direction 

    Returns: 
        dict: dictionary with truth values if an occurrence combination is required 
    """

    # get the dependency type 
    dep_type = exist_dep.type

    # Key: flag name → True = must appear, False = must NOT appear, None = don't care
    base = {
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

    # exception for the case that we have an implication and we must check the direction 
    if dep_type == ExistentialType.IMPLICATION and exist_dep.direction == Direction.BACKWARD:
        base = {  # direction Backward: a <- b
            "exists_both":    True,   # required
            "exists_only_a":  True,  # required
            "exists_only_b":  False,   # forbidden
            "exists_neither": None,   # don't care
        }

    # return the final value 
    return base 