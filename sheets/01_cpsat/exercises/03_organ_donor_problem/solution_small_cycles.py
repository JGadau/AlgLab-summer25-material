import math
import networkx as nx
from data_schema import Donation, Solution
from database import TransplantDatabase
from ortools.sat.python import cp_model


"""
- finds all 2 and 3 person swap cycles in a compatibility graph,
- makes one variable per cycle, a
- ensure no patient is in more than one cycle.
- Choose the best set of small cycles to maximize transplants 
- unpacks them into donor->recipient donations.
"""

class CycleLimitingCrossoverTransplantSolver:
    def __init__(self, database: TransplantDatabase) -> None:
        self.database = database
        self.solver = cp_model.CpSolver()
        self.solver.parameters.log_search_progress = True

    def optimize(self, timelimit: float = math.inf) -> Solution:
        if timelimit <= 0.0:
            return Solution(donations=[])
        if timelimit < math.inf:
            self.solver.parameters.max_time_in_seconds = timelimit

        model = cp_model.CpModel()

        ## BUILD THE GRAPH
        G = nx.DiGraph()
        for donor in self.database.get_all_donors():
            donor_id = donor.id
            partner = self.database.get_partner_recipient(donor)
            for recipient in self.database.get_compatible_recipients(donor):
                if partner.id != recipient.id:
                    G.add_edge(partner.id, recipient.id, donor=donor)

        ## FIND CYCLES OF 2 OR 3"
        cycles = []

        # 2-cycles
        for u, v in G.edges:
            if G.has_edge(v, u):
                cycles.append([u, v])

        # 3-cycles
        for u in G.nodes:
            for v in G.successors(u):
                for w in G.successors(v):
                    if G.has_edge(w, u):
                        cycles.append([u, v, w])


        ## CREATE VARIABLE FOR EACH CYCLE
        cycle_vars = {}
        for idx, cycle in enumerate(cycles):
            cycle_vars[idx] = model.NewBoolVar(f"cycle_{idx}")
        
        ## CONSTRAINTS
        # Each patient (represented recipient) can participate in at most one selected cycle
        all_patient_ids = [r.id for r in self.database.get_all_recipients()]

        for patient_id in all_patient_ids:
            involved_cycles = []
            for idx, cycle in enumerate(cycles):
                if patient_id in cycle:
                    involved_cycles.append(cycle_vars[idx])
            if involved_cycles:
                model.Add(sum(involved_cycles) <= 1)

        ## OBJECTIVE maximize number of transplants
        model.Maximize(sum(len(cycles[idx]) * cycle_vars[idx] for idx in cycle_vars))

        ## SOLVE
        status = self.solver.Solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return Solution(donations=[])

        ## Build solution
        donations = []
        recipients = {r.id: r for r in self.database.get_all_recipients()}
        donors = {d.id: d for d in self.database.get_all_donors()}

        for idx, var in cycle_vars.items():
            if self.solver.Value(var) == 1:
                cycle = cycles[idx]
                for i in range(len(cycle)):
                    r_from = cycle[i] #  go around the cycle’s node-list in order, pairing each node r_from with its successor r_to (the modulo wrap-around makes the last node give back to the first).
                    r_to = cycle[(i + 1) % len(cycle)] # retrieve the original donor object stored as edge data on G[r_from][r_to].
                    donor = G.edges[r_from, r_to]["donor"]
                    donations.append(Donation(donor=donor, recipient=recipients[r_to])) # create a Donation(donor, recipient) for that arc and add it to donations.

        return Solution(donations=donations)
