from itertools import permutations

# method for the parallelization, we assume the validation took place 
# activities_parallelization defines the set of activities to be parallelized 
# activity_positioning defiens the activity where the other activities are moved together at, we assume that by the previous functions it is confirmed that it is part of the activities for parallleization
def parallelize_move_activities(acceptance_sequences, activities_parallelization, activity_positioning): 

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


# method for the parallelization, we assume the validation took place 
# activities_parallelization defines the set of activities to be parallelized 
# activities_in_between describes the set of activities happening in between 
def parallelize_expand_set(acceptance_sequences, activities_parallelization, activities_in_between): 

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



# *************************************************
# define an acceptance sequence for testing 
acceptance_sequences = [['A', 'B', 'C', 'D']]



variants = parallelize_expand_set(acceptance_sequences, ['B', 'D'], ['C'])

print(variants)

            

        
        

