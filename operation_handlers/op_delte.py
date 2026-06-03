# ── Core imports ────────────────────────────────────────────────────────────
from adjacency_matrix import AdjacencyMatrix

# ── Change-operation imports ─────────────────────────────────────────────────
from change_operations.delete_operation    import delete_activity

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


def op_delete(matrix: AdjacencyMatrix, locked_dependencies):
    """
    Operation handler for deleting an activity from the process

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
    #  Step 1: Get the reuqired input from teh user 
    # ════════════════════════════════════════════════════════════════════════════

    # verify that the activity is part of the process
    while True: 
        # get the activity 
        activity = prompt("Activity to delete")   

        if activity not in matrix.activities: 
            print(f"  ✗  Activity '{activity}' is not part of the process") 
            continue

        break
        

    # ════════════════════════════════════════════════════════════════════════════
    #  Check for violations of locked dependencies, which can not be resolved 
    # ════════════════════════════════════════════════════════════════════════════

    # define a set of involved locks for the set of activities affected 
    involved_locks = [(from_act, to_act) for (from_act, to_act) in locked_dependencies if from_act == activity or to_act == activity]
    
    # inform the user with a banner 
    if involved_locks: 
        banner("Check for unresolvable violations to locked dependencies")

        # inform the user that the activity to de-collapse has locked dependencies
        print(f"\nActivity '{activity}' for deletion has locked dependencies to other activities of the process")
        print("Deletion would violate the locked dependencies.")
        print("If the locked dependencies are uphold, the change operation becomes infesible.")
        print("The following list provides an overview of the affected locked dependencies:")

    # provide a list of the effected dependencies
    for (from_act, to_act) in involved_locks: 
        
        # get the effected dependencies 
        temp, exist = locked_dependencies[(from_act, to_act)]

        temp_str = dep_label_temp(temp) + " " if temp is not None else ""
        exist_str = dep_label_exist(exist) + " " if exist is not None else ""

        print(f"   - ({from_act} {temp_str}, {exist_str} {to_act})")

    # ask the user if the dependency should be deleted to perfom the change operation 
    if confirm("\nDo you want to delete all the locked dependencies, to be able to perfom the change operation 'delete'?"): 
        # delete the entry from the locked dependencies 
        for (from_act, to_act) in involved_locks: 
            # chek that the entry is contained 
            if (from_act, to_act) in locked_dependencies: 
                del locked_dependencies[(from_act, to_act)]

                # delete the reverse entry 
                if (to_act, from_act) in locked_dependencies: 
                    del locked_dependencies[(to_act, from_act)]

    else: 
        # if the user does not accept, change operation is not possible and we return an error 
        raise ValueError("Delete can not be performed when there are locked dependencies which would be violated")
        

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 2: Try performance of the change operation  
    # ════════════════════════════════════════════════════════════════════════════

    result = delete_activity(matrix, activity)

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
            
            # For delete no combined dependnecies are need, just delete the activity and setup already done before 

            # inform the user that the skeleton is used 
            banner("Using skeleton to resolve violations of locked dependencies")
            print("\nUsing dependency relaxation was unable to resolve (all) violations.")

            # perfom the skeleton approach
            result = perform_skeleton_algorithm(result, locked_dependencies)


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 4: Return the reuslt to the user
    # ════════════════════════════════════════════════════════════════════════════

    return result, locked_dependencies