from adjacency_matrix import AdjacencyMatrix
from optimized_acceptance_variants import generate_optimized_acceptance_variants as generate_acceptance_variants
from dependencies import ExistentialType


def replace_activity(
    matrix: AdjacencyMatrix, activity_to_replace: str, activity_to_insert: str
) -> AdjacencyMatrix:
    """
    Replaces an activity from the process by:
    1. Renaming all occurences of the activity in the matrix to the new activity

    Args:
        matrix: The input adjacency matrix
        activity_to_replace: The name of the activity currently in process to be replaced
        activity_to_insert: The name of the activity which should be inserted instead of the current activity

    Returns:
        A new adjacency matrix with the activity replaced

    Raises:
        ValueError: If activity not found or activity to insert is already part of the matrix
        ValueError: If activity to inserted is already in matrix
    """

    # modify the name of the activity to be replaced by the newly named activity
    activities = matrix.get_activities()
    dependencies = matrix.get_dependencies()

    if activity_to_replace not in activities:
        raise ValueError(f"Activity {activity_to_replace} not found in matrix")

    # Check that activity to be inserted is not already in process
    if activity_to_insert in activities:
        raise ValueError(
            f"Activity {activity_to_insert} already in matrix. Activities may not appear double to ensure uniqueness"
        )

    # replace names in activities
    activities[activities.index(activity_to_replace)] = activity_to_insert

    # replace in dict with dependencies
    new_matrix = AdjacencyMatrix(activities)
    for (from_act, to_act), (temporal_dep, existential_dep) in dependencies.items():
        updated_from = (
            activity_to_insert if from_act == activity_to_replace else from_act
        )
        updated_to = activity_to_insert if to_act == activity_to_replace else to_act
        new_matrix.add_dependency(
            updated_from, updated_to, temporal_dep, existential_dep
        )

    return new_matrix
