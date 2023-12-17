import argparse
import random
import time
from typing import TYPE_CHECKING

from ga.vrpdfd import ProblemConfig, VRPDFDIndividual, VRPDFDSolution


class Namespace(argparse.Namespace):
    if TYPE_CHECKING:
        problem: str
        iterations: int
        size: int
        mutation_rate: float
        verbose: bool


parser = argparse.ArgumentParser(description="Genetic algorithm for VRPDFD problem")
parser.add_argument("problem", type=str, help="the problem name (e.g. \"6.5.1\", \"200.10.1\", ...)")
parser.add_argument("-i", "--iterations", default=500, type=int, help="the number of generations (default: 500)")
parser.add_argument("-s", "--size", default=100, type=int, help="the population size (default: 100)")
parser.add_argument("-m", "--mutation-rate", default=0.6, type=float, help="the mutation rate (default: 0.6)")
parser.add_argument("-v", "--verbose", action="store_true", help="turn on verbose mode")


namespace = Namespace()
parser.parse_args(namespace=namespace)
print(namespace)


config = ProblemConfig(namespace.problem)
config.mutation_rate = namespace.mutation_rate
random.seed(time.time())
solution = VRPDFDIndividual.genetic_algorithm(
    generations_count=namespace.iterations,
    population_size=namespace.size,
    population_expansion_limit=2 * namespace.size,
    solution_cls=VRPDFDSolution,
    verbose=namespace.verbose,
)
if solution is None:
    print("No feasible solution found")

else:
    print(f"Got solution with profit = {-solution.cost}:\n{solution}")
    if solution is not None and not solution.feasible():
        message = "Solution is infeasible"
        raise ValueError(message)
