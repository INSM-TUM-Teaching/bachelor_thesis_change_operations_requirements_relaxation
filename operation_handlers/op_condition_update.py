# ── Core imports ────────────────────────────────────────────────────────────
from adjacency_matrix import AdjacencyMatrix

# ── Change-operation imports ─────────────────────────────────────────────────
from change_operations.condition_update    import condition_update

# ── Skeleton algorithm ─────────────────────────────────────────────────
from solution_strategies.skeleton_strategies import perform_skeleton_algorithm

# ── Helper functions ─────────────────────────────────────────────────
from utils.console_helpers import banner
from utils.console_helpers import prompt

# ── Locked dependency functions ─────────────────────────────────────────────────
from utils.utils_lock_dependencies import are_locked_dependencies_violated

# ── Dependency relaxation ─────────────────────────────────────────────────
from utils.dependency_relaxation import perform_dependency_relaxation


def op_condition_update(matrix: AdjacencyMatrix, 
                        locked_dependencies
):
    """
    Operation handler for cconditional update: an activity can only occur if another activity occurs (conditional activity) and perform the check for violations of 
    locked dependencies 

    1. get the required input from the user and validate it 
    2. Check for violations which can not be resolved 
    3. Perform the change operation 
    4. Check for violations of locked dependencies 
    4.1. Apply dependency relaxation 
    4.2. Apply the skeleton strategy 
    5. return the new matrix and the (modified) locked dependencies 

    Args: 
        matrix: Adacency of the matrix to perform the change operation on 
        locked_dependencies: dict of locked dependencies

    Returns: 
        modified matrix 
        locked_dependencies after potential relaxations
    """

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 1: Get the reuqired input from teh user 
    # ════════════════════════════════════════════════════════════════════════════

    print(f"\n  Current activities: {matrix.activities}")
    print("\n  Specify the condition-update activities:")

    while True:
        condition_activity = prompt("Condition activity")
        if condition_activity not in matrix.activities:
            print(f"  ✗  '{condition_activity}' is not in the current activity list: {matrix.activities}")
            continue

        break

    while True: 
        depending_activity = prompt("Depending activity")
        if depending_activity not in matrix.activities:
            print(f"  ✗  '{depending_activity}' is not in the current activity list: {matrix.activities}")
            continue
        
        if depending_activity == condition_activity: 
            print(f"  ✗  '{depending_activity}' can not be defined as self-depending, please insert a differnt activity")
            continue

        break

    # ════════════════════════════════════════════════════════════════════════════
    #  Step 2: Try performance of the change operation  
    # ════════════════════════════════════════════════════════════════════════════

    result = condition_update(matrix, condition_activity, depending_activity)

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

            banner("Using skeleton to resolve violations of locked dependencies")
            print("\nUsing dependency relaxation was unable to resolve (all) violations.")
            
            # perfom the skeleton approach
            result = perform_skeleton_algorithm(result, locked_dependencies)


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 4: Return the reuslt to the user
    # ════════════════════════════════════════════════════════════════════════════

    return result, locked_dependencies