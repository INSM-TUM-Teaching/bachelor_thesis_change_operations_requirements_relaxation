import pytest

from acceptance_skeleton import generate_skeleton


from adjacency_matrix import AdjacencyMatrix
from dependencies import (
    TemporalDependency,
    ExistentialDependency,
    TemporalType,
    ExistentialType,
    Direction,
)

from variants_to_matrix import variants_to_matrix
from utils.console_helpers import deps_to_matrix


# Re-use shorthand constructors from the shared test setup
from tests.test_setup import DIRECT, EVENTUAL, INDEP, EQUIV, IMPL, NEG_EQUIV, OR, NAND, FWD, BWD, BOTH 

# ── Solution strategies ─────────────────────────────────────────────────
from solution_strategies.parallelization_strategies import parallelize_expand_set, parallelize_move_activities
from solution_strategies.collapse_strategies import collapse_expand_set, collapse_move_activities


def test_three_seq_expand_parallelize(): 
    # four sequential activities, parallelize outermost 

    # define acceptance sequences 
    acceptance_sequnces = [["A", "B", "C"]]

    # generate matrix 
    matrix = variants_to_matrix(acceptance_sequnces)

    result_sequences = parallelize_expand_set(acceptance_sequnces, ["A", "C"], ["B"])

    assert ["A", "B", "C"] in result_sequences
    assert ["A", "C", "B"] in result_sequences
    assert ["B", "A", "C"] in result_sequences
    assert ["B", "C", "A"] in result_sequences
    assert ["C", "A", "B"] in result_sequences
    assert ["C", "B", "A"] in result_sequences


def test_three_seq_move_parallelize(): 
    # four sequential activities, parallelize outermost 

    # define acceptance sequences 
    acceptance_sequnces = [["A", "B", "C"]]

    # generate matrix 
    matrix = variants_to_matrix(acceptance_sequnces)

    result_sequences = parallelize_move_activities(acceptance_sequnces, ["A", "C"], "A")

    assert ["A", "C", "B"] in result_sequences
    assert ["C", "A", "B"] in result_sequences


def test_unrealted_act_move_parallelize(): 
    # ensure unrealted variants are unchanged 

    # define acceptance sequences 
    acceptance_sequnces = [["A", "B", "C"], ["X", "Y"]]

    # generate matrix 
    matrix = variants_to_matrix(acceptance_sequnces)

    result_sequences = parallelize_move_activities(acceptance_sequnces, ["A", "C"], "A")

    assert ["X", "Y"] in result_sequences
    


# --------------------------------------------------------
# Collapse 
# --------------------------------------------------------

def test_three_seq_expand_collapse(): 
    # four sequential activities, parallelize outermost 

    # define acceptance sequences 
    acceptance_sequnces = [["A", "B", "C"]]

    # generate matrix 
    matrix = variants_to_matrix(acceptance_sequnces)

    result_sequences = collapse_expand_set(acceptance_sequnces, ["A", "C"], ["B"], "X")

    assert not any(
        "A" in seq or "B" in seq or "C" in seq
        for seq in result_sequences
    ), "Found acceptance sequence where activities were not collapsed"


def test_three_seq_move_collapse(): 
    # four sequential activities, parallelize outermost 

    # define acceptance sequences 
    acceptance_sequnces = [["A", "B", "C"]]

    # generate matrix 
    matrix = variants_to_matrix(acceptance_sequnces)

    result_sequences = collapse_move_activities(acceptance_sequnces, ["A", "C"], "X", "A")

    assert ["X", "B"] in result_sequences, "Moving activities for collapse fails"

    assert not any(
        "A" in seq or "C" in seq
        for seq in result_sequences
    ), "Found acceptance sequence where activities were not collapsed"


    


