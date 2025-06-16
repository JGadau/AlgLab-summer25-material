import bisect
import logging
import math
from typing import Iterable

import networkx as nx
from pysat.solvers import Solver as SATSolver

logging.basicConfig(level=logging.INFO)

# Define the node ID type. It is an integer but this helps to make the code more readable.
NodeId = int


class Distances:
    """
    This class provides a convenient interface to query distances between nodes in a graph.
    All distances are precomputed and stored in a dictionary, making lookups efficient.
    """

    def __init__(self, graph: nx.Graph) -> None:
        self.graph = graph
        # Compute all-pairs shortest paths
        self._distances = dict(nx.all_pairs_dijkstra_path_length(self.graph))
        # Log the computation details
        logging.info("Computed all-pairs shortest paths for %d nodes", len(self._distances))

    def all_vertices(self) -> Iterable[NodeId]:
        """Returns an iterable of all node IDs in the graph."""
        return self._distances.keys()

    def dist(self, u: NodeId, v: NodeId) -> float:
        """Returns the distance between nodes `u` and `v`."""
        return self._distances[u].get(v, math.inf)

    def max_dist(self, centers: Iterable[NodeId]) -> float:
        """Returns the maximum distance from any node to the closest center."""
        return max(min(self.dist(c, u) for c in centers) for u in self.all_vertices())

    def vertices_in_range(self, u: NodeId, limit: float) -> Iterable[NodeId]:
        """Returns an iterable of nodes within `limit` distance from node `u`."""
        return (v for v, d in self._distances[u].items() if d <= limit)

    def sorted_distances(self) -> list[float]:
        """Returns a sorted list of all pairwise distances in the graph."""
        dists = sorted(
            dist
            for dist_dict in self._distances.values()
            for dist in dist_dict.values()
        )
        logging.info("Collected and sorted %d pairwise distances with a range from %f to %f", len(dists), dists[0], dists[-1])
        return dists


class KCenterDecisionVariant:
    def __init__(self, distances: Distances, k: int) -> None:
        self.distances = distances
        self.k = k # anzahl der platzierenden Zentren
        logging.info("Initializing KCenterDecisionVariant for k=%d", k)
        # TODO: Implement me!
        # Solution model
        # jeder knoten ID bekommt eindeutigen Variable für SAT solver
        self._var_idx = {v: i + 1 for i, v in enumerate(distances.all_vertices())} # 
        self._reverse_var_idx = {i: v for v, i in self._var_idx.items()} # #  umgekehrte Zuordnung von SAT-Variable zurück zu Knotennummer
        self._solver = SATSolver()
        self._solution = None # Lösung speichern


        #self._solution: list[NodeId] | None = None
### Baue SAT-Formulierung
    def limit_distance(self, limit: float) -> None:
        """Adds constraints to the SAT solver to ensure coverage within the given distance."""
        logging.info("Limiting to distance: %f", limit)
        # TODO: Implement me!
        from pysat.card import CardEnc, EncType

        # falls vorher schon ein Solver existierte: Lösche ihn
        self._solver.delete()  # reset SAT solver on each limit update
        self._solver = SATSolver()

        vars = list(self._var_idx.values()) # liste aller möglichen Zentrum Variablen

        # höchstens k dieser Variablen/zentren dürfen True sein
        card = CardEnc.atmost(lits=vars, bound=self.k, encoding=EncType.seqcounter)
        for clause in card.clauses:
            self._solver.add_clause(clause)

        # Für jeden Knoten im Graph
        for u in self.distances.all_vertices():
            # welche Zentren sind innerhalb der erlaubten Entfernung erreichbar
            reachable_vars = [
                self._var_idx[v]
                for v in self.distances.vertices_in_range(u, limit)
            ]
            # mindestens eines dieser erreichbaren Zentren muss existieren
            if reachable_vars:
                self._solver.add_clause(reachable_vars)
            else: # falls kein Zentrum erreichbar ist, ist das Problem unlösbar für diese Grenze

                raise ValueError(f"No reachable centers within limit for node {u}")

                #self._solver.add_clause([-1])  # Force unsat


### SAT Formulierung lösen
### Solver prüft, ob die Einschränkungen erfüllbar sind
##### Falls true: Extrahiere alle positiven Variablen aus dem Modell und wandle sie zurück in Knotennummern.
    def solve(self) -> list[NodeId] | None:
        """Solves the SAT problem and returns the list of selected nodes, if feasible."""
        logging.info("Attempting to solve the SAT formulation")
        # TODO: Implement me!
        logging.info("SAT solver solution: %s", self._solution)
        #return self._solution
        if self._solver.solve():
            model = self._solver.get_model() # Liste true und solvable Variablen
            self._solution = [
                self._reverse_var_idx[abs(v)]
                for v in model
                if v > 0 and abs(v) in self._reverse_var_idx
            ]
            return self._solution
        else:
            self._solution = None
            return None


    def get_solution(self) -> list[NodeId]:
        """Returns the solution if available; raises an error otherwise."""
        if self._solution is None:
            msg = "No solution available. Ensure `solve` is called first."
            raise ValueError(msg)
        return self._solution

### Optimale Lösung mit binärer Suche
class KCentersSolver:
    def __init__(self, graph: nx.Graph) -> None:
        """
        Creates a solver for the k-centers problem on the given networkx graph.
        The graph may not be complete, and edge weights are used to represent distances.
        """
        self.graph = graph
        # Initialize distances helper
        self.distances = Distances(self.graph) 
        logging.info("KCentersSolver initialized with graph of %d nodes and %d edges", 
                     self.graph.number_of_nodes(), self.graph.number_of_edges())


### Greedy ansatz, immer den schlimmsten Knoten abdecken
    def solve_heur(self, k: int) -> list[NodeId]:
        """
        Calculate a heuristic solution to the k-centers problem.
        Returns the k selected centers as a list of node IDs.
        """
        logging.info("Starting heuristic computation for k=%d", k)
        # TODO: Implement me!
        #centers = None
        #logging.info("Heuristic centers selected: %s", centers)
        #return centers
        # 
        all_nodes = list(self.distances.all_vertices())
        centers = [all_nodes[0]] # beginne mit beliebigen Knoten

        for _ in range(1, k): # Füge k-1 weitere Zentren hinzu
             # wähle Knoten der am weitesten entfernt ist von zentrum
            max_dist_node = max(
                all_nodes,
                key=lambda u: min(self.distances.dist(u, c) for c in centers)
            )
            centers.append(max_dist_node)

        logging.info("Heuristic centers selected: %s", centers)
        return centers

    def solve(self, k: int) -> list[NodeId]:
        """
        Calculate the optimal solution to the k-centers problem for the given k.
        Returns the selected centers as a list of node IDs.
        """
        self.k = k
        dists = self.distances.sorted_distances()
        lb = 0
        ub = len(dists) - 1

        # Start with a heuristic solution
        centers = self.solve_heur(k)
        best = centers
        best_val = self.distances.max_dist(best)

        # binäre Suche über Distanzgrenzen
        while lb <= ub:
            mid = (lb + ub) // 2
            c = dists[mid] # Aktuelle Kandidaten-Distanz
            decision = KCenterDecisionVariant(self.distances, k)
            decision.limit_distance(c)

            if decision.solve() is not None: #Versuche kleinere Distanz
                best = decision.get_solution() 
                best_val = c
                ub = mid - 1
            else:
                lb = mid + 1 # Versuche größere Distanz

        return best


