from __future__ import annotations

import argparse
import asyncio
import itertools
import json
import tempfile
import traceback
from typing import Dict, List, Tuple, TYPE_CHECKING

import tqdm

if TYPE_CHECKING:
    from ga.vrpdfd import SolutionJSON


class Namespace(argparse.Namespace):
    if TYPE_CHECKING:
        problem: str


Parameter = Tuple[float, int, float]


parser = argparse.ArgumentParser(description="Hyperparameters optimization for VRPDFD problem", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("problem", type=str, help="the problem name (e.g. \"6.5.1\", \"200.10.1\", ...)")
parser.add_argument("-i", "--iterations", default=200, type=int, help="the number of generations")
namespace = Namespace()
parser.parse_args(namespace=namespace)
print(namespace)


parameters_cache: Dict[Parameter, float] = {}
max_concurrency = asyncio.Semaphore(3)


async def run_single_test(parameters: Parameter) -> Tuple[Parameter, float]:
    try:
        return parameters, parameters_cache[parameters]
    except KeyError:
        with tempfile.NamedTemporaryFile("r", encoding="utf-8", suffix=".json", delete=False) as file:
            arguments = [
                "python3", "vrpdfd.py",
                namespace.problem,
                "--mutation-rate", str(parameters[0]),
                "--reset-after", str(parameters[1]),
                "--stuck-penalty-increase-rate", str(parameters[2]),
                "--dump", file.name,
            ]

            async with max_concurrency:
                process = await asyncio.create_subprocess_exec(
                    *arguments,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await process.communicate()

            if process.returncode != 0:
                print(f"Return code {process.returncode} for {parameters}")

            data: SolutionJSON = json.load(file)
            parameters_cache[parameters] = profit = data["solution"]["profit"]
            return parameters, profit


async def main() -> None:
    mutation_rate = (0.2, 0.4, 0.6, 0.8)
    reset_after = (10, 15, 25)
    stuck_penalty_increase_rate = (1, 10, 50, 100)

    tasks = [asyncio.create_task(run_single_test(p)) for p in itertools.product(mutation_rate, reset_after, stuck_penalty_increase_rate)]
    print(f"Running {len(tasks)} tasks")

    results: Tuple[List[Parameter], float] = ([], -float("inf"))
    try:
        for task in tqdm.tqdm(tasks):
            r = await task
            if r[1] > results[1]:
                results = ([r[0]], r[1])

            elif r[1] == results[1]:
                results[0].append(r[0])

    except KeyboardInterrupt:
        traceback.print_exc()

    print(f"Best configuration: {results}")


asyncio.run(main())
