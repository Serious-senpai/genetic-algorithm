import argparse
import code
import json
import pickle
import random
import sys
import time
import traceback
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from ga import utils
from ga.vrpdfd import InfeasibleSolution, ProblemConfig, VRPDFDIndividual, VRPDFDSolution, SolutionJSON, path_cache_info, setup_path_cache


class Namespace(argparse.Namespace):
    if TYPE_CHECKING:
        problem: str
        iterations: int
        size: int
        mutation_rate: float
        reset_after: int
        stuck_penalty_increase_rate: float
        local_search_batch: int
        verbose: bool
        cache_limit: int
        fake_tsp_solver: bool
        dump: List[str]
        extra: Optional[str]
        log: Optional[str]
        interactive: bool


parser = argparse.ArgumentParser(description="Genetic algorithm for VRPDFD problem", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("problem", type=str, help="the problem name (e.g. \"6.5.1\", \"200.10.1\", ...)")
parser.add_argument("-i", "--iterations", default=200, type=int, help="the number of generations")
parser.add_argument("--size", default=100, type=int, help="the population size")
parser.add_argument("--mutation-rate", default=0.1, type=float, help="the mutation rate")
parser.add_argument("--reset-after", default=10, type=int, help="the number of non-improving generations before applying stuck penalty and local search")
parser.add_argument("--stuck-penalty-increase-rate", default=0, type=float, help="the stuck penalty increase rate")
parser.add_argument("--local-search-batch", default=50, type=int, help="the batch size for local search")
parser.add_argument("-v", "--verbose", action="store_true", help="turn on verbose mode")
parser.add_argument("--cache-limit", default=50000, type=int, help="set limit for individuals and TSP cache")
parser.add_argument("--fake-tsp-solver", action="store_true", help="use fake TSP solver")
parser.add_argument("--dump", nargs="*", default=[], type=str, help="dump the solution to a file(s), supports *.json, *.pkl and *.png")
parser.add_argument("--extra", type=str, help="extra data dump to file specified by --dump")
parser.add_argument("--log", type=str, help="log each generation to a file")
parser.add_argument("--interactive", action="store_true", help="open interactive shell after running the algorithm")


namespace = Namespace()
parser.parse_args(namespace=namespace)
print(namespace)


if namespace.fake_tsp_solver:
    utils.tsp_solver = utils.fake_tsp_solver
    print(f"Using fake TSP solver {utils.tsp_solver!r}")


config = ProblemConfig.get_config(namespace.problem)
ProblemConfig.context = namespace.problem
config.mutation_rate = namespace.mutation_rate
config.reset_after = namespace.reset_after
config.stuck_penalty_increase_rate = namespace.stuck_penalty_increase_rate
config.local_search_batch = namespace.local_search_batch

VRPDFDIndividual.cache.capacity = namespace.cache_limit
setup_path_cache(namespace.cache_limit)

if namespace.log is not None:
    log_path = Path(namespace.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    config.logger = log_path.open("w", encoding="utf-8")
    config.logger.write(
        ",".join(
            (
                "Generation",
                "Current result",
                "Population best",
                "Population worst",
                "Population average",
                "Feasible count",
                "Time violation coefficient",
                "Weight violation coefficient",
                "Average time violation",
                "Average weight violation",
            ),
        ),
    )
    config.logger.write("\n")


random.seed(time.time())


start = time.perf_counter()
try:
    individual = VRPDFDIndividual.genetic_algorithm(
        generations_count=namespace.iterations,
        population_size=namespace.size,
        population_expansion_limit=2 * namespace.size,
        solution_cls=VRPDFDSolution,
        verbose=namespace.verbose,
    )

finally:
    total_time = time.perf_counter() - start

    try:
        solution = individual.decode()  # type: ignore  # pyright is so dumb
    except NameError:
        if VRPDFDIndividual.genetic_algorithm_result is None:
            raise RuntimeError("No feasible solution was found")

        solution = VRPDFDIndividual.genetic_algorithm_result.decode()

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
                data: SolutionJSON = {
                    "problem": namespace.problem,
                    "generations": VRPDFDIndividual.genetic_algorithm_generation + 1,
                    "population_size": namespace.size,
                    "mutation_rate": namespace.mutation_rate,
                    "reset_after": namespace.reset_after,
                    "stuck_penalty_increase_rate": namespace.stuck_penalty_increase_rate,
                    "local_search_batch": namespace.local_search_batch,
                    "solution": solution.to_json(),
                    "time": total_time,
                    "fake_tsp_solver": namespace.fake_tsp_solver,
                    "last_improved": VRPDFDIndividual.genetic_algorithm_last_improved,
                    "extra": namespace.extra,
                    "cache_info": {
                        "limit": namespace.cache_limit,
                        "individual": VRPDFDIndividual.cache.to_json(),
                        "tsp": path_cache_info(),
                    },
                }
                json.dump(data, json_file)

            print(f"Saved solution as JSON to {dump_path}")

        elif path.endswith(".pkl"):
            sys.setrecursionlimit(100000)
            try:
                with dump_path.open("wb") as pickle_file:
                    pickle.dump(solution.encode(), pickle_file)

            except RecursionError:
                traceback.print_exc()

            else:
                print(f"Pickled solution to {dump_path}")

        elif path.endswith(".png"):
            solution.plot(path)
            print(f"Saved solution plot to {dump_path}")

        else:
            print(f"Unrecognized file extension {dump_path}")

    if config.logger is not None:
        config.logger.close()
        print(f"Saved log to {namespace.log}")


if namespace.interactive:
    code.interact(local=locals())
