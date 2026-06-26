# ── Core imports ────────────────────────────────────────────────────────────
from adjacency_matrix import AdjacencyMatrix

# ── Change-operation imports ─────────────────────────────────────────────────
from change_operations.modify_operation    import modify_dependencies

# ── Skeleton algorithm ─────────────────────────────────────────────────
from solution_strategies.skeleton_strategies import perform_skeleton_algorithm

# ── Helper functions ─────────────────────────────────────────────────
from utils.console_helpers import banner
from utils.console_helpers import prompt
from utils.console_helpers import confirm
from utils.console_helpers import dep_label_temp
from utils.console_helpers import dep_label_exist
from utils.console_helpers import ask_temporal
from utils.console_helpers import ask_existential
from utils.console_helpers import choose

# ── Transitive closure ────────────────────────────────────────────────────────────
from transitive_closure import compute_full_closure_with_chain_endpoints

# ── Locked dependency functions ─────────────────────────────────────────────────
from utils.utils_lock_dependencies import are_locked_dependencies_violated

# ── Dependency relaxation ─────────────────────────────────────────────────
from utils.dependency_relaxation import perform_dependency_relaxation

# ── Debug mode ─────────────────────────────────────────────────
from utils.debug_mode import log

# ── Reverse dependency function ─────────────────────────────────────────────────
from utils.console_helpers import reverse_dependency


