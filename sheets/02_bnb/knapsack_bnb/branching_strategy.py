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
import math

from .bnb_nodes import BnBNode, BranchingDecisions
from .relaxation import MyRelaxationSolver

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

############################
class MyBranchingStrategy(BranchingStrategy):  

    def make_branching_decisions(self, node: BnBNode) -> Tuple[BranchingDecisions, ...]:
        # alles schon verzweigt, dann nix mehr
        if all(val is not None for val in node.branching_decisions):
            return ()

        items = node.relaxed_solution.instance.items # alle items mit Gewicht, Wert
        decisions = node.branching_decisions # bisherige auswahl

        # kandidaten: Nur noch nicht fixierte(weder 0/1) Items
        candidates = [i for i, val in enumerate(decisions) if val is None]

        # wähle das Item mit dem höchsten value/weight Verhältnis
        best_idx = max(candidates, key=lambda i: items[i].value / items[i].weight)

        return decisions.split_on(best_idx) # erzeuge zwei neue
##############################
