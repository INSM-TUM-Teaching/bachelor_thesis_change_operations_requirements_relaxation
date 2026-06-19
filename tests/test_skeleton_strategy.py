import pytest 

from solution_strategies.skeleton_strategies import adapt_acceptance_sequence, adapt_process, get_combined_occurrences_containing, get_contained_occurence_combinations
from solution_strategies.skeleton_strategies import contained_ordering_pairs, sequences_containing_pairs


class TestContainedOrderingPairs: 
    # test the contained ordering pairs method 
    # used to identify which ordering pairs from a list are contained in a sequence 

    def test_all_pairs_present_in_order(self):
        sequence = ["A", "B", "C"]
        pairs = [("A", "B"), ("B", "C"), ("A", "C")]
        result = contained_ordering_pairs(sequence, pairs)
        assert ("A", "B") in result
        assert ("B", "C") in result
        assert ("A", "C") in result
 
    def test_pair_present_but_wrong_order_excluded(self):
        sequence = ["B", "A", "C"]
        pairs = [("A", "B"), ("B", "C")]
        result = contained_ordering_pairs(sequence, pairs)
        # A comes after B → ("A","B") not satisfied
        assert ("A", "B") not in result
        # B before C → satisfied
        assert ("B", "C") in result
 
    def test_pair_with_missing_activity_excluded(self):
        sequence = ["A", "C"]
        pairs = [("A", "B"), ("A", "C")]
        result = contained_ordering_pairs(sequence, pairs)
        assert ("A", "B") not in result
        assert ("A", "C") in result
 
    def test_empty_sequence_returns_no_pairs(self):
        result = contained_ordering_pairs([], [("A", "B")])
        assert result == []
 
    def test_empty_pairs_list_returns_empty(self):
        result = contained_ordering_pairs(["A", "B", "C"], [])
        assert result == []
 
    def test_single_activity_sequence(self):
        result = contained_ordering_pairs(["A"], [("A", "B")])
        assert result == []
 
    def test_skeleton_placeholder_ignored(self):
        # Placeholders '_' should not disrupt pair detection
        sequence = ["_", "A", "_", "B", "_"]
        pairs = [("A", "B")]
        result = contained_ordering_pairs(sequence, pairs)
        assert ("A", "B") in result


class TestSequencesContainingPairs:
    # test the seqeunces containing pairs method 
    # used to identify for a given ordering pair all sequences which contain this pair 
 
    def test_basic_pair_found(self):
        sequences = [["A", "B", "C"], ["C", "A", "B"], ["B", "A"]]
        result = sequences_containing_pairs(sequences, ("A", "B"))
        assert ["A", "B", "C"] in result
        assert ["C", "A", "B"] in result
        # ["B", "A"] has wrong order
        assert ["B", "A"] not in result
 
    def test_pair_with_missing_activity(self):
        sequences = [["A", "C"], ["A", "B"]]
        result = sequences_containing_pairs(sequences, ("A", "B"))
        assert ["A", "C"] not in result
        assert ["A", "B"] in result
 
    def test_empty_sequences_list(self):
        result = sequences_containing_pairs([], ("A", "B"))
        assert result == []
 
    def test_no_sequence_matches(self):
        sequences = [["B", "A"], ["C", "D"]]
        result = sequences_containing_pairs(sequences, ("A", "B"))
        assert result == []
 
    def test_all_sequences_match(self):
        sequences = [["A", "B"], ["X", "A", "Y", "B"]]
        result = sequences_containing_pairs(sequences, ("A", "B"))
        assert len(result) == 2
 
    def test_skeleton_sequences_with_placeholders(self):
        sequences = [["_", "A", "_", "B", "_"], ["_", "B", "_", "A", "_"]]
        result = sequences_containing_pairs(sequences, ("A", "B"))
        assert ["_", "A", "_", "B", "_"] in result
        assert ["_", "B", "_", "A", "_"] not in result


