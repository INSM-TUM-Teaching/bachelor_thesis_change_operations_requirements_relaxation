import os
import sys
import copy
import yaml
from typing import List, Tuple, Dict, Optional

# ── Core imports ────────────────────────────────────────────────────────────
from adjacency_matrix import AdjacencyMatrix, parse_yaml_to_adjacency_matrix
from dependencies import (
    TemporalDependency, ExistentialDependency,
    TemporalType, ExistentialType, Direction,
)
from variants_to_matrix import variants_to_matrix
from acceptance_variants import generate_acceptance_variants

# ── Change-operation imports ─────────────────────────────────────────────────
from change_operations.delete_operation    import delete_activity
from change_operations.insert_operation    import insert_activity
from change_operations.modify_operation    import modify_dependencies
from change_operations.move_operation      import move_activity
from change_operations.swap_operation      import swap_activities
from change_operations.skip_operation      import skip_activity
from change_operations.replace_operation   import replace_activity
from change_operations.collapse_operation  import collapse_operation
from change_operations.de_collapse_operation import decollapse_operation
from change_operations.parallelize_operation import parallelize_activities
from change_operations.condition_update    import condition_update

# ── Change-operation helper functions imports ─────────────────────────────────────────────────
from change_operations.parallelize_operation import get_activities_happening_between

# ── Change-operation solution strategies imports ─────────────────────────────────────────────────
from solution_strategies.parallelization_strategies import parallelize_expand_set
from solution_strategies.parallelization_strategies import parallelize_move_activities
from solution_strategies.collapse_strategies import collapse_expand_set
from solution_strategies.collapse_strategies import collapse_move_activities

# ── Skeleton algorithm ─────────────────────────────────────────────────
from solution_strategies.skeleton_strategies import perfom_skeleton_algorithm


# ── Helper functions ─────────────────────────────────────────────────
from utils.console_helpers import banner
from utils.console_helpers import prompt
from utils.console_helpers import choose
from utils.console_helpers import confirm
from utils.console_helpers import _dep_label
from utils.console_helpers import dep_label_temp
from utils.console_helpers import dep_label_exist
from utils.console_helpers import print_matrix
from utils.console_helpers import ask_temporal
from utils.console_helpers import ask_existential
from utils.console_helpers import ask_dependencies
from utils.console_helpers import deps_to_matrix

# ── Locked dependency functions ─────────────────────────────────────────────────
from utils.utils_lock_dependencies import get_locked_dependencies
from utils.utils_lock_dependencies import is_relaxation
from utils.utils_lock_dependencies import is_temp_relaxation
from utils.utils_lock_dependencies import is_exist_relaxation
from utils.utils_lock_dependencies import are_locked_dependencies_violated

# ── Dependency relaxation ─────────────────────────────────────────────────
from utils.dependency_relaxation import perform_dependency_relaxation


