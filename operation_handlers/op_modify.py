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
from change_operations.modify_operation    import modify_dependencies

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



def op_modify(matrix: AdjacencyMatrix, locked_dependencies):
    """
    Modify the dependency and perfom the check for violated locked dependencies

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
    modifications = []
    print("\n  Enter modification:")
    
    while True:
        from_act = prompt("    From activity")
        if from_act not in matrix.activities:
            print(f"  ✗  '{from_act}' is not in the activity list: {matrix.activities}")
            continue

        to_act = prompt("    To activity")
        if to_act not in matrix.activities:
            print(f"  ✗  '{to_act}' is not in the activity list: {matrix.activities}")
            continue

        if from_act == to_act:
            print(f"  ✗  From and To activity must be different.")
            continue

        temp  = ask_temporal()
        exist = ask_existential()

        if temp is None and exist is None:
            print("  ✗  Modify requires at least one dependency to be specified.")
            continue

        # valid input received
        break

    modification = [(from_act, to_act, temp, exist)]

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 2: Try performance of the change operation  
    # ════════════════════════════════════════════════════════════════════════════

    result, _ = modify_dependencies(matrix, modification)

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

            # we must check for overlaps, if they exist, we raise an error 
            if (from_act, to_act) not in locked_dependencies:
                combined[(from_act, to_act)] = (temp, exist)
            else: 
                # get the dependencies from the locked one 
                locked_temp, locked_exist = locked_dependencies[(from_act, to_act)]

                if locked_temp is not None and temp is not None:
                    raise ValueError(
                        f"Conflict on temporal dependency ({from_act} → {to_act}): "
                        f"locked as '{dep_label_temp(locked_temp)}' but modification "
                        f"also specifies '{dep_label_temp(temp)}'. "
                        f"Cannot apply both — please relax the locked dependency first."
                    )

                if locked_exist is not None and exist is not None:
                    raise ValueError(
                        f"Conflict on existential dependency ({from_act} → {to_act}): "
                        f"locked as '{dep_label_exist(locked_exist)}' but modification "
                        f"also specifies '{dep_label_exist(exist)}'. "
                        f"Cannot apply both — please relax the locked dependency first."
                    )
                
                # if no overlap exists, we can just merge them 
                combined[(from_act, to_act)] = (
                    temp  if temp  is not None else locked_temp,
                    exist if exist is not None else locked_exist,
                )

            banner("Using skeleton to resolve violations of locked dependencies")
            print("\nUsing dependency relaxation was unable to resolve (all) violations.")

            # perfom the skeleton approach
            result = perfom_skeleton_algorithm(result, combined)


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 4: Return the reuslt to the user
    # ════════════════════════════════════════════════════════════════════════════

    return result, locked_dependencies