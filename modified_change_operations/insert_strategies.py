from acceptance_skeleton import generate_skeleton
from typing import List, Tuple, Dict, Set

import similarity_score

def insert_variant(acceptance_sequences, activity, conditions_insertion) -> List[List[str]]: 
    """
    For the change operation insert, perform it when contradictions in the process araised earlier  
    1. Generate the skeleton based on conditions & locked dependencies 
    2. Calculate the similarity score between acceptance - and skeleton sequence 
    3. For each acceptance sequence select the matching skeleton sequence 
    4. Adapt the acceptance sequence and perform the change operation 

    Args:
        acceptance_sequences: acceptance sequences of the process for insertion 
        activity: activity to be inserted 
        conditions_insertion: dependencies which are defined for the insertion 
        
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
        # TODO
        