def op_collapse(matrix: AdjacencyMatrix, locked_dependencies):
    """
    Collapse a fragment and perfom the check for violated locked dependencies

    Args: 
        matrix: Adacency of the matrix to perform the change operation on 
        locked_dependencies: dict of locked dependencies

    Return: 
        modified matrix 
        locked_dependencies after potential relaxations
    """

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 1: Get the reuqired input from the user 
    # ════════════════════════════════════════════════════════════════════════════

    print(f"\n  Current activities: {matrix.activities}")

    while True: 
        collapsed_name = prompt("Name of new collapsed activity")

        if collapsed_name in matrix.activities: 
            print(f"  ✗  Activity '{collapsed_name}' is already part of the process") 
            continue

        break
    
    while True:
        raw = prompt("Activities to collapse (comma-separated)")
        collapse_acts = [a.strip() for a in raw.split(",") if a.strip()]

        if all(act in matrix.activities for act in collapse_acts):
            break

        print(f"  Invalid activities. Please enter only activities from: {matrix.activities}")
        raw = prompt("Activities to collapse (comma-separated)")


    # ════════════════════════════════════════════════════════════════════════════
    #  Check for violations of locked dependencies, which can not be resolved 
    # ════════════════════════════════════════════════════════════════════════════

    # define a set of involved locks for the set of activities affected 
    involved_locks = [(from_act, to_act) for (from_act, to_act) in locked_dependencies if from_act in collapse_acts or to_act in collapse_acts]
    
    # inform the user with a banner 
    if involved_locks: 
        banner("Check for unresolvable violations to locked dependencies")

    # for each of the involved locked dependencies, perfom the check
    for (from_act, to_act) in involved_locks: 
        
        # get the effected dependencies 
        temp, exist = locked_dependencies[(from_act, to_act)]

        temp_str = dep_label_temp(temp) + " " if temp is not None else ""
        exist_str = dep_label_exist(exist) + " " if exist is not None else ""

        # if only one activity part of collapse, ask if to accept and remove dependency 
        if (from_act in collapse_acts and to_act not in collapse_acts) or (from_act not in collapse_acts and to_act in collapse_acts): 
            
            str_act = from_act if from_act in collapse_acts else to_act

            print(f"\nActivity '{str_act}' is in the set of activities to be collapsed and part of a locked dependency")
            print("Collapsing would violate the locked dependency.")
            print("If the locked dependency is uphold, the change operation becomes infesible.")
            print(f"The affected dependency is ({from_act} {temp_str}, {exist_str} {to_act})")

            # ask the user if the dependency should be deleted to perfom the change operation 
            if confirm("Do you want to delete the locked dependency?"): 
                # delete the entry from the locked dependencies 
                del locked_dependencies[(from_act, to_act)]

                # delete also the reverse entry, check that it exists first 
                if (to_act, from_act) in locked_dependencies:  
                    del locked_dependencies[(to_act, from_act)]

            else: 
                # if the user does not accept, change operation is not possible and we return an error 
                raise ValueError("Collapse can not be performed when there are locked dependencies which would be violated")

        # else both are part of collapse, inform the user and remove the locked dependency 
        else:  
            # inform the user about the deletion 
            print(f"\nThe activities {from_act}, {to_act} are both part of the set to be collapsed and have the dependency ({from_act} {temp_str}{exist_str}{to_act})")
            print("To perfom the collapse operation, the locked dependecies are getting removed - they can be seen as preserved in the collapsed process")
            
            # delete the activities 
            del locked_dependencies[(from_act, to_act)]

            # also delete the reverse entry, if it exists 
            if (to_act, from_act) in locked_dependencies: 
                del locked_dependencies[(to_act, from_act)]
        

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 2: Try performance of the change operation  
    # ════════════════════════════════════════════════════════════════════════════

    # perform the change operation, if activities in between catch the error and perform the alternative change operations 
    try: 
        result = collapse_operation(matrix, collapsed_name, collapse_acts)
    # check that we catch the correct error message 
    except ValueError as e:
        msg = str(e)
        # check if it is the error 
        if "happen between the activities to be collapsed" in msg: 
            # offer the user the selection of solution strategies (either move activities, for the different activities to parallelized / include activities to be parallelized)
            
            # create the set of moving options
            options = ["Move all activities to activity " + act for act in collapse_acts]

            # get the activities happening in between 
            list_str = msg.split("Activities ")[1].split(" happen between the activities to be collapsed")[0]
            activities_in_between = list_str.strip("[]").split("', '")
            activities_in_between = [a.strip("'") for a in activities_in_between]

            # if less then 5 activities, offer to parallelize also activities in between 
            if len(activities_in_between) <= 5: 
                options = ["Collapse including activities " + str(activities_in_between)] + options

            # let the user choose a solution strategy
            solution_strategy = choose("Choose a solution strategy: ", options)

            # based on the selected solution strategy, we perform the change operation 
            if "Collapse including activities " in solution_strategy: 
                # include the activities in between in the parallelization 
                acceptance_sequences = collapse_expand_set(generate_acceptance_variants(matrix), collapse_acts, activities_in_between, collapsed_name)

                # convert the acceptance sequences to a matrix and return
                result = variants_to_matrix(acceptance_sequences)
            
            else: 
                # get the activity to which the others should be moved from the chosen option 
                activity_positioning = solution_strategy.split("Move all activities to activity ")[1]
                
                # perform the adapted change operation
                acceptance_sequences = collapse_move_activities(generate_acceptance_variants(matrix), collapse_acts, collapsed_name, activity_positioning)

                # convert the acceptance sequences to a matrix and return
                result = variants_to_matrix(acceptance_sequences)
    

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 3: Check for violation of locked dependencies 
    # ════════════════════════════════════════════════════════════════════════════
    
    # check if the locked dependencies are violated 
    exist_violations = are_locked_dependencies_violated(locked_dependencies, result)

    # if we encounter violations, we first try to resolve them by dependency relaxation 
    if exist_violations:

        # reset the existing violations 
        exist_violations = False 

        # perform the dependency relaxation
        locked_dependencies, exist_violations = perform_dependency_relaxation(result, locked_dependencies)

        # in case dependency relaxation was unable to resolve violations of locked dependencies 
        if exist_violations: 

            banner("Using skeleton algorithm to resolve violations of locked dependencies")
            print("\nUsing dependency relaxation was unable to resolve (all) violations.")
            
            # perfom the skeleton approach
            result = perfom_skeleton_algorithm(result, locked_dependencies)


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 4: Return the reuslt to the user
    # ════════════════════════════════════════════════════════════════════════════

    return result, locked_dependencies