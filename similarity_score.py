from typing import List, Tuple, Dict, Set
from itertools import combinations

def similarity_calculation_occurence(acceptence_sequence: List[str], skeleton_sequence: List[str], all_skeleton_activities: List[str]) -> float: 
    """
    For a given acceptance sequence and a skeleton sequence calculate the similarity score for the occurence (float) 
    1. Compare the occurences of activities in skeleton with acceptance sequence 
    2. Compare how many of the occurences are correct 
    3. Calculate based on difference a similarity score

    Args:
        acceptance_sequence: single acceptance sequence 
        skeleton_sequence: single skeleton sequence with placeholders '_'
        all_skeleton_activities: list of all activities which are part of locked / conditional dependencies 
        
    Returns:
        A similarity score of the occurence for the two seqeunces, the closer the score is to 1, the higher is the similarity  
    """

    # for the empty skeleton sequence, make a comparison 
    if skeleton_sequence == [] and acceptence_sequence == []:
        return 1.0
    elif skeleton_sequence == [] and acceptence_sequence != []: 
        return 0.0

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

    # implement a guar if there are no skeleton activities 
    if num_all_skeleton_act == 0 or num_skeleton_act == 0: 
        return 1
    else: 
        # Calculate the similarity score, optimal score is 1 for full similarity 
        return (1 - (difference / num_skeleton_act))


def similarity_calculation_ordering(acceptence_sequence: List[str], skeleton_sequence: List[str]) -> float: 
    """
    For a given acceptance sequence and a skeleton sequence calculate the similarity score for the orderings(float) 
    1. Compare the ordering of activities in acceptance sequence with skeleton sequence (we only consider the activities occuring in the acceptance sequence)
    2. Compare how many of the orderings are correct 
    3. Calculate a similarity score 

    Args:
        acceptance_sequence: single acceptance sequence 
        skeleton_sequence: single skeleton sequence with placeholders '_'
        all_skeleton_activities: list of all activities which are part of locked / conditional dependencies 
        
    Returns:
        A similarity score of the ordering for the two seqeunces, the closer the score is to 1, the higher is the similarity  
    """

    # for the empty skeleton sequence, make a comparison 
    if skeleton_sequence == [] and acceptence_sequence == []:
        return 1.0
    elif skeleton_sequence == [] and acceptence_sequence != []: 
        return 0.0
    
    # define a list to store the unique activities in the provided skeleton 
    activities_skeleton = []

    # from the skeleton get the activities, which are not a placeholder 
    for act in skeleton_sequence: 
        if act != '_' and act not in activities_skeleton and act in acceptence_sequence: 
            activities_skeleton.append(act)

    # define a variable num_combinations to count the orderings to check 
    num_combinations = 0

    # define a variable num_mis_order to count the number of wrong orderings 
    num_mis_order = 0

    # for all pairs of activities which are in the skeleton sequence and acceptance sequences iterate over them 
    for ai, aj in combinations(activities_skeleton, 2):    
        # increment the number of combinations 
        num_combinations += 1

        # check if the ordering does not match
        if (acceptence_sequence.index(ai) < acceptence_sequence.index(aj)) != (skeleton_sequence.index(ai) < skeleton_sequence.index(aj)): 
            num_mis_order += 1

    # if no combinations found, we define that the order is correct. Guard needed to prevent divisison by zero 
    if num_combinations == 0: 
        return 1
    else: 
        # calculate the similarity score 
        return (1 - (num_mis_order / num_combinations))