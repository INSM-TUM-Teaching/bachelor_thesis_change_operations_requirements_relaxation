"""
This file simplifies the validation and evaluation. For every WCP used, it specifies the acceptance sequences. 

Additionally the setup is simplified, as the user does not has to specify the initial setup in the console interface, but it is done in code. 
"""

# ── Core imports ────────────────────────────────────────────────────────────
from dependencies import (
    TemporalDependency, ExistentialDependency,
    TemporalType, ExistentialType, Direction,
)
from variants_to_matrix import variants_to_matrix
from acceptance_variants import generate_acceptance_variants

# ── Helper functions ─────────────────────────────────────────────────
from utils.console_helpers import print_matrix
from utils.console_helpers import print_matrix_difference

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

# ── Debug mode ─────────────────────────────────────────────────
from utils.debug_mode import enable as enable_debug_mode

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
#  Definitions of acceptance seqeunces for WCPs 
#  Select the desired one by removing the comments 
# ════════════════════════════════════════════════════════════════════════════

# default empty acceptance seqeunce 
acceptance_sequences = []

# WCP 1 
# acceptance_sequences = [['A', 'B', 'C', 'D']]

# WCP 2 
# acceptance_sequences = [['A', 'B', 'C'],['A', 'C', 'B'],['B', 'A', 'C'],['B', 'C', 'A'],['C', 'A', 'B'],['C', 'B', 'A']]

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

# WCP 10 
"""
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

# WCP 17
"""
acceptance_sequences = [
    ['A', 'B', 'C'],
    ['A', 'C', 'B'],
    ['C', 'A', 'B'],
]
"""

#WCP 19
"""
# acceptance_sequences = [['A', 'B'], ['A']]
"""



# ════════════════════════════════════════════════════════════════════════════
#  Definitions of acceptance seqeunces for the processes used for validation 
#  Select the desired one by removing the comments 
# ════════════════════════════════════════════════════════════════════════════


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
"""
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
"""

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


# ════════════════════════════════════════════════════════════════════════════
#  Definitions of acceptance sequences for the running example in the thesis
# ════════════════════════════════════════════════════════════════════════════

"""
acceptance_sequences = [['A', 'B', 'C', 'D'], 
                        ['B', 'A', 'C', 'D'], 
                        ['A', 'B', 'D'], 
                        ['B', 'A', 'D'], 
                    ]
"""


# ════════════════════════════════════════════════════════════════════════════
#  Definitions of locked dependencies 
#  Adapt the provided dependencies 
# ════════════════════════════════════════════════════════════════════════════

# default - no locked dependencies 
locked_dependencies = dict()

# setup to add locked dependencies - add in both directions, since the algorithm also always dds them in both directions 
"""
locked_dependencies = {
    ("X", "D"): (TemporalDependency(type=DIRECT, direction=BWD), None), 
    ("D", "X"): (TemporalDependency(type=DIRECT, direction=FWD), None), 

    ("X", "A"): (TemporalDependency(type=DIRECT, direction=FWD), None), 
    ("A", "X"): (TemporalDependency(type=DIRECT, direction=BWD), None), 
}
"""

# ════════════════════════════════════════════════════════════════════════════
#  Application of change operation 
#  Just adapt the change operation provided in code in line 274 and insert the appropriate application handler 
# ════════════════════════════════════════════════════════════════════════════

# build the matrix
matrix = variants_to_matrix(acceptance_sequences)

# print the matrix to the console 
print_matrix(matrix, "Initial Matrix")

# enable the debug mode - allow for a better understanding 
enable_debug_mode()

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
    print_matrix_difference(original_matrix=matrix, modified_matrix=result, title="Modified Matrix")
else:
    print("\n  ℹ  Matrix unchanged : no modified matrix to display.")

# output the resulting acceptance sequences 
print(generate_acceptance_variants(result))

