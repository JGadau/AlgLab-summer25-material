import math
from data_schema import Donation, Solution
from database import TransplantDatabase
from ortools.sat.python.cp_model import CpModel, CpSolver, OPTIMAL, FEASIBLE
"""

- creates x[d,r] for every possible donor->recipient match, 
- add rules so each donor and recipient is used at most once and cycles balance give/receive.
- picks as many matches as possible
- return each chosen donor->recipient pair."""

class CrossoverTransplantSolver:
    def __init__(self, database: TransplantDatabase) -> None:
        """
        Constructs a new solver instance, using the instance data from the given database instance.
        :param database: The organ donor/recipients database.
        """
        self.database = database
        self.solver = CpSolver()
        self.solver.parameters.log_search_progress = True

    def optimize(self, timelimit: float = math.inf) -> Solution:
        """
        Solves the constraint programming model and returns the optimal solution (if found within time limit).
        :param timelimit: The maximum time limit for the solver.
        :return: A list of Donation objects representing the best solution, or an empty solution if no solution is found.
        """
        if timelimit <= 0.0:
            return Solution(donations=[])
        if timelimit < math.inf:
            self.solver.parameters.max_time_in_seconds = timelimit

        # Create Model
        model = CpModel()

        ## CREATE VARIABLES
        # only create variables where a donation is actually possible
        x = {}
        for donor in self.database.get_all_donors():
            d_id = donor.id
            partner = self.database.get_partner_recipient(donor)
            for recip in self.database.get_compatible_recipients(donor):
                r_id = recip.id
                # skip trivial self-match 
                if r_id == partner.id:
                    continue
                x[(d_id, r_id)] = model.NewBoolVar(f"x_{d_id}_{r_id}")

        ## CCONSTRAINS

        # recipient receives at most once
        for recip in self.database.get_all_recipients():
            incoming = [x[(d_id, recip.id)]
                        for (d_id, r_id) in x
                        if r_id == recip.id]
            if incoming:
                model.Add(sum(incoming) <= 1)

        # donor donates at most once
        for donor in self.database.get_all_donors():
            outgoing = [x[(donor.id, r_id)]
                        for (d_id, r_id) in x
                        if d_id == donor.id]
            if outgoing:
                model.Add(sum(outgoing) <= 1)

        # reciprocity: if a donor donates, their partner must also receive
        for donor in self.database.get_all_donors():
            d_id = donor.id
            partner = self.database.get_partner_recipient(donor).id

            outgoing = [x[(d_id, r_id)]
                        for (d_id_, r_id) in x
                        if d_id_ == d_id]
            incoming = [x[(d_id_, partner)]
                        for (d_id_, r_id) in x
                        if r_id == partner]
            if outgoing and incoming:
                model.Add(sum(outgoing) <= sum(incoming))

        # partner linkage: if a patient receives, exactly one of their own donors must donate
        for recip in self.database.get_all_recipients():
            incoming = [x[(d_id, recip.id)]
                        for (d_id, r_id) in x
                        if r_id == recip.id]

            partner_donors = self.database.get_partner_donors(recip)
            outgoing_from_partners = [x[(donor.id, r_id)]
                                      for donor in partner_donors
                                      for (d_id, r_id) in x
                                      if d_id == donor.id]

            if incoming and outgoing_from_partners:
                model.Add(sum(incoming) == sum(outgoing_from_partners))

        ## OBJECTIVE FUNCTION##
        # maximize number of successful transplants
        model.Maximize(sum(x.values()))

        ## SOLVE
        status = self.solver.Solve(model)
        if status not in (OPTIMAL, FEASIBLE):
            return Solution(donations=[])

        # Build solution of which donor pairs the solver actually picked and packages into solution object
        donors_map = {d.id: d for d in self.database.get_all_donors()} # look-up tables
        recipients_map = {r.id: r for r in self.database.get_all_recipients()}

        donations = [] # collect chosen donations
        ''' loop over every Boolean decision variable x[(d_id, r_id)]. If the solver set it to 1,
         that pair made the cut. You look up the real Donor and Recipient objects and create a 
         Donation(donor, recipient) for each.'''
        for (d_id, r_id), var in x.items():
            if self.solver.Value(var) == 1:
                donor = donors_map[d_id] 
                recipient = recipients_map[r_id]
                donations.append(Donation(donor=donor, recipient=recipient))

        return Solution(donations=donations)
