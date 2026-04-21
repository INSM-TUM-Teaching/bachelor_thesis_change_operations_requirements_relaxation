from dataclasses import dataclass
import yaml
from typing import Dict, Tuple, List, Optional
from dependencies import (
    TemporalDependency,
    ExistentialDependency,
    TemporalType,
    ExistentialType,
    Direction,
)


@dataclass
class AdjacencyMatrix:
    """
    Represents an adjacency matrix for process activities,
    mapping pairs of activities to their temporal and existential dependencies.
    """

    dependencies: Dict[
        Tuple[str, str],
        Tuple[Optional[TemporalDependency], Optional[ExistentialDependency]],
    ]
    activities: List[str]

    def __init__(self, activities: List[str]):
        self.activities = activities
        self.dependencies = {}

    def add_dependency(
        self,
        from_activity: str,
        to_activity: str,
        temporal_dep: Optional[TemporalDependency],
        existential_dep: Optional[ExistentialDependency],
    ):
        """Adds a dependency to the matrix."""
        if from_activity not in self.activities or to_activity not in self.activities:
            raise ValueError("Activities must be in the predefined list of activities.")
        self.dependencies[(from_activity, to_activity)] = (
            temporal_dep,
            existential_dep,
        )

    def get_dependency(
        self, from_activity: str, to_activity: str
    ) -> Optional[Tuple[Optional[TemporalDependency], Optional[ExistentialDependency]]]:
        """Retrieves the dependency between two activities."""
        return self.dependencies.get((from_activity, to_activity))
    
    def get_dependencies(self) -> Dict[
        Tuple[str, str],
        Tuple[Optional[TemporalDependency], Optional[ExistentialDependency]]]:

        return self.dependencies
    
    def get_activities(self):
        return self.activities


def parse_yaml_to_adjacency_matrix(file_path: str) -> AdjacencyMatrix:
    """
    Parses a YAML file defining process dependencies into an AdjacencyMatrix.
    """
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    metadata = data.get("metadata", {})
    activities = metadata.get("activities", [])
    if not activities:
        raise ValueError("YAML file must define a list of activities in metadata.")

    matrix = AdjacencyMatrix(activities=activities)

    yaml_dependencies = data.get("dependencies", [])
    for dep in yaml_dependencies:
        from_activity = dep.get("from")
        to_activity = dep.get("to")

        if not from_activity or not to_activity:
            raise ValueError("Each dependency must specify 'from' and 'to' activities.")

        temporal_data = dep.get("temporal")
        temporal_dep_obj = None
        if temporal_data and temporal_data.get("type"):
            try:
                ttype = TemporalType.from_yaml(temporal_data["type"])
                tdirection = Direction.BOTH
                if ttype in [TemporalType.DIRECT, TemporalType.EVENTUAL]:
                    tdirection_str = temporal_data.get("direction", "forward")
                    tdirection = Direction.from_yaml(tdirection_str)
                temporal_dep_obj = TemporalDependency(type=ttype, direction=tdirection)
            except ValueError as e:
                print(
                    f"Warning: Skipping temporal dependency for ({from_activity}, {to_activity}) due to unknown type: {e}"
                )

        existential_data = dep.get("existential")
        existential_dep_obj = None
        if existential_data and existential_data.get("type"):
            try:
                etype = ExistentialType.from_yaml(existential_data["type"])
                edirection = Direction.BOTH
                if etype == ExistentialType.IMPLICATION:
                    edirection_str = existential_data.get("direction", "forward")
                    edirection = Direction.from_yaml(edirection_str)
                existential_dep_obj = ExistentialDependency(
                    type=etype, direction=edirection
                )
            except ValueError as e:
                print(
                    f"Warning: Skipping existential dependency for ({from_activity}, {to_activity}) due to unknown type: {e}"
                )

        matrix.add_dependency(
            from_activity, to_activity, temporal_dep_obj, existential_dep_obj
        )

    return matrix
