# ── Core imports ────────────────────────────────────────────────────────────
from adjacency_matrix import AdjacencyMatrix
from dependencies import (
    TemporalDependency, ExistentialDependency,
    TemporalType, ExistentialType, Direction,
)

# ── Change-operation imports ─────────────────────────────────────────────────
from change_operations.swap_operation      import swap_activities

# ── Skeleton algorithm ─────────────────────────────────────────────────
from solution_strategies.skeleton_strategies import perform_skeleton_algorithm

# ── Helper functions ─────────────────────────────────────────────────
from utils.console_helpers import banner
from utils.console_helpers import prompt
from utils.console_helpers import confirm
from utils.console_helpers import dep_label_temp

# ── Locked dependency functions ─────────────────────────────────────────────────
from utils.utils_lock_dependencies import are_locked_dependencies_violated

# ── Dependency relaxation ─────────────────────────────────────────────────
from utils.dependency_relaxation import perform_dependency_relaxation

# ── reverse dependency ─────────────────────────────────────────────────
from utils.console_helpers import reverse_dependency


def op_swap(matrix: AdjacencyMatrix, locked_dependencies):
    """
    Operation handler for swap a pair of activities

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

    print(f"\n  Current activities: {matrix.activities}")

    while True: 
        act1 = prompt("First activity")

        if act1 not in matrix.activities: 
            print(f"  ✗  Activity '{act1}' is not in the process")
            continue

        break

    while True: 
        act2 = prompt("Second activity")

        if act2 not in matrix.activities: 
            print(f"  ✗  Activity '{act2}' is not in the process")
            continue

        break

    # ════════════════════════════════════════════════════════════════════════════
    #  Check for violations of locked dependencies, which can not be resolved 
    # ════════════════════════════════════════════════════════════════════════════

    # check if the activities to be swapped have a locked dependency 
    if (act1, act2) in locked_dependencies: 
        locked_temp, locked_exist = locked_dependencies[(act1, act2)]

        # check that the pair has a locked temp. dependency and that it is not indpendence; meaning swap must cause a violation 
        if (locked_temp is not None) and (locked_temp.type != TemporalType.INDEPENDENCE):

            # inform the user 
            banner("Check for unresolvable violations to locked dependencies")

            # inform the user that the activity to de-collapse has locked dependencies
            print(f"\nThe activities to swap have a locked temporal dependency ({act1} {dep_label_temp(locked_temp)} {act2})")
            print(f"To be able to perfom the swap, the locked temporal dependency must be deleted.")
            
            # ask the user if the dependency should be deleted to perfom the change operation 
            if confirm("\nDo you want to delete the locked temporal dependency (otherwise the change operation can not be performed)?"): 
                # delete the entry from the locked dependencies 
                del locked_dependencies[(act1, act2)]

                # also delete the reverse
                if (act2, act1) in locked_dependencies: 
                    del locked_dependencies[(act2, act1)]

                # if there is a locked existential dependency, reinsert it 
                if locked_exist is not None: 
                    locked_dependencies[(act1, act2)] = (None, locked_exist)

                    # reinsert the revers 
                    locked_dependencies[(act2, act1)] = (None, reverse_dependency(locked_exist))

                print(f"\n  ✓  The temporal dependency between activities '{act1}' and '{act2}' were deleted.")

            else: 
                # if the user does not accept, change operation is not possible and we return an error 
                raise ValueError("Swap can not be performed when there are locked dependencies which would be violated")
     
    

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 2: Try performance of the change operation  
    # ════════════════════════════════════════════════════════════════════════════

    result = swap_activities(matrix, act1, act2)

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
            # if they becirehand had temproal dependnecies, they should afterwards be changed 
            modified_locked_dependencies = locked_dependencies

            # get the temporal dependencies from the matrix 
            deps = matrix.get_dependency(act1, act2)

            if deps is not None: 
                original_temp_dep, _ = deps

                # check if the original temporal dependency is unequal to independence; if this is the case, we invert their order  
                if (original_temp_dep is not None) and (original_temp_dep.type is not TemporalType.INDEPENDENCE): 

                    # get the inverted dependency type 
                    inverted_temp_dep = reverse_dependency(original_temp_dep)

                    # if pair already in locked dependencies, we must only modify the temporal dependency component 
                    if (act1, act2) in modified_locked_dependencies: 
                        # get the locked existential dependency 
                        _, exist_dep = modified_locked_dependencies[(act1, act2)]

                        # overwrite the entries 
                        modified_locked_dependencies[(act1, act2)] = (inverted_temp_dep, exist_dep)
                        modified_locked_dependencies[(act2, act1)] = (original_temp_dep, reverse_dependency(exist_dep))

                    # if not already part, we must add the entry oto the locked dependencies
                    else: 
                        
                        # add the temporal dependencies to the modified locked dependencies, without an existential component 
                        modified_locked_dependencies[(act1, act2)] = (inverted_temp_dep, None)
                        modified_locked_dependencies[(act2, act1)] = (original_temp_dep, None)

                
            banner("Using skeleton to resolve violations of locked dependencies")
            print("\nUsing dependency relaxation was unable to resolve (all) violations.")

            # perfom the skeleton approach
            result = perform_skeleton_algorithm(result, modified_locked_dependencies)


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 4: Return the reuslt to the user
    # ════════════════════════════════════════════════════════════════════════════

    return result, locked_dependencies