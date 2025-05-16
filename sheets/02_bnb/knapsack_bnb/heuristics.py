"""
Heuristics Module

In branch-and-bound, a relaxation gives an upper bound on the best objective in a branch.
To tighten pruning, you need feasible (integral) solutions to serve as lower bounds.
Instead of waiting for an integral node, you can derive feasible solutions from the relaxation
(e.g., rounding, greedy inclusion) to improve search efficiency.

You can implement heuristics by subclassing `Heuristics` and overriding `search(instance, node)`.
`search` should yield zero or more feasible `RelaxedSolution` objects.
"""

import math
from abc import ABC, abstractmethod
from typing import Iterable, Tuple

from .bnb_nodes import BnBNode, RelaxedSolution
from .instance import Instance
from .relaxation import RelaxedSolution


class Heuristics(ABC):
    """
    Abstract base for heuristic generators.

    Implement `search` to produce feasible solutions from a node's relaxed solution.
    """

    @abstractmethod
    def search(self, instance: Instance, node: BnBNode) -> Iterable[RelaxedSolution]:
        """
        Return an iterable of feasible `RelaxedSolution` objects for pruning.
        """
        ...
class MyHeuristic(Heuristics):
    def search(self, instance: Instance, node: BnBNode):
        items = instance.items
        capacity = instance.capacity
        total_weight = 0
        total_value = 0
        selection = [0] * len(items)

        decisions = node.relaxed_solution.selection  # Correct way


        for i, decision in enumerate(decisions):
            if decision == 1:
                total_weight += items[i].weight
                total_value += items[i].value
                selection[i] = 1
            elif decision == 0:
                selection[i] = 0

        if total_weight > capacity:
            return []

        undecided = [
            (i, items[i]) for i in range(len(items)) if decisions[i] is None
        ]
        undecided.sort(key=lambda x: -x[1].value / x[1].weight)

        for i, item in undecided:
            if total_weight + item.weight <= capacity:
                selection[i] = 1
                total_weight += item.weight
                total_value += item.value

        return [RelaxedSolution(instance, selection, total_value)]
