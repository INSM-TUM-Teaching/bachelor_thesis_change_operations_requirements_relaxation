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
from change_operations.parallelize_operation import parallelize_activities

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



def op_parallelize(matrix: AdjacencyMatrix, locked_dependencies):
    """
    Parallelize a set of activities and perfom the check for violated locked dependencies

    Args: 
        matrix: Adacency of the matrix to perform the change operation on 
        locked_dependencies: dict of locked dependencies

    Return: 
        modified matrix 
        locked_dependencies after potential relaxations
    """

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 1: Get the reuqired input from teh user 
    # ════════════════════════════════════════════════════════════════════════════

    print(f"\n  Current activities: {matrix.activities}")
    raw = prompt("Activities to parallelize (comma-separated)")
    activities_parallelization = [a.strip() for a in raw.split(",") if a.strip()]

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 2: Try performance of the change operation  
    # ════════════════════════════════════════════════════════════════════════════

    # perform the change operation, if activities in between catch the error and perform the alternative change operations 
    try: 
        result = parallelize_activities(matrix, activities_parallelization)
    # check that we catch the correct error message 
    except ValueError as e:
        msg = str(e)
        # check if it is the error 
        if "are in between the activities to be parallelized" in msg: 
            # offer the user the selection of solution strategies (either move activities, for the different activities to parallelized / include activities to be parallelized)
            
            # create the set of moving options
            options = ["Move all activities to activity " + act for act in activities_parallelization]

            # get the activities happening in between 
            list_str = msg.split("Activities ")[1].split(" are in between")[0]
            activities_in_between = list_str.strip("[]").split("', '")
            activities_in_between = [a.strip("'") for a in activities_in_between]

            # if less then 5 activities, offer to parallelize also activities in between 
            if len(activities_in_between) <= 5: 
                options = ["Parallelize including activities " + str(activities_in_between)] + options

            # let the user choose a solution strategy
            solution_strategy = choose("Choose a solution strategy: ", options)

            # based on the selected solution strategy, we perform the change operation 
            if "Parallelize including activities " in solution_strategy: 
                # include the activities in between in the parallelization 
                acceptance_sequences = parallelize_expand_set(generate_acceptance_variants(matrix), activities_parallelization, activities_in_between)

                # convert the acceptance sequences to a matrix and return
                result = variants_to_matrix(acceptance_sequences)
            
            else: 
                # get the activity to which the others should be moved from the chosen option 
                activity_positioning = solution_strategy.split("Move all activities to activity ")[1]
                
                # perform the adapted change operation
                acceptance_sequences = parallelize_move_activities(generate_acceptance_variants(matrix), activities_parallelization, activity_positioning)

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
            
            # use the locked dependencies as a base 
            combined = dict(locked_dependencies)  

            # build a dict for the parallelize activities 
            for from_act in activities_parallelization: 
                for to_act in activities_parallelization: 
                    # filter that we do not include self pairs 
                    if from_act == to_act: 
                        continue

                    # check that there is no conflict with an existing locked dependency
                    if (from_act, to_act) in combined: 
                        locked_temp, locked_exist = combined[(from_act, to_act)]


                        if locked_temp is not None and locked_temp.type != TemporalType.INDEPENDENCE:
                            print(
                                f"  ✗  Conflict on temporal dependency ({from_act} → {to_act}): "
                                f"locked as '{dep_label_temp(locked_temp)}' but parallelization "
                                f"requires INDEPENDENCE. Cannot apply — please relax the locked "
                                f"dependency first."
                            )
                            return result, locked_dependencies  

                        if locked_exist is not None and locked_exist.type != ExistentialType.EQUIVALENCE:
                            print(
                                f"  ✗  Conflict on existential dependency ({from_act} → {to_act}): "
                                f"locked as '{dep_label_exist(locked_exist)}' but parallelization "
                                f"requires EQUIVALENCE. Cannot apply — please relax the locked "
                                f"dependency first."
                            )
                            return result, locked_dependencies  
                        
                    
                    # add the entry to the dictionary 
                    combined[(from_act, to_act)] = (
                        TemporalDependency(type=TemporalType.INDEPENDENCE, direction=Direction.BOTH),
                        ExistentialDependency(type=ExistentialType.EQUIVALENCE, direction=Direction.BOTH),
                    )

            
            banner("Using skeleton to resolve violations of locked dependencies")
            print("\nUsing dependency relaxation was unable to resolve (all) violations.")

            # perfom the skeleton approach
            result = perfom_skeleton_algorithm(result, locked_dependencies)


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 4: Return the reuslt to the user
    # ════════════════════════════════════════════════════════════════════════════

    return result, locked_dependencies
