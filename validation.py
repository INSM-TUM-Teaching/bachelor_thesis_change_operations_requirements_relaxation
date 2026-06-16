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

from acceptance_skeleton import generate_skeleton

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

# ── Debug mode ─────────────────────────────────────────────────
from utils.debug_mode import enable as enable_debug_mode
from utils.debug_mode import log

# --- define the dependnecies 
DIRECT     = TemporalType.DIRECT
EVENTUAL   = TemporalType.EVENTUAL
INDEP      = TemporalType.INDEPENDENCE
EQUIV      = ExistentialType.EQUIVALENCE
IMPL       = ExistentialType.IMPLICATION
NEG_EQUIV  = ExistentialType.NEGATED_EQUIVALENCE
OR         = ExistentialType.OR
NAND       = ExistentialType.NAND
FWD        = Direction.FORWARD
BWD        = Direction.BACKWARD
BOTH       = Direction.BOTH
# ════════════════════════════════════════════════════════════════════════════
#  Step 1 – Define the input for the change operation 
# ════════════════════════════════════════════════════════════════════════════

# WCP 1 
acceptance_sequences = [['A', 'B', 'C', 'D']]

# WCP 2 acceptance_sequences = [['A', 'B', 'C'],['A', 'C', 'B'],['B', 'A', 'C'],['B', 'C', 'A'],['C', 'A', 'B'],['C', 'B', 'A']]

# WCP 3 
# acceptance_sequences = [['A', 'B', 'C'], ['B', 'A', 'C']]

# WCP 4 Exclusive coice 
# acceptance_sequences = [['A'], ['B']]

# WCP 5
# acceptance_sequences = [['A', 'D'], ['B', 'D'], ['C', 'D']]

# WCP 6 multi choice 
"""
acceptance_sequences = [
    ['A', 'B'],
    ['A', 'C'],
    ['A', 'D'],
    ['A', 'B', 'C'],
    ['A', 'B', 'D'],
    ['A', 'C', 'B'],
    ['A', 'C', 'D'],
    ['A', 'D', 'B'],
    ['A', 'D', 'C'],
    ['A', 'B', 'C', 'D'],
    ['A', 'B', 'D', 'C'],
    ['A', 'C', 'B', 'D'],
    ['A', 'C', 'D', 'B'],
    ['A', 'D', 'B', 'C'],
    ['A', 'D', 'C', 'B'],
]
"""




# WCP 7 structured synchronization merge 
"""
acceptance_sequences = [
    ['A', 'D'],
    ['B', 'D'],
    ['C', 'D'],
    ['A', 'B', 'D'],
    ['A', 'C', 'D'],
    ['B', 'A', 'D'],
    ['B', 'C', 'D'],
    ['C', 'A', 'D'],
    ['C', 'B', 'D'],
    ['A', 'B', 'C', 'D'],
    ['A', 'C', 'B', 'D'],
    ['B', 'A', 'C', 'D'],
    ['B', 'C', 'A', 'D'],
    ['C', 'A', 'B', 'D'],
    ['C', 'B', 'A', 'D'],
]
"""

"""
# WCP 10 
acceptance_sequences = [
    ['A', 'B', 'C'],
    ['A', 'B', 'C', 'B', 'C'],
    ['A', 'B', 'C', 'B', 'C', 'B', 'C'],
    ['C'],
    ['B', 'C'],
    ['B', 'C', 'B', 'C'],
    ['B', 'C', 'B', 'C', 'B', 'C']
]
"""

"""
# WCP 17
acceptance_sequences = [
    ['A', 'B', 'C'],
    ['A', 'C', 'B'],
    ['C', 'A', 'B'],
]
"""
"""
#WCP 19
# acceptance_sequences = [['A', 'B'], ['A']]
"""
"""
LOCKED_DEPENDENCIES: Dict[
    Tuple[str, str],
    Tuple[Optional[TemporalDependency], Optional[ExistentialDependency]]
] = {
    # Example: lock the temporal ordering of A→B (must stay direct) but leave
    # the existential dependency unlocked.
    # ("A", "B"): (temp(DIRECT), None),
 
    # Example: lock only the existential dependency between A and C.
    # ("A", "C"): (None, exist(EQUIV)),
}
"""

# acceptance_sequences = [['A', 'B', 'C']]

# acceptance_sequences =[['A', 'B'], ['A']]


# ----------------------------------------------
# Validation Phase II
# ----------------------------------------------


