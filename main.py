"""
Business Process Redesign : Console Interface
=============================================
Run with:  python main.py

Workflow
--------
1. Load a process model (YAML file OR raw acceptance sequences)
2. Inspect the resulting adjacency matrix
3. Pick a change operation and supply its parameters
4. Inspect the modified matrix
5. Optionally export it as YAML and/or apply further operations
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
        if temporal.type == TemporalType.INDEPENDENCE:
            temporal_name = "-"
        elif temporal.type == TemporalType.DIRECT:
            if temporal.direction == Direction.FORWARD:
                temporal_name = ">_d"
            elif temporal.direction == Direction.BACKWARD:
                temporal_name = "<_d"
            else:  # BOTH
                temporal_name = "<>_d"
        elif temporal.type == TemporalType.EVENTUAL:
            if temporal.direction == Direction.FORWARD:
                temporal_name = ">_e"
            elif temporal.direction == Direction.BACKWARD:
                temporal_name = "<_e"
            else:  # BOTH
                temporal_name = "<>_e"
        else:
            temporal_name = "?"
        parts.append(temporal_name.center(_W))

    if existential:
        if existential.type == ExistentialType.INDEPENDENCE:
            existential_name = "-"
        elif existential.type == ExistentialType.IMPLICATION:
            if existential.direction == Direction.FORWARD:
                existential_name = "=>_i"
            elif existential.direction == Direction.BACKWARD:
                existential_name = "<=_i"
            else:  # BOTH
                existential_name = "<=>_i"
        elif existential.type == ExistentialType.EQUIVALENCE:
            existential_name = "<=>_eq"
        elif existential.type == ExistentialType.OR:
            existential_name = "∨"
        elif existential.type == ExistentialType.NAND:
            existential_name = "¬∧"
        elif existential.type == ExistentialType.NEGATED_EQUIVALENCE:
            existential_name = "</=>"
        else:
            existential_name = "?"
        parts.append(existential_name.center(_W))

    return " , ".join(parts) if parts else "—".center(_W)


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


# ════════════════════════════════════════════════════════════════════════════
#  Step 1 – Load process model
# ════════════════════════════════════════════════════════════════════════════

def load_from_yaml() -> AdjacencyMatrix:
    while True:
        path = prompt("Path to YAML file")
        if not path:
            continue
        path = os.path.expanduser(path)
        if not os.path.isfile(path):
            print(f"  ✗  File not found: {path}")
            continue
        try:
            matrix = parse_yaml_to_adjacency_matrix(path)
            print(f"  ✓  Loaded {len(matrix.activities)} activities: {matrix.activities}")
            return matrix
        except Exception as e:
            print(f"  ✗  Could not parse YAML: {e}")


def load_from_sequences() -> AdjacencyMatrix:
    """
    Ask the user to enter acceptance sequences, one per line.
    Each sequence is a comma-separated list of activity names, e.g.:
        A, B, C
        A, C, B
    """
    print("\n  Enter acceptance sequences, one per line.")
    print("  Each line: comma-separated activity names, e.g.  A, B, C")
    print("  Enter a blank line when finished.\n")

    sequences: list[list[str]] = []
    while True:
        line = prompt(f"  Sequence {len(sequences) + 1} (blank to finish)")
        if not line:
            if not sequences:
                print("  ✗  Please enter at least one sequence.")
                continue
            break
        seq = [a.strip() for a in line.split(",") if a.strip()]
        if seq:
            sequences.append(seq)
            print(f"     → {seq}")

    matrix = variants_to_matrix(sequences)
    print(f"\n  ✓  Matrix derived from {len(sequences)} sequence(s).")
    print(f"     Activities discovered: {matrix.activities}")
    return matrix


def step_load_model() -> AdjacencyMatrix:
    banner("Step 1 : Load Process Model")
    choice = choose(
        "How do you want to provide the process model?",
        ["YAML file", "Acceptance sequences (manual input)"],
    )
    if choice == "YAML file":
        return load_from_yaml()
    return load_from_sequences()

# ════════════════════════════════════════════════════════════════════════════
#  Step 2 – Ask for locked dependencies and store them
# ════════════════════════════════════════════════════════════════════════════

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

    # return the dictionary with all the locked dependencies 
    return deps

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
    # use a guard to check if it is None 
    if old_dependency is None or new_dependency is None:
        return old_dependency != new_dependency
    
    # extract the temporal and existential component 
    old_temp, old_exist = old_dependency
    new_temp, new_exist = new_dependency

    # compare the dependencies, if they were changes 
    temp_unchanged = old_temp == new_temp
    exist_unchanged = old_exist == new_exist

    return not(temp_unchanged and exist_unchanged)
    

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

    # if one of the dependencies is missing, we are not speaking about a relaxation 
    if old_dependency is None or new_dependency is None:
        return False

    old_temp, old_exist = old_dependency
    new_temp, new_exist = new_dependency

    # for both, exiatntial and temporal dependencies, check if they are a relaxation of each other
    temp_relaxed = (
        old_temp is not None
        and new_temp is not None
        and is_temp_relaxation(old_temp, new_temp)
    )
    exist_relaxed = (
        old_exist is not None
        and new_exist is not None
        and is_exist_relaxation(old_exist, new_exist)
    )

    # check if the dependency types remained unchanged 
    temp_unchanged = old_temp == new_temp
    exist_unchanged = old_exist == new_exist

    # At least one component must be relaxed,
    # and the other must not be made stricter (i.e. also relaxed or unchanged)
    return (
        (temp_relaxed and exist_relaxed)
        or (temp_relaxed and exist_unchanged)
        or (exist_relaxed and temp_unchanged)
    )


def is_temp_relaxation(old_temp_dep: TemporalDependency, new_temp_dep: TemporalDependency): 
    """
    For temporal dependencies, check if it is a relaxation (old is direct and new is eventual)
    """
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

# ════════════════════════════════════════════════════════════════════════════
#  Step 3 – Select & execute change operation
# ════════════════════════════════════════════════════════════════════════════

OPERATIONS = [
    "delete",
    "insert",
    "modify",
    "move",
    "swap",
    "skip",
    "replace",
    "collapse",
    "de-collapse",
    "parallelize",
    "condition_update",
    "── (done / no operation) ──",
]


def op_delete(matrix: AdjacencyMatrix) -> AdjacencyMatrix:
    activity = prompt("Activity to delete")
    return delete_activity(matrix, activity)


def op_insert(matrix: AdjacencyMatrix) -> AdjacencyMatrix:
    activity = prompt("New activity name")
    print(f"\n  Current activities: {matrix.activities}")
    deps = ask_dependencies(matrix.activities + [activity])

    #######################################
    # begin new implementataion 
    #######################################
    try: 
        # try to perform the insert operation
        return insert_activity(matrix, activity, deps)
    except ValueError as e: 
        # indicate to the user that the standard insert method does not work here 
        print("The insert operation is ambigous, we use the new skeleton approach to adapt the acceptance sequnces")

        # we offer the user the option to choose the method to calculate the similarity score
        options = ["Pure occurence similarity score - focus on preserving existential dependencies", 
                   "Pure ordering similarity score - focus on preserving temporal dependencies",
                   "Combined similarity score - allowing for a balanced consideration"]
        
        similarity_strategy = choose("Choose a method to calculate the similarity score between skeleton sequences and acceptance sequences: ", options)

        if "occurence" in similarity_strategy: 
            similarity_strategy = "occurence"
        elif "ordering" in similarity_strategy: 
            similarity_strategy = "ordering"
        else: 
            similarity_strategy = "combined"

        # if an error occurs, we use the new insert opportunity 
        modified_acceptance_sequences = adapt_acceptance_skeleton(generate_acceptance_variants(matrix), deps_to_matrix(deps), similarity_strategy)

        # return the modified matrix
        return variants_to_matrix(modified_acceptance_sequences)


def op_modify(matrix: AdjacencyMatrix) -> AdjacencyMatrix:
    """
    modify_dependencies expects a list of
    (from_act, to_act, TemporalDependency, ExistentialDependency) tuples.
    """
    print(f"\n  Current activities: {matrix.activities}")
    modifications = []
    print("\n  Enter modifications (blank 'from' to stop):")
    while True:
        from_act = prompt("    From activity (blank to finish)")
        if not from_act:
            break
        to_act = prompt("    To activity")
        temp  = ask_temporal()
        exist = ask_existential()
        if temp is None or exist is None:
            print("  ✗  Modify requires both temporal and existential dependencies.")
            continue
        modifications.append((from_act, to_act, temp, exist))
    if not modifications:
        print("  ✗  No modifications specified – operation cancelled.")
        return matrix
    result, _ = modify_dependencies(matrix, modifications)
    return result


def op_move(matrix: AdjacencyMatrix) -> AdjacencyMatrix:
    print(f"\n  Current activities: {matrix.activities}")
    activity = prompt("Activity to move")
    print("\n  Specify the new dependencies that define the new position:")
    deps = ask_dependencies(matrix.activities)
    return move_activity(matrix, activity, deps)


def op_swap(matrix: AdjacencyMatrix) -> AdjacencyMatrix:
    print(f"\n  Current activities: {matrix.activities}")
    act1 = prompt("First activity")
    act2 = prompt("Second activity")
    return swap_activities(matrix, act1, act2)


def op_skip(matrix: AdjacencyMatrix) -> AdjacencyMatrix:
    print(f"\n  Current activities: {matrix.activities}")
    activity = prompt("Activity to make optional (skip)")
    return skip_activity(matrix, activity)


def op_replace(matrix: AdjacencyMatrix) -> AdjacencyMatrix:
    print(f"\n  Current activities: {matrix.activities}")
    old_act = prompt("Activity to replace")
    new_act = prompt("New activity name")
    return replace_activity(matrix, old_act, new_act)


def op_collapse(matrix: AdjacencyMatrix) -> AdjacencyMatrix:
    print(f"\n  Current activities: {matrix.activities}")
    collapsed_name = prompt("Name of new collapsed activity")
    raw = prompt("Activities to collapse (comma-separated)")
    collapse_acts = [a.strip() for a in raw.split(",") if a.strip()]

    # perform the change operation, if activities in between catch the error and perform the alternative change operations 
    try: 
        return collapse_operation(matrix, collapsed_name, collapse_acts)
    # check that we catch the correct error message 
    except ValueError as e:
        msg = str(e)
        # check if it is the error 
        if "happen between the activities to be collapsed" in msg: 
            print("error caught")
            # offer the user the selection of solution strategies (either move activities, for the different activities to parallelized / include activities to be parallelized)
            
            # create the set of moving options
            options = ["Move all activities to activity " + act for act in collapse_acts]

            # get the activities happening in between 
            list_str = msg.split("Activities ")[1].split(" happen between the activities to be collapsed")[0]
            activities_in_between = list_str.strip("[]").split("', '")
            activities_in_between = [a.strip("'") for a in activities_in_between]

            # if less then 5 activities, offer to parallelize also activities in between 
            if len(activities_in_between) <= 5: 
                options = ["Collapse including activities " + str(activities_in_between)] + options

            # let the user choose a solution strategy
            solution_strategy = choose("Choose a solution strategy: ", options)

            # based on the selected solution strategy, we perform the change operation 
            if "Collapse including activities " in solution_strategy: 
                # include the activities in between in the parallelization 
                acceptance_sequences = collapse_expand_set(generate_acceptance_variants(matrix), collapse_acts, activities_in_between, collapsed_name)

                # convert the acceptance sequences to a matrix and return
                return variants_to_matrix(acceptance_sequences)
            
            else: 
                # get the activity to which the others should be moved from the chosen option 
                activity_positioning = solution_strategy.split("Move all activities to activity ")[1]
                
                # perform the adapted change operation
                acceptance_sequences = collapse_move_activities(generate_acceptance_variants(matrix), collapse_acts, collapsed_name, activity_positioning)

                # convert the acceptance sequences to a matrix and return
                return variants_to_matrix(acceptance_sequences)
    


def op_decollapse(matrix: AdjacencyMatrix) -> AdjacencyMatrix:
    print(f"\n  Current activities: {matrix.activities}")
    collapsed_act = prompt("Activity to de-collapse")
    print("\n  Provide the sub-process matrix for the collapsed activity:")
    sub_choice = choose(
        "Load sub-process model from:",
        ["YAML file", "Acceptance sequences (manual input)"],
    )
    if sub_choice == "YAML file":
        sub_matrix = load_from_yaml()
    else:
        sub_matrix = load_from_sequences()
    return decollapse_operation(matrix, collapsed_act, sub_matrix)


def op_parallelize(matrix: AdjacencyMatrix) -> AdjacencyMatrix:
    print(f"\n  Current activities: {matrix.activities}")
    raw = prompt("Activities to parallelize (comma-separated)")
    activities_parallelization = [a.strip() for a in raw.split(",") if a.strip()]

    # perform the change operation, if activities in between catch the error and perform the alternative change operations 
    try: 
        return parallelize_activities(matrix, activities_parallelization)
    # check that we catch the correct error message 
    except ValueError as e:
        msg = str(e)
        # check if it is the error 
        if "are in between the activities to be parallelized" in msg: 
            print("error caught")
            # offer the user the selection of solution strategies (either move activities, for the different activities to parallelized / include activities to be parallelized)
            
            # create the set of moving options
            options = ["Move all activities to activity " + act for act in activities_parallelization]

            # get the activities happening in between 
            list_str = msg.split("Activities ")[1].split(" are in between")[0]
            activities_in_between = list_str.strip("[]").split("', '")
            activities_in_between = [a.strip("'") for a in activities_in_between]

            # if less then 5 activities, offer to parallelize also activities in between 
            if len(activities_in_between) <= 5: 
                options = ["Parallelize including activities " + str(activities_in_between)] + options

            # let the user choose a solution strategy
            solution_strategy = choose("Choose a solution strategy: ", options)

            # based on the selected solution strategy, we perform the change operation 
            if "Parallelize including activities " in solution_strategy: 
                # include the activities in between in the parallelization 
                acceptance_sequences = parallelize_expand_set(generate_acceptance_variants(matrix), activities_parallelization, activities_in_between)

                # convert the acceptance sequences to a matrix and return
                return variants_to_matrix(acceptance_sequences)
            
            else: 
                # get the activity to which the others should be moved from the chosen option 
                activity_positioning = solution_strategy.split("Move all activities to activity ")[1]
                
                # perform the adapted change operation
                acceptance_sequences = parallelize_move_activities(generate_acceptance_variants(matrix), activities_parallelization, activity_positioning)

                # convert the acceptance sequences to a matrix and return
                return variants_to_matrix(acceptance_sequences)
        


def op_condition_update(matrix: AdjacencyMatrix) -> AdjacencyMatrix:
    print(f"\n  Current activities: {matrix.activities}")
    print("\n  Specify the condition-update dependencies:")
    deps = ask_dependencies(matrix.activities)
    return condition_update(matrix, deps)


OP_HANDLERS = {
    "delete":           op_delete,
    "insert":           op_insert,
    "modify":           op_modify,
    "move":             op_move,
    "swap":             op_swap,
    "skip":             op_skip,
    "replace":          op_replace,
    "collapse":         op_collapse,
    "de-collapse":      op_decollapse,
    "parallelize":      op_parallelize,
    "condition_update": op_condition_update,
}


def step_apply_operation(matrix: AdjacencyMatrix) -> AdjacencyMatrix | None:
    """
    Returns the modified matrix, or None if the user chose to exit.
    """
    banner("Step 3 : Select Change Operation")
    operation = choose("Select an operation:", OPERATIONS)

    if operation.startswith("──"):
        return None

    handler = OP_HANDLERS.get(operation)
    if handler is None:
        print(f"  ✗  Handler for '{operation}' not found.")
        return matrix

    print(f"\n  ── Parameters for: {operation.upper()} ──")
    try:
        # try to perform the change operation 
        result = handler(matrix)
        print(f"\n  ✓  Operation '{operation}' applied successfully.")
        return result
    except ValueError as e:
        print(f"\n  ✗  Operation failed: {e}")
        return matrix
    except Exception as e:
        print(f"\n  ✗  Unexpected error: {e}")
        return matrix


# ════════════════════════════════════════════════════════════════════════════
#  Export
# ════════════════════════════════════════════════════════════════════════════

def export_matrix_to_yaml(matrix: AdjacencyMatrix) -> None:
    path = prompt("Save path for YAML file", "output_matrix.yaml")
    path = os.path.expanduser(path)

    data: dict = {
        "metadata": {"activities": matrix.activities},
        "dependencies": [],
    }

    for (from_act, to_act), (temp_dep, exist_dep) in matrix.dependencies.items():
        entry: dict = {"from": from_act, "to": to_act}

        if temp_dep:
            entry["temporal"] = {
                "type":      temp_dep.type.name.lower(),
                "direction": temp_dep.direction.name.lower(),
            }
        if exist_dep:
            entry["existential"] = {
                "type":      exist_dep.type.name.lower(),
                "direction": exist_dep.direction.name.lower(),
            }

        data["dependencies"].append(entry)

    with open(path, "w") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    print(f"  ✓  Matrix exported to: {os.path.abspath(path)}")


# ════════════════════════════════════════════════════════════════════════════
#  Main loop
# ════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("\n" + "═" * 60)
    print("   Business Process Redesign : Console Tool")
    print("═" * 60)

    # ── 1. Load initial model ────────────────────────────────────────────────
    current_matrix = step_load_model()
    print_matrix(current_matrix, "Initial Matrix")

    # ── 2. Define locked dependencies ────────────────────────────────────────
    banner("Step 2 : Define locked dependendencies")
    locked_dependencies = get_locked_dependencies(current_matrix)

    # ── 3. Operation loop ────────────────────────────────────────────────────
    while True:
        result = step_apply_operation(current_matrix)

        # check if the user wants to end the application 
        if result is None:
            print("\n  No further operations selected.  Exiting.\n")
            break

        # check if the locked dependencies are violated 
        exist_violations = are_locked_dependencies_violated(locked_dependencies, result)

        # 2) if there are violations, we check if can resolve them by relaxation 
        if exist_violations: 

            print("The performance of the change operation caused a violation of the locked dependencies.")
            print("In the next steps we want to resolve these violations")

            # our status variable exist_violations is set to False 
            exist_violations = False

            # we know there are violations, check if they can be solved using dependency relaxation  
            for (from_act, to_act), locked_dep in locked_dependencies.items():
                
                # get the dependency type from the modified matrix 
                new_dependency = result.get_dependency(from_act, to_act)

                # check if it is violated, if yes check for relaxation 
                if is_violated(locked_dep, new_dependency): 

                    # check if the dependency is a relaxation and ask the user, if he accepts the relaxation
                    if is_relaxation(locked_dep, new_dependency):  

                        # extract the dependency types, to provide them to the user as information 
                        locked_temp_dep, locked_exist_dep = locked_dep
                        new_temp_dep, new_exist_dep = new_dependency

                        # ask the user, if applicable, to relax the existential dependency 
                        if is_exist_relaxation(locked_exist_dep, new_exist_dep): 

                            if confirm(f"Do you want to relax the existential between activities {from_act, to_act} dependency from {locked_exist_dep} to the relaxed {new_exist_dep}?"): 
                                # if the user agrees on the relaxation, adapt the locked dependencies accordingly 
                                locked_dependencies[(from_act, to_act)] = (locked_temp_dep, new_exist_dep)
                                
                                # update the variable of the locked dependency, used for the relaxation of the temporal dependency
                                locked_exist_dep = new_exist_dep
                            
                            else: 
                                # there is a difference, which can be seen as a relaxation, but the user does not want to see it as a relxation 
                                # we have a violation of a locked dependency
                                exist_violations = True


                        # ask the user, if applicable, to relax the temporal dependency 
                        if is_temp_relaxation(locked_temp_dep, new_temp_dep): 

                            if confirm(f"Do you want to relax the temporal between activities {from_act, to_act} dependency from {locked_temp_dep} to the relaxed {new_temp_dep}?"): 
                                # if the user agrees on the relaxation, adapt the locked dependencies accordingly 
                                locked_dependencies[(from_act, to_act)] = (new_temp_dep, locked_exist_dep)
                            
                            else: 
                                # there is a difference, which can be seen as a relaxation, but the user does not want to see it as a relxation 
                                # we have a violation of a locked dependency
                                exist_violations = True

                    else: 
                        # if we do not have a relaxation but a violation, we need the skeleton approach 
                        exist_violations = True

        # 3) if there are still violations, we must use the skeleton approch 
        if exist_violations: 
            # inform the user that dependency relacation was not enough 
            print("Using dependency relaxation was unable to resolve (all) violations.")
            print("The skeleton approch will be used to resolve the violations.")

            # we offer the user the option to choose the method to calculate the similarity score
            options = ["Pure occurence similarity score - focus on preserving existential dependencies", 
                    "Pure ordering similarity score - focus on preserving temporal dependencies",
                    "Combined similarity score - allowing for a balanced consideration"]
            
            similarity_strategy = choose("Choose a method to calculate the similarity score between skeleton sequences and acceptance sequences: ", options)

            if "occurence" in similarity_strategy: 
                similarity_strategy = "occurence"
            elif "ordering" in similarity_strategy: 
                similarity_strategy = "ordering"
            else: 
                similarity_strategy = "combined"

            # if an error occurs, we use the new insert opportunity 
            modified_acceptance_sequences = adapt_acceptance_skeleton(generate_acceptance_variants(result), deps_to_matrix(locked_dependencies), similarity_strategy)

            # get the result by translating the modified acceptance sequences in the matrix
            result = variants_to_matrix(modified_acceptance_sequences)


        # if the matrix did not change, display this information 
        if result is not current_matrix:
            print_matrix(result, "Modified Matrix")
        else:
            print("\n  ℹ  Matrix unchanged – no modified matrix to display.")

        if confirm("Export this matrix to YAML?"):
            export_matrix_to_yaml(result)

        if confirm("Apply another operation to the MODIFIED matrix?"):
            current_matrix = result
            continue

        if confirm("Apply another operation to the ORIGINAL matrix?"):
            # current_matrix is still the original – just loop again
            continue

        # No further work
        print("\n  Done.  Goodbye!\n")
        break


if __name__ == "__main__":
    main()