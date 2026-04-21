from enum import Enum, auto
from dataclasses import dataclass


class Direction(Enum):
    """
    Defines the direction of a dependency.
    """

    FORWARD = auto()
    BACKWARD = auto()
    BOTH = auto()

    @classmethod
    def from_yaml(cls, yaml_direction_str: str) -> "Direction":
        """Converts a YAML string type to a Direction enum member."""
        mapping = {
            "forward": cls.FORWARD,
            "backward": cls.BACKWARD,
            "both": cls.BOTH,
        }
        lower_value = yaml_direction_str.lower()
        if lower_value not in mapping:
            raise ValueError(
                f"Unknown direction string from YAML: '{yaml_direction_str}'"
            )
        return mapping[lower_value]


class TemporalType(Enum):
    """
    Defines the type of temporal relationship between two activities.
    """

    DIRECT = auto()
    EVENTUAL = auto()
    INDEPENDENCE = auto()

    @classmethod
    def from_yaml(cls, yaml_type_str: str) -> "TemporalType":
        """Converts a YAML string type to a TemporalType enum member."""
        mapping = {
            "direct": cls.DIRECT,
            "eventual": cls.EVENTUAL,
            "independence": cls.INDEPENDENCE,
        }
        lower_value = yaml_type_str.lower()
        if lower_value not in mapping:
            raise ValueError(
                f"Unknown temporal type string from YAML: '{yaml_type_str}'"
            )
        return mapping[lower_value]


@dataclass
class TemporalDependency:
    """
    Represents a temporal dependency between two activities.
    The direction is implicit from the (source, target) key in the main matrix.
    - If (A, B) maps to TemporalDependency(type=TemporalType.DIRECT), it means A <d B.
    - If (A, B) maps to TemporalDependency(type=TemporalType.EVENTUAL), it means A <e B.
    """

    type: TemporalType
    direction: Direction


class ExistentialType(Enum):
    """
    Defines the type of existential dependency between two activities.
    """

    IMPLICATION = auto()  # A => B: If A occurs, B must occur or must have occurred.
    EQUIVALENCE = auto()  # A <=> B: A => B and B => A.
    NEGATED_EQUIVALENCE = auto()  # A <~> B: Either A or B occurs (exclusive OR).
    NAND = auto()  # A | B: If A occurs, B does not, and vice versa; or neither occurs.
    OR = auto()  # A v B: At least one of A or B must occur.
    INDEPENDENCE = auto()  # A and B are existentially independent.

    @classmethod
    def from_yaml(cls, yaml_type_str: str) -> "ExistentialType":
        """Converts a YAML string type to an ExistentialType enum member."""
        mapping = {
            "implication": cls.IMPLICATION,
            "equivalence": cls.EQUIVALENCE,
            "negated equivalence": cls.NEGATED_EQUIVALENCE,
            "negated_equivalence": cls.NEGATED_EQUIVALENCE,
            "nand": cls.NAND,
            "or": cls.OR,
            "independence": cls.INDEPENDENCE,
        }
        lower_value = yaml_type_str.lower()
        if lower_value not in mapping:
            raise ValueError(
                f"Unknown existential type string from YAML: '{yaml_type_str}'"
            )
        return mapping[lower_value]


@dataclass
class ExistentialDependency:
    """
    Represents an existential dependency between two activities.
    The direction is implicit from the (source, target) key in the main matrix.
    For symmetric relationships (EQUIVALENCE, NEGATED_EQUIVALENCE, NAND, INDEPENDENCE),
    the entry (A,B) would be the same as (B,A).
    For IMPLICATION and OR, the direction matters.
    - If (A, B) maps to ExistentialDependency(type=ExistentialType.IMPLICATION), it means A => B.
    - If (A, B) maps to ExistentialDependency(type=ExistentialType.OR), it means A v B.
    """

    type: ExistentialType
    direction: Direction
