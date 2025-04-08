from data_schema import Instance, Solution


def solve(instance: Instance) -> Solution:

    # replaced numbers = instance.numbers with a sorted version
    sorted_numbers = sorted(instance.numbers)

    return Solution(
        number_a=sorted_numbers[0],
        number_b=sorted_numbers[-1],
        distance=abs(sorted_numbers[0] - sorted_numbers[-1]),
    )

