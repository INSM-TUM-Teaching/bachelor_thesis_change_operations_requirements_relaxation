from typing import List

def collapse_move_activities(acceptance_sequences: List[List[str]], 
                             activities_collapse: List[str], 
                             collapsed_activity, 
                             activity_positioning
                            ) -> List[List[str]]: 
    """
    Moves the collapsed fragment to one activity of the set to be collapsed.

    1) Iterate over all acceptance sequences 
        1.1) if the activity for positioning is contained, replace it with the collapsed activity 
        1.2) remove all other activities for collapse from the sequence 
    2) Return the list of modified acceptance sequences 
    
    Args: 
        acceptance_sequences: list of acceptance sequences of the process 
        activities_collapse: defines the list of activities to be collapsed
        collapsed_activity: new activity to be inserted for the collapsed activities 
        activity_positioning: activity at which the collapsed activity is positioned 

    Returns: 
        modified acceptance sequences 
    
    """

    # empty list to store the new acceptance sequences after the parallelization 
    acceptance_sequences_modified = []

    for acceptance_sequence in acceptance_sequences: 
        # if the activity is contained, replace it by collapsed_activity 
        if activity_positioning in acceptance_sequence: 
            # remove all other activities, except the activity to be replaced 
            seq_without_others = [a for a in acceptance_sequence if a not in activities_collapse or a == activity_positioning]

            # index of the anchor activity 
            idx = seq_without_others.index(activity_positioning)

            # replace the anchor activity with the collapsed activity 
            new_seq = seq_without_others[:idx] + [collapsed_activity] + seq_without_others[idx + 1:]

            # verify that we do not have duplicates 
            if new_seq not in acceptance_sequences_modified: 
                acceptance_sequences_modified.append(new_seq)

        # if the activity is not contained, remove all the other activities of the list activities_collapse
        else: 
            # remove all other activities 
            seq_without_others = [a for a in acceptance_sequence if a not in activities_collapse]

            # verify that we do not get duplicates 
            if seq_without_others not in acceptance_sequences_modified:
                acceptance_sequences_modified.append(seq_without_others)

    return acceptance_sequences_modified


def collapse_expand_set(acceptance_sequences: List[List[str]], 
                        activities_collapse: List[str], 
                        activities_in_between: List[str], 
                        collapsed_activity: str
                        ) -> List[List[str]]:
    """
    Collapse the set of activities by inclduing the activities happening in between in the set for collapse 

    1) Iterate over each acceptance sequence 
        1.1) Replace the first occurrence of an activity for collapse, with the collapsed activity 
        1.2) Delete all other activities for collapse from the sequence 
    2) Return the list of modified acceptance sequences

    Args: 
        acceptance_sequences: List of acceptance seqeunces of the process 
        activities_collapse: List of activities for collapse
        activities_in_between: List of activities happening between the activities for collapse 
        collapsed_activity: name of the collapsed activity 

    Returns: 
        List[List[str]]: Modified acceptance seqeunces 

    """

    # empty list to store the new acceptance sequences after the parallelization 
    new_acceptance_sequences = []

    # merge the two sets 
    activities_collapse = activities_collapse + activities_in_between

    # iterate over all the acceptance sequences and perform the modifications 
    for acceptance_seqeunce in acceptance_sequences:
        # define variable to save the position of the first occurence 
        pos = -1
        # copy to create a variant without the activities for parallelization
        variant_without_collapse = acceptance_seqeunce.copy()

        # get the pos of the first activity of the activity for parallelization
        for activity in activities_collapse:
            if activity in acceptance_seqeunce:
                # if it is the first occurence, save the position 
                if pos == -1:
                    pos = acceptance_seqeunce.index(activity)
                # remove the activity 
                variant_without_collapse.remove(activity)
        # if none of the activities was contained, we can just add the sequence without modifcations
        if pos == -1:
            new_acceptance_sequences.append(acceptance_seqeunce.copy())
            continue
        # insert the permutations
        new_acceptance_sequence = variant_without_collapse.copy()
        # insert the collapsed activity 
        new_acceptance_sequence.insert(pos, collapsed_activity)

        # check that we do not have duplicates in acceptance sequences 
        if new_acceptance_sequence not in new_acceptance_sequences: 
            new_acceptance_sequences.append(new_acceptance_sequence)

    return new_acceptance_sequences

            

        
        

