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
#########################
class MyHeuristic(Heuristics):
    def search(self, instance: Instance, node: BnBNode) -> Iterable[RelaxedSolution]:
        sol = node.relaxed_solution
        results: list[RelaxedSolution] = []
        items = instance.items
        capacity = instance.capacity

        # help function (berechnet den Wert der Auswahl (selection) durch Summe aller value * selection.
        def compute_obj(selection: list[float]) -> float:
            return sum(item.value * sel for item, sel in zip(items, selection))

        def is_valid(selection: list[float]) -> bool: # aktuelle auswahl soll kapazität nicht überschreiten
            return sum(item.weight * sel for item, sel in zip(items, selection)) <= capacity

        # prüfe ob RelaxedSolution bereits gültig
        if sol.is_integral() and sol.does_obey_capacity_constraint():
            results.append(sol)
            return tuple(results)
        """
        # Threshold rounding + greedy fill 
        thr_sel = [1.0 if x >= 0.5 else 0.0 for x in sol.selection] # rundet alle Werte der Relaxed-Lösung auf: >= 0.5 wird zu 1.0, sonst 0.0 

        used_weight = sum(item.weight for item, sel in zip(items, thr_sel) if sel > 0) # gesamt Gewicht der gerundeten Lösung

        if used_weight <= capacity:
            rem = capacity - used_weight
            unfixed_indices = [i for i, sel in enumerate(thr_sel) if sel < 1]
            unfixed_indices.sort(key=lambda i: items[i].value / items[i].weight, reverse=True) #  alle nicht genommenen Items werden nach (value/weight) sortiert 

            for i in unfixed_indices: # solange wie möglich weitere Items vollständig aufnehmen
                if items[i].weight <= rem:
                    thr_sel[i] = 1.0
                    rem -= items[i].weight

            if is_valid(thr_sel): # wenn gefüllte Lösung gültig, dann speichern
                obj = compute_obj(thr_sel)
                results.append(RelaxedSolution(instance, thr_sel, obj))
        """
        # Greedy knapsack (ohne Relaxation) 
        greedy_sel = [0.0] * len(items) # starte leer
        rem_cap = capacity
        idx_sorted = sorted(range(len(items)), key=lambda i: items[i].value / items[i].weight, reverse=True) # neu sortieren

        # Nimm greedy die Items mit dem besten Verhältnis, bis der Rucksack voll ist
        for i in idx_sorted:
            if items[i].weight <= rem_cap:
                greedy_sel[i] = 1.0
                rem_cap -= items[i].weight

        # auch Lösung hinzufügen, wenn gültig
        if is_valid(greedy_sel):
            obj = compute_obj(greedy_sel)
            results.append(RelaxedSolution(instance, greedy_sel, obj))

        return tuple(results)

###################################



