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
    
    # check if there are missing anchors, iff insert them 
    if missing_anchors: 

        for missing_anchor in missing_anchors: 

            # find neighboruing activities in skeleton sequence (if they exist), which are also in acceptanec sequence
            missing_idx = skeleton_sequence.index(missing_anchor)

            # search left in skeleton order for the nearest anchor already in adapted
            prev_anchor = next(
                (skeleton_sequence[i] for i in range(missing_idx - 1, -1, -1)
                 if skeleton_sequence[i] in candidates[0]),
                None
            )

            # search right in skeleton order for the nearest anchor already in adapted
            next_anchor = next(
                (skeleton_anchors[i] for i in range(missing_idx + 1, len(skeleton_anchors))
                 if skeleton_anchors[i] in candidates[0]),
                None
            )

            # for the neighboruing activities get the indexes

            # based on the indexes calculate all possible positions in between where it can be inserted, if no distance, then we need a direct insertion 

            # insert the actvity at each of the possible positions for insertion 
            # 
            # TODO  



def insert_variant(acceptance_sequences, conditions_insertion) -> List[List[str]]: 
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

    # get the list of all activities of the skeleton 
    activities_in_skeleton = []

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
        modified_variants = adapt_anchor_sort_reinsert(acceptance_sequence, skeleton_sequence, activities_in_skeleton)
        