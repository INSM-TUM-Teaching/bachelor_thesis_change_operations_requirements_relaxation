from acceptance_skeleton import generate_skeleton
from typing import List, Tuple, Dict

import similarity_score


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

                # given that both anchors are present 
                if next_anchor and prev_anchor: 
                    # TODO 
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


def insert_variants_strategy(acceptance_sequences, conditions_insertion) -> List[List[str]]: 
    """
    For the change operation insert, perform it when contradictions in the process araised earlier  
    1. Generate the skeleton based on conditions & locked dependencies 
    2. Calculate the similarity score between acceptance - and skeleton sequence 
    3. For each acceptance sequence select the matching skeleton sequence 
    4. Adapt the acceptance sequence and perform the change operation 

    Args:
        acceptance_sequences: acceptance sequences of the process for insertion 
        conditions_insertion: dependencies which are defined for the insertion, this also contains the activity to be inserted
        
    Returns:
        The modified acceptance sequences for which the insertion is performed  
    """

    # generate the skeleton sequences 
    skeleton_sequences = generate_skeleton(conditions_insertion)

    if skeleton_sequences == [[]]: 
        raise ValueError("There is a contradiction in the input and no skeleton can be built, please ensure the input does not contain contradictions in itself")

    # get the list of all activities of the skeleton 
    activities_in_skeleton = []

    # list to store the new acceptance sequences 
    acceptance_sequences_new = []

    for skeleton_sequence in skeleton_sequences: 
        for act in skeleton_sequence: 
            if act not in activities_in_skeleton and act != "_": 
                activities_in_skeleton.append(act)


    # calculate for all acceptance sequence and skeleton sequence the similarity score 
    for acceptance_sequence in acceptance_sequences:

        # initialize the max score 
        max_sim_score_occurence = -10
        max_sim_score_ordering = -10

        selected_skeleton_sequence = []

        # iterate over all the possible skeleton sequences and select the sequence with the highest sim_score
        for skeleton_sequence in skeleton_sequences:

            # calculate the similarity score of occurence  
            sim_score_occurence = similarity_score.similarity_calculation_occurence(acceptance_sequence, skeleton_sequence, activities_in_skeleton)

            # we search for the highest occurence sim score, if found also update the ordering 
            if sim_score_occurence > max_sim_score_occurence: 
                max_sim_score_occurence = sim_score_occurence
                selected_skeleton_sequence = skeleton_sequence
                max_sim_score_ordering = similarity_score.similarity_calculation_ordering(acceptance_sequence, skeleton_sequence)
            
            # if the same sim_score for occurence, use the sim_score of ordering for detrmination 
            elif sim_score_occurence == max_sim_score_occurence:  
                sim_score_ordering = similarity_score.similarity_calculation_ordering(acceptance_sequence, skeleton_sequence)

                if sim_score_ordering > max_sim_score_ordering: 
                    max_sim_score_ordering = sim_score_ordering
                    selected_skeleton_sequence = skeleton_sequence

        # perfom the adaption of the acceptance sequence 
        modified_variants = adapt_anchor_sort_reinsert(acceptance_sequence, selected_skeleton_sequence, activities_in_skeleton)

        acceptance_sequences_new = acceptance_sequences_new + modified_variants

    # return the result 
    return acceptance_sequences_new
        