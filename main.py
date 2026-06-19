import os
import yaml

# ── Core imports ────────────────────────────────────────────────────────────
from adjacency_matrix import AdjacencyMatrix

# ── Change-operation helper functions imports ─────────────────────────────────────────────────
from change_operations.parallelize_operation import get_activities_happening_between

# ── Helper functions ─────────────────────────────────────────────────
from utils.console_helpers import banner
from utils.console_helpers import prompt
from utils.console_helpers import choose
from utils.console_helpers import confirm
from utils.console_helpers import print_matrix

# ── Locked dependency functions ─────────────────────────────────────────────────
from utils.utils_lock_dependencies import get_locked_dependencies

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

# ── Debug mode ─────────────────────────────────────────────────
from utils.debug_mode import enable as enable_debug_mode
from utils.debug_mode import log

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


def step_apply_operation(matrix: AdjacencyMatrix, locked_dependencies):
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
        return matrix, locked_dependencies

    print(f"\n  ── Parameters for: {operation.upper()} ──")
    try:
        # try to perform the change operation
        result, locked_dependencies = handler(matrix, locked_dependencies)
        return result, locked_dependencies, True
    except ValueError as e:
        print(f"\n  ✗  Operation failed: {e} \n")
        return matrix, locked_dependencies, False
    except Exception as e:
        print(f"\n  ✗  Unexpected error: {e} \n")
        return matrix, locked_dependencies, False


# ════════════════════════════════════════════════════════════════════════════
#  Export
# ════════════════════════════════════════════════════════════════════════════

def export_matrix_to_yaml(matrix: AdjacencyMatrix) -> None:
    path = prompt("Name of the matrix to save", "output_matrix.yaml")

    if path != "output_matrix.yaml": 
        path = path + ".yaml"
        
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
    """
    Business Process Redesign : Console Interface
    Run with:  python main.py

    Workflow
    --------
    1. Load a process model (YAML file OR raw acceptance sequences)
    2. Inspect the resulting adjacency matrix
    3. Pick a change operation and supply its parameters
    4. Inspect the modified matrix
    5. Optionally export it as YAML and/or apply further operations
    """
    
    print("\n" + "═" * 60)
    print("   Business Process Redesign : Console Tool")
    print("═" * 60)

    # ── 0. Ask for debug mode ────────────────────────────────────────────────
    if confirm("Enable detailed information mode?"):
        enable_debug_mode()

    # ── 1. Load initial model ────────────────────────────────────────────────
    current_matrix = step_load_model()
    print_matrix(current_matrix, "Initial Matrix")
    
    # ── 2. Define locked dependencies ────────────────────────────────────────
    banner("Step 2 : Define locked dependendencies")
    locked_dependencies = get_locked_dependencies(current_matrix)

    # ── 3. Operation loop ────────────────────────────────────────────────────
    while True:
        result, locked_dependencies, operation_successful = step_apply_operation(current_matrix, locked_dependencies)

        # check if the user wants to end the application 
        if result is None:
            print("\n  No further operations selected.  Exiting.\n")
            break

        # if no error occurred while implementing the change operation 
        if operation_successful: 
            # if the matrix did not change, display this information 
            if result is not current_matrix:
                # inform the user that the change operation was applied succesfully 
                print(f"\n  ✓  Change operation applied successfully.")
                print_matrix(result, "Modified Matrix")

                if confirm("Export this matrix to YAML?"):
                    export_matrix_to_yaml(result)

                if confirm("Apply another operation to the MODIFIED matrix?"):
                    current_matrix = result
                    continue

                if confirm("Apply another operation to the ORIGINAL matrix?"):
                    # current_matrix is still the original – just loop again
                    continue
             
            else:
                # if the matrix remained unchanged 
                print("\n  ℹ  Matrix unchanged : no modified matrix to display.")

                if confirm("Apply another operation to the original matrix?"):
                    continue

        else: 
            # if the change operation failed 
            if confirm("Apply another operation to the original matrix?"):
                continue

        # No further work
        print("\n  Done.  Goodbye!\n")
        break


if __name__ == "__main__":
    main()