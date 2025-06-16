import itertools
import logging

import networkx as nx
from pysat.solvers import Solver as SATSolver

# Configure logging to show INFO messages
logging.basicConfig(level=logging.INFO)


class HamiltonianCycleModel:
    def __init__(self, graph: nx.Graph) -> None:
        # Log model initialization details
        logging.info(
            "Initializing HamiltonianCycleModel with %d nodes and %d edges...",
            graph.number_of_nodes(),
            graph.number_of_edges(),
        )
        self.graph = graph
        self.solver = SATSolver("Minicard")
        self.assumptions = []
        # TODO: Implement me!
        # Neue Variablen für Kanten
        self.edge_vars = {} #  Kante (u,v) -> SAT-Variable
        self.var_to_edge = {} # SAT-Variable -> Kante (u,v)
        self.counter = 1 # Startzähler für SAT-Variablen

        ## Jeder Kante im Graph eine eindeutige Variable zuweisen
        for u, v in self.graph.edges():
            key = tuple(sorted((u, v))) # # Reihenfolge normalisieren
            if key not in self.edge_vars:
                self.edge_vars[key] = self.counter
                self.var_to_edge[self.counter] = key
                self.counter += 1

        # Für jeden Knoten: exakt 2 Kanten dürfen aktiv sein
        for node in self.graph.nodes():
            incident_vars = [
                self.edge_vars[tuple(sorted((node, neighbor)))]
                for neighbor in self.graph.neighbors(node)
                if tuple(sorted((node, neighbor))) in self.edge_vars
            ]
            # # At most 2 Kanten -> Knotengrad <= 2
            self.solver.add_atmost(incident_vars, 2)
            #self.solver.add_atleast(incident_vars, 2)
            # At least 2 Kanten -> Knotengrad >= 2 
            self.solver.add_atmost([-lit for lit in incident_vars], len(incident_vars) - 2) #PySat Minicard does not support add_atmost

        # Log model initialization completion
        logging.info("HamiltonianCycleModel initialized successfully!")

 


    def solve(self):
        while True:
            # Prüfe Zeitlimit, wenn Timer vorhanden ist
            if hasattr(self, "timer") and self.timer.is_out_of_time():
                return None
            # SAT lösen mit aktuellen Einschränkungen
            if not self.solver.solve(assumptions=self.assumptions):
                return None # Keine Lösung möglich

            # Extrahiere Modell (SAT-Zuweisung)
            model = self.solver.get_model()
            # Sammle alle "True"-Variablen, die zu echten Kanten gehören
            selected_edges = [self.var_to_edge[abs(v)] for v in model if v > 0 and abs(v) in self.var_to_edge]
            # Erzeuge Graph aus den selektierten Kanten
            G_sol = nx.Graph()
            G_sol.add_edges_from(selected_edges)
            # Prüfe, ob Ergebnis zusammenhängend ist
            components = list(nx.connected_components(G_sol))
            
            #  Wenn nicht verbunden -> Verhindere diese Trennung in Zukunft

            if len(components) == 1:
                return selected_edges
            for comp in components:
                if len(comp) == self.graph.number_of_nodes():
                    continue # Ignoriere vollständige Lösung
                # Finde alle "Grenzkanten" (zwischen dieser Komponente und dem Rest)
                boundary_vars = []
                for u in comp:
                    for v in self.graph.neighbors(u):
                        if v not in comp:
                            var = self.edge_vars.get(tuple(sorted((u, v))))
                            if var:
                                boundary_vars.append(var)
                # Füge Klausel hinzu: Mindestens eine Grenzkante muss aktiv sein
                if boundary_vars:
                    self.solver.add_clause(boundary_vars)

    #def solve(self) -> list[tuple[int, int]] | None:
        """
        Solves the Hamiltonian Cycle Problem. If a HC is found,
        its edges are returned as a list.
        If the graph has no HC, 'None' is returned.
        """
        # Log the start of solving process
     #   logging.info("Starting Hamiltonian cycle search with %d assumptions", len(self.assumptions))
        # TODO: Implement me!
