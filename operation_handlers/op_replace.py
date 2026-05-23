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
from change_operations.replace_operation   import replace_activity

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



def op_replace(matrix: AdjacencyMatrix, locked_dependencies):
    """
    Replace an activity from the process with another

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
        old_act = prompt("Activity to replace")

        if old_act not in matrix.activities: 
            print(f"  ✗  Activity '{old_act}' is not in the process")
            continue

        break

    while True:
        new_act = prompt("New activity name")

        if new_act in matrix.activities: 
            print(f"  ✗  Activity '{new_act}' is already in the process")
            continue

        break

    # ════════════════════════════════════════════════════════════════════════════
    #  Check for violations of locked dependencies, which can not be resolved 
    # ════════════════════════════════════════════════════════════════════════════

    # define a set of involved locks for the set of activities affected 
    involved_locks = [(from_act, to_act) for (from_act, to_act) in locked_dependencies if from_act == old_act or to_act == old_act]
    
    # inform the user with a banner 
    if involved_locks: 
        banner("Check for unresolvable violations to locked dependencies")

        # inform the user that the activity to de-collapse has locked dependencies
        print(f"\nActivity '{old_act}' for replacement has locked dependencies to other activities of the process")
        print(f"Replacement would violate the locked dependencies, if they are not deleted or transfered to the new activity '{new_act}'.")
        print("The following list provides an overview of the affected locked dependencies:")

        # provide a list of the effected dependencies
        for (from_act, to_act) in involved_locks: 
            
            # get the effected dependencies 
            temp, exist = locked_dependencies[(from_act, to_act)]

            temp_str = dep_label_temp(temp) + " " if temp is not None else ""
            exist_str = dep_label_exist(exist) + " " if exist is not None else ""

            print(f"   - ({from_act} {temp_str}, {exist_str} {to_act})")

        # ask the user if the dependency should be deleted to perfom the change operation 
        if confirm("\nDo you want to delete all the locked dependencies (otherwise the dependencies will be transferred to the new activity)?"): 
            # delete the entry from the locked dependencies 
            for (from_act, to_act) in involved_locks: 
                del locked_dependencies[(from_act, to_act)]

            print(f"\n  ✓  Locked dependencies involving activity '{old_act}' are deleted.")

        else: 
            # transfer all the locked dependencies to the new activity 
            for (from_act, to_act) in involved_locks: 
                # get the dependencies
                locked_temp, locked_exist = locked_dependencies[(from_act, to_act)]

                # delete the old entry
                del locked_dependencies[(from_act, to_act)]

                # add the new entry with the new activity 
                if from_act == old_act: 
                    locked_dependencies[(new_act, to_act)] = (locked_temp, locked_exist)
                else: 
                    locked_dependencies[(from_act, new_act)] = (locked_temp, locked_exist)

            print(f"\n  ✓  Locked dependencies from activity '{old_act}' are transfered to the new activity '{new_act}'.")
     

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 2: Try performance of the change operation  
    # ════════════════════════════════════════════════════════════════════════════

    result = replace_activity(matrix, old_act, new_act) 

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
            
            # create a dict of combined dependencies 
            # TODO

            banner("Using skeleton to resolve violations of locked dependencies")
            print("\nUsing dependency relaxation was unable to resolve (all) violations.")

            # perfom the skeleton approach
            result = perfom_skeleton_algorithm(result, locked_dependencies)


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 4: Return the reuslt to the user
    # ════════════════════════════════════════════════════════════════════════════

    return result, locked_dependencies