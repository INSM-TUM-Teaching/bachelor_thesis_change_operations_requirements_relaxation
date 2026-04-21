from itertools import permutations
from typing import List, Tuple, Dict, Set, Optional, FrozenSet
from functools import lru_cache
from dependencies import (
    TemporalType,
    ExistentialType,
    TemporalDependency,
    ExistentialDependency,
    Direction,
)
from adjacency_matrix import AdjacencyMatrix
from constraint_logic import check_temporal_relationship, check_existential_relationship
from acceptance_variants import satisfies_temporal_constraints, satisfies_existential_constraints


def generate_optimized_acceptance_variants(adj_matrix: AdjacencyMatrix) -> List[List[str]]:
    """
    Generates all valid acceptance variants from an adjacency matrix using an optimized approach.
    
    Optimizations:
    1. Uses cached validation functions
    2. Employs directed graph logic for temporal constraints to prune invalid permutations early
    3. Processes existential constraints before generating permutations
    4. Uses bitwise operations for faster subset generation and validation
    """
    activities = adj_matrix.activities
    temporal_deps: Dict[Tuple[str, str], TemporalDependency] = {}
    existential_deps: Dict[Tuple[str, str], ExistentialDependency] = {}
    
    # Extract dependencies
    for (source, target), (temp_dep, exist_dep) in adj_matrix.dependencies.items():
        if temp_dep:
            temporal_deps[(source, target)] = temp_dep
        if exist_dep:
            existential_deps[(source, target)] = exist_dep
    
    # Convert activities to indices for faster operations
    activity_to_idx = {activity: idx for idx, activity in enumerate(activities)}
    idx_to_activity = {idx: activity for idx, activity in enumerate(activities)}
    
    # Create a directed graph representation of direct temporal constraints
    direct_constraints = {}
    eventual_constraints = {}
    for (source, target), dep in temporal_deps.items():
        if dep.type == TemporalType.DIRECT and dep.direction in [Direction.FORWARD, Direction.BOTH]:
            src_idx = activity_to_idx[source]
            tgt_idx = activity_to_idx[target]
            if src_idx not in direct_constraints:
                direct_constraints[src_idx] = set()
            direct_constraints[src_idx].add(tgt_idx)
        
        if dep.type == TemporalType.EVENTUAL and dep.direction in [Direction.FORWARD, Direction.BOTH]:
            src_idx = activity_to_idx[source]
            tgt_idx = activity_to_idx[target]
            if src_idx not in eventual_constraints:
                eventual_constraints[src_idx] = set()
            eventual_constraints[src_idx].add(tgt_idx)
    
    # Create reverse direct constraints (for backward direction)
    reverse_direct_constraints = {}
    reverse_eventual_constraints = {}
    for (source, target), dep in temporal_deps.items():
        if dep.type == TemporalType.DIRECT and dep.direction in [Direction.BACKWARD, Direction.BOTH]:
            src_idx = activity_to_idx[source]
            tgt_idx = activity_to_idx[target]
            if tgt_idx not in reverse_direct_constraints:
                reverse_direct_constraints[tgt_idx] = set()
            reverse_direct_constraints[tgt_idx].add(src_idx)
        
        if dep.type == TemporalType.EVENTUAL and dep.direction in [Direction.BACKWARD, Direction.BOTH]:
            src_idx = activity_to_idx[source]
            tgt_idx = activity_to_idx[target]
            if tgt_idx not in reverse_eventual_constraints:
                reverse_eventual_constraints[tgt_idx] = set()
            reverse_eventual_constraints[tgt_idx].add(src_idx)
    
    # Cache for existential constraint validation
    @lru_cache(maxsize=1024)
    def satisfies_existential_constraints_cached(subset_bitset: int) -> bool:
        """
        Checks if a subset of activities satisfies all existential constraints.
        Uses bitset for faster operations.
        """
        for (src, tgt), dependency in existential_deps.items():
            src_idx = activity_to_idx[src]
            tgt_idx = activity_to_idx[tgt]
            
            in_subset_src = (subset_bitset & (1 << src_idx)) > 0
            in_subset_tgt = (subset_bitset & (1 << tgt_idx)) > 0
            
            if dependency.type == ExistentialType.INDEPENDENCE:
                continue

            if dependency.type == ExistentialType.OR:
                # at least one must be present
                if not (in_subset_src or in_subset_tgt):
                    return False
                continue

            if dependency.type == ExistentialType.EQUIVALENCE:
                if in_subset_src != in_subset_tgt:
                    return False
                continue

            if not check_existential_relationship(
                in_subset_src, in_subset_tgt, dependency.type, dependency.direction
            ):
                return False
        
        return True
    
    # Function to generate valid variants using topological sorting principles
    def generate_valid_permutations(subset_bitset: int) -> List[List[int]]:
        """
        Generates valid permutations based on temporal constraints.
        Uses a modified topological sort approach that respects direct and eventual constraints.
        """
        # Convert bitset to list of activity indices
        subset_indices = [i for i in range(len(activities)) if subset_bitset & (1 << i)]
        if not subset_indices:
            return [[]]
            
        # If only one activity, no need for permutation checks
        if len(subset_indices) == 1:
            return [subset_indices]
        
        # For small subsets, we can still use permutations efficiently
        if len(subset_indices) <= 3:
            all_perms = list(permutations(subset_indices))
            valid_perms = []
            
            for perm in all_perms:
                if is_valid_permutation(list(perm)):
                    valid_perms.append(list(perm))
            
            return valid_perms
        
        # For larger subsets, use a more optimized approach
        valid_perms = []
        
        # Use a recursive backtracking approach to generate valid permutations
        def backtrack(remaining: Set[int], current_path: List[int]):
            if not remaining:
                valid_perms.append(current_path.copy())
                return
                
            for next_idx in list(remaining):
                # Check if adding next_idx violates any direct constraints with the current path
                if not can_add_to_path(current_path, next_idx):
                    continue
                    
                current_path.append(next_idx)
                remaining.remove(next_idx)
                
                backtrack(remaining, current_path)
                
                remaining.add(next_idx)
                current_path.pop()
        
        backtrack(set(subset_indices), [])
        return valid_perms
    
    def can_add_to_path(current_path: List[int], next_idx: int) -> bool:
        """
        Checks if adding next_idx to the current path violates any direct temporal constraints.
        """
        if not current_path:
            return True

        next_direct = direct_constraints.get(next_idx, set())
        next_reverse_direct = reverse_direct_constraints.get(next_idx, set())

        for idx in current_path:
            idx_direct = direct_constraints.get(idx, set())
            idx_reverse_direct = reverse_direct_constraints.get(idx, set())

            # If there's a direct constraint from next_idx -> idx, it's invalid
            if idx in next_direct:
                return False

            # If there's a direct constraint from idx -> next_idx where idx is not the last element
            if next_idx in idx_direct and idx != current_path[-1]:
                return False

            # Check reverse direct constraints
            if idx in next_reverse_direct:
                return False

            if next_idx in idx_reverse_direct and idx != current_path[-1]:
                return False

        return True
    
    def is_valid_permutation(perm: List[int]) -> bool:
        """
        Performs a final validation of a permutation against all temporal constraints.
        """
        idx_to_pos = {idx: pos for pos, idx in enumerate(perm)}
        
        for (src, tgt), dep in temporal_deps.items():
            if dep.type == TemporalType.INDEPENDENCE:
                continue
                
            src_idx = activity_to_idx[src]
            tgt_idx = activity_to_idx[tgt]
            
            # Skip if either activity is not in the permutation
            if src_idx not in idx_to_pos or tgt_idx not in idx_to_pos:
                continue
                
            pos_src = idx_to_pos[src_idx]
            pos_tgt = idx_to_pos[tgt_idx]
            
            if not check_temporal_relationship(
                pos_src, pos_tgt, dep.type, dep.direction
            ):
                return False
                
        return True
    
    # Main generation algorithm
    acceptance_variants = []
    n = len(activities)
    
    # Define nested function for processing subsets of each size
    def process_subsets_of_size(size):
        if size == 0:
            if satisfies_existential_constraints_cached(0):
                acceptance_variants.append([])
            return

        if size == 1:
            # Single-element subsets are handled directly
            for i in range(n):
                subset_bitset = 1 << i
                if satisfies_existential_constraints_cached(subset_bitset):
                    acceptance_variants.append([activities[i]])
            return
            
        def generate_combinations(start_idx, remaining_size, current_bitset):
            if remaining_size == 0:
                if satisfies_existential_constraints_cached(current_bitset):
                    for valid_perm_indices in generate_valid_permutations(current_bitset):
                        valid_perm = [idx_to_activity[idx] for idx in valid_perm_indices]
                        acceptance_variants.append(valid_perm)
                return
                
            for i in range(start_idx, n - remaining_size + 1):
                generate_combinations(i + 1, remaining_size - 1, current_bitset | (1 << i))
                
        generate_combinations(0, size, 0)
    
    # Use a custom loop to process subsets in increasing size
    # This helps with memoization and pruning
    for size in range(0, n + 1):
        # Process subsets of each size separately to improve locality
        process_subsets_of_size(size)

    copy_variants = acceptance_variants.copy()
    for variant in copy_variants:
        if not satisfies_temporal_constraints(variant, temporal_deps):
            acceptance_variants.remove(variant)

    return acceptance_variants