"""        
class MyHeuristic(Heuristics):
    best_value_seen = float("-inf")
    def search(self, instance: Instance, node: BnBNode) -> Tuple[RelaxedSolution, ...]:
        items = instance.items
        selection = [0.0] * len(items)
        remaining_capacity = instance.capacity
        solutions = []

        # Apply fixed decisions
        for i, d in enumerate(node.branching_decisions):
            if d == 1:
                selection[i] = 1.0
                remaining_capacity -= items[i].weight
                if remaining_capacity < 0:
                    return ()
            elif d == 0:
                selection[i] = 0.0

        # Greedy fill
        remaining = [
            (i, items[i]) for i in range(len(items)) if node.branching_decisions[i] is None
        ]
        remaining.sort(key=lambda x: (-x[1].value / x[1].weight, -x[1].value))
        greedy_sel = selection[:]
        cap = remaining_capacity

        for i, item in remaining:
            if item.weight <= cap:
                greedy_sel[i] = 1.0
                cap -= item.weight

        val = sum(item.value * sel for item, sel in zip(items, greedy_sel))
        if val > MyHeuristic.best_value_seen:
            MyHeuristic.best_value_seen = val
            solutions.append(RelaxedSolution(instance, greedy_sel, val))

    # Try rounded relaxed solution too
        relaxed_sel = node.relaxed_solution.selection
        rounded_sel = [round(x) for x in relaxed_sel]
        if sum(item.weight * s for item, s in zip(items, rounded_sel)) <= instance.capacity:
            val = sum(item.value * s for item, s in zip(items, rounded_sel))
            if val > MyHeuristic.best_value_seen:
                MyHeuristic.best_value_seen = val
                solutions.append(RelaxedSolution(instance, rounded_sel, val))

        return tuple(solutions)


class MyHeuristic(Heuristics):
    best_value_seen = float("-inf")

    def search(self, instance: Instance, node: BnBNode) -> Tuple[RelaxedSolution, ...]:
        items = instance.items
        selection = [0.0] * len(items)
        remaining_capacity = instance.capacity
        for i, d in enumerate(node.branching_decisions):
            if d == 1:
                selection[i] = 1.0
                remaining_capacity -= items[i].weight
                if remaining_capacity < 0:
                    return ()
            elif d == 0:
                selection[i] = 0.0

        remaining = [
            (i, items[i]) for i in range(len(items)) if node.branching_decisions[i] is None
        ]
        remaining.sort(key=lambda x: -x[1].value / x[1].weight)

        for i, item in remaining:
            if item.weight <= remaining_capacity:
                selection[i] = 1.0
                remaining_capacity -= item.weight
            else:
                break  # exit loop early

        total_value = sum(item.value * sel for item, sel in zip(items, selection))
    
    # Try simple rounding of relaxed solution as backup
        fallback = node.relaxed_solution.selection
        rounded = [1.0 if x >= 0.9999 else 0.0 for x in fallback]
        if (
            sum(i.weight for i, sel in zip(items, rounded) if sel) <= instance.capacity
            and (val := sum(i.value for i, sel in zip(items, rounded) if sel)) > total_value
        ):
            selection = rounded
            total_value = val

        if total_value > MyHeuristic.best_value_seen:
            MyHeuristic.best_value_seen = total_value
            return (RelaxedSolution(instance, selection, total_value),)

        return ()



class MyHeuristic(Heuristics):
    best_value_seen = float("-inf")

    def search(self, instance: Instance, node: BnBNode) -> Tuple[RelaxedSolution, ...]:
        items = instance.items
        branching = node.branching_decisions
        selection = [0.0] * len(items)
        remaining_capacity = instance.capacity

        # Apply branching decisions
        for i, d in enumerate(branching):
            if d == 1:
                selection[i] = 1.0
                remaining_capacity -= items[i].weight
                if remaining_capacity < 0:
                    return ()  # infeasible node
            elif d == 0:
                selection[i] = 0.0

        # Greedy packing by value-to-weight
        remaining = [(i, items[i]) for i in range(len(items)) if branching[i] is None]
        remaining.sort(key=lambda x: (-x[1].value / x[1].weight, -x[1].value))

        greedy_selection = selection[:]
        cap = remaining_capacity

        for i, item in remaining:
            if item.weight <= cap:
                greedy_selection[i] = 1.0
                cap -= item.weight
            if cap <= 0:
                break  # early stop once full

        total_value = sum(item.value * sel for item, sel in zip(items, greedy_selection))

        solutions = []

        # Add greedy solution if valid
        if total_value >= 0:
            solutions.append(RelaxedSolution(instance, greedy_selection, total_value))
            if total_value > MyHeuristic.best_value_seen:
                MyHeuristic.best_value_seen = total_value

        # Try rounding relaxed solution as backup
        relaxed_selection = node.relaxed_solution.selection
        rounded_selection = [round(x) for x in relaxed_selection]

        # Check feasibility
        rounded_total_weight = sum(item.weight * sel for item, sel in zip(items, rounded_selection))
        if rounded_total_weight <= instance.capacity:
            rounded_value = sum(item.value * sel for item, sel in zip(items, rounded_selection))
            solutions.append(RelaxedSolution(instance, rounded_selection, rounded_value))
            if rounded_value > MyHeuristic.best_value_seen:
                MyHeuristic.best_value_seen = rounded_value

        return tuple(solutions)


     def search(self, instance: Instance, node: BnBNode) -> Tuple[RelaxedSolution, ...]:
        items = instance.items
        selection = [0.0] * len(items)
        remaining_capacity = instance.capacity

        for i, d in enumerate(node.branching_decisions):
            if d == 1:
                selection[i] = 1.0
                remaining_capacity -= items[i].weight
                if remaining_capacity < 0:
                    return ()
            elif d == 0:
                selection[i] = 0.0

        # Greedy selection
        remaining = [
            (i, items[i]) for i in range(len(items)) if node.branching_decisions[i] is None
        ]
        remaining.sort(key=lambda x: -x[1].value / x[1].weight)
        #remaining.sort(key=lambda x: (-x[1].value / x[1].weight, -x[1].value))


        for i, item in remaining:
            if item.weight <= remaining_capacity:
                selection[i] = 1.0
                remaining_capacity -= item.weight

        total_value = sum(item.value * sel for item, sel in zip(items, selection))

        if total_value > MyHeuristic.best_value_seen:
            MyHeuristic.best_value_seen = total_value
            return (RelaxedSolution(instance, selection, total_value),)
        return ()


   
    Your heuristic implementation.

    The simplest heuristic returns the node's relaxed solution
    if it is already feasible (integral and within capacity).
  

    def search(self, instance: Instance, node: BnBNode) -> Tuple[RelaxedSolution, ...]:
        sol = node.relaxed_solution
        if sol.does_obey_capacity_constraint() and sol.is_integral():
            return (sol,)
        return ()
  """

