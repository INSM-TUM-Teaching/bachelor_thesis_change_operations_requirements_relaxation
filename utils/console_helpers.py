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


# ════════════════════════════════════════════════════════════════════════════
#  Small helpers
# ════════════════════════════════════════════════════════════════════════════

SEP = "─" * 60


def banner(text: str) -> None:
    print(f"\n{SEP}\n  {text}\n{SEP}")


def prompt(msg: str, default: str = "") -> str:
    # Show a prompt and return stripped input.  Ctrl-C exits gracefully.
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"  {msg}{suffix}: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\nBye!")
        sys.exit(0)
    return value if value else default


def choose(msg: str, options: list[str]) -> str:
    """Present a numbered menu and return the chosen option string."""
    print(f"\n  {msg}")
    for i, opt in enumerate(options, 1):
        print(f"    [{i}] {opt}")
    while True:
        raw = prompt("Enter number")
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("  ✗  Invalid choice – try again.")


def confirm(msg: str) -> bool:
    return prompt(f"{msg} (y/n)", "n").lower() == "y"


# ════════════════════════════════════════════════════════════════════════════
#  Matrix display
# ════════════════════════════════════════════════════════════════════════════

_W = 6  # fixed width for all symbols

def _dep_label(temporal, existential) -> str:
    parts = []

    if temporal: 
        temporal_name = dep_label_temp(temporal)
        parts.append(temporal_name.center(_W))

    if existential: 
        existential_name = dep_label_exist(existential)
        parts.append(existential_name.center(_W))

    return " , ".join(parts) if parts else "—".center(_W)

def dep_label_temp(temporal) -> str: 
    if temporal:
        if temporal.type == TemporalType.INDEPENDENCE:
            temporal_name = "-"
        elif temporal.type == TemporalType.DIRECT:
            if temporal.direction == Direction.FORWARD:
                temporal_name = "<_d"
            elif temporal.direction == Direction.BACKWARD:
                temporal_name = ">_d"
            else:  # BOTH
                temporal_name = "<>_d"
        elif temporal.type == TemporalType.EVENTUAL:
            if temporal.direction == Direction.FORWARD:
                temporal_name = "<"
            elif temporal.direction == Direction.BACKWARD:
                temporal_name = ">"
            else:  # BOTH
                temporal_name = "<>"
        else:
            temporal_name = "?"

        return temporal_name

        
def dep_label_exist(existential) -> str: 
    if existential:
        if existential.type == ExistentialType.INDEPENDENCE:
            existential_name = "-"
        elif existential.type == ExistentialType.IMPLICATION:
            if existential.direction == Direction.FORWARD:
                existential_name = "=>"
            elif existential.direction == Direction.BACKWARD:
                existential_name = "<="
            else:  # BOTH
                existential_name = "<=>"
        elif existential.type == ExistentialType.EQUIVALENCE:
            existential_name = "<=>"
        elif existential.type == ExistentialType.OR:
            existential_name = "∨"
        elif existential.type == ExistentialType.NAND:
            existential_name = "¬∧"
        elif existential.type == ExistentialType.NEGATED_EQUIVALENCE:
            existential_name = "</=>"
        else:
            existential_name = "?"
        
        return existential_name


def print_matrix(matrix: AdjacencyMatrix, title: str = "Adjacency Matrix") -> None:
    banner(title)
    activities = matrix.activities
    col_w = 22

    # Header row
    header = f"{'':>14}" + "".join(f"{a:^{col_w}}" for a in activities)
    print(header)
    print("  " + "─" * (14 + col_w * len(activities)))

    for row_act in activities:
        row = f"  {row_act:>12}  "
        for col_act in activities:
            if row_act == col_act:
                cell = "·"
            else:
                dep = matrix.get_dependency(row_act, col_act)
                if dep:
                    temp, exist = dep
                    cell = _dep_label(temp, exist)
                else:
                    cell = ""
            row += f"{cell:^{col_w}}"
        print(row)
    print()


# ════════════════════════════════════════════════════════════════════════════
#  Dependency input helpers
# ════════════════════════════════════════════════════════════════════════════

TEMPORAL_TYPES   = [t.name for t in TemporalType]
EXISTENTIAL_TYPES = [t.name for t in ExistentialType]
DIRECTIONS       = [d.name for d in Direction]


def ask_temporal() -> TemporalDependency | None:
    """Interactively ask for an optional temporal dependency."""
    if not confirm("  Specify temporal dependency?"):
        return None
    t_type = choose("Temporal type:", TEMPORAL_TYPES)
    if TemporalType[t_type] in (TemporalType.DIRECT, TemporalType.EVENTUAL):
        direction = choose("Direction:", DIRECTIONS)
    else:
        direction = Direction.BOTH.name
    return TemporalDependency(TemporalType[t_type], Direction[direction])


def ask_existential() -> ExistentialDependency | None:
    """Interactively ask for an optional existential dependency."""
    if not confirm("  Specify existential dependency?"):
        return None
    e_type = choose("Existential type:", EXISTENTIAL_TYPES)
    if ExistentialType[e_type] == ExistentialType.IMPLICATION:
        direction = choose("Direction:", DIRECTIONS)
    else:
        direction = Direction.BOTH.name
    return ExistentialDependency(ExistentialType[e_type], Direction[direction])


def ask_dependencies(activities: list[str]) -> dict:
    """
    Ask the user to specify one or more (from, to, temporal, existential) tuples.
    Returns a dict keyed by (from_act, to_act).
    """
    deps: dict = {}
    print("\n  Enter dependencies (empty 'from' to stop):")
    while True:
        from_act = prompt("    From activity (or blank to finish)")
        if not from_act:
            break
        if from_act not in activities:
            print(f"  ✗  '{from_act}' is not in the current activity list: {activities}")
            continue
        to_act = prompt("    To activity")
        if to_act not in activities:
            print(f"  ✗  '{to_act}' is not in the activity list.")
            continue
        temp  = ask_temporal()
        exist = ask_existential()
        deps[(from_act, to_act)] = (temp, exist)
    return deps


def deps_to_matrix(deps: dict) -> AdjacencyMatrix:
    """
    Builds a minimal AdjacencyMatrix from an insertion dependencies dict.
    Activities are inferred from the (from, to) keys of the dict.
    """
    # collect all unique activity names, preserving insertion order
    activities = []
    for (from_act, to_act) in deps:
        if from_act not in activities:
            activities.append(from_act)
        if to_act not in activities:
            activities.append(to_act)

    matrix = AdjacencyMatrix(activities)

    for (from_act, to_act), (temp_dep, exist_dep) in deps.items():
        matrix.add_dependency(from_act, to_act, temp_dep, exist_dep)

    return matrix