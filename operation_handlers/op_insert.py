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
from change_operations.insert_operation    import insert_activity

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
from utils.console_helpers import ask_dependencies_insertion
from utils.console_helpers import deps_to_matrix

# ── Locked dependency functions ─────────────────────────────────────────────────
from utils.utils_lock_dependencies import get_locked_dependencies
from utils.utils_lock_dependencies import is_relaxation
from utils.utils_lock_dependencies import is_temp_relaxation
from utils.utils_lock_dependencies import is_exist_relaxation
from utils.utils_lock_dependencies import are_locked_dependencies_violated

# ── Dependency relaxation ─────────────────────────────────────────────────
from utils.dependency_relaxation import perform_dependency_relaxation

# ── Debug mode ─────────────────────────────────────────────────
from utils.debug_mode import log





def op_insert(matrix: AdjacencyMatrix, locked_dependencies: dict):
    """
    Logic applied in muliple steps to perform the change operation insert 

    1. Get the required input from the user 
    2. Try to perfom the change operation 
    3. Check for violation of locked dependencies 
        3.1. Try dependency relaxation 
        3.2. Use skeleton approach 
    4. Return the result to the user 

    Args: 
        matrix: adjacency matrix of the process for insertion 
        locked_dependencies: dict of locked dependencies 

    Return: 
        Adjacency matrix in the modified form 
        Dependecies which were provided for insertion 
    """

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 1: Get the reuqired input from teh user 
    # ════════════════════════════════════════════════════════════════════════════

    # get the parameters for the change operation

    # get the name of the new activity - ensure it is not alreday part of the process
    while True: 
        activity = prompt("New activity name")

        if activity in matrix.activities: 
            print(f"  ✗  Activity '{activity}' already exists in the process") 
            continue
    
        break

    print(f"\n  Current activities: {matrix.activities}")

    # TODO modify so that only dependencies including the activity for insertion can be provided
    deps = ask_dependencies_insertion(matrix.activities + [activity], activity)

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 2: Try performance of the change operation  
    # ════════════════════════════════════════════════════════════════════════════

    try: 
        # try to perform the insert operation
        result = insert_activity(matrix, activity, deps)
    
    except ValueError as e: 
        # indicate to the user that the standard insert method does not work here 
        print("\nFor the insert operation there is a contradiction between the inputs, we use the skeleton approach to resolve it")

        result = perfom_skeleton_algorithm(matrix, deps, activity)


    # ════════════════════════════════════════════════════════════════════════════
    #  Check that in result all activities are present, which were also part of the initial matrix
    # ════════════════════════════════════════════════════════════════════════════

    # get the list of activities from the original matrix, add the inserted activity
    original_activities = set(matrix.get_activities()) | {activity}

    # get the list of activities from the new matrix
    result_activities = set(result.get_activities())

    # check if they contain the same activities 
    not_cor_activities = original_activities != result_activities

    # check if the new dependencies do not match the intended modification 
    if not_cor_activities: 
        print("\nFor the insert operation there is a contradiction between the inputs, we use the skeleton approach to resolve it")

        log("\nThe standard insertion algorithm was unable to perform the insertion.")
        log("We use the skeleton algorithm to perfom the insertion")     

        result = perfom_skeleton_algorithm(matrix, deps)


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
            # use the locked dependencies as a base 
            combined = dict(locked_dependencies)  

            # we can not have any overlaps here, so no checks are required 
            # the deps are always including the new activity, which can not be part of the process 
            for (from_act, to_act), (ins_temp, ins_exist) in deps.items():
                combined[(from_act, to_act)] = (ins_temp, ins_exist)

            # perfom the skeleton approach
            result = perfom_skeleton_algorithm(result, combined, activity)


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 4: Return the reuslt to the user
    # ════════════════════════════════════════════════════════════════════════════

    return result, locked_dependencies