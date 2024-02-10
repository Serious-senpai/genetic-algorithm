import argparse
import json
import pickle
import random
import time
import traceback
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from ga import utils
from ga.vrpdfd import HistoryRecord, InfeasibleSolution, ProblemConfig, VRPDFDIndividual, VRPDFDSolution


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
        cache_limit: int
        fake_tsp_solver: bool
        dump: List[str]
        extra: Optional[str]
        log: Optional[str]
        record_history: bool


parser = argparse.ArgumentParser(description="Genetic algorithm for VRPDFD problem", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("problem", type=str, help="the problem name (e.g. \"6.5.1\", \"200.10.1\", ...)")
parser.add_argument("-i", "--iterations", default=200, type=int, help="the number of generations")
parser.add_argument("-s", "--size", default=200, type=int, help="the population size")
parser.add_argument("-m", "--mutation-rate", default=0.8, type=float, help="the mutation rate")
parser.add_argument("-f", "--initial-fine-coefficient", default=1000.0, type=float, help="the initial fine coefficient")
parser.add_argument("-r", "--fine-coefficient-increase-rate", default=10.0, type=float, help="the fine coefficient increase rate")
parser.add_argument("-a", "--reset-after", default=15, type=int, help="the number of non-improving generations before applying stuck penalty and local search")
parser.add_argument("-p", "--stuck-penalty-increase-rate", default=10.0, type=float, help="the stuck penalty")
parser.add_argument("-b", "--local-search-batch", default=100, type=int, help="the batch size for local search")
parser.add_argument("-v", "--verbose", action="store_true", help="turn on verbose mode")
parser.add_argument("--cache-limit", default=50000, type=int, help="set limit for individuals and TSP cache")
parser.add_argument("--fake-tsp-solver", action="store_true", help="use fake TSP solver")
parser.add_argument("--dump", nargs="*", default=[], type=str, help="dump the solution to a file, supports *.json, *.pickle, *.history")
parser.add_argument("--extra", type=str, help="extra data dump to file specified by --dump")
parser.add_argument("--log", type=str, help="log each generation to a file")
parser.add_argument("--record-history", action="store_true", help="record history of each individual")


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
config.stuck_penalty_increase_rate = namespace.stuck_penalty_increase_rate
config.local_search_batch = namespace.local_search_batch
config.record_history = namespace.record_history
VRPDFDIndividual.cache.max_size = config.cache_limit = namespace.cache_limit
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


additional = " (including pyplot interactive duration)" if namespace.verbose else ""
print(f"Got solution with profit = {-solution.cost} after {total_time:.4f}s{additional}:\n{solution}")


try:
    solution.assert_feasible()
except InfeasibleSolution:
    traceback.print_exc()
    feasible = False
else:
    feasible = True


for path in namespace.dump:
    dump_path = Path(path)
    dump_path.parent.mkdir(parents=True, exist_ok=True)

    if path.endswith(".json"):
        with dump_path.open("w", encoding="utf-8") as json_file:
            data = {
                "problem": namespace.problem,
                "generations": namespace.iterations,
                "population_size": namespace.size,
                "mutation_rate": namespace.mutation_rate,
                "initial_fine_coefficient": namespace.initial_fine_coefficient,
                "fine_coefficient_increase_rate": namespace.fine_coefficient_increase_rate,
                "reset_after": namespace.reset_after,
                "stuck_penalty_increase_rate": namespace.stuck_penalty_increase_rate,
                "local_search_batch": namespace.local_search_batch,
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
                "cache_info": {
                    "limit": namespace.cache_limit,
                    "individual": VRPDFDIndividual.cache.to_json(),
                    "tsp": config.tsp_cache.to_json(),
                },
            }
            json.dump(data, json_file)

        print(f"Saved solution as JSON to {dump_path}")

    elif path.endswith(".pickle"):
        with dump_path.open("wb") as pickle_file:
            pickle.dump(solution.encode(), pickle_file)

        print(f"Pickled solution to {dump_path}")

    elif path.endswith(".history"):
        with dump_path.open("w", encoding="utf-8") as history_file:
            individual = solution.encode()
            history_file.write(HistoryRecord.display(individual))

        print(f"Saved individual history to {dump_path}")

    else:
        print(f"Unrecognized file extension {dump_path}")
