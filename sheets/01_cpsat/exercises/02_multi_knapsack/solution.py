import math
from typing import List

from data_schema import Instance, Item, Solution
from ortools.sat.python.cp_model import FEASIBLE, OPTIMAL, CpModel, CpSolver


class MultiKnapsackSolver:
    """
    This class can be used to solve the Multi-Knapsack problem
    (also the standard knapsack problem, if only one capacity is used).

    Attributes:
    - instance (Instance): The multi-knapsack instance
        - items (List[Item]): a list of Item objects representing the items to be packed.
        - capacities (List[int]): a list of integers representing the capacities of the knapsacks.
    - model (CpModel): a CpModel object representing the constraint programming model.
    - solver (CpSolver): a CpSolver object representing the constraint programming solver.
    """

    def __init__(self, instance: Instance, activate_toxic: bool = False):
        """
        Initialize the solver with the given Multi-Knapsack instance.

        Args:
        - instance (Instance): an Instance object representing the Multi-Knapsack instance.
        """
        self.items = instance.items
        self.activate_toxic = activate_toxic
        self.capacities = instance.capacities
        self.model = CpModel()
        self.solver = CpSolver()
        self.solver.parameters.log_search_progress = True
        # TODO: Implement me!



    def solve(self, timelimit: float = math.inf) -> Solution:
        """
        Solve the Multi-Knapsack instance with the given time limit.

        Args:
        - timelimit (float): time limit in seconds for the cp-sat solver.

        Returns:
        - Solution: a list of lists of Item objects representing the items packed in each knapsack
        """
        # handle given time limit
        if timelimit <= 0.0:
            return Solution(trucks=[])  # empty solution
        if timelimit < math.inf:
            self.solver.parameters.max_time_in_seconds = timelimit


        ##DECISION VARIABLES##

        #eaxh item in the truck needs a variable -> so created variables
        x={} # item_idx, truck_idx keys

        for i, item in enumerate(self.items):
            for j, capacity in enumerate(self.capacities):
                x[(i, j)] = self.model.NewBoolVar(f"x_{i}_{j}") # store created variable into x... dictionary diectly

        #create one variable per truck
        y={} 
        y = {}
        for j in range(len(self.capacities)):
            y[j] = self.model.NewBoolVar(f"y_{j}")

        

        ##CONSTRAINTS##

        #for each truck the total weight of selected items <= truck capacity (CONSTRAINT)
        for j, capacity in enumerate(self.capacities):
            self.model.Add(
                sum(self.items[i].weight * x[(i,j)] for i in range(len(self.items)))
                <=capacity
            )

        #each item can be ssigned to at most one truck (CONSTRAINT)
        for i in range(len(self.items)):
            self.model.Add(
                sum(x[(i,j)] for j in range(len(self.capacities)))<= 1
            )

        # toxic constraint for each truck and each item
        if self.activate_toxic:
            for i, item in enumerate(self.items):
                for j in range(len(self.capacities)):
                    if (i, j) not in x:
                        continue
                    if item.toxic:
                        self.model.Add(x[(i, j)] <= y[j])
                    else:
                        self.model.Add(x[(i, j)] <= 1 - y[j])



        ##OBJECTIVE FUNCTION##

        # objective is to maximize total values

        self.model.Maximize(
            sum(self.items[i].value * x[(i,j)] for i in range(len(self.items)) for j in range(len(self.capacities)))
        )

        ##SOLVER##

        status =self.solver.Solve(self.model)

        ##SOLUTION##
        # TODO: Implement me!

        # create list of trucks
        if status in (OPTIMAL, FEASIBLE):
            trucks = [[] for _ in range(len(self.capacities))]
            for i, item in enumerate(self.items):
                for j in range(len(self.capacities)):
                    if self.solver.Value(x[(i, j)]) == 1:
                        trucks[j].append(item)
                        break
            return Solution(trucks=trucks)
        else:
            return Solution(trucks=[])# empty solution

