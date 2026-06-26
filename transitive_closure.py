from itertools import permutations
from typing import List, Tuple, Dict, Set, Optional
from dependencies import (
    TemporalType,
    ExistentialType,
    TemporalDependency,
    ExistentialDependency,
    Direction,
)
from adjacency_matrix import AdjacencyMatrix

# import acceptance variants, since we can reuse most of the functions
from acceptance_variants import satisfies_existential_constraints
from acceptance_variants import satisfies_temporal_constraints
from acceptance_variants import build_permutations

# ── Skeleton generation ────────────────────────────────────────────────────────────
from acceptance_skeleton import generate_skeleton
from utils.console_helpers import deps_to_matrix

# import for BFS 
from collections import deque


def compute_transitive_closure(
    deps: dict,
) -> Dict:
    """
    Rteurns a dict with the transitive clsoure of the provided dependnecies (exist & temp), without the original dependnecies 

    Args: 
        temporal_deps: dictionary of the temporal dependnecies 
        
    Returns: 
        modified dict of the temporal dependencies with transitive closure 
    """

    # define a dictionary to store the closed dependnecies 
    closed_dependencies = dict()


    # iterate through all the locked dependencies 
    for (from_act_1, to_act_1), (temp_dep_1, exist_dep_1) in deps.items():
        
        # prevent checking duplicates 
        if to_act_1 > from_act_1: 
            continue

        for (from_act_2, to_act_2), (temp_dep_2, exist_dep_2) in deps.items():

            # reset the dependnecie sto be used 
            temp_dep_fwd = None 
            temp_dep_bwd = None 

            exist_dep_fwd = None 
            exist_dep_bwd = None 

            # prevent checking duplicates 
            if to_act_2 > from_act_2 or (to_act_1 == to_act_2 and from_act_1 == from_act_2): 
                continue

            # check if they have exactly one activity in common  
            if (from_act_1 == from_act_2) and (to_act_1 != to_act_2): 
                # to_act_1 - from_act_1 / from_act_2 - to_act_2

                act1 = to_act_1
                act2 = to_act_2

                # must compute the temporal closure 
                if temp_dep_1 and temp_dep_2: 

                    # check if both have the same direction  
                    if temp_dep_1.direction == Direction.BACKWARD and temp_dep_2.direction == Direction.FORWARD: 

                        # add the new temporal dependency 
                        temp_dep_fwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.FORWARD,
                        )

                        temp_dep_bwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.BACKWARD,
                        )

                    # check if both have the same direction  
                    elif temp_dep_1.direction == Direction.FORWARD and temp_dep_2.direction == Direction.BACKWARD: 

                        # add the new temporal dependency 
                        temp_dep_fwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.BACKWARD,
                        )

                        temp_dep_bwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.FORWARD,
                        )


                # compute the existential closure 
                if exist_dep_1 and exist_dep_2: 

                    # get the keys for the dependencies 
                    key1 = _to_key(reverse_dependency(exist_dep_1))
                    key2 = _to_key(exist_dep_2)

                    # derive the transitive dependnecy type 
                    result = _COMPOSE[(key1, key2)]
                    trans_exist_dep = _from_key(result)

                    # add the composed case
                    if trans_exist_dep: 
                        exist_dep_fwd = trans_exist_dep
                        exist_dep_bwd = reverse_dependency(trans_exist_dep)


            elif (from_act_1 != from_act_2) and (to_act_1 == to_act_2): 
                # from_act_1 - to_act_1 / to_act_2 - from_act_2

                act1 = from_act_1
                act2 = from_act_2

                # must compute the temporal closure 
                if temp_dep_1 and temp_dep_2: 

                    # check if both have the same direction  
                    if temp_dep_1.direction == Direction.FORWARD and temp_dep_2.direction == Direction.BACKWARD: 

                        # add the new temporal dependency 
                        temp_dep_fwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.FORWARD,
                        )

                        temp_dep_bwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.BACKWARD,
                        )

                    # check if both have the same direction  
                    elif temp_dep_1.direction == Direction.BACKWARD and temp_dep_2.direction == Direction.FORWARD: 

                        # add the new temporal dependency 
                        temp_dep_fwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.BACKWARD,
                        )

                        temp_dep_bwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.FORWARD,
                        )

                # compute the existential closure 
                if exist_dep_1 and exist_dep_2: 

                    # get the keys for the dependencies 
                    key1 = _to_key(exist_dep_1)
                    key2 = _to_key(reverse_dependency(exist_dep_2))

                    # derive the transitive dependnecy type 
                    result = _COMPOSE[(key1, key2)]
                    trans_exist_dep = _from_key(result)

                    # add the composed case
                    if trans_exist_dep: 
                        exist_dep_fwd = trans_exist_dep
                        exist_dep_bwd = reverse_dependency(trans_exist_dep)


            elif (from_act_1 == to_act_2) and (to_act_1 != from_act_2): 
                # to_act_1 - from_act_1 / to_act_2 - from_act_2

                act1 = to_act_1
                act2 = from_act_2

                # must compute the temporal closure 
                if temp_dep_1 and temp_dep_2: 

                    # check if both have the same direction  
                    if temp_dep_1.direction == Direction.BACKWARD and temp_dep_2.direction == Direction.BACKWARD: 

                        # add the new temporal dependency 
                        temp_dep_fwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.FORWARD,
                        )

                        temp_dep_bwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.BACKWARD,
                        )

                    # check if both have the same direction  
                    elif temp_dep_1.direction == Direction.BACKWARD and temp_dep_2.direction == Direction.FORWARD: 

                        # add the new temporal dependency 
                        temp_dep_fwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.BACKWARD,
                        )

                        temp_dep_bwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.FORWARD,
                        )

                # compute the existential closure 
                if exist_dep_1 and exist_dep_2: 

                    # get the keys for the dependencies 
                    key1 = _to_key(reverse_dependency(exist_dep_1))
                    key2 = _to_key(reverse_dependency(exist_dep_2))

                    # derive the transitive dependnecy type 
                    result = _COMPOSE[(key1, key2)]
                    trans_exist_dep = _from_key(result)

                    # add the composed case
                    if trans_exist_dep: 
                        exist_dep_fwd = trans_exist_dep
                        exist_dep_bwd = reverse_dependency(trans_exist_dep)


            elif (from_act_1 != to_act_2) and (to_act_1 == from_act_2): 
                # from_act_1 - to_act_1 / from_act_2 - to_act_2

                act1 = from_act_1
                act2 = to_act_2

                # must compute the temporal closure 
                if temp_dep_1 and temp_dep_2: 

                    # check if both have the same direction  
                    if temp_dep_1.direction == Direction.FORWARD and temp_dep_2.direction == Direction.FORWARD: 

                        # add the new temporal dependency 
                        temp_dep_fwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.FORWARD,
                        )

                        temp_dep_bwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.BACKWARD,
                        )

                    # check if both have the same direction  
                    elif temp_dep_1.direction == Direction.BACKWARD and temp_dep_2.direction == Direction.FORWARD: 

                        # add the new temporal dependency 
                        temp_dep_fwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.BACKWARD,
                        )

                        temp_dep_bwd = TemporalDependency(
                            type=TemporalType.EVENTUAL,
                            direction=Direction.FORWARD,
                        )

                # compute the existential closure 
                if exist_dep_1 and exist_dep_2: 

                    # get the keys for the dependencies 
                    key1 = _to_key(exist_dep_1)
                    key2 = _to_key(exist_dep_2)

                    # derive the transitive dependnecy type 
                    result = _COMPOSE[(key1, key2)]
                    trans_exist_dep = _from_key(result)

                    # add the composed case
                    if trans_exist_dep: 
                        exist_dep_fwd = trans_exist_dep
                        exist_dep_bwd = reverse_dependency(trans_exist_dep)


            else:
                # the two canonical pairs share no activity -> nothing to compose
                continue

            # nothing derived in either direction, don't write empty entries
            if (temp_dep_fwd is None and exist_dep_fwd is None
                    and temp_dep_bwd is None and exist_dep_bwd is None):
                continue

            # merge without letting a None clobber an already-derived value
            old_fwd = closed_dependencies.get((act1, act2), (None, None))
            old_bwd = closed_dependencies.get((act2, act1), (None, None))

            closed_dependencies[(act1, act2)] = (
                temp_dep_fwd if temp_dep_fwd is not None else old_fwd[0],
                exist_dep_fwd if exist_dep_fwd is not None else old_fwd[1],
            )
            closed_dependencies[(act2, act1)] = (
                temp_dep_bwd if temp_dep_bwd is not None else old_bwd[0],
                exist_dep_bwd if exist_dep_bwd is not None else old_bwd[1],
            )
            
            
    return closed_dependencies


