import json
import os
import re
from collections import defaultdict
from pathlib import Path
from traceback import print_exc
from typing import Any, Dict, DefaultDict, List, Optional, Tuple, TypedDict

from ga.utils import isclose
from ga.vrpdfd import ProblemConfig, VRPDFDSolution


class SolutionInfo(TypedDict):
    profit: float
    feasible: bool
    truck_paths: List[List[Tuple[int, float]]]
    drone_paths: List[List[List[Tuple[int, float]]]]


class SolutionJSON(TypedDict):
    problem: str
    generations: int
    population_size: int
    mutation_rate: float
    initial_fine_coefficient: float
    fine_coefficient_increase_rate: float
    stuck_penalty_increase_rate: float
    solution: SolutionInfo
    time: str
    fake_tsp_solver: bool
    last_improved: int
    extra: Optional[str]


class MILPSolutionJSON(TypedDict):
    # We only annotate the fields in need here
    data_set: str
    status: str
    solve_time: float
    obj_value: float
    truck: Dict[str, float]
    drone: Dict[str, float]
    cusWeightByDrone: Dict[str, float]
    cusWeightByTruck: Dict[str, float]


def wrap_double_quotes(text: Any) -> str:
    return f"\"{text}\""


_read_milp_solution_cache: Dict[str, VRPDFDSolution] = {}


def read_milp_solution(data: MILPSolutionJSON) -> VRPDFDSolution:
    try:
        return _read_milp_solution_cache[data["data_set"]]

    except KeyError:
        problem_size = int(data["data_set"].split(".")[0])

        truck_volumes: List[DefaultDict[int, float]] = []
        for key, value in data["cusWeightByTruck"].items():
            match = re.fullmatch(r"m\[(\d+),(\d+)\]", key)
            assert match is not None

            customer, truck = map(int, match.groups())
            while len(truck_volumes) <= truck:
                truck_volumes.append(defaultdict(lambda: 0.0))

            truck_volumes[truck][customer] = value

        drone_volumes: List[List[DefaultDict[int, float]]] = []
        for key, value in data["cusWeightByDrone"].items():
            match = re.fullmatch(r"m\[(\d+),(\d+),(\d+)\]", key)
            assert match is not None

            customer, drone, path_id = map(int, match.groups())
            while len(drone_volumes) <= drone:
                drone_volumes.append([])

            while len(drone_volumes[drone]) <= path_id:
                drone_volumes[drone].append(defaultdict(lambda: 0.0))

            drone_volumes[drone][path_id][customer] = value

        truck_after: List[Dict[int, int]] = []
        for key, value in data["truck"].items():
            if isclose(value, 1.0):
                match = re.fullmatch(r"x\[(\d+),(\d+),(\d+)\]", key)
                assert match is not None

                before, after, truck = map(int, match.groups())
                while len(truck_after) <= truck:
                    truck_after.append({})

                truck_after[truck][before] = after

        drone_after: List[List[Dict[int, int]]] = []
        for key, value in data["drone"].items():
            if isclose(value, 1.0):
                match = re.fullmatch(r"y\[(\d+),(\d+),(\d+),(\d+)\]", key)
                assert match is not None

                before, after, drone, path_id = map(int, match.groups())
                while len(drone_after) <= drone:
                    drone_after.append([])

                while len(drone_after[drone]) <= path_id:
                    drone_after[drone].append({})

                drone_after[drone][path_id][before] = after

        truck_paths: List[List[Tuple[int, float]]] = []
        for truck, path_data in enumerate(truck_after):
            truck_paths.append([])
            current = 0
            while current != problem_size + 1:
                truck_paths[-1].append((current, truck_volumes[truck][current]))
                current = path_data[current]

            truck_paths[-1].append((0, 0.0))

        drone_paths: List[List[List[Tuple[int, float]]]] = []
        for drone, paths_data in enumerate(drone_after):
            drone_paths.append([])
            for path_id, path_data in enumerate(paths_data):
                drone_paths[-1].append([])
                current = 0
                while current != problem_size + 1:
                    drone_paths[-1][-1].append((current, drone_volumes[drone][path_id][current]))
                    current = path_data[current]

                drone_paths[-1][-1].append((0, 0.0))

        _read_milp_solution_cache[data["data_set"]] = solution = VRPDFDSolution(
            truck_paths=tuple(map(tuple, truck_paths)),
            drone_paths=tuple(tuple(map(tuple, paths)) for paths in drone_paths),
        )

        try:
            if not isclose(milp_data["obj_value"], -solution.cost):
                message = f"MILP solution for {problem_name} reported profit {milp_data['obj_value']}, actual value {-solution.cost}:\n{solution}"
                raise ValueError(message) from None

        except ValueError:
            print_exc()

        return solution


summary_dir = Path("vrpdfd-summary")
field_names = (
    "Problem",
    "Generations",
    "Population size",
    "Mutation rate",
    "Initial fine coefficient",
    "Fine coefficient increase rate",
    "Stuck penalty increase rate",
    "Profit",
    "Feasible",
    "Truck paths",
    "Drone paths",
    "Computation time",
    "Fake TSP solver",
    "Last improved",
    "Extra",
    "MILP profit",
    "MILP status",
    "MILP computation time",
)


summary_dir.mkdir(parents=True, exist_ok=True)
with open(summary_dir / "vrpdfd-summary.csv", "w") as csvfile:
    csvfile.write(",".join(field_names) + "\n")
    for file in sorted(os.listdir(summary_dir)):
        if file.startswith("output-"):
            with open(summary_dir / file, "r", encoding="utf-8") as f:
                data: SolutionJSON = json.load(f)

            fields = [
                data["problem"],
                data["generations"],
                data["population_size"],
                data["mutation_rate"],
                data["initial_fine_coefficient"],
                data["fine_coefficient_increase_rate"],
                data["stuck_penalty_increase_rate"],
                data["solution"]["profit"],
                int(data["solution"]["feasible"]),
                wrap_double_quotes(data["solution"]["truck_paths"]),
                wrap_double_quotes(data["solution"]["drone_paths"]),
                data["time"],
                int(data["fake_tsp_solver"]),
                data["last_improved"],
                data["extra"],
            ]

            problem_name = data["problem"]
            problem_size = problem_name.split(".")[0]
            milp_path = Path("problems/vrpdfd/results") / f"{problem_size}Cus" / f"result_{problem_name}.json"
            if milp_path.exists():
                with open(milp_path, "r", encoding="utf-8") as f:
                    milp_data: MILPSolutionJSON = json.load(f)

                assert milp_data["data_set"] == problem_name
                ProblemConfig.get_config(problem_name).initial_fine_coefficient = 10 ** 3
                ProblemConfig.context = problem_name

                milp_solution = read_milp_solution(milp_data)

                fields.append(-milp_solution.cost)
                fields.append(milp_data["status"])
                fields.append(milp_data["solve_time"])

            csvfile.write(",".join(map(str, fields)) + "\n")
