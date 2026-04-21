from dependencies import (Direction, ExistentialType, TemporalType)

# --- Temporal Evaluation Helpers ---

def is_directly_follows(pos_first: int, pos_second: int) -> bool:
    """Checks if an event at pos_second directly follows an event at pos_first."""
    return pos_second == pos_first + 1

def is_eventually_follows(pos_first: int, pos_second: int) -> bool:
    """
    Checks if an event at pos_second eventually (but not necessarily directly)
    follows an event at pos_first.
    """
    return pos_first < pos_second

# --- Existential Evaluation Helpers ---

def evaluate_implication(antecedent_present: bool, consequent_present: bool) -> bool:
    """Checks if (antecedent_present => consequent_present) is true."""
    # True if not (antecedent is present and consequent is absent)
    return not (antecedent_present and not consequent_present)

def evaluate_equivalence(first_present: bool, second_present: bool) -> bool:
    """Checks if (first_present <=> second_present) is true."""
    return first_present == second_present

def evaluate_negated_equivalence(first_present: bool, second_present: bool) -> bool:
    """Checks if (first_present XOR second_present) is true."""
    return first_present != second_present

def evaluate_nand(first_present: bool, second_present: bool) -> bool:
    """Checks if NOT (first_present AND second_present) is true."""
    return not (first_present and second_present)

def evaluate_or(first_present: bool, second_present: bool) -> bool:
    """Checks if (first_present OR second_present) is true."""
    return first_present or second_present

# --- Combined Checkers ---

def check_temporal_relationship(
    source_pos: int,
    target_pos: int,
    relationship_type: TemporalType,
    direction: Direction,
) -> bool:
    """
    Checks if the positions of source and target satisfy the specified temporal relationship.
    """
    if direction == Direction.BACKWARD:
        source_pos, target_pos = target_pos, source_pos

    if relationship_type == TemporalType.DIRECT:
        return is_directly_follows(source_pos, target_pos)
    elif relationship_type == TemporalType.EVENTUAL:
        return is_eventually_follows(source_pos, target_pos)
    elif relationship_type == TemporalType.INDEPENDENCE:
        return True
    raise ValueError(f"Unsupported temporal relationship type: {relationship_type}")


def check_existential_relationship(
    source_present: bool,
    target_present: bool,
    relationship_type: ExistentialType,
    direction: Direction,
) -> bool:
    """
    Checks if the presence/absence of source and target satisfies the specified existential relationship.
    """
    if direction == Direction.BACKWARD:
        source_present, target_present = target_present, source_present

    if relationship_type == ExistentialType.IMPLICATION:
        return evaluate_implication(source_present, target_present)
    elif relationship_type == ExistentialType.EQUIVALENCE:
        return evaluate_equivalence(source_present, target_present)
    elif relationship_type == ExistentialType.NEGATED_EQUIVALENCE:
        return evaluate_negated_equivalence(source_present, target_present)
    elif relationship_type == ExistentialType.NAND:
        return evaluate_nand(source_present, target_present)
    elif relationship_type == ExistentialType.OR:
        return evaluate_or(source_present, target_present)
    elif relationship_type == ExistentialType.INDEPENDENCE:
        return True
    raise ValueError(f"Unsupported existential relationship type: {relationship_type}")
