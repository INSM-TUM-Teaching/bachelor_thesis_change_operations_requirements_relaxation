from typing import List, Dict, Tuple
from adjacency_matrix import AdjacencyMatrix
from optimized_acceptance_variants import generate_optimized_acceptance_variants as generate_acceptance_variants
from dependencies import TemporalType, ExistentialType


def _dependencies_equal(dep1, dep2) -> bool:
    """Check if two dependencies are equal, treating INDEPENDENCE as equivalent to None."""
    is_independence_or_none_1 = dep1 is None or (hasattr(dep1, 'type') and dep1.type == TemporalType.INDEPENDENCE) or (hasattr(dep1, 'type') and dep1.type == ExistentialType.INDEPENDENCE)
    is_independence_or_none_2 = dep2 is None or (hasattr(dep2, 'type') and dep2.type == TemporalType.INDEPENDENCE) or (hasattr(dep2, 'type') and dep2.type == ExistentialType.INDEPENDENCE)
    
    if is_independence_or_none_1 and is_independence_or_none_2:
        return True
    if is_independence_or_none_1 or is_independence_or_none_2:
        return False
    return dep1.type == dep2.type and dep1.direction == dep2.direction


def locked_dependencies_preserved(initial_matrix: AdjacencyMatrix, modified_matrix: AdjacencyMatrix, locked_dependencies: Dict[Tuple[str, str], Tuple[bool, bool]], deletion_allowed: List[str]) -> bool:
    """
    Check if provided constraints are fulfilled, meaning that dependencies which are locked are not modified when applying the change operation 
    
    Args:
        initial_matrix: The adjacency matrix before performing the change operation
        modified_matrix: The adjacency matrix after performing the change operation
        locked_dependencies: List of dependencies which are locked (activity1, activity2, dependency_type) which should be ensured. The first tuples describes the activities and the second one (temporal, dependency) 
        describes which of the depencies are locked  
        deletion_allowed: List of activities that are allowed to be deleted without violating a locked dependency.
        
    Returns:
        Boolean value, depending on, if the check passes. If the dependencies are preserved, return true, else return false
        
    """
    initial_dependencies = initial_matrix.get_dependencies()

    for (source, target), (temp_locked, exist_locked) in locked_dependencies.items():

        source_deleted = source not in modified_matrix.get_activities()
        target_deleted = target not in modified_matrix.get_activities()

        if source_deleted and source not in deletion_allowed and exist_locked:
            return False
        
        if target_deleted and target not in deletion_allowed and exist_locked:
            return False
                
        if not source_deleted and not target_deleted:
            dependency = modified_matrix.get_dependency(source, target)
            if dependency is not None: 
                modi_temp_dep, modi_exist_dep = dependency
                temporal_dependency, existential_dependency = initial_dependencies.get((source, target), (None, None))

                if temp_locked and not _dependencies_equal(modi_temp_dep, temporal_dependency):
                    return False
                if exist_locked and not _dependencies_equal(modi_exist_dep, existential_dependency):
                    return False
        
    return True


def get_violated_locked_dependencies(
    initial_matrix: AdjacencyMatrix,
    modified_matrix: AdjacencyMatrix,
    locked_dependencies: Dict[Tuple[str, str], Tuple[bool, bool]],
    deletion_allowed: List[str]
) -> Dict[Tuple[str, str], Tuple[bool, bool]]:
    """
    Returns a dictionary of violated locked dependencies, indicating whether the temporal and/or existential 
    constraint was violated for each dependency.

    Args:
        initial_matrix: The adjacency matrix before performing the change operation.
        modified_matrix: The adjacency matrix after performing the change operation.
        locked_dependencies: Dictionary where key is (source, target) and value is (temporal_locked, existential_locked).
        deletion_allowed: List of activities that are allowed to be deleted without violating a locked dependency.

    Returns:
        A dictionary mapping (source, target) to a tuple (temporal_violated, existential_violated). It so indicates which dependencies were violated
    """
    violations: Dict[Tuple[str, str], Tuple[bool, bool]] = {}
    initial_dependencies = initial_matrix.get_dependencies()


    for (source, target), (temp_locked, exist_locked) in locked_dependencies.items():
        temporal_violated = False
        existential_violated = False

        source_deleted = source not in modified_matrix.get_activities()
        target_deleted = target not in modified_matrix.get_activities()

        if source_deleted and source not in deletion_allowed:
            if exist_locked:
                existential_violated = True
        
        if target_deleted and target not in deletion_allowed:
            if exist_locked:
                existential_violated = True

        if not source_deleted and not target_deleted:
            dependency = modified_matrix.get_dependency(source, target)
            if dependency is not None:
                modi_temp_dep, modi_exist_dep = dependency
                temporal_dependency, existential_dependency = initial_dependencies.get((source, target), (None, None))

                if temp_locked and not _dependencies_equal(modi_temp_dep, temporal_dependency):
                    temporal_violated = True
                if exist_locked and not _dependencies_equal(modi_exist_dep, existential_dependency):
                    existential_violated = True

        if temporal_violated or existential_violated:
            violations[(source, target)] = (temporal_violated, existential_violated)

    return violations