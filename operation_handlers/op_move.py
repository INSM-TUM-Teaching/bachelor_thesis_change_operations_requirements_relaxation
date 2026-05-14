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
from solution_strategies.skeleton_strategies import adapt_acceptance_skeleton

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


def op_move(matrix: AdjacencyMatrix, locked_dependencies):
    """
    Move an activity to a new position, by asking for the activity and the dependencies to specify the new position 

    Args: 
        matrix: Adacency of the matrix to perform the change operation on 
        locked_dependencies: dict of locked dependencies 

    Return: 
        modified matrix 
        locked_dependencies after potential modification because of relaxation
    """

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 1: Get the reuqired input from teh user 
    # ════════════════════════════════════════════════════════════════════════════

    # get the parameters for the change operation
    print(f"\n  ── Parameters for: insert ──")

    print(f"\n  Current activities: {matrix.activities}")
    activity = prompt("Activity to move")
    print("\n  Specify the new dependencies that define the new position:")
    deps = ask_dependencies(matrix.activities)
    

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 2: Try performance of the change operation  
    # ════════════════════════════════════════════════════════════════════════════

    try: 
        # try to perform the insert operation
        result =  move_activity(matrix, activity, deps)
    
    except ValueError as e: 
        # indicate to the user that the standard insert method does not work here 
        print("The move operation is ambigous, we use the new skeleton approach to adapt the acceptance sequences")

        # we offer the user the option to choose the method to calculate the similarity score
        options = ["Pure occurence similarity score - focus on preserving existential dependencies", 
                   "Pure ordering similarity score - focus on preserving temporal dependencies",
                   "Combined similarity score - allowing for a balanced consideration"]
        
        similarity_strategy = choose("Choose a method to calculate the similarity score between skeleton sequences and acceptance sequences: ", options)

        if "occurence" in similarity_strategy: 
            similarity_strategy = "occurence"
        elif "ordering" in similarity_strategy: 
            similarity_strategy = "ordering"
        else: 
            similarity_strategy = "combined"

        # TODO 
        # define how exactly the new dependencies can be used; especially when overlapping with new dependencies 

        # if an error occurs, we use the new insert opportunity 
        modified_acceptance_sequences = adapt_acceptance_skeleton(generate_acceptance_variants(matrix), deps_to_matrix(deps), similarity_strategy)

        # return the modified matrix
        result = variants_to_matrix(modified_acceptance_sequences)


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

            # perfom the skeleton approach
            result = perfom_skeleton_algorithm(result, locked_dependencies)


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 4: Return the reuslt to the user
    # ════════════════════════════════════════════════════════════════════════════

    return result, locked_dependencies