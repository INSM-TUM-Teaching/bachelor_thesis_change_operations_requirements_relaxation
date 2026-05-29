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

# TODO
# allow to import locked dependencies using a YAML file 

def get_locked_dependencies(matrix: AdjacencyMatrix) -> Dict[
        Tuple[str, str],
        Tuple[Optional[TemporalDependency], Optional[ExistentialDependency]]
    ]: 
    """
    Ask the user, based on the adjacency matrix, which dependencies should be locked to be preserved 

    Args:
        matrix: the original matrix, used to get the activities and types to be locked  

    Returns: 
        dictionary of the locked dependencies with the activities and the dependency type 
    """

    # get the list of activities from the matrix 
    activities = matrix.activities

    # define the dictionary to store the locked dependencies 
    deps: dict = {}

    # ask the user to enter the dependnecies, he wants to lock, we can only lock what is in the process 
    print("\n  Enter dependencies (empty 'from' to stop) to be locked:")
    while True:
        from_act = prompt("\n    From activity (or blank to finish)")
        if not from_act:
            break
        if from_act not in activities:
            print(f"  ✗  '{from_act}' is not in the current activity list: {activities}")
            continue
        to_act = prompt("    To activity")
        if to_act not in activities:
            print(f"  ✗  '{to_act}' is not in the activity list.")
            continue

        # ask the user which dependency type should be locked 
        if confirm("Lock temporal dependency?"):
            temp, _ = matrix.get_dependency(from_act, to_act)
        else: 
            temp = None

        if confirm("Lock existential dependency?"):
            _, exist = matrix.get_dependency(from_act, to_act)
        else: 
            exist = None
        
        # insert the locked dependency in the dict
        deps[(from_act, to_act)] = (temp, exist)

        # insert the opposite direction also 
        deps[(to_act, from_act)] = (reverse_dependency(temp), reverse_dependency(exist))

    
    return deps

def reverse_dependency(dependency): 
    """
    For given depenency, reverse its direction. This method works for a dependency, regardless if existential or temporal 

    Args: 
        dependency: dependency (either temproal or existential)

    Returns: 
        dependency with reversed directions 
    """

    # filter the case, that the dependency is none (eg. for locked dependencies)
    if dependency is None:
        return None

    # cretae a depency map dictionary, map every direction to its reversed direction 
    direction_map = {
        Direction.FORWARD: Direction.BACKWARD,
        Direction.BACKWARD: Direction.FORWARD,
        Direction.BOTH: Direction.BOTH,
    }
    
    # get the reverse direction 
    reversed_direction = direction_map[dependency.direction]

    # return the dependency with the reversed direction
    if isinstance(dependency, TemporalDependency):
        return TemporalDependency(dependency.type, direction=reversed_direction)
    elif isinstance(dependency, ExistentialDependency):
        return ExistentialDependency(dependency.type, direction=reversed_direction)
    else:
        raise TypeError(f"Unsupported dependency type: {type(dependency)}")


def is_violated(
    old_dependency: Tuple[TemporalDependency | None, ExistentialDependency | None] | None,
    new_dependency: Tuple[TemporalDependency | None, ExistentialDependency | None] | None,
) -> bool:
    """
    For a pair of dependencies, check if they are different. 
    For locked dependencies the difference would imply a violation

    Returns: 
        bool: true if there is a violation, false if they are the same 
    """
    if old_dependency is None or new_dependency is None:
        return old_dependency != new_dependency

    old_temp, old_exist = old_dependency
    new_temp, new_exist = new_dependency

    # Only check components that were actually locked (non-None)
    if old_temp is not None and old_temp != new_temp:
        return True
    if old_exist is not None and old_exist != new_exist:
        return True

    return False
    

def is_relaxation(
    old_dependency: Tuple[TemporalDependency | None, ExistentialDependency | None] | None,
    new_dependency: Tuple[TemporalDependency | None, ExistentialDependency | None] | None,
) -> bool:
    """
    For provided dependencies, check if they are a relaxation of each other.
    A relaxation requires at least one component (temporal or existential) to be
    relaxed, while the other is either also relaxed or completely unchanged.

    Returns: 
        bool: true if one of the dimensions is a relaxation, while the others remained without a violation 
    """

    old_temp, old_exist = old_dependency
    new_temp, new_exist = new_dependency

    # locked temporal dependency 
    if old_temp is not None: 
        if is_temp_relaxation(old_temp, new_temp): 
            return True
        
    # locked existential dependency 
    if old_exist is not None: 
        if is_exist_relaxation(old_exist, new_exist): 
            return True
    
    # if neither temporal nor existential relaxation, return false 
    return False

    
def is_temp_relaxation(old_temp_dep: TemporalDependency, new_temp_dep: TemporalDependency): 
    """
    For temporal dependencies, check if it is a relaxation (old is direct and new is eventual)
    """
    if new_temp_dep is None:
        return False
    
    return (
        old_temp_dep.type == TemporalType.DIRECT
        and new_temp_dep.type == TemporalType.EVENTUAL
        and old_temp_dep.direction == new_temp_dep.direction
    )

def is_exist_relaxation(old_exist_dep: TemporalDependency, new_exist_dep: TemporalDependency): 
    """
    For existential dependencies, check if it is a relaxation, using the in the thesis defined relaxations

    Returns: 
        bool: true if it is a relxataion (only for relaxations and not for the same type)
    """

    return (
        (old_exist_dep.type == ExistentialType.EQUIVALENCE and new_exist_dep.type == ExistentialType.IMPLICATION) 
        or (old_exist_dep.type == ExistentialType.NEGATED_EQUIVALENCE and 
            (new_exist_dep.type == ExistentialType.NAND or new_exist_dep.type == ExistentialType.OR))
    )
    


def are_locked_dependencies_violated(locked_dependencies, matrix): 
    """
    Based on the list of locked depencies and their type, check if the matrix meets these conditions

    Args: 
        locked_dependencies: dict of the locked dependencies 
        matrix: adjacency matrix, for this we check if the dependnecies match the locked dependencies 
    
    Returns: 
        bool: true if 
    """
    exist_violations = False

    # check if there are any violations 
    for (from_act, to_act), locked_dep in locked_dependencies.items():
            
        # get the dependency type from the modified matrix 
        new_dependency = matrix.get_dependency(from_act, to_act)

        # check if it is violated, if yes check for relaxation 
        if is_violated(locked_dep, new_dependency):
            exist_violations = True
            break

    return exist_violations