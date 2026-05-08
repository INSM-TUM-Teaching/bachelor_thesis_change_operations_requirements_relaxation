from acceptance_skeleton import generate_skeleton
from typing import List, Tuple, Dict, Set

import similarity_score

def _occurrence_set(skeleton_sequence: List[str]) -> frozenset:
    """
    Reduce a skeleton sequence to its set of anchor activities (no order, no placeholders).
    """
    return frozenset(a for a in skeleton_sequence if a != "_")




def adapt_anchor_sort_reinsert(
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


def adapt_acceptance_skeleton(acceptance_sequences, conditions, similarity_strategy) -> List[List[str]]: 
    """
    For the change operations (especially insert and when using locked dependencies), 
    perform it when contradictions in the process araised earlier  
    1. Generate the skeleton based on conditions & locked dependencies 
    2. Calculate the similarity score between acceptance - and skeleton sequence 
    3. For each acceptance sequence select the matching skeleton sequence 
    4. Adapt the acceptance sequence and perform the change operation 

    Args:
        acceptance_sequences: acceptance sequences of the process for insertion 
        conditions: dependencies which must hold (insertion, locked dependencies)
        similarity_strategy: str, defines which score to be used for the similarity 
        
    Returns:
        The modified acceptance sequences for which the insertion is performed  
    """

    # generate the skeleton sequences 
    skeleton_sequences = generate_skeleton(conditions)

    if skeleton_sequences == [[]] or skeleton_sequences is None: 
        raise ValueError("There is a contradiction in the input and no skeleton can be built, please ensure the input does not contain contradictions in itself")

    # get the list of all activities of the skeleton 
    activities_in_skeleton = []

    # list to store the new acceptance sequences 
    acceptance_sequences_new = []

    for skeleton_sequence in skeleton_sequences: 
        for act in skeleton_sequence: 
            if act not in activities_in_skeleton and act != "_": 
                activities_in_skeleton.append(act)

    # define a set to store all the used skeleton occurence combinations  
    used_occurence_combinations = set()

    # ----------------------------------------------
    # Phase 1 - adapt all acceptance sequences 
    # ----------------------------------------------

    # calculate for all acceptance sequence and skeleton sequence the similarity score 
    for acceptance_sequence in acceptance_sequences:

        # initialize the max score 
        max_sim_score_occurence = -10
        max_sim_score_ordering = -10

        max_sim_score_combined = -10

        selected_skeleton_sequence = []

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

        # TODO adapt that we do not consider used skeleton sequences but the skeleton occurence sets 
        # add the used skeleton sequence to the set of skeleton sequences used 
        used_occurence_combinations.add(_occurrence_set(selected_skeleton_sequence))

        # perfom the adaption of the acceptance sequence 
        modified_variants = adapt_anchor_sort_reinsert(acceptance_sequence, selected_skeleton_sequence, activities_in_skeleton)

        # ensure that we do not add duplicates 
        for v in modified_variants: 
            if v not in acceptance_sequences_new: 
                acceptance_sequences_new.append(v)

    # ----------------------------------------------
    # Phase 2 - adapt all unused skeleton sequence occurence combinations 
    # ----------------------------------------------

    # group all skeleton sequences by their occurrence combination
    combinations_to_skeletons: Dict[frozenset, List[List[str]]] = {}
    for skeleton in skeleton_sequences:
        combinations_to_skeletons.setdefault(_occurrence_set(skeleton), []).append(skeleton)


    # for all the skeleton sequences which were not used so far, find the acceptance sequence with the highest sim score 
    for combo, skeletons_in_combo in combinations_to_skeletons.items(): 

        # if the occurence combination was already used, we can skip it
        if combo in used_occurence_combinations: 
            continue 

        # initialize the max score 
        max_sim_score_occurence = -10
        max_sim_score_ordering = -10

        max_sim_score_combined = -10

        selected_acceptance_sequence = []

        for skeleton_sequence in skeletons_in_combo: 
            for acceptance_sequence in acceptance_sequences:

                # calculate the similarity score of occurence and ordering  
                sim_score_occurence = similarity_score.similarity_calculation_occurence(acceptance_sequence, skeleton_sequence, activities_in_skeleton)
                sim_score_ordering = similarity_score.similarity_calculation_ordering(acceptance_sequence, skeleton_sequence)

                
                # based on the selected similarity startegy, select the skeleton sequence 
                if similarity_strategy == "occurence": 
                    # we search for the highest occurence sim score, if found also update the ordering 
                    if sim_score_occurence > max_sim_score_occurence: 
                        max_sim_score_occurence = sim_score_occurence
                        selected_acceptance_sequence = acceptance_sequence
                        max_sim_score_ordering = sim_score_ordering
                    
                    # if the same sim_score for occurence, use the sim_score of ordering for detrmination 
                    elif sim_score_occurence == max_sim_score_occurence:  

                        if sim_score_ordering > max_sim_score_ordering: 
                            max_sim_score_ordering = sim_score_ordering
                            selected_acceptance_sequence = acceptance_sequence
                
                elif similarity_strategy == "ordering": 
                    # for the similarity score of ordering, select the skeleton sequence 
                    if sim_score_ordering > max_sim_score_ordering: 
                        max_sim_score_ordering = sim_score_ordering
                        selected_acceptance_sequence = acceptance_sequence
                        max_sim_score_occurence = sim_score_occurence
                    
                    # if the same sim_score for occurence, use the sim_score of ordering for detrmination 
                    elif sim_score_ordering == max_sim_score_ordering:  

                        if sim_score_occurence > max_sim_score_occurence: 
                            max_sim_score_occurence = sim_score_occurence
                            selected_acceptance_sequence = acceptance_sequence

                else: 
                    # combined
                    sim_score_combined = (sim_score_occurence + sim_score_ordering) / 2

                    if sim_score_combined > max_sim_score_combined: 
                        max_sim_score_combined = sim_score_combined
                        selected_acceptance_sequence = acceptance_sequence

        # perfom the adaption of the acceptance sequence 
        modified_variants = adapt_anchor_sort_reinsert(selected_acceptance_sequence, skeleton_sequence, activities_in_skeleton)

        # ensure that we do not add duplicates 
        for v in modified_variants: 
            if v not in acceptance_sequences_new: 
                acceptance_sequences_new.append(v)

    print(acceptance_sequences_new)          

    # return the result 
    return acceptance_sequences_new
        