from typing import List, Tuple, Dict, Optional

# ── Core imports ────────────────────────────────────────────────────────────
from adjacency_matrix import AdjacencyMatrix, parse_yaml_to_adjacency_matrix
from dependencies import (
    TemporalDependency, ExistentialDependency,
    TemporalType, ExistentialType, Direction,
)
from variants_to_matrix import variants_to_matrix
from acceptance_variants import generate_acceptance_variants

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

# ── Reverse function for dependencies ─────────────────────────────────────────────────
from utils.console_helpers import reverse_dependency


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

        # ensure that we only ask in one direction, so we only use the correcty ordered pair 
        if from_act > to_act:
            continue

        # get the dependency type from the modified matrix 
        new_dependency = matrix.get_dependency(from_act, to_act)

        # check if it is violated, if yes check for relaxation 
        if is_violated(locked_dep, new_dependency): 

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

                        # also adapt the revrse 
                        locked_dependencies[(to_act, from_act)] = (reverse_dependency(locked_temp_dep), reverse_dependency(new_exist_dep))
                        
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

                        # also relax the reverse dependency 
                        locked_dependencies[(to_act, from_act)] = (reverse_dependency(new_temp_dep), reverse_dependency(locked_exist_dep))
                    
                    else: 
                        # there is a difference, which can be seen as a relaxation, but the user does not want to see it as a relxation 
                        # we have a violation of a locked dependency
                        exist_violations = True

            else: 
                # if we do not have a relaxation but a violation, we need the skeleton approach 
                exist_violations = True

    # return the locked dependencies and the indicator if there are still violations 
    return locked_dependencies, exist_violations