def compute_full_transitive_closure(deps: dict) -> dict: 
    """
    For dependnecies, who might form longer dependency chains, compute the transitive closure. 
    Perform the calculation in multiple iterations, until it converges and no new dependencies are added

    Args: 
        dict: dictionary of the dependnecies, for which the closure is calculated 

    Returns: 
        dict of the closed dependencies without the original ones 
    """

    # pool of everything known so far (originals + derived); input for each pass
    all_deps = dict(deps)

    # accumulator for the derived dependencies only
    derived: dict = {}

    # result 
    result = dict()

    while True:
        new_closure = compute_transitive_closure(all_deps)

        added_something = False

        for key, (temp_dep, exist_dep) in new_closure.items():

            # an empty derivation carries no constraint
            if temp_dep is None and exist_dep is None:
                continue

            # already known (original or derived in an earlier pass) -> nothing new
            if key in all_deps:
                continue

            derived[key] = (temp_dep, exist_dep)
            all_deps[key] = (temp_dep, exist_dep)
            added_something = True

            if key not in deps: 
                result[key] = (temp_dep, exist_dep)

        # fixpoint reached: no pass produced a new pair
        if not added_something:
            break

    return result


def compute_full_closure_with_provenance(deps: dict):
    """
    Full transitive closure (multi-hop) that also records, for each derived
    dependency, the original edges its derivation used.

    Returns:
        closed: dict[(a, c)] -> (temp_dep, exist_dep)   # derived pairs only
        prov:   dict[(a, c)] -> {'temporal': set[frozenset], 'existential': set[frozenset]}
                each set holds the original *undirected* edges on a witness path
    """
    activities = {a for pair in deps for a in pair}

    # ── temporal "before" relation: (x,y) reachable ⇒ x eventually-before y ──
    before = {
        (x, y): {frozenset((x, y))}
        for (x, y), (temp, _e) in deps.items()
        if temp is not None and temp.direction == Direction.FORWARD
    }
    for m in activities:                       # Floyd–Warshall, keep first witness
        for a in activities:
            if a == m or (a, m) not in before:
                continue
            for c in activities:
                if c in (a, m) or (m, c) not in before or (a, c) in before:
                    continue
                before[(a, c)] = before[(a, m)] | before[(m, c)]

    # ── existential relation, composed via _COMPOSE on directed keys ──
    exist_key = {
        (x, y): (_to_key(ex), {frozenset((x, y))})
        for (x, y), (_t, ex) in deps.items()
        if ex is not None and ex.type != ExistentialType.INDEPENDENCE
    }
    for m in activities:
        for a in activities:
            if a == m or (a, m) not in exist_key:
                continue
            ka, pa = exist_key[(a, m)]
            for c in activities:
                if c in (a, m) or (m, c) not in exist_key or (a, c) in exist_key:
                    continue
                kc, pc = exist_key[(m, c)]
                kr = _COMPOSE[(ka, kc)]
                if kr is not None:
                    exist_key[(a, c)] = (kr, pa | pc)


    # ── assemble derived-only result, both directions, with provenance ──
    closed, prov = {}, {}

    def put(pair, slot, dep, edges):
        if pair in deps:                       # never shadow an original
            return
        cur = list(closed.get(pair, (None, None)))
        cur[slot] = dep
        closed[pair] = tuple(cur)
        p = prov.setdefault(pair, {'temporal': set(), 'existential': set()})
        p['temporal' if slot == 0 else 'existential'] = edges

    for (a, c), edges in before.items():
        fwd = TemporalDependency(TemporalType.EVENTUAL, Direction.FORWARD)
        put((a, c), 0, fwd, edges)
        put((c, a), 0, reverse_dependency(fwd), edges)

    for (a, c), (k, edges) in exist_key.items():
        dep = _from_key(k)
        if dep is None:
            continue
        put((a, c), 1, dep, edges)
        put((c, a), 1, reverse_dependency(dep), edges)

    return closed, prov

    


