import csv
import json
import os
from pathlib import Path
from typing import Any, Dict

from ga.vrpdfd import SolutionJSON


def wrap_double_quotes(text: Any) -> str:
    return f"\"{text}\""


def sdvrp_results() -> Dict[str, int]:
    sd_results: Dict[str, int] = {}
    with open("problems/vrpdfd/results/sdvrp-summary.csv", "r", encoding="utf-8", newline="") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",", quotechar="\"")
        csvlines = iter(csvreader)
        next(csvlines)  # Skip header
        for csvline in csvlines:
            problem = csvline[1].removesuffix(".txt")
            result = int(csvline[2])

            sd_results[problem] = result

    return sd_results


summary_dir = Path("vrpdfd-summary")
summary_dir.mkdir(parents=True, exist_ok=True)
field_names = (
    "Problem",
    "Generations",
    "Population size",
    "Mutation rate",
    "Reset after",
    "Stuck penalty increase rate",
    "Local search batch",
    "Profit",
    "Feasible",
    "Truck paths",
    "Drone paths",
    "Computation time",
    "Fake TSP solver",
    "Last improved",
    "Extra",
    "SDVRP max",
    "Improved to max [%]",
)
sd_summary = sdvrp_results()
with open(summary_dir / "vrpdfd-summary.csv", "w") as csvfile:
    csvfile.write(",".join(field_names) + "\n")
    for index, file in enumerate(
        sorted(f for f in os.listdir(summary_dir) if f.startswith("output-") and f.endswith(".json")),
        start=2,
    ):
        with open(summary_dir / file, "r", encoding="utf-8") as f:
            data: SolutionJSON = json.load(f)

        fields = [
            data["problem"],
            data["generations"],
            data["population_size"],
            data["mutation_rate"],
            data["reset_after"],
            data["stuck_penalty_increase_rate"],
            data["local_search_batch"],
            data["solution"]["profit"],
            int(data["solution"]["feasible"]),
            wrap_double_quotes(data["solution"]["truck_paths"]),
            wrap_double_quotes(data["solution"]["drone_paths"]),
            data["time"],
            int(data["fake_tsp_solver"]),
            data["last_improved"],
            data["extra"],
        ]

        try:
            sd_max = sd_summary[data["problem"]]
            fields.extend(
                [
                    sd_max,
                    wrap_double_quotes(f"=ROUND(100 * (H{index} - P{index}) / ABS(P{index}), 4)"),
                ],
            )
        except KeyError:
            pass

        csvfile.write(",".join(map(str, fields)) + "\n")
