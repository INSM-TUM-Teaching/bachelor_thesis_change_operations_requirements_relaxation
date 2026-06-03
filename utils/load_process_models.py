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

# ── Helper functions ─────────────────────────────────────────────────
from utils.console_helpers import prompt


def load_from_yaml() -> AdjacencyMatrix:
    """
    Load a process model from a YAML file. 

    1) Ask the user to provide the path for the YAML file 
    2) Try to load the file 
    3) Return the matrix derived from the YAML file 

    Returns: 
        AdjacencyMatrix: matrix loaded from the file 
    """
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

    Returns: 
        AdjacencyMatrix: matrix derived from the acceptance sequences
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