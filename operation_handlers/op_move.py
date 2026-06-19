# ── Core imports ────────────────────────────────────────────────────────────
from adjacency_matrix import AdjacencyMatrix

# ── Change-operation imports ─────────────────────────────────────────────────
from change_operations.move_operation      import move_activity

# ── Skeleton algorithm ─────────────────────────────────────────────────
from solution_strategies.skeleton_strategies import perform_skeleton_algorithm

# ── Helper functions ─────────────────────────────────────────────────
from utils.console_helpers import banner
from utils.console_helpers import prompt
from utils.console_helpers import confirm
from utils.console_helpers import dep_label_temp
from utils.console_helpers import dep_label_exist
from utils.console_helpers import ask_dependencies_insertion

# ── Locked dependency functions ─────────────────────────────────────────────────
from utils.utils_lock_dependencies import are_locked_dependencies_violated

# ── Dependency relaxation ─────────────────────────────────────────────────
from utils.dependency_relaxation import perform_dependency_relaxation

# ── Dependency reversion ─────────────────────────────────────────────────
from utils.console_helpers import reverse_dependency

# ── Debug mode ─────────────────────────────────────────────────
from utils.debug_mode import log


def op_move(matrix: AdjacencyMatrix, locked_dependencies):
    """
    Operation handler for move an activity to a new position

    1) get the required input from the user and validate it 
    2) Check for violations which can not be resolved 
    3) Try to perform the change operation 
        3.1) use the skeleton approach for contradictions between inputs 
    4) Check for violations of locked dependencies 
        4.1) Apply dependency relaxation 
        4.2) Apply the skeleton strategy 
    5) return the new matrix and the (modified) locked dependencies 

    Args: 
        matrix: Adacency of the matrix to perform the change operation on 
        locked_dependencies: dict of locked dependencies 

    Return: 
        modified matrix 
        locked_dependencies after potential modification because of relaxation
    """

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 1: Get the reuqired input from the user 
    # ════════════════════════════════════════════════════════════════════════════

    # get the parameters for the change operation
    print(f"\n  ── Parameters for: move ──")

    print(f"\n  Current activities: {matrix.activities}")

    # get the activity to move - ensure it is in the process 
    while True: 
        activity = prompt("Activity to move")

        if activity not in matrix.activities: 
            print(f"  ✗  Activity {activity} is not in the process.")
            continue

        break
            
    print("\n  Specify the new dependencies that define the new position:")
    deps = ask_dependencies_insertion(matrix.activities, activity)


    # ════════════════════════════════════════════════════════════════════════════
    #  Check if insertion conditions, violate locked dependencies  
    # ════════════════════════════════════════════════════════════════════════════

    banner("Check for the requierement to alter a locked dependency")
    print("\nYou are trying to modify a locked dependency. \n")
    
    # iterate over all dependencies for insertion and check if there exists a locked dependency for it 
    for (from_act, to_act), (temp_dep, exist_dep) in list(deps.items()):

        # ensure we only cover each pair once
        if to_act < from_act: 
            continue

        # check if for the modified dependencies there are locked dependencies; check in one direction sufficient since the locked deps are mirrored  
        if (from_act, to_act) in locked_dependencies:
            
            temp_locked, exist_locked = locked_dependencies[(from_act, to_act)]

            # ── Temporal component conflict ───────────────────────────────────────
            if (temp_locked is not None) and (temp_dep is not None) and (temp_locked != temp_dep):

                print(f"\nThe locked temporal dependency is:    ({from_act} {dep_label_temp(temp_locked)} {to_act})")
                print(f"The requested temporal depenency for insertion is:  ({from_act} {dep_label_temp(temp_dep)} {to_act})")

                if confirm("Keep the locked temporal dependency? (temporal part of insertion will be skipped)"):
                    # remove the temporal part from the deps 
                    exist_dep_current = deps[(from_act, to_act)][1]

                    # modify the entry, by either deleting it if no exist dependency is locked, or modifying it 
                    if exist_locked_current is None:
                        del deps[(from_act, to_act)]

                        # also delete other direction 
                        if (to_act, from_act) in deps: 
                            del deps[(to_act, from_act)]

                    else:
                        deps[(from_act, to_act)] = (None, exist_dep_current)

                        # modify also the reverse entry 
                        deps[(to_act, from_act)] = (None, reverse_dependency(exist_dep_current))

                    
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
            if (exist_locked is not None) and (exist_dep is not None) and (exist_locked != exist_dep):

                print(f"\nThe locked existential dependency is:    ({from_act} {dep_label_exist(exist_locked)} {to_act})")
                print(f"The requested existential dependency for insertion:  ({from_act} {dep_label_exist(exist_dep)} {to_act})")

                if confirm("Keep the locked existential dependency? (existential part of modification will be skipped)"):
                    # remove the existential part of the deps for insertion, keep the lock intact
                    temp_deps_current = deps.get((from_act, to_act), (None, None))[0]
                    
                    # if no temporal dep provided, just delete the entry 
                    if temp_deps_current is None:
                        del deps[(from_act, to_act)]

                        # delete also the reversed entry, if it exists 
                        if (to_act, from_act) in deps: 
                            del deps[(to_act, from_act)]

                    else:
                        deps[(from_act, to_act)] = (temp_deps_current, None)

                        # modify also the reverse entry 
                        deps[(to_act, from_act)] = (reverse_dependency(temp_deps_current), None)
                    
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
    if not deps:
        print("\n  ℹ  All modifications were suppressed by locked dependencies. No changes applied.")
        return matrix, locked_dependencies
    
    

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 2: Try performance of the change operation  
    # ════════════════════════════════════════════════════════════════════════════

    try: 
        # try to perform the insert operation
        result =  move_activity(matrix, activity, deps)
    
    except ValueError as e: 
        # indicate to the user that the standard insert method does not work here 
        print("\nThe move operation is ambigous, we use the new skeleton approach to adapt the acceptance sequences")

        # return the modified matrix
        result = perform_skeleton_algorithm(matrix, locked_dependencies)

    
    # ════════════════════════════════════════════════════════════════════════════
    #  Check that in result all activities are present, which were also part of the initial matrix
    # ════════════════════════════════════════════════════════════════════════════

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
    if not_cor_activities: 
        print("\nFor the modify operation there is a contradiction between the inputs, we use the skeleton approach to resolve it")

        log("\nThe standard modification algorithm was unable to perform the modification.")
        log("We use the skeleton algorithm to perfom the modification")     

        result = perform_skeleton_algorithm(matrix, deps)


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
            for ((from_act, to_act), (temp_dep_move, exist_dep_move)) in deps.items():  

                # without overlaps, we can just add the dependencies from the move operation  
                if (from_act, to_act) not in locked_dependencies:
                    combined[(from_act, to_act)] = (temp_dep_move, exist_dep_move)

                    # add the reverse 
                    combined[(to_act, from_act)] = (reverse_dependency(temp_dep_move), reverse_dependency(exist_dep_move))

                # if we have an overlap, we must chec if we can resolve it 
                else: 
                    # get the dependencies from the locked one 
                    locked_temp, locked_exist = locked_dependencies[(from_act, to_act)]

                    if locked_temp is not None and temp_dep_move is not None:
                        raise ValueError(
                            f"Conflict on temporal dependency ({from_act} → {to_act}): "
                            f"locked as '{dep_label_temp(locked_temp)}' but modification "
                            f"also specifies '{dep_label_temp(temp_dep_move)}'. "
                            f"Cannot apply both — please relax the locked dependency first."
                        )

                    if locked_exist is not None and exist_dep_move is not None:
                        raise ValueError(
                            f"Conflict on existential dependency ({from_act} → {to_act}): "
                            f"locked as '{dep_label_exist(locked_exist)}' but modification "
                            f"also specifies '{dep_label_exist(exist_dep_move)}'. "
                            f"Cannot apply both — please relax the locked dependency first."
                        )
                    
                    # if no overlap exists, we can just merge them 
                    combined[(from_act, to_act)] = (
                        temp_dep_move  if temp_dep_move  is not None else locked_temp,
                        exist_dep_move if exist_dep_move is not None else locked_exist,
                    )

            banner("Using skeleton to resolve violations of locked dependencies")
            print("\nUsing dependency relaxation was unable to resolve (all) violations.")

            # perfom the skeleton approach
            result = perform_skeleton_algorithm(result, combined)

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 4: Return the reuslt to the user
    # ════════════════════════════════════════════════════════════════════════════

    return result, locked_dependencies