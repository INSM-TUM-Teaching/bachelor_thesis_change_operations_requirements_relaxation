"""

"""

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
from change_operations.delete_operation    import delete_activity
from change_operations.insert_operation    import insert_activity
from change_operations.modify_operation    import modify_dependencies
from change_operations.move_operation      import move_activity
from change_operations.swap_operation      import swap_activities
from change_operations.skip_operation      import skip_activity
from change_operations.replace_operation   import replace_activity
from change_operations.collapse_operation  import collapse_operation
from change_operations.de_collapse_operation import decollapse_operation
from change_operations.parallelize_operation import parallelize_activities
from change_operations.condition_update    import condition_update

# ── Change-operation helper functions imports ─────────────────────────────────────────────────
from change_operations.parallelize_operation import get_activities_happening_between

# ── Change-operation solution strategies imports ─────────────────────────────────────────────────
from modified_change_operations.parallelization_strategies import parallelize_expand_set
from modified_change_operations.parallelization_strategies import parallelize_move_activities
from modified_change_operations.collapse_strategies import collapse_expand_set
from modified_change_operations.collapse_strategies import collapse_move_activities
from modified_change_operations.skeleton_strategies import adapt_acceptance_skeleton

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
from utils.utils_lock_dependencies import is_violated


def perform_dependency_relaxation(matrix, locked_dependencies):
    """
    For a given matrix and the locked dependency, for each locked dependency check if it holds 
    If there is a violation, ask if the user wants to relax it 

    Args: 
        matrix: Adjacency matrix of the process 
        locked_dependencies: Dict of the locked dependencies 

    Return: 
        updated dict of locked dependencies based on dependency relaxation 
        indicator if there are still violations of the locked dependencies

    """  
    # our status variable exist_violations is set to False 
    exist_violations = False

    # inform the user, that locked dependnecies were violated
    banner("Step 4: Resolve violations of locked dependencies")
    print("\nThe performance of the change operation caused a violation of the locked dependencies.")

    # we know there are violations, check if they can be solved using dependency relaxation  
    for (from_act, to_act), locked_dep in locked_dependencies.items():
        
        # get the dependency type from the modified matrix 
        new_dependency = matrix.get_dependency(from_act, to_act)

        # check if it is violated, if yes check for relaxation 
        if is_violated(locked_dep, new_dependency): 

            ###########################################
            # we reach this point 
            print(f"\n The locked dependency from activity {from_act} to activity {to_act} is violated")

            # check if the dependency is a relaxation and ask the user, if he accepts the relaxation
            if is_relaxation(locked_dep, new_dependency): 

                # extract the dependency types, to provide them to the user as information 
                locked_temp_dep, locked_exist_dep = locked_dep
                new_temp_dep, new_exist_dep = new_dependency

                # ask the user, if applicable, to relax the existential dependency 
                if (locked_exist_dep is not None and new_exist_dep is not None
                    and is_exist_relaxation(locked_exist_dep, new_exist_dep)): 

                    if confirm(f"Do you want to relax the existential dependency between activities {from_act, to_act} from dependency \n type {dep_label_exist(locked_exist_dep)} to the relaxed dependency type {dep_label_exist(new_exist_dep)}?"): 
                        # if the user agrees on the relaxation, adapt the locked dependencies accordingly 
                        locked_dependencies[(from_act, to_act)] = (locked_temp_dep, new_exist_dep)
                        
                        # update the variable of the locked dependency, used for the relaxation of the temporal dependency
                        locked_exist_dep = new_exist_dep
                    
                    else: 
                        # there is a difference, which can be seen as a relaxation, but the user does not want to see it as a relxation 
                        # we have a violation of a locked dependency
                        exist_violations = True


                # ask the user, if applicable, to relax the temporal dependency 
                if (locked_temp_dep is not None and new_temp_dep is not None
                    and is_temp_relaxation(locked_temp_dep, new_temp_dep)):

                    if confirm(f"Do you want to relax the temporal dependency between activities {from_act, to_act} from the dependency type {dep_label_temp(locked_temp_dep)} to the relaxed dependency type {dep_label_temp(new_temp_dep)}?"): 
                        # if the user agrees on the relaxation, adapt the locked dependencies accordingly 
                        locked_dependencies[(from_act, to_act)] = (new_temp_dep, locked_exist_dep)
                    
                    else: 
                        # there is a difference, which can be seen as a relaxation, but the user does not want to see it as a relxation 
                        # we have a violation of a locked dependency
                        exist_violations = True

            else: 
                # if we do not have a relaxation but a violation, we need the skeleton approach 
                exist_violations = True

    # return the locked dependencies and the indicator if there are still violations 
    return locked_dependencies, exist_violations