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
    """
    Print a banner to the console 

    Args: 
        text: Text to be shown in the console 
    """

    print(f"\n{SEP}\n {text}\n{SEP}")


def prompt(msg: str, default: str = "") -> str:
    """
    Show a prompt and return stripped input.  
    Ctrl-C exits.
    """
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"  {msg}{suffix}: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\nBye!")
        sys.exit(0)
    return value if value else default


def choose(msg: str, options: list[str]) -> str:
    """
    Present a numbered menu and return the chosen option string.
    """
    print(f"\n  {msg}")
    for i, opt in enumerate(options, 1):
        print(f"    [{i}] {opt}")
    while True:
        raw = prompt("Enter number")
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            print("\n")
            return options[int(raw) - 1]
        print("  ✗  Invalid choice : try again.")


def confirm(msg: str) -> bool:
    """
    Show a prompt and ask the user to confirm. 
    False by default. 
    """
    return prompt(f"{msg} (y/n)", "n").lower() == "y"
 


# ════════════════════════════════════════════════════════════════════════════
#  Matrix display
# ════════════════════════════════════════════════════════════════════════════

# fixed width for all symbols
_W = 6  

def _dep_label(temporal, existential) -> str:
    """
    For a pair of temporal and existential dependencies, return the string represneting them 
    """
    parts = []

    if temporal: 
        temporal_name = dep_label_temp(temporal)
    else: 
        temporal_name = "-"

    parts.append(temporal_name.center(_W))

    if existential: 
        existential_name = dep_label_exist(existential)
    else: 
        existential_name = "-"
        
    parts.append(existential_name.center(_W))

    return " , ".join(parts) if parts else "—".center(_W)


def dep_label_temp(temporal) -> str: 
    """
    For a temporal dependency, get the String representing the dependency. 
    """
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
    """
    For an existential dependency, get the String representing the dependency. 
    """
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
    """
    Print the matrix to the console 

    Args: 
        matrix: matrix to be printed 
        title: title of the matrix to be shown, "Adjacency Matrix" by default
    """
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


def print_matrix_difference(original_matrix: AdjacencyMatrix, modified_matrix: AdjacencyMatrix, title: str = "Adjacency Matrix") -> None:
    """
    Print the modified matrix to the console.
    Entries which differ from the original matrix are printed in bold.

    Args:
        original_matrix: matrix before the change operation
        modified_matrix: matrix after the change operation
        title: title of the matrix to be shown, "Adjacency Matrix" by default
    """
    BOLD  = "\033[1m"
    RESET = "\033[0m"

    banner(title)
    print("  Dependencies changed by the operation are marked with [ ]")

    activities = modified_matrix.activities
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
                row += f"{cell:^{col_w}}"
                continue

            new_dep = modified_matrix.get_dependency(row_act, col_act)
           
            if new_dep:
                temp, exist = new_dep
                cell = _dep_label(temp, exist)
            else:
                cell = ""

            # Determine whether this cell changed.
            # The activity pair may not exist in the original at all
            # (e.g. after insert / collapse introduced a new activity).
            row_in_orig = row_act in original_matrix.activities
            col_in_orig = col_act in original_matrix.activities

            if row_in_orig and col_in_orig:
                old_dep = original_matrix.get_dependency(row_act, col_act)
            else:
                old_dep = None  # new activity → treat as changed

            changed = new_dep != old_dep

            padded = f"{cell:^{col_w}}"
            if changed:
                # Wrap in brackets and re-center within col_w,
                # keeping visual width consistent
                marked = f"[{cell}]"
                row += f"{marked:^{col_w}}"
            else:
                row += padded

        print(row)
    print()


# ════════════════════════════════════════════════════════════════════════════
#  Dependency input helpers
# ════════════════════════════════════════════════════════════════════════════

TEMPORAL_TYPES   = [t.name for t in TemporalType]
EXISTENTIAL_TYPES = [t.name for t in ExistentialType]
DIRECTIONS       = [d.name for d in Direction]


