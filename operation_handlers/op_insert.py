# ── Core imports ────────────────────────────────────────────────────────────
from adjacency_matrix import AdjacencyMatrix

# ── Transitive closure ────────────────────────────────────────────────────────────
from transitive_closure import compute_transitive_closure
from transitive_closure import compute_full_transitive_closure

# ── Change-operation imports ─────────────────────────────────────────────────
from change_operations.insert_operation    import insert_activity

# ── Skeleton algorithm ─────────────────────────────────────────────────
from solution_strategies.skeleton_strategies import perform_skeleton_algorithm

# ── Helper functions ─────────────────────────────────────────────────
from utils.console_helpers import prompt
from utils.console_helpers import ask_dependencies_insertion
from utils.console_helpers import choose
from utils.console_helpers import dep_label_temp
from utils.console_helpers import dep_label_exist
from utils.console_helpers import ask_dependencies_insertion

# ── Locked dependency functions ─────────────────────────────────────────────────
from utils.utils_lock_dependencies import are_locked_dependencies_violated

# ── Dependency relaxation ─────────────────────────────────────────────────
from utils.dependency_relaxation import perform_dependency_relaxation

# ── Helper functions ─────────────────────────────────────────────────
from utils.console_helpers import banner
from utils.console_helpers import prompt
from utils.console_helpers import confirm
from utils.console_helpers import dep_label_temp
from utils.console_helpers import dep_label_exist
from utils.console_helpers import ask_dependencies_insertion

# ── Reverse dependency function ─────────────────────────────────────────────────
from utils.console_helpers import reverse_dependency


def op_insert(matrix: AdjacencyMatrix, locked_dependencies: dict):
    """
    Operation handler for inserting an activity 

    1) get the required input from the user and validate it 
    2) Check for violations which can not be resolved 
    3) Try to perform the change operation 
        3.1) use the skeleton approach for contradictions between inputs 
    4) Check for violations of locked dependencies 
        4.1) Apply dependency relaxation 
        4.2) Apply the skeleton strategy 
    5) return the new matrix and the (modified) locked dependencies 

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
    perform_skeleton = False 

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
    #  1) Check if insertion conditions (closed by transitivity), violate locked dependencies by transitivity 
    # ════════════════════════════════════════════════════════════════════════════

    # print the banner only once 
    alreday_conflict = False

    if locked_dependencies: 
        # compute the transitive closure of the deps and use the transitive deps
        trans_closure_deps = compute_transitive_closure(deps)
        
        # iterate over all dependencies for insertion and check if there exists a locked dependency for it 
        for (from_act, to_act), (temp_dep, exist_dep) in list(trans_closure_deps.items()):

            # ensure we only cover each pair once
            if to_act < from_act: 
                continue

            # check if for the transitive dependencies there are locked dependencies; check in one direction sufficient since the locked deps are mirrored  
            if (from_act, to_act) in locked_dependencies:
                
                temp_locked, exist_locked = locked_dependencies[(from_act, to_act)]

                # ── Temporal component conflict ───────────────────────────────────────
                if (temp_locked is not None) and (temp_dep is not None) and (temp_locked != temp_dep):

                    if not alreday_conflict: 
                        banner("Resolve violations of locked dependencies")
                        alreday_conflict = True 

                    print(f"\nThe locked temporal dependency is:  ({from_act} {dep_label_temp(temp_locked)} {to_act})")
                    print(f"The requested temporal dependency by transitivity is: ({from_act} {dep_label_temp(temp_dep)} {to_act})")

                    # provide the different options to resolve the conflict 
                    options = ["Delete locked temporal dependency " + from_act + " " + dep_label_temp(temp_locked) + " " + to_act, 
                            "Remove temporal input dependency (" + str(from_act) + str(dep_label_temp(deps[(from_act, activity)][0])) + " " + str(activity) + ")", 
                            "Remove temporal input dependency (" + str(to_act) + str(dep_label_temp(deps[(to_act, activity)][0])) + " " + str(activity) + ")",
                            "Discard change operation"
                            ]
                    
                    selection = choose("Choose one temporal dependency to be removed, to resolve the conflict", options)

                    if "Delete locked temporal dependency" in selection:
                    
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


                    elif "(" + str(from_act) in selection: 
                        # remove the temporal dependnecy including the from_act
                        exist_dep_current = deps[(from_act, activity)][1]

                        # modify the entry, by either deleting it if no exist dependency is locked, or modifying it 
                        if exist_dep_current is None:
                            del deps[(from_act, activity)]

                            # also delete other direction 
                            if (activity, from_act) in deps: 
                                del deps[(activity, from_act)]

                        else:
                            deps[(from_act, activity)] = (None, exist_dep_current)

                            # modify also the reverse entry 
                            deps[(activity, from_act)] = (None, reverse_dependency(exist_dep_current))

                    elif "(" + str(to_act) in selection:  
                        # remove the temporal dependnecy including the to_act
                        exist_dep_current = deps[(to_act, activity)][1]

                        # modify the entry, by either deleting it if no exist dependency is locked, or modifying it 
                        if exist_dep_current is None:
                            del deps[(to_act, activity)]

                            # also delete other direction 
                            if (activity, to_act) in deps: 
                                del deps[(activity, to_act)]

                        else:
                            deps[(to_act, activity)] = (None, exist_dep_current)

                            # modify also the reverse entry 
                            deps[(activity, to_act)] = (None, reverse_dependency(exist_dep_current))

                    else: 
                        print("\n All modifications were suppressed by locked dependencies. No changes applied.")
                        return matrix, locked_dependencies


                # ── Existential component conflict ────────────────────────────────────
                if (exist_locked is not None) and (exist_dep is not None) and (exist_locked != exist_dep):

                    if not alreday_conflict: 
                        banner("Resolve violations of locked dependencies")
                        alreday_conflict = True 

                    print(f"\nThe locked existential dependency is:    ({from_act} {dep_label_exist(exist_locked)} {to_act})")
                    print(f"The requested existential dependency by transitivity is: ({from_act} {dep_label_exist(exist_dep)} {to_act})")

                    # get the temporal dependencies involved 

                    options = ["Delete locked existential dependency " + from_act + " " + dep_label_exist(exist_locked) + " " + to_act, 
                            "Remove existential input dependency (" + str(from_act) + " " + str(dep_label_exist(deps[(from_act, activity)][1])) + " " + str(activity) + ")", 
                            "Remove existential input dependency (" + str(to_act) + " " + str(dep_label_exist(deps[(to_act, activity)][1])) + " " + str(activity) + ")",
                            "Discard change operation"
                            ]
                    
                    selection = choose("Choose one dependency to be removed, to resolve the conflict", options)

                    if "Delete locked existential dependency" in selection:
                    
                        # user accepts overriding — remove only the temporal component from the lock
                        temp_locked_current = locked_dependencies[(from_act, to_act)][0]

                        # modify the entry, by either deleting it if no exist dependency is locked, or modifying it 
                        if temp_locked_current is None:
                            del locked_dependencies[(from_act, to_act)]

                            # also delete other direction 
                            if (to_act, from_act) in locked_dependencies: 
                                del locked_dependencies[(to_act, from_act)]

                        else:
                            locked_dependencies[(from_act, to_act)] = (temp_locked_current, None)

                            # modify also the reverse entry 
                            locked_dependencies[(to_act, from_act)] = (reverse_dependency(temp_locked_current), None)


                    elif "(" + str(from_act) in selection: 
                        # remove the temporal dependnecy including the from_act
                        temp_dep_current = deps[(from_act, activity)][0]

                        # modify the entry, by either deleting it if no exist dependency is locked, or modifying it 
                        if temp_dep_current is None:
                            del deps[(from_act, activity)]

                            # also delete other direction 
                            if (activity, from_act) in deps: 
                                del deps[(activity, from_act)]

                        else:
                            deps[(from_act, activity)] = (temp_dep_current, None)

                            # modify also the reverse entry 
                            deps[(activity, from_act)] = (reverse_dependency(temp_dep_current), None)

                    elif "(" + str(to_act) in selection: 
                        # remove the temporal dependnecy including the to_act
                        temp_dep_current = deps[(to_act, activity)][0]

                        # modify the entry, by either deleting it if no exist dependency is locked, or modifying it 
                        if temp_dep_current is None:
                            del deps[(to_act, activity)]

                            # also delete other direction 
                            if (activity, to_act) in deps: 
                                del deps[(activity, to_act)]

                        else:
                            deps[(to_act, activity)] = (temp_dep_current, None)

                            # modify also the reverse entry 
                            deps[(activity, to_act)] = (reverse_dependency(temp_dep_current), None)   

                    else: 
                        print("\n All modifications were suppressed by locked dependencies. No changes applied.")
                        return matrix, locked_dependencies


    # ════════════════════════════════════════════════════════════════════════════
    #  2) Check if insertion conditions (closed by transitivity), violate locked dependencies (closed by transitivity)
    # ════════════════════════════════════════════════════════════════════════════


    if locked_dependencies: 
        # compute the transitive closure of the deps and use the transitive deps
        trans_closure_deps = compute_transitive_closure(deps)

        # compute the transitive closure of the deps and use the transitive deps
        trans_closure_locked_deps = compute_full_transitive_closure(locked_dependencies)
        
        # iterate over all dependencies for insertion and check if there exists a locked dependency for it 
        for (from_act, to_act), (temp_dep, exist_dep) in list(trans_closure_deps.items()):

            # ensure we only cover each pair once
            if to_act < from_act: 
                continue

            # check if for the transitive dependencies there are locked dependencies; check in one direction sufficient since the locked deps are mirrored  
            if (from_act, to_act) in trans_closure_locked_deps:
                
                temp_locked, exist_locked = trans_closure_locked_deps[(from_act, to_act)]

                # ── Temporal component conflict ───────────────────────────────────────
                if (temp_locked is not None) and (temp_dep is not None) and (temp_locked != temp_dep):

                    print(f"\nThe locked trasnitive temporal dependency is:  ({from_act} {dep_label_temp(temp_locked)} {to_act})")
                    print(f"The requested temporal dependency by transitivity is: ({from_act} {dep_label_temp(temp_dep)} {to_act})")

                    # provide the different options to resolve the conflict 
                    options = ["Remove temporal input dependency (" + str(from_act) + str(dep_label_temp(deps[(from_act, activity)][0])) + " " + str(activity) + ")", 
                            "Remove temporal input dependency (" + str(to_act) + str(dep_label_temp(deps[(to_act, activity)][0])) + " " + str(activity) + ")",
                            "Discard change operation"
                            ]
                    
                    selection = choose("Choose one temporal dependency to be removed, to resolve the conflict", options)

                    if "(" + str(from_act) in selection: 
                        # remove the temporal dependnecy including the from_act
                        exist_dep_current = deps[(from_act, activity)][1]

                        # modify the entry, by either deleting it if no exist dependency is locked, or modifying it 
                        if exist_dep_current is None:
                            del deps[(from_act, activity)]

                            # also delete other direction 
                            if (activity, from_act) in deps: 
                                del deps[(activity, from_act)]

                        else:
                            deps[(from_act, activity)] = (None, exist_dep_current)

                            # modify also the reverse entry 
                            deps[(activity, from_act)] = (None, reverse_dependency(exist_dep_current))

                    elif "(" + str(to_act) in selection:  
                        # remove the temporal dependnecy including the to_act
                        exist_dep_current = deps[(to_act, activity)][1]

                        # modify the entry, by either deleting it if no exist dependency is locked, or modifying it 
                        if exist_dep_current is None:
                            del deps[(to_act, activity)]

                            # also delete other direction 
                            if (activity, to_act) in deps: 
                                del deps[(activity, to_act)]

                        else:
                            deps[(to_act, activity)] = (None, exist_dep_current)

                            # modify also the reverse entry 
                            deps[(activity, to_act)] = (None, reverse_dependency(exist_dep_current))

                    else: 
                        print("\n All modifications were suppressed by locked dependencies. No changes applied.")
                        return matrix, locked_dependencies


                # ── Existential component conflict ────────────────────────────────────
                if (exist_locked is not None) and (exist_dep is not None) and (exist_locked != exist_dep):


                    print(f"\nThe locked trasnitive existential dependency is:    ({from_act} {dep_label_exist(exist_locked)} {to_act})")
                    print(f"The requested existential dependency by transitivity is: ({from_act} {dep_label_exist(exist_dep)} {to_act})")

                    # get the temporal dependencies involved 

                    options = ["Remove existential input dependency (" + str(from_act) + " " + str(dep_label_exist(deps[(from_act, activity)][1])) + " " + str(activity) + ")", 
                            "Remove existential input dependency (" + str(to_act) + " " + str(dep_label_exist(deps[(to_act, activity)][1])) + " " + str(activity) + ")",
                            "Discard change operation"
                            ]
                    
                    selection = choose("Choose one dependency to be removed, to resolve the conflict", options)

                    if "(" + str(from_act) in selection: 
                        # remove the temporal dependnecy including the from_act
                        temp_dep_current = deps[(from_act, activity)][0]

                        # modify the entry, by either deleting it if no exist dependency is locked, or modifying it 
                        if temp_dep_current is None:
                            del deps[(from_act, activity)]

                            # also delete other direction 
                            if (activity, from_act) in deps: 
                                del deps[(activity, from_act)]

                        else:
                            deps[(from_act, activity)] = (temp_dep_current, None)

                            # modify also the reverse entry 
                            deps[(activity, from_act)] = (reverse_dependency(temp_dep_current), None)

                    elif "(" + str(to_act) in selection: 
                        # remove the temporal dependnecy including the to_act
                        temp_dep_current = deps[(to_act, activity)][0]

                        # modify the entry, by either deleting it if no exist dependency is locked, or modifying it 
                        if temp_dep_current is None:
                            del deps[(to_act, activity)]

                            # also delete other direction 
                            if (activity, to_act) in deps: 
                                del deps[(activity, to_act)]

                        else:
                            deps[(to_act, activity)] = (temp_dep_current, None)

                            # modify also the reverse entry 
                            deps[(activity, to_act)] = (reverse_dependency(temp_dep_current), None)   

                    else: 
                        print("\n All modifications were suppressed by locked dependencies. No changes applied.")
                        return matrix, locked_dependencies
                    
        
    # ════════════════════════════════════════════════════════════════════════════
    #  Step 2: Try performance of the change operation  
    # ════════════════════════════════════════════════════════════════════════════

    try: 
        # try to perform the insert operation
        result = insert_activity(matrix, activity, deps)
    
    except ValueError as e: 
        # indicate to the user that the standard insert method does not work here 
        print("\nFor the insert operation there is a contradiction between the inputs, we use the skeleton approach to resolve it.")

        result = perform_skeleton_algorithm(matrix, deps, insert_activity=activity)


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

        result = perform_skeleton_algorithm(matrix, deps, insert_activity=activity)


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

            # check if the combined dependencies do not have a contradiction 
            # generate the skeleton sequences 
            skeleton_sequences = generate_skeleton(deps_to_matrix(combined))

            # check that the provided input does not have a contradiction in itself, preventing the creation of the skeleton sequences 
            if skeleton_sequences == [[]] or skeleton_sequences == [] or skeleton_sequences is None: 
                raise ValueError("The combination of the dependencies for the change operation and the dependencies from locked dependencies cause a contradiction")

            # perfom the skeleton approach
            result = perform_skeleton_algorithm(result, combined, insert_activity=activity)


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 4: Return the reuslt to the user
    # ════════════════════════════════════════════════════════════════════════════

    return result, locked_dependencies