# case I
"""
acceptance_sequences = [
    ['X', 'Y', 'Z', 'D'],
    ['X', 'Z', 'Y', 'D'],
    ['Y', 'X', 'Z', 'D'],
    ['Y', 'Z', 'X', 'D'],
    ['Z', 'Y', 'X', 'D'],
    ['Z', 'X', 'Y', 'D'],
    ['B', 'D'],
    ['C', 'D'],
]
"""



# case II
acceptance_sequences = [['A', 'Y', 'Z'],
    ['A', 'Z', 'Y'],
    ['Y', 'A', 'Z'],
    ['Y', 'Z', 'A'],
    ['Z', 'Y', 'A'],
    ['Z', 'A', 'Y'],
    ['B', 'Y', 'Z'],
    ['B', 'Z', 'Y'],
    ['Y', 'B', 'Z'],
    ['Y', 'Z', 'B'],
    ['Z', 'Y', 'B'],
    ['Z', 'B', 'Y']
]



# case III
"""
acceptance_sequences = [['X', 'Y', 'Z', 'A'],
                        ['X', 'Z', 'Y', 'A'],
                        ['Y', 'X', 'Z', 'A'],
                        ['Y', 'Z', 'X', 'A'],
                        ['Z', 'Y', 'X', 'A'],
                        ['Z', 'X', 'Y', 'A'],

                        ['X', 'Y', 'Z', 'B'],
                        ['X', 'Z', 'Y', 'B'],
                        ['Y', 'X', 'Z', 'B'],
                        ['Y', 'Z', 'X', 'B'],
                        ['Z', 'Y', 'X', 'B'],
                        ['Z', 'X', 'Y', 'B'],

                        ['X', 'Y', 'Z', 'C'],
                        ['X', 'Z', 'Y', 'C'],
                        ['Y', 'X', 'Z', 'C'],
                        ['Y', 'Z', 'X', 'C'],
                        ['Z', 'Y', 'X', 'C'],
                        ['Z', 'X', 'Y', 'C'],
                    ]
"""

# case IV
"""
acceptance_sequences = [['A', 'B', 'X'],
                        ['A', 'X', 'B'],
                        ['X', 'A', 'B'],

                        ['A', 'B', 'Y'],
                        ['A', 'Y', 'B'],
                        ['Y', 'A', 'B'],

                        ['A', 'B', 'X', 'Y'],
                        ['A', 'X', 'Y', 'B'],
                        ['X', 'Y', 'A', 'B'],

                        ['A', 'B', 'Y', 'X'],
                        ['A', 'Y', 'X', 'B'],
                        ['Y', 'X', 'A', 'B'],
                    ]
"""

# case V
"""
acceptance_sequences = [['A', 'X'],
                        ['A', 'Y'],
                        ['A', 'Z'],

                        ['B', 'X'],
                        ['B', 'Y'],
                        ['B', 'Z'],

                        ['C', 'X'],
                        ['C', 'Y'],
                        ['C', 'Z']
                    ]
"""

locked_dependencies = dict()

# example for thesis 
# acceptance_sequences = [['A', 'B', 'C', 'D'], ['B', 'A', 'C', 'D']]




"""
locked_dependencies = {
    ("X", "D"): (TemporalDependency(type=DIRECT, direction=BWD), None), 
    ("D", "X"): (TemporalDependency(type=DIRECT, direction=FWD), None), 

    ("X", "A"): (TemporalDependency(type=DIRECT, direction=FWD), None), 
    ("A", "X"): (TemporalDependency(type=DIRECT, direction=BWD), None), 
}
"""






# build the matrix
matrix = variants_to_matrix(acceptance_sequences)

print_matrix(matrix, "Initial Matrix")

# enable the debug mode 
enable_debug_mode()

print("\n" + "═" * 60)
print("   Business Process Redesign : Console Tool")
print("═" * 60)

# define change operation here 
result, locked_dependencies = op_insert(matrix, locked_dependencies)

# check if the user wants to end the application 
if result is None:
    print("\n  No further operations selected.  Exiting.\n")
    exit

# inform the user that the change operation was applied succesfully 
print(f"\n  ✓  Change operation applied successfully.")

# if the matrix did not change, display this information 
if result is not matrix:
    print_matrix(result, "Modified Matrix")
else:
    print("\n  ℹ  Matrix unchanged : no modified matrix to display.")

print(generate_acceptance_variants(result))

