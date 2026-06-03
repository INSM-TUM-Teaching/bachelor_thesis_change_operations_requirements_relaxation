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
from solution_strategies.skeleton_strategies import perform_skeleton_algorithm

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

# ── Debug mode ─────────────────────────────────────────────────
from utils.debug_mode import log

# ── Reverse dependency function ─────────────────────────────────────────────────
from utils.console_helpers import reverse_dependency


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
    
    # get the from activity and ensure it is part of the process 
    while True:
        from_act = prompt("    From activity")
        if from_act not in matrix.activities:
            print(f"  ✗  '{from_act}' is not in the activity list: {matrix.activities}")
            continue

        break

    # get the to activit and ensure it is in the process 
    while True:
        to_act = prompt("    To activity")
        if to_act not in matrix.activities:
            print(f"  ✗  '{to_act}' is not in the activity list: {matrix.activities}")
            continue

        if from_act == to_act:
            print(f"  ✗  From and To activity must be different.")
            continue

        break

    # get the dependencies for modification and ensure at least one of the dependencies is not None 
    while True: 

        temp  = ask_temporal()
        exist = ask_existential()

        if temp is None and exist is None:
            print("  ✗  Modify requires at least one dependency to be specified.")
            continue

        # valid input received
        break

    # based on the input define the modification; modify operation handles the inverse automatically  
    modification = [(from_act, to_act, temp, exist)]

    # ════════════════════════════════════════════════════════════════════════════
    #  Check for violations of locked dependencies, which can not be resolved 
    # ════════════════════════════════════════════════════════════════════════════

    # check if for the modified dependencies there are locked dependencies; check in one direction sufficient since the locked deps are mirrored  
    if (from_act, to_act) in locked_dependencies:

        banner("Check for unresolvable violations to locked dependencies")
        print("\nYou are trying to modify a locked dependency.")

        temp_locked, exist_locked = locked_dependencies[(from_act, to_act)]

        # ── Temporal component conflict ───────────────────────────────────────
        if (temp_locked is not None) and (temp is not None) and (temp_locked != temp):

            print(f"\nThe locked temporal dependency is:    ({from_act} {dep_label_temp(temp_locked)} {to_act})")
            print(f"The requested temporal modification:  ({from_act} {dep_label_temp(temp)} {to_act})")

            if confirm("Keep the locked temporal dependency? (temporal part of modification will be skipped)"):
                # drop the temporal part of the modification, keep the lock intact
                temp = None
            else:
                # user accepts overriding — remove only the temporal component from the lock
                exist_locked_current = locked_dependencies[(from_act, to_act)][1]

                # modify the entry, by either deleting it if no exist dependency is locked, or modifying it 
                if exist_locked_current is None:
                    del locked_dependencies[(from_act, to_act)]

                    # also delete other direction 
                    if (to_act, from_act) in locked_dependencies: 
                        del locked_dependencies[(to_act, from_act)]

                else:
                    locked_dependencies[(from_act, to_act)] = (None, exist_locked_current)

                    # modify also the reverse entry 
                    locked_dependencies[(to_act, from_act)] = (None, reverse_dependency(exist_locked_current))


        # ── Existential component conflict ────────────────────────────────────
        if (exist_locked is not None) and (exist is not None) and (exist_locked != exist):

            print(f"\nThe locked existential dependency is:    ({from_act} {dep_label_exist(exist_locked)} {to_act})")
            print(f"The requested existential modification:  ({from_act} {dep_label_exist(exist)} {to_act})")

            if confirm("Keep the locked existential dependency? (existential part of modification will be skipped)"):
                # drop the existential part of the modification, keep the lock intact
                exist = None
            else:
                # user accepts overriding — remove only the existential component from the lock
                temp_locked_current = locked_dependencies.get((from_act, to_act), (None, None))[0]
                if temp_locked_current is None:
                    del locked_dependencies[(from_act, to_act)]

                    # delete also the reversed entry, if it exists 
                    if (to_act, from_act) in locked_dependencies: 
                        del locked_dependencies[(to_act, from_act)]

                else:
                    locked_dependencies[(from_act, to_act)] = (temp_locked_current, None)

                    # modify also the reverse entry 
                    locked_dependencies[(to_act, from_act)] = (reverse_dependency(temp_locked_current), None)


    # ── Early exit if the user suppressed both components ────────────────────
    if temp is None and exist is None:
        print("\n  ℹ  All modifications were suppressed by locked dependencies. No changes applied.")
        return matrix, locked_dependencies

    # rebuild modification tuple with the (possibly narrowed) components; modify operation builds teh inverse 
    modification = [(from_act, to_act, temp, exist)]


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 2: Try performance of the change operation  
    # ════════════════════════════════════════════════════════════════════════════

    # using the standard algorithm, in the next step we need to check, that the modification really took place 
    try: 
        result, _ = modify_dependencies(matrix, modification)
        log("Standard algorithm used for the modify operation\n")

    except Exception as e:
        print("\nThe standard modification algorithm was unable to perform the modification. \nWe use the skeleton algorithm to perfom the modification")

        # build the dictionary for the skeleton algorithm 
        modified_dependencies = {(from_act, to_act): (temp, exist), 
                                 (to_act, from_act): (reverse_dependency(temp), reverse_dependency(exist))}

        result = perform_skeleton_algorithm(matrix, modified_dependencies)

    # initialize variables to store the violations of modifications 
    not_cor_temp = False
    not_cor_exist = False
    act_in_result = True

    # --------- Check 1: the new dependencies match the intended result of the modification 

    # ask for the dependency after the modification 
    deps = result.get_dependency(from_act, to_act)

    # we check for the case of the activities not contained / empty matrix
    if deps is None: 
        act_in_result = False
    else: 
        mod_temp_dep, mod_exist_dep = deps

        # compare if the dependency types are correct 
        if temp is not None: 
            if temp != mod_temp_dep: 
                not_cor_temp = True
        
        if exist is not None: 
            if exist != mod_exist_dep: 
                not_cor_exist = True 


    # --------- Check 2: all activities are still present in the new result 

    # get the list of activities from the original matrix
    original_activities = matrix.get_activities()

    # get the list of activities from the new matrix
    result_activities = result.get_activities()

    # check if they contain the same ativities 
    if set(original_activities) != set(result_activities): 

        # variable to indicate that there is a mismatch between the activities
        not_cor_activities = True
    else: 
        not_cor_activities = False

    # check if the new dependencies do not match the intended modification 
    if not_cor_exist or not_cor_temp or not_cor_activities or not act_in_result: 
        log("\nThe standard modification algorithm was unable to perform the modification.")
        log("We use the skeleton algorithm to perfom the modification")

        # build the dictionary for the skeleton algorithm 
        modified_dependencies = {(from_act, to_act): (temp, exist), 
                                 (to_act, from_act): (reverse_dependency(temp), reverse_dependency(exist))}

        result = perform_skeleton_algorithm(matrix, modified_dependencies)


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
                combined[(to_act, from_act)] = (reverse_dependency(temp), reverse_dependency(exist))
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
            result = perform_skeleton_algorithm(result, combined)


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 4: Return the reuslt to the user
    # ════════════════════════════════════════════════════════════════════════════

    return result, locked_dependencies