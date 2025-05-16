"""
Branching Strategy Module

Defines how to split (branch) a BnB tree node when its current relaxed solution
is not yet a feasible integer solution. At each branching step:
 1. Select a decision variable that has not been fixed.
 2. Create two children by fixing that variable to 0 (exclude) and 1 (include).
 3. If all variables are fixed, no branches are returned (leaf node).

You should implement your own strategies by subclassing `BranchingStrategy`.
"""

from abc import ABC, abstractmethod
from typing import Iterable, Tuple

from .bnb_nodes import BnBNode, BranchingDecisions


class BranchingStrategy(ABC):
    """
    Abstract base for branching policies based on a node's relaxed solution.

    Subclasses must implement `make_branching_decisions` to return zero,
    two, or more `BranchingDecisions` objects describing child nodes.
    """

    @abstractmethod
    def make_branching_decisions(self, node: BnBNode) -> Iterable[BranchingDecisions]:
        """
        Return an iterable of `BranchingDecisions` to create child nodes.
        If no decisions can be made (all variables fixed), return an empty iterable.
        """
        ...


class FirstUndecidedBranchingStrategy(BranchingStrategy):
    """
    Branch on the first variable that has not yet been fixed.
    """

    def make_branching_decisions(self, node: BnBNode) -> Tuple[BranchingDecisions, ...]:
        # find the smallest index i where no decision has been made
        first_unfixed = min(
            (i for i, val in enumerate(node.branching_decisions) if val is None),
            default=-1,
        )
        if first_unfixed < 0:
            return ()  # leaf node, nothing to branch
        return node.branching_decisions.split_on(first_unfixed)


class MyBranchingStrategy(BranchingStrategy):
    """
    Your implementation of a branching strategy.

    Decide which variable(s) to branch on at each node using information
    from the node's relaxed solution (e.g., fractional values, scores, etc.).
    The simplest strategy is to pick an unfixed variable and split on 0/1.
    """
   
    def make_branching_decisions(self, node: BnBNode):
        # get LP solution and the real Instance
        relaxed = node.relaxed_solution.selection
        inst    = node.relaxed_solution.instance

        # all still-undecided item indices
        undecided = [i for i, d in enumerate(node.branching_decisions) if d is None]
        if not undecided:
            return ()

        # pick the most fractional var (min(r,1−r)), tie-break by density
        most_frac = max(
            undecided,
            key=lambda i: (
                min(relaxed[i], 1 - relaxed[i]),
                inst.items[i].value / inst.items[i].weight
            )
        )

        left, right = node.branching_decisions.split_on(most_frac)

        # enqueue “include” first if LP says ≥0.5, else “exclude” first
        if relaxed[most_frac] >= 0.5:
            return (right, left)
        else:
            return (left, right)


    """
    def make_branching_decisions(self, node: BnBNode) -> Tuple[BranchingDecisions, ...]:
        relaxed = node.relaxed_solution.selection
        undecided = [i for i, d in enumerate(node.branching_decisions) if d is None]
        if not undecided:
            return ()

        # Focus on fractional variables
        fractional = [(i, abs(relaxed[i] - 0.5)) for i in undecided if 0.01 < relaxed[i] < 0.99]
        if fractional:
            # Pick variable closest to 0.5 and high value-to-weight
            most_frac = min(fractional, key=lambda x: x[1])[0]
        else:
            # fallback: highest value/weight among undecided
            #most_frac = max(undecided, key=lambda i: node.instance.items[i].value / node.instance.items[i].weight)
            # In MyBranchingStrategy
            most_frac = max(undecided,key=lambda i: (min(relaxed[i], 1 - relaxed[i]), instance.items[i].value / instance.items[i].weight))

        return node.branching_decisions.split_on(most_frac)
    """
    """
    def make_branching_decisions(self, node: BnBNode) -> Tuple[BranchingDecisions, ...]:
        relaxed = node.relaxed_solution
        values = relaxed.selection

        # Choose the variable closest to 0.5 (most fractional)
        undecided = [
            i for i, d in enumerate(node.branching_decisions) if d is None
        ]
        if not undecided:
            return ()

        most_frac = min(undecided, key=lambda i: abs(values[i] - 0.5))
        return node.branching_decisions.split_on(most_frac)
    
        # placeholder: branch on the first unfixed variable
        first_unfixed = min(
            (i for i, val in enumerate(node.branching_decisions) if val is None),
            default=-1,
        )
        if first_unfixed < 0:
            return ()
        return node.branching_decisions.split_on(first_unfixed)"""