def op_modify(matrix: AdjacencyMatrix, locked_dependencies):
    """
    Operation handler for modifying dependencies 

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

        banner("Check for the requierement to alter a locked dependency")
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
        print("\n  The resolution caused the removal of all specified modifications. No changes applied.")
        return matrix, locked_dependencies

    # rebuild modification tuple with the (possibly narrowed) components; modify operation builds teh inverse 
    modification = [(from_act, to_act, temp, exist)]


    # ════════════════════════════════════════════════════════════════════════════
    #  Check for violations of trasnitive closure of locked dependencies, which can not be resolved 
    # ════════════════════════════════════════════════════════════════════════════

    while True:
 
        # compute the closure with the chain locks touching the endpoints
        locked_dependencies_trans_closure, chain_endpoints = compute_full_closure_with_chain_endpoints(locked_dependencies)
 
        # no transitive lock for the modified pair -> nothing to resolve
        if (from_act, to_act) not in locked_dependencies_trans_closure:
            break
 
        temp_locked, exist_locked = locked_dependencies_trans_closure.get((from_act, to_act), (None, None))
 
        # flag to indicate that a chain lock was deleted, so we recompute the closure
        chain_lock_deleted = False
 
        # ── Temporal component conflict ───────────────────────────────────────
        if (temp_locked is not None) and (temp is not None) and (temp_locked != temp):
 
            banner("The modification alters a locked dependency derived by trasnitivity")
 
            print(f"\nThe locked transitive temporal dependency is:    ({from_act} {dep_label_temp(temp_locked)} {to_act})")
            print(f"The requested temporal modification:  ({from_act} {dep_label_temp(temp)} {to_act})")
 
            # the explicit temporal chain locks touching the endpoints, which can be deleted to break the chain
            chain_locks = []
            for (x, y) in chain_endpoints.get((from_act, to_act), {}).get('temporal', set()):
                if locked_dependencies.get((x, y), (None, None))[0] is not None and (x, y) not in chain_locks:
                    chain_locks.append((x, y))
 
            # build the options: discard the modify component, delete one chain lock, or abort
            options = ["Discard temporal component of modify operation"]
            for (x, y) in chain_locks:
                options.append("Delete locked temporal dependency (" + str(x) + " " + str(dep_label_temp(locked_dependencies[(x, y)][0])) + " " + str(y) + ")")
            options.append("Do not apply the change operation")
 
            selection = choose("Choose how to resolve the conflict with the transitive locked dependency", options)
 
            if selection.startswith("Discard"):
                # drop the temporal part of the modification, keep the chain intact
                temp = None
 
            elif selection == "Do not apply the change operation":
                # change op not possible — keep the locks intact
                print("Change operation can with this configuration not be applied")
                return matrix, locked_dependencies
 
            else:
                # map the selection back to the chosen chain lock and delete its temporal component
                leg = chain_locks[options.index(selection) - 1]
                x, y = leg
 
                # remove only the temporal component, keep the existential one
                exist_locked_current = locked_dependencies[leg][1]
                if exist_locked_current is None:
                    del locked_dependencies[leg]
 
                    # also delete the other direction
                    if (y, x) in locked_dependencies:
                        del locked_dependencies[(y, x)]
 
                else:
                    locked_dependencies[leg] = (None, exist_locked_current)
 
                    # modify also the reverse entry
                    locked_dependencies[(y, x)] = (None, reverse_dependency(exist_locked_current))
 
                # a chain lock was deleted -> recompute the closure
                chain_lock_deleted = True
 
        # ── Existential component conflict ────────────────────────────────────
        if (exist_locked is not None) and (exist is not None) and (exist_locked != exist):
 
            banner("The modification alters a locked dependency derived by trasnitivity")
 
            print(f"\nThe locked transitive existential dependency is:    ({from_act} {dep_label_exist(exist_locked)} {to_act})")
            print(f"The requested existential modification:  ({from_act} {dep_label_exist(exist)} {to_act})")
 
            # the explicit existential chain locks touching the endpoints, which can be deleted to break the chain
            chain_locks = []
            for (x, y) in chain_endpoints.get((from_act, to_act), {}).get('existential', set()):
                if locked_dependencies.get((x, y), (None, None))[1] is not None and (x, y) not in chain_locks:
                    chain_locks.append((x, y))
 
            # build the options: discard the modify component, delete one chain lock, or abort
            options = ["Discard existential component of modify operation"]
            for (x, y) in chain_locks:
                options.append("Delete locked existential dependency (" + str(x) + " " + str(dep_label_exist(locked_dependencies[(x, y)][1])) + " " + str(y) + ")")
            options.append("Do not apply the change operation")
 
            selection = choose("Choose how to resolve the conflict with the transitive locked dependency", options)
 
            if selection.startswith("Discard"):
                # drop the existential part of the modification, keep the chain intact
                exist = None
 
            elif selection == "Do not apply the change operation":
                # change op not possible — keep the locks intact
                print("Change operation can with this configuration not be applied")
                return matrix, locked_dependencies
 
            else:
                # map the selection back to the chosen chain lock and delete its existential component
                leg = chain_locks[options.index(selection) - 1]
                x, y = leg
 
                # remove only the existential component, keep the temporal one
                temp_locked_current = locked_dependencies[leg][0]
                if temp_locked_current is None:
                    del locked_dependencies[leg]
 
                    # also delete the other direction
                    if (y, x) in locked_dependencies:
                        del locked_dependencies[(y, x)]
 
                else:
                    locked_dependencies[leg] = (temp_locked_current, None)
 
                    # modify also the reverse entry
                    locked_dependencies[(y, x)] = (reverse_dependency(temp_locked_current), None)
 
                # a chain lock was deleted -> recompute the closure
                chain_lock_deleted = True
 
        # if no chain lock was deleted, the conflicts were resolved by discarding -> done
        if not chain_lock_deleted:
            break
 
        # otherwise loop again: recompute the closure against the (now broken) chain
 
 
    # ── Early exit if the user suppressed both components ────────────────────
    if temp is None and exist is None:
        print("\n  The resolution caused the removal of all specified modifications. No changes applied.")
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
        print("The standard modification algorithm was unable to perform the modification. \nWe use the skeleton algorithm to perfom the modification")

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
        print("The standard modification algorithm was unable to perform the modification. \nWe use the skeleton algorithm to perfom the modification")


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