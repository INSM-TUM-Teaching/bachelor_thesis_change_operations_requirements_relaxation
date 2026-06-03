# ── Core imports ────────────────────────────────────────────────────────────
from adjacency_matrix import AdjacencyMatrix

# ── Change-operation imports ─────────────────────────────────────────────────
from change_operations.replace_operation   import replace_activity

# ── Skeleton algorithm ─────────────────────────────────────────────────
from solution_strategies.skeleton_strategies import perform_skeleton_algorithm

# ── Helper functions ─────────────────────────────────────────────────
from utils.console_helpers import banner
from utils.console_helpers import prompt
from utils.console_helpers import confirm
from utils.console_helpers import dep_label_temp
from utils.console_helpers import dep_label_exist

# ── Locked dependency functions ─────────────────────────────────────────────────
from utils.utils_lock_dependencies import are_locked_dependencies_violated

# ── Dependency relaxation ─────────────────────────────────────────────────
from utils.dependency_relaxation import perform_dependency_relaxation

# ── Dependency reverse ─────────────────────────────────────────────────
from utils.console_helpers import reverse_dependency



def op_replace(matrix: AdjacencyMatrix, locked_dependencies):
    """
    Operation handler for replace an activity from the process with another

    1) get the required input from the user and validate it 
    2) Check for violations which can not be resolved 
    3) Perform the change operation 
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

                # delete also the reverse 
                if (to_act, from_act) in locked_dependencies:
                    del locked_dependencies[(to_act, from_act)] 

            print(f"\n  ✓  Locked dependencies involving activity '{old_act}' are deleted.")

        else: 
            # transfer all the locked dependencies to the new activity 
            for (from_act, to_act) in involved_locks: 
                # get the dependencies
                locked_temp, locked_exist = locked_dependencies[(from_act, to_act)]

                # delete the old entry
                del locked_dependencies[(from_act, to_act)]

                # delete the reverse entry 
                if (to_act, from_act) in locked_dependencies: 
                    del locked_dependencies[(to_act, from_act)]

                # add the new entry with the new activity 
                if from_act == old_act: 
                    locked_dependencies[(new_act, to_act)] = (locked_temp, locked_exist)
                    
                    # insert the reverse also to the locked dependencies 
                    locked_dependencies[(to_act, new_act)] = (reverse_dependency(locked_temp), reverse_dependency(locked_exist))
                else: 
                    locked_dependencies[(from_act, new_act)] = (locked_temp, locked_exist)

                    # insert the reveresed dependencies also to the locked dependnecies
                    locked_dependencies[(new_act, from_act)] = (reverse_dependency(locked_temp), reverse_dependency(locked_exist))

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

            banner("Using skeleton to resolve violations of locked dependencies")
            print("\nUsing dependency relaxation was unable to resolve (all) violations.")

            # perfom the skeleton approach
            result = perform_skeleton_algorithm(result, locked_dependencies)


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 4: Return the reuslt to the user
    # ════════════════════════════════════════════════════════════════════════════

    return result, locked_dependencies