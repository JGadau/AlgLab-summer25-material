from data_schema import Instance, Solution
from ortools.sat.python import cp_model


def solve(instance: Instance) -> Solution:
    numbers = instance.numbers

    model = cp_model.CpModel()

    length= len(numbers)

    # for single_number_test
    if length == 1:
        return Solution(
            number_a=numbers[0],
            number_b=numbers[0],
            distance=0,
        )

    # iterate
    i = model.NewIntVar(0, length - 1, 'i') # creates integer variable i that can take values from 0 to n-1
    j = model.NewIntVar(0, length - 1, 'j')
    model.Add(i != j) # constraint

    # make variables for the numbers
    number_a = model.NewIntVar(min(numbers), max(numbers), 'number_a') # creates integer variable number_b that reps one value from numbers list
    number_b = model.NewIntVar(min(numbers), max(numbers), 'number_b')
    model.AddElement(i, numbers, number_a) # links number_a to numbers[i] ex. when i=2, then number_a=numbers[2]
    model.AddElement(j, numbers, number_b)

    # distance between selected numbers
    distance = model.NewIntVar(0, max(numbers) - min(numbers), 'distance')
    model.AddAbsEquality(distance, number_a - number_b) # absolute value differences 

    # maximize distance and solve
    model.Maximize(distance)

    solver = cp_model.CpSolver()
    solver.Solve(model)

    return Solution(
        number_a=solver.Value(number_a),
        number_b=solver.Value(number_b),
        distance=solver.Value(distance),
    )
