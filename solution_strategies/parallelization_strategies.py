from itertools import permutations
from typing import List

def parallelize_move_activities(acceptance_sequences: List[str], 
                                activities_parallelization: List[str], 
                                activity_positioning: str
                                ) -> List[List[str]]: 
    """
    Parallelize a set of activities, by moving the activities all to one selected activity. 

    1) Iterate over all acceptance sequences 
        1.1) if the activity for positioning is contained, replace it with all permutations of the activities for parallelization 
        1.2) remove all other activities for parallelize from the sequence 
    2) Return the list of modified acceptance sequences 
    
    Args: 
        acceptance_sequences: list of acceptance sequences of the process 
        activities_parallelization: defines the list of activities to be parallelized
        activity_positioning: activity at which the parallelized fragment is positioned 

    Returns: 
        List[List[str]]: modified acceptance sequences 
    
    """

     # empty list to store the new acceptance sequences after the parallelization 
    acceptance_sequences_modified = []

    # generate the permutations 
    perms = [list(p) for p in permutations(activities_parallelization, len(activities_parallelization))]

    for acceptance_sequence in acceptance_sequences: 
        # if the activity is contained, replace it by all permutations 
        if activity_positioning in acceptance_sequence: 
            # remove all other activities, except the activity to be replaced 
            seq_without_others = [a for a in acceptance_sequence if a not in activities_parallelization or a == activity_positioning]

            # index of the anchor activity 
            idx = seq_without_others.index(activity_positioning)

            # replace the anchor activity with each of the permutations 
            for perm in perms: 
                new_seq = seq_without_others[:idx] + perm + seq_without_others[idx + 1:]

                # verify that we do not have duplicates 
                if new_seq not in acceptance_sequences_modified: 
                    acceptance_sequences_modified.append(new_seq)

        # if the activity is not contained, remove all the other activities of the list activities_parallelization
        else: 
            # remove all other activities 
            seq_without_others = [a for a in acceptance_sequence if a not in activities_parallelization]

            # verify that we do not get duplicates 
            if seq_without_others not in acceptance_sequences_modified:
                acceptance_sequences_modified.append(seq_without_others)

    return acceptance_sequences_modified


def parallelize_expand_set(acceptance_sequences: List[List[str]], 
                           activities_parallelization: List[str], 
                           activities_in_between: List[str]
                           ) -> List[List[str]]: 
    """
    Parallelize the set of activities by inclduing the activities happening in between in the set for parallelization  

    1) Expand the set for parallelization by the activities happening in between 
    2) Iterate over each acceptance sequence 
        2.1) Replace the first occurrence of an activity for parallelization, with all permutations of the activities for parallelize 
        2.2) Delete all other activities for parallelization from the sequence 
    3) Return the list of modified acceptance sequences

    Args: 
        acceptance_sequences: List of acceptance seqeunces of the process 
        activities_collapse: List of activities for parallelization
        activities_in_between: List of activities happening between the activities for parallelization 

    Returns: 
        List[List[str]]: Modified acceptance seqeunces 
    """

    # define the new set of activities to be parallelized 
    activities_parallelization = activities_parallelization + activities_in_between

    # generate the permutations 
    perms = [list(p) for p in permutations(activities_parallelization, len(activities_parallelization))]

    # define the new acceptance sequences 
    new_acceptance_sequences = []

    for acceptance_seqeunce in acceptance_sequences:
        # define variable to save the position of the first occurence 
        pos = -1
        # copy to create a variant without the activities for parallelization
        variant_without_parallels = acceptance_seqeunce.copy()

        # get the pos of the first activity of the activity for parallelization
        for activity in activities_parallelization:
            if activity in acceptance_seqeunce:
                # if it is the first occurence, save the position 
                if pos == -1:
                    pos = acceptance_seqeunce.index(activity)
                # remove the activity 
                variant_without_parallels.remove(activity)
        # if none of the activities was contained, we can just add the sequence without modifcations
        if pos == -1:
            new_acceptance_sequences.append(acceptance_seqeunce.copy())
            continue
        # insert the permutations
        for permutation in perms:
            new_acceptance_sequence = variant_without_parallels.copy()
            for activity in permutation:
                new_acceptance_sequence.insert(pos, activity)

            # check that we do not have duplicates in acceptance sequences 
            if new_acceptance_sequence not in new_acceptance_sequences: 
                new_acceptance_sequences.append(new_acceptance_sequence)

    return new_acceptance_sequences


            

        
        

