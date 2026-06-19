from adjacency_matrix import AdjacencyMatrix
from dependencies import (
    TemporalDependency, ExistentialDependency,
    TemporalType, ExistentialType, Direction,
)
from acceptance_skeleton import generate_skeleton

# ── Build the conditions matrix ──────────────────────────────────────────────
# Activities: A, B, C
# Existential:  A <=> B  (EQUIVALENCE)
#               B </=> C (NEGATED_EQUIVALENCE / XOR)
# Temporal:     all INDEPENDENCE (no ordering constraints)

matrix = AdjacencyMatrix(activities=["A", "B", "C"])

temp_indep   = TemporalDependency(type=TemporalType.INDEPENDENCE, direction=Direction.BOTH)
exist_equiv  = ExistentialDependency(type=ExistentialType.EQUIVALENCE,         direction=Direction.BOTH)
exist_negequiv = ExistentialDependency(type=ExistentialType.NEGATED_EQUIVALENCE, direction=Direction.BOTH)
exist_indep  = ExistentialDependency(type=ExistentialType.INDEPENDENCE,         direction=Direction.BOTH)

# A <=> B
matrix.add_dependency("A", "B", temp_indep, exist_equiv)
matrix.add_dependency("B", "A", temp_indep, exist_equiv)

# B </=> C
matrix.add_dependency("B", "C", temp_indep, exist_negequiv)
matrix.add_dependency("C", "B", temp_indep, exist_negequiv)

# A -- C  (no constraint between A and C directly)
matrix.add_dependency("A", "C", temp_indep, exist_indep)
matrix.add_dependency("C", "A", temp_indep, exist_indep)

# ── Generate skeleton ─────────────────────────────────────────────────────────
skeleton = generate_skeleton(matrix)

print("Skeleton sequences:")
for seq in skeleton:
    print(" ", seq if seq else "[]  (empty sequence)")