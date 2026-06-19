# ── Core imports ────────────────────────────────────────────────────────────
from adjacency_matrix import AdjacencyMatrix

# ── Change-operation imports ─────────────────────────────────────────────────
from change_operations.de_collapse_operation import decollapse_operation

# ── Skeleton algorithm ─────────────────────────────────────────────────
from solution_strategies.skeleton_strategies import perform_skeleton_algorithm

# ── Helper functions ─────────────────────────────────────────────────
from utils.console_helpers import banner
from utils.console_helpers import prompt
from utils.console_helpers import choose
from utils.console_helpers import confirm
from utils.console_helpers import dep_label_temp
from utils.console_helpers import dep_label_exist

# ── Locked dependency functions ─────────────────────────────────────────────────
from utils.utils_lock_dependencies import are_locked_dependencies_violated

# ── Dependency relaxation ─────────────────────────────────────────────────
from utils.dependency_relaxation import perform_dependency_relaxation

# ── Load process models ─────────────────────────────────────────────────
from utils.load_process_models import load_from_sequences
from utils.load_process_models import load_from_yaml


def op_decollapse(matrix: AdjacencyMatrix, locked_dependencies):
    """
    Operation handler for decollapse an activity 

    1) get the required input from the user and validate it 
    2) Check for violations of locked dependencies which can not be resolved 
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

    # ensure the activity is in the process 
    while True: 
        collapsed_act = prompt("Activity to de-collapse")

        if collapsed_act not in matrix.activities: 
            print(f"  ✗  '{collapsed_act}' is not in the activity list of the process: {matrix.activities}")
            continue
    
        break 

    print("\n  Provide the sub-process matrix for the collapsed activity:")
    sub_choice = choose(
        "Load sub-process model from:",
        ["YAML file", "Acceptance sequences (manual input)"],
    )
    
    if sub_choice == "YAML file":
        while True:
            sub_matrix = load_from_yaml()
            duplicates = [a for a in sub_matrix.activities if a in matrix.activities]
            if not duplicates:
                break
            print(f"  ✗  Activities {duplicates} already exist in the main process; provide a sub-process with unique activities")
    else:
        while True:
            sub_matrix = load_from_sequences()
            duplicates = [a for a in sub_matrix.activities if a in matrix.activities]
            if not duplicates:
                break
            print(f"  ✗  Activities {duplicates} already exist in the main process; provide a sub-process with unique activities")

    
    # ════════════════════════════════════════════════════════════════════════════
    #  Check for violations of locked dependencies, which can not be resolved 
    # ════════════════════════════════════════════════════════════════════════════

    # define a set of involved locks for the set of activities affected 
    involved_locks = [(from_act, to_act) for (from_act, to_act) in locked_dependencies if from_act == collapsed_act or to_act == collapsed_act]
    
    # inform the user with a banner 
    if involved_locks: 
        banner("Check for the requierement to alter a locked dependency")

        # inform the user that the activity to de-collapse has locked dependencies
        print(f"\nActivity '{collapsed_act}' has locked dependencies to other activities of the process")
        print("De-collapsing would violate the locked dependencies.")
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
        if confirm("\nDo you want to delete all the locked dependencies, to be able to perfom the change operation 'collapse'?"): 
            # delete the entry from the locked dependencies 
            for (from_act, to_act) in involved_locks: 
                # delete the entry 
                if (from_act, to_act) in locked_dependencies: 
                    del locked_dependencies[(from_act, to_act)]

                    # delete the reverse 
                    if (to_act, from_act) in locked_dependencies: 
                        del locked_dependencies[(to_act, from_act)]

        else: 
            # if the user does not accept, change operation is not possible and we return an error 
            raise ValueError("'Collapse' can not be performed when there are locked dependencies which would be violated")


    # ════════════════════════════════════════════════════════════════════════════
    #  Step 2: Try performance of the change operation  
    # ════════════════════════════════════════════════════════════════════════════

    result = decollapse_operation(matrix, collapsed_act, sub_matrix)

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