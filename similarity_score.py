from typing import List, Tuple, Dict, Set

def similarity_calculation(acceptence_sequence: List[str], skeleton_sequence: List[str], all_skeleton_activities: List[str]) -> float: 
    """
    For a given acceptance sequence and a skeleton sequence calculate the similarity score (float) 
    1. Compare the occurences of activities in skeleton with acceptance sequence 
    2. Compare how many of the orderings are correct 
    3. Combine them in a combined score

    Args:
        acceptance_sequence: single acceptance sequence 
        skeleton_sequence: single skeleton sequence with placeholders '_'
        all_skeleton_activities: list of all activities which are part of locked / conditional dependencies 
        
    Returns:
        A combined similarity score of the occurence and ordering for the two seqeunces 
    """

    # define a list to store the unique activities in the provided skeleton 
    activities_skeleton = []

    # from the skeleton get the activities, which are not a placeholder 
    for act in skeleton_sequence: 
        if act != '_' and act not in activities_skeleton: 
            activities_skeleton.append(act)
    
    # define a variable num_act_skeleton_acceptance to count
    num_act_skeleton_acceptance = 0

    # define a variable num_act_all_skeleton_acceptance to count 
    num_add_act = 0

    # define other numbers
    num_all_skeleton_act = len(all_skeleton_activities)
    num_skeleton_act = len(activities_skeleton)

    # iterate over all activities in the acceptance sequence
    for act in acceptence_sequence: 
        # check how many of the activities from the skeleton occur in the acceptance sequence 
        if act in activities_skeleton: 
            num_act_skeleton_acceptance += 1
        
        # check how many of the activities from the all_skeleton occur in the acceptance sequence but not in the skeleton sequence, so these are additional activities 
        if act in all_skeleton_activities and act not in activities_skeleton: 
            num_add_act += 1
    
    # calculate the number of activities which are different between skeleton and the acceptance sequence     
    difference = num_add_act + (num_skeleton_act - num_act_skeleton_acceptance)

    # Calculate the similarity score, optimal score is 1 for full similarity 
    similarity_score = 1 - (difference / num_skeleton_act)

    return similarity_score