def ask_temporal() -> TemporalDependency | None:
    """
    Interactively ask for an optional temporal dependency.
    Returns None if not provided.
    """

    if not confirm("  Specify temporal dependency?"):
        return None
    t_type = choose("Temporal type:", TEMPORAL_TYPES)
    if TemporalType[t_type] in (TemporalType.DIRECT, TemporalType.EVENTUAL):
        direction = choose("Direction:", DIRECTIONS)
    else:
        direction = Direction.BOTH.name
    return TemporalDependency(TemporalType[t_type], Direction[direction])


def ask_existential() -> ExistentialDependency | None:
    """
    Interactively ask for an optional existential dependency.
    Returns None if not provided. 
    """

    if not confirm("  Specify existential dependency?"):
        return None
    e_type = choose("Existential type:", EXISTENTIAL_TYPES)
    if ExistentialType[e_type] == ExistentialType.IMPLICATION:
        direction = choose("Direction:", DIRECTIONS)
    else:
        direction = Direction.BOTH.name
    return ExistentialDependency(ExistentialType[e_type], Direction[direction])


def ask_dependencies_insertion(activities: list[str], mandatory_activity: str) -> dict:
    """
    Ask the user to specify one or more (from, to, temporal, existential) tuples.
    Returns a dict keyed by (from_act, to_act).
    At least one existential dependency must be provided and each tuple must contain the mandatory_activity 
    Rteurns a dict with the dependencies in both directions 

    Args: 
        activities: list of all the activities contained
        mandatory_activity: the activity for insertion / for move, every tuple needs to contain this activity 

    Returns: 
        dict of dependencies 
    """

    deps: dict = {}
    print("\n  Enter dependencies (empty 'to' to stop):")
    while True:
        from_act = mandatory_activity
        print(f"\n    From activity (is the mandatory activity): {mandatory_activity}")

        # ask the user to provide the second activity
        to_act = prompt("    To activity (or blank to finish) ")

        if not to_act: 

            # check that any dependency was provided
            has_existential = any(exist is not None for (_, exist) in deps.values())
            has_temporal = any(temp is not None for (temp, _) in deps.values())

            if not has_existential and not has_temporal:
                print("  ✗  At least one dependency is required. Please add one before finishing.")
                continue
            else: 
                # if no activity provided, break the loop 
                break

        # ensure the provided activity is in the activities 
        if to_act not in activities:
            print(f"  ✗  '{to_act}' is not in the activity list.")
            continue

        # ensure that no self dependencies are defined 
        if to_act == from_act:
            print(f"  ✗  '{to_act}' is the same as from activity.")
            continue

        # ask for the dependencies 
        temp  = ask_temporal()
        exist = ask_existential()

        # add the dependencies to the dictionary - if at least one dependency exists
        if temp is None and exist is None: 
            print(f"  ✗  For '({from_act}, {to_act})' no dependencies were provided.")
            continue

        # check if they are already in the dictionary 
        if (from_act, to_act) in deps: 
            print(f"  ✗  For '({from_act}, {to_act})' exists already an entry to specify dependencies.")
            
            # ask the user if the entry should be overwritten 
            if confirm("Do you want to overwrite that entry?"): 
                deps[(from_act, to_act)] = (temp, exist)
                deps[(to_act, from_act)] = (reverse_dependency(temp), reverse_dependency(exist))

        else: 
            deps[(from_act, to_act)] = (temp, exist)
            deps[(to_act, from_act)] = (reverse_dependency(temp), reverse_dependency(exist))

    # return the new dependencies 
    return deps


def ask_dependencies(activities: list[str]) -> dict:
    """
    Ask the user to specify one or more (from, to, temporal, existential) tuples.
    Returns a dict keyed by (from_act, to_act), including always the reverse dependency. 

    Args: 
        activities: list of all the activities contained

    Returns: 
        dict: dictionary of the provided dependnecies 
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

        # insert them forward 
        deps[(from_act, to_act)] = (temp, exist)

        # insert backwards 
        deps[(to_act, from_act)] = (reverse_dependency(temp), reverse_dependency(exist))
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

def reverse_dependency(dependency): 
    """
    For given depenency, reverse its direction. This method works for any dependency, regardless if existential or temporal 

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