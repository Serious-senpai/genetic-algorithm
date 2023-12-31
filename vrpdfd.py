import argparse
import json
import math
import random
import time
import traceback
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from ga import utils
from ga.vrpdfd import InfeasibleSolution, ProblemConfig, VRPDFDIndividual, VRPDFDSolution


class Namespace(argparse.Namespace):
    if TYPE_CHECKING:
        problem: str
        iterations: int
        size: int
        mutation_rate: float
        initial_fine_coefficient: float
        fine_coefficient_increase_rate: float
        reset_after: int
        stuck_penalty_increase_rate: float
        local_search_batch: int
        verbose: bool
        fake_tsp_solver: bool
        dump: Optional[str]
        extra: Optional[str]
        log: Optional[str]


parser = argparse.ArgumentParser(description="Genetic algorithm for VRPDFD problem")
parser.add_argument("problem", type=str, help="the problem name (e.g. \"6.5.1\", \"200.10.1\", ...)")
parser.add_argument("-i", "--iterations", default=100, type=int, help="the number of generations (default: 100)")
parser.add_argument("-s", "--size", default=200, type=int, help="the population size (default: 200)")
parser.add_argument("-m", "--mutation-rate", default=0.6, type=float, help="the mutation rate (default: 0.6)")
parser.add_argument("-f", "--initial-fine-coefficient", default=1000.0, type=float, help="the initial fine coefficient (default: 1000.0)")
parser.add_argument("-r", "--fine-coefficient-increase-rate", default=10.0, type=float, help="the fine coefficient increase rate (default: 10.0")
parser.add_argument("-a", "--reset-after", default=15, type=int, help="the number of non-improving generations before applying stuck penalty and local search (default: 15)")
parser.add_argument("-p", "--stuck-penalty-increase-rate", default=10.0, type=float, help="the stuck penalty (default: 10.0)")
parser.add_argument("-b", "--local-search-batch", default=10, type=int, help="the batch size for local search (default: 10)")
parser.add_argument("-v", "--verbose", action="store_true", help="turn on verbose mode")
parser.add_argument("--fake-tsp-solver", action="store_true", help="use fake TSP solver")
parser.add_argument("--dump", type=str, help="dump the solution to a file")
parser.add_argument("--extra", type=str, help="extra data dump to file specified by --dump")
parser.add_argument("--log", type=str, help="log each generation to a file")


namespace = Namespace()
parser.parse_args(namespace=namespace)
print(namespace)


if namespace.fake_tsp_solver:
    utils.tsp_solver = utils.fake_tsp_solver
    print(f"Using fake TSP solver {utils.tsp_solver!r}")


config = ProblemConfig.get_config(namespace.problem)
ProblemConfig.context = namespace.problem
config.mutation_rate = namespace.mutation_rate
config.initial_fine_coefficient = namespace.initial_fine_coefficient
config.fine_coefficient_increase_rate = namespace.fine_coefficient_increase_rate
config.reset_after = namespace.reset_after
config.local_search_batch = namespace.local_search_batch
if namespace.log is not None:
    config.logger = open(namespace.log, "w", encoding="utf-8")


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


print(f"Got solution with profit = {-solution.cost} after {total_time:.4f}s:\n{solution}")
if math.isnan(solution.cost):
    print(f"Oops! Got a solution with NaN cost {solution.cost}. The underlying attributes are as follows:")
    print(f"truck_distance = {solution.truck_distance}")
    print(f"drone_distance = {solution.drone_distance}")
    print(f"fine_coefficient = {solution.fine_coefficient}")

    print("Evaluating solution again:")
    re_solution = VRPDFDSolution(
        truck_paths=solution.truck_paths,
        drone_paths=solution.drone_paths,
    )

    print(f"Got solution with profit = {-re_solution.cost}")


try:
    solution.assert_feasible()
except InfeasibleSolution:
    traceback.print_exc()
    feasible = False
else:
    feasible = True


if namespace.dump is not None:
    dump_path = Path(namespace.dump)
    dump_path.parent.mkdir(parents=True, exist_ok=True)
    with open(namespace.dump, "w", encoding="utf-8") as file:
        data = {
            "problem": namespace.problem,
            "generations": namespace.iterations,
            "population_size": namespace.size,
            "mutation_rate": namespace.mutation_rate,
            "initial_fine_coefficient": namespace.initial_fine_coefficient,
            "fine_coefficient_increase_rate": namespace.fine_coefficient_increase_rate,
            "reset_after": namespace.reset_after,
            "stuck_penalty_increase_rate": namespace.stuck_penalty_increase_rate,
            "solution": {
                "profit": -solution.cost,
                "feasible": feasible,
                "truck_paths": solution.truck_paths,
                "drone_paths": solution.drone_paths,
            },
            "time": total_time,
            "fake_tsp_solver": namespace.fake_tsp_solver,
            "last_improved": VRPDFDIndividual.genetic_algorithm_last_improved,
            "extra": namespace.extra,
        }
        json.dump(data, file)

    print(f"Saved solution to {namespace.dump}")
