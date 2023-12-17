import json
import os
from pathlib import Path
from typing import Any, List, Tuple, TypedDict


class SolutionInfo(TypedDict):
    profit: float
    truck_paths: List[List[Tuple[int, float]]]
    drone_paths: List[List[List[Tuple[int, float]]]]


class SolutionJSON(TypedDict):
    problem: str
    generations: int
    population_size: int
    mutation_rate: float
    solution: SolutionInfo
    time: str


def wrap_double_quotes(text: Any) -> str:
    return f"\"{text}\""


summary_dir = Path("vrpdfd-summary")
field_names = (
    "Problem",
    "Generations",
    "Population size",
    "Mutation rate",
    "Profit",
    "Truck paths",
    "Drone paths",
    "Computation time",
    "MILP profit",
)


summary_dir.mkdir(parents=True, exist_ok=True)
with open(summary_dir / "vrpdfd-summary.csv", "w") as csvfile:
    csvfile.write(",".join(field_names) + "\n")
    for file in os.listdir(summary_dir):
        if file.startswith("output-"):
            with open(summary_dir / file, "r", encoding="utf-8") as f:
                data: SolutionJSON = json.load(f)

            fields = [
                data["problem"],
                data["generations"],
                data["population_size"],
                data["mutation_rate"],
                data["solution"]["profit"],
                wrap_double_quotes(data["solution"]["truck_paths"]),
                wrap_double_quotes(data["solution"]["drone_paths"]),
                data["time"],
            ]

            problem_size = data["problem"].split(".")[0]
            problem_name = data["problem"]
            milp_path = Path("problems/vrpdfd/results") / f"{problem_size}Cus" / f"result_{problem_name}.json"
            if milp_path.exists():
                with open(milp_path, "r", encoding="utf-8") as f:
                    milp_data = json.load(f)

                fields.append(milp_data["obj_value"])

            csvfile.write(",".join(map(str, fields)) + "\n")
