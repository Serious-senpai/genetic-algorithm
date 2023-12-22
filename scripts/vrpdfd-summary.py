import json
import os
from pathlib import Path
from typing import Any, List, Optional, Tuple, TypedDict


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


def wrap_double_quotes(text: Any) -> str:
    return f"\"{text}\""


summary_dir = Path("vrpdfd-summary")
field_names = (
    "Problem",
    "Generations",
    "Population size",
    "Mutation rate",
    "Initial fine coefficient",
    "Fine coefficient increase rate",
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
                data["solution"]["profit"],
                data["solution"]["feasible"],
                wrap_double_quotes(data["solution"]["truck_paths"]),
                wrap_double_quotes(data["solution"]["drone_paths"]),
                data["time"],
                data["fake_tsp_solver"],
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
                fields.append(milp_data["obj_value"])
                fields.append(milp_data["status"])
                fields.append(milp_data["solve_time"])

            csvfile.write(",".join(map(str, fields)) + "\n")