# dictionary to define the closure 
_COMPOSE = {
    ('IMP_FWD', 'IMP_FWD'): 'IMP_FWD',
    ('IMP_FWD', 'IMP_BWD'): None,
    ('IMP_FWD', 'EQUIV'): 'IMP_FWD',
    ('IMP_FWD', 'NEGEQ'): 'NAND',
    ('IMP_FWD', 'NAND'): 'NAND',
    ('IMP_FWD', 'OR'): None,
    ('IMP_FWD', 'INDEP'): None,
    ('IMP_BWD', 'IMP_FWD'): None,
    ('IMP_BWD', 'IMP_BWD'): 'IMP_BWD',
    ('IMP_BWD', 'EQUIV'): 'IMP_BWD',
    ('IMP_BWD', 'NEGEQ'): 'OR',
    ('IMP_BWD', 'NAND'): None,
    ('IMP_BWD', 'OR'): 'OR',
    ('IMP_BWD', 'INDEP'): None,
    ('EQUIV', 'IMP_FWD'): 'IMP_FWD',
    ('EQUIV', 'IMP_BWD'): 'IMP_BWD',
    ('EQUIV', 'EQUIV'): 'EQUIV',
    ('EQUIV', 'NEGEQ'): 'NEGEQ',
    ('EQUIV', 'NAND'): 'NAND',
    ('EQUIV', 'OR'): 'OR',
    ('EQUIV', 'INDEP'): None,
    ('NEGEQ', 'IMP_FWD'): 'OR',
    ('NEGEQ', 'IMP_BWD'): 'NAND',
    ('NEGEQ', 'EQUIV'): 'NEGEQ',
    ('NEGEQ', 'NEGEQ'): 'EQUIV',
    ('NEGEQ', 'NAND'): 'IMP_BWD',
    ('NEGEQ', 'OR'): 'IMP_FWD',
    ('NEGEQ', 'INDEP'): None,
    ('NAND', 'IMP_FWD'): None,
    ('NAND', 'IMP_BWD'): 'NAND',
    ('NAND', 'EQUIV'): 'NAND',
    ('NAND', 'NEGEQ'): 'IMP_FWD',
    ('NAND', 'NAND'): None,
    ('NAND', 'OR'): 'IMP_FWD',
    ('NAND', 'INDEP'): None,
    ('OR', 'IMP_FWD'): 'OR',
    ('OR', 'IMP_BWD'): None,
    ('OR', 'EQUIV'): 'OR',
    ('OR', 'NEGEQ'): 'IMP_BWD',
    ('OR', 'NAND'): 'IMP_BWD',
    ('OR', 'OR'): None,
    ('OR', 'INDEP'): None,
    ('INDEP', 'IMP_FWD'): None,
    ('INDEP', 'IMP_BWD'): None,
    ('INDEP', 'EQUIV'): None,
    ('INDEP', 'NEGEQ'): None,
    ('INDEP', 'NAND'): None,
    ('INDEP', 'OR'): None,
    ('INDEP', 'INDEP'): None,
}


