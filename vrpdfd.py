import argparse
import json
import random
import time
from datetime import timedelta
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from ga.vrpdfd import ProblemConfig, VRPDFDIndividual, VRPDFDSolution


class Namespace(argparse.Namespace):
    if TYPE_CHECKING:
        problem: str
        iterations: int
        size: int
        mutation_rate: float
        verbose: bool
        dump: Optional[str]


parser = argparse.ArgumentParser(description="Genetic algorithm for VRPDFD problem")
parser.add_argument("problem", type=str, help="the problem name (e.g. \"6.5.1\", \"200.10.1\", ...)")
parser.add_argument("-i", "--iterations", default=200, type=int, help="the number of generations (default: 200)")
parser.add_argument("-s", "--size", default=100, type=int, help="the population size (default: 100)")
parser.add_argument("-m", "--mutation-rate", default=0.6, type=float, help="the mutation rate (default: 0.6)")
parser.add_argument("-v", "--verbose", action="store_true", help="turn on verbose mode")
parser.add_argument("--dump", type=str, help="dump the solution to a file")


namespace = Namespace()
parser.parse_args(namespace=namespace)
print(namespace)


config = ProblemConfig(namespace.problem)
config.mutation_rate = namespace.mutation_rate
random.seed(time.time())


start = time.perf_counter()
solution = VRPDFDIndividual.genetic_algorithm(
    generations_count=namespace.iterations,
    population_size=namespace.size,
    population_expansion_limit=2 * namespace.size,
    solution_cls=VRPDFDSolution,
    verbose=namespace.verbose,
).decode()
total_time = time.perf_counter() - start


if solution is None:
    message = "No feasible solution found"
    raise ValueError(message)


print(f"Got solution with profit = {-solution.cost}:\n{solution}")
solution.assert_feasible()


if namespace.dump is not None:
    dump_path = Path(namespace.dump)
    dump_path.parent.mkdir(parents=True, exist_ok=True)
    with open(namespace.dump, "w", encoding="utf-8") as file:
        data = {
            "problem": namespace.problem,
            "generations": namespace.iterations,
            "population_size": namespace.size,
            "mutation_rate": namespace.mutation_rate,
            "solution": {
                "profit": -solution.cost,
                "truck_paths": solution.truck_paths,
                "drone_paths": solution.drone_paths,
            },
            "time": str(timedelta(seconds=total_time)),
            "last_improved": VRPDFDIndividual.genetic_algorithm_last_improved,
        }
        json.dump(data, file)

    print(f"Saved solution to {namespace.dump}")
