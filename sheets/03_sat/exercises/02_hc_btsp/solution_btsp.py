import math
import logging
from enum import Enum

import itertools #added
import networkx as nx
from _timer import Timer
from solution_hamiltonian import HamiltonianCycleModel

# Configure logging to show INFO messages
logging.basicConfig(level=logging.INFO)

class SearchStrategy(Enum):
    """
    Different search strategies for the solver.
    """

    SEQUENTIAL_UP = 1  # Try smallest possible k first.
    SEQUENTIAL_DOWN = 2  # Try any improvement.
    BINARY_SEARCH = 3  # Try a binary search for the optimal k.

    def __str__(self):
        return self.name.title()

    @staticmethod
    def from_str(s: str):
        return SearchStrategy[s.upper()]


class BottleneckTSPSolver:
    def __init__(self, graph: nx.Graph) -> None:
        """
        Creates a solver for the Bottleneck Traveling Salesman Problem on the given networkx graph.
        You can assume that the input graph is complete, so all nodes are neighbors.
        The distance between two neighboring nodes is a numeric value (int / float), saved as
        an edge data parameter called "weight".
        There are multiple ways to access this data, and networkx also implements
        several algorithms that automatically make use of this value.
        Check the networkx documentation for more information!
        """
        # Log initialization details
        logging.info("Initializing BottleneckTSPSolver with %d nodes and %d edges...", 
                     graph.number_of_nodes(), graph.number_of_edges())
        self.graph = graph
        # TODO: Implement me!
        # Log initialization completion
        logging.info("BottleneckTSPSolver initialized successfully!")
###########################
    def _simple_hamiltonian(self, G: nx.Graph) -> list[tuple[int,int]] | None:
        """
    Schneller Heuristik-Test, um zu prüfen, ob ein Hamiltonkreis *möglich* ist.
    Gibt eine gefundene Tour (als Kantenliste) zurück oder None.
        """
        # 1- graph must be connected and min-degree >= 2
        if not nx.is_connected(G) or any(d < 2 for _, d in G.degree()):
            return None

        # 2- Finde ein Startdreieck (3 Knoten die miteinander verbunden sind)
        for u in G:
            nbrs = list(G.neighbors(u))
            for v, w in itertools.combinations(nbrs, 2):
                if G.has_edge(v, w):
                    cycle = [u, v, w] # startzyklus gefunden
                    break
            else:
                continue
            break
        else:
            return None # keinenn Dreieck gefunden

        # 3- greedy-insert the rest
        remaining = set(G) - set(cycle)
        for x in remaining:
            for i in range(len(cycle)):
                a, b = cycle[i], cycle[(i+1) % len(cycle)]
                if G.has_edge(a, x) and G.has_edge(x, b):
                    cycle.insert(i+1, x)
                    break
            else:
                return None

        # 4) build kantenliste
        return [(cycle[i], cycle[(i+1) % len(cycle)]) for i in range(len(cycle))]

    def lower_bound(self) -> list[float]:
    """
    Gibt eine sortierte Liste möglicher Gewichtsgrenzen zurück.
    Bei großen Graphen wird die Liste gesampelt, um Rechenzeit zu sparen.
    """
        weights = sorted(set(nx.get_edge_attributes(self.graph, "weight").values()))
    
        n = self.graph.number_of_nodes()

        # verwende alle Werten bei kleineren Graphen
        if n <= 400:
            return weights

        ## Bei großen Graphen: nur jede x-te Gewichtsschwelle
        step = max(1, len(weights) // 100)
        return weights[::step]
##################################
        # TODO: Implement me!

    def optimize_bottleneck(
        self,
        time_limit: float = math.inf,
        search_strategy: SearchStrategy = SearchStrategy.BINARY_SEARCH,
    ) -> list[tuple[int, int]] | None:
        """
        Find the optimal bottleneck tsp tour.
        Führt die Optimierung durch: Suche die kleinstmögliche Bottleneck-Grenze,
        bei der ein Hamiltonkreis möglich ist.
        """
        # Initialize timer
        self.timer = Timer(time_limit)
        logging.info("Timer initialized with limit %f seconds", time_limit)
###############################

        # Hole alle potenziellen Schwellenwerte
        weights = self.lower_bound()

        #full_weights = sorted(set(nx.get_edge_attributes(self.graph, "weight").values()))
        #step = max(1, len(full_weights) // 100)  # Sample 100 or fewer
        #weights = full_weights[::step]

        left, right = 0, len(weights) - 1
        best_solution = None

        # Binary Search über mögliche Schwellenwerte
        while left <= right and not self.timer.is_out_of_time():
            mid = (left + right) // 2
            threshold = weights[mid]
            # Erzeuge Teilgraph, der nur Kanten <= threshold enthält
            G_sub = nx.Graph()
            G_sub.add_nodes_from(self.graph.nodes())
            for u, v, d in self.graph.edges(data=True):
                if d["weight"] <= threshold:
                    G_sub.add_edge(u, v)
            # FAST NO-CYCLE CHECKS
            if not nx.is_connected(G_sub) or any(deg < 2 for _, deg in G_sub.degree()):
                left = mid + 1
                continue
            # FAST GREEDY CHECK
            heur = self._simple_hamiltonian(G_sub)
            if heur is not None:
                best_solution = heur
                right = mid - 1 # versuche kleinere Schwelle
                continue
            # aufwendiger ILP-Solver wenn nötig
            hc_solver = HamiltonianCycleModel(G_sub)
            hc_solver.timer = self.timer  # Optional: for early timeout support
            solution = hc_solver.solve()


            if solution:
                best_solution = solution
                right = mid - 1
            else:
                left = mid + 1

        return best_solution

################################