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
from modified_change_operations.skeleton_strategies import perfom_skeleton_algorithm

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

# ── dependency relaxation ─────────────────────────────────────────────────
from utils.dependency_relaxation import perform_dependency_relaxation

# ── Change operation handlers ─────────────────────────────────────────────────
from operation_handlers.op_insert import op_insert
from operation_handlers.op_collapse import op_collapse
from operation_handlers.op_condition_update import op_condition_update
from operation_handlers.op_decollapse import op_decollapse
from operation_handlers.op_delte import op_delete
from operation_handlers.op_modify import op_modify
from operation_handlers.op_move import op_move
from operation_handlers.op_parallelize import op_parallelize
from operation_handlers.op_replace import op_replace
from operation_handlers.op_skip import op_skip
from operation_handlers.op_swap import op_swap

# ── Load process models ─────────────────────────────────────────────────
from utils.load_process_models import load_from_sequences
from utils.load_process_models import load_from_yaml


# ════════════════════════════════════════════════════════════════════════════
#  Step 1 – Load process model
# ════════════════════════════════════════════════════════════════════════════

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


def step_apply_operation(matrix: AdjacencyMatrix, locked_dependencies) -> AdjacencyMatrix | None:
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
        result, locked_dependencies = handler(matrix, locked_dependencies)
        # print(f"\n  ✓  Operation '{operation}' applied successfully.")
        return result, locked_dependencies
    except ValueError as e:
        print(f"\n  ✗  Operation failed: {e}")
        return matrix, locked_dependencies
    except Exception as e:
        print(f"\n  ✗  Unexpected error: {e}")
        return matrix, locked_dependencies


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
        result, locked_dependencies = step_apply_operation(current_matrix, locked_dependencies)

        # check if the user wants to end the application 
        if result is None:
            print("\n  No further operations selected.  Exiting.\n")
            break

        # inform the user that the change operation was applied succesfully 
        print(f"\n  ✓  Change operation applied successfully.")
        
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