def _to_key(dep: ExistentialDependency) -> str:
    # reduce an existential dependency, based on type and direction to a unique key 

    if dep is None or dep.type == ExistentialType.INDEPENDENCE:
        return 'INDEP'
    if dep.type == ExistentialType.EQUIVALENCE:
        return 'EQUIV'
    if dep.type == ExistentialType.NEGATED_EQUIVALENCE:
        return 'NEGEQ'
    if dep.type == ExistentialType.NAND:
        return 'NAND'
    if dep.type == ExistentialType.OR:
        return 'OR'
    if dep.type == ExistentialType.IMPLICATION:
        # antecedent => consequent in terms of (left, right)
        if dep.direction == Direction.FORWARD:
            return 'IMP_FWD'      # left => right
        if dep.direction == Direction.BACKWARD:
            return 'IMP_BWD'      # right => left
    return 'INDEP'


def _from_key(key: str) -> Optional[ExistentialDependency]:
    # Build the ExistentialDependency for a family key, or None for independence.

    if key == 'EQUIV':
        return ExistentialDependency(type=ExistentialType.EQUIVALENCE, direction=Direction.BOTH)
    if key == 'NEGEQ':
        return ExistentialDependency(type=ExistentialType.NEGATED_EQUIVALENCE, direction=Direction.BOTH)
    if key == 'NAND':
        return ExistentialDependency(type=ExistentialType.NAND, direction=Direction.BOTH)
    if key == 'OR':
        return ExistentialDependency(type=ExistentialType.OR, direction=Direction.BOTH)
    if key == 'IMP_FWD':
        return ExistentialDependency(type=ExistentialType.IMPLICATION, direction=Direction.FORWARD)
    if key == 'IMP_BWD':
        return ExistentialDependency(type=ExistentialType.IMPLICATION, direction=Direction.BACKWARD)
    return None


def reverse_dependency(dependency): 
    """
    For given depenency, reverse its direction. This method works for any dependency, regardless if existential or temporal 

    Args: 
        dependency: dependency (either temproal or existential)

    Returns: 
        dependency with reversed directions 
    """

    # filter the case, that the dependency is none (eg. for locked dependencies)
    if dependency is None:
        return None

    # cretae a depency map dictionary, map every direction to its reversed direction 
    direction_map = {
        Direction.FORWARD: Direction.BACKWARD,
        Direction.BACKWARD: Direction.FORWARD,
        Direction.BOTH: Direction.BOTH,
    }
    
    # get the reverse direction 
    reversed_direction = direction_map[dependency.direction]

    # return the dependency with the reversed direction
    if isinstance(dependency, TemporalDependency):
        return TemporalDependency(dependency.type, direction=reversed_direction)
    elif isinstance(dependency, ExistentialDependency):
        return ExistentialDependency(dependency.type, direction=reversed_direction)
    else:
        raise TypeError(f"Unsupported dependency type: {type(dependency)}")

        


    


    