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