from typing import Tuple, Optional, Dict
from dependencies import (
    TemporalDependency,
    ExistentialDependency,
)


def split_dependencies(
    dependencies: Dict[
        Tuple[str, str],
        Tuple[Optional[TemporalDependency], Optional[ExistentialDependency]],
    ]
) -> Tuple[
    Dict[Tuple[str, str], TemporalDependency],
    Dict[Tuple[str, str], ExistentialDependency],
]:
    """
    Splits a dictionary of combined dependencies into separate dictionaries
    for temporal and existential dependencies.

    Args:
        dependencies: Dictionary with (temporal, existential) dependency tuples.

    Returns:
        A tuple with two dictionaries: (temporal_dependencies, existential_dependencies)
    """
    temporal_deps: Dict[Tuple[str, str], TemporalDependency] = {}
    existential_deps: Dict[Tuple[str, str], ExistentialDependency] = {}

    for (source, target), (temp_dep, exist_dep) in dependencies.items():
        if temp_dep:
            temporal_deps[(source, target)] = temp_dep
        if exist_dep:
            existential_deps[(source, target)] = exist_dep

    return temporal_deps, existential_deps