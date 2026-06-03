from typing import Tuple, Optional, Dict, List
from utils.check_contradictions import has_temporal_contradiction, has_existential_contradiction
from utils.split_dependencies import split_dependencies
from dependencies import (
    TemporalDependency,
    ExistentialDependency,
)

def is_valid_input(
    activities,
    new_activities,
    activity: str,
    variants: List[List[str]],
    total_dependencies: Dict[
        Tuple[str, str],
        Tuple[Optional[TemporalDependency], Optional[ExistentialDependency]],
    ],
) -> bool:
    """
    Checks if input is valid

    Args:
        activities: All activities from original matrix.
        new_activites: All activities from original matrix and activity to be inserted.
        activity: The name of the activity to insert.
        variants: All variants reslting from matrix.
        total_dependencies: The dependencies defining the position of the activity to be inserted.

    Returns:
        True: If input is valid
        False: If input is invalid
    """
    temporal_deps, existential_deps = split_dependencies(total_dependencies)

    if activity in activities:
        raise ValueError(f"The activity '{activity}' is already present in the matrix.")
    if has_existential_contradiction(existential_deps):
        raise ValueError("Existential dependencies cause a contradiction.")
    if has_temporal_contradiction(temporal_deps, existential_deps, new_activities, activity, variants):
        raise ValueError("Temporal dependencies cause a contradiction.")
    return True