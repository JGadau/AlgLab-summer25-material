"""
Relaxation Module

In branch-and-bound, a relaxation of the original 0/1 knapsack yields an upper bound
on the best feasible solution within a branch. If this bound does not exceed your
current best feasible solution, you can prune that branch and skip exploring it.

This file provides three example strategies:
  1. VeryNaiveRelaxationSolver:
     - Ignores capacity entirely, sets every unfixed item to 1.
     - Fastest, loosest bound.
  2. NaiveRelaxationSolver:
     - Checks that already-fixed items of 1 fit capacity.
     - Sets all unfixed items to 1, ignoring capacity beyond fixed part.
     - Slightly tighter bound than VeryNaive.
  3. MyRelaxationSolver:
     - Stub for your own algorithm (e.g., fractional knapsack, propagation).

You should subclass `RelaxationSolver` and implement `solve(instance, decisions)`
so that:
  a) fixed decisions remain unchanged;
  b) objective >= best 0/1 solution consistent with those decisions.
"""

import abc
import math

from .instance import Instance
from .branching_decisions import BranchingDecisions
from .relaxed_solution import RelaxedSolution


class RelaxationSolver(abc.ABC):
    """
    Abstract base for relaxation strategies.

    Implement `solve` to compute an upper bound on the best 0/1 solution
    consistent with given decisions.
    """

    @abc.abstractmethod
    def solve(
        self, instance: Instance, decisions: BranchingDecisions
    ) -> RelaxedSolution:
        """
        Return a `RelaxedSolution` satisfying:
          - fixed items in `decisions` remain at 0 or 1;
          - upper_bound >= best feasible 0/1 solution under those decisions.
        """
        ...


class VeryNaiveRelaxationSolver(RelaxationSolver):
    """
    A relaxation solver for the knapsack problem that naively sets every unfixed
    item to 1 without considering the capacity constraint. This approach provides
    a very loose upper bound for the problem.

    Explanation:
    The solver assumes that all unfixed items can be fully included in the knapsack
    (i.e., their selection is set to 1.0) regardless of the capacity constraint.
    This results in an overestimation of the objective value, making it an upper
    bound. The rationale is that the true optimal solution cannot exceed this
    value since it must respect the capacity constraint, which this naive approach
    ignores.
    """

    def solve(
        self, instance: Instance, decisions: BranchingDecisions
    ) -> RelaxedSolution:
        # build selection: 1.0 for fixed 1 or unfixed, 0 for fixed 0
        selection = [0.0 if x == 0 else 1.0 for x in decisions]
        # compute objective value
        upper = sum(item.value * sel for item, sel in zip(instance.items, selection))
        return RelaxedSolution(instance, selection, upper)


class NaiveRelaxationSolver(RelaxationSolver):
    """
    Ensure fixed 1's fit capacity; set every unfixed item to 1.
    """

    def solve(
        self, instance: Instance, decisions: BranchingDecisions
    ) -> RelaxedSolution:
        # compute capacity after fixed 1 items
        used = sum(item.weight for item, x in zip(instance.items, decisions) if x == 1)
        if used > instance.capacity:
            return RelaxedSolution.create_infeasible(instance)

        selection = [0.0 if x == 0 else 1.0 for x in decisions]
        upper = sum(item.value * sel for item, sel in zip(instance.items, selection))
        return RelaxedSolution(instance, selection, upper)


#################################
class MyRelaxationSolver(RelaxationSolver):
    def solve(self, instance: Instance, decisions: BranchingDecisions) -> RelaxedSolution:
        # items und capacity bekommen
        items = instance.items
        capacity = instance.capacity

        # Liste initialisieren (0.0 ist noch nicht ausgewählt)
        selection = [0.0] * len(items)

        # Anfang ist er leer
        remaining_capacity = capacity

        ### Feste Entscheidungen anwenden
        for i, decision in enumerate(decisions):

             # wenn genommen
            if decision == 1:
                remaining_capacity -= items[i].weight # Gewicht abzeiehen
                selection[i] = 1.0
                if remaining_capacity < 0: # wenn Gewicht überschritten -> ungültig
                    return RelaxedSolution.create_infeasible(instance)

             # wenn nicht genommen
            elif decision == 0: # 
                selection[i] = 0.0

        # remaining_items (no decision) sortieren
        remaining_items = [(i, items[i]) for i in range(len(items)) if decisions[i] is None]
        remaining_items.sort(key=lambda x: -x[1].value / x[1].weight) #sortieren nach Wertvollsten pro Gewicht zuerst

        # kleinstes Speichern um zu gucken ob noch kleineres reinpasst
        if remaining_items:
            smallest_weight = min(item.weight for _, item in remaining_items)
        else:
            smallest_weight = float('inf')

        # Ganzzahlige Items + ggf. Bruchteil hinzufügen
        for i, item in remaining_items:
            if remaining_capacity < smallest_weight:
                break
            elif item.weight <= remaining_capacity:
                selection[i] = 1.0 # einfügen
                remaining_capacity -= item.weight
            else:
                # Teil passt noch rein
                fraction = remaining_capacity / item.weight
                # Wert abrunden
                added_value = math.floor(fraction * item.value)
                # Bruchteil in die Auswahl
                fraction = added_value / item.value
                selection[i] = fraction
                break

        # berechne den Wert dieser Auswahl (ganzzahlige + evtl. ein fractional Item), und gebe als RelaxedSolution zurück.
        #  Korrekte Berechnung des upper_bounds aus gesamter Auswahl
        upper_bound = sum(item.value * sel for item, sel in zip(items, selection))
        return RelaxedSolution(instance, selection, upper_bound)

###################################


