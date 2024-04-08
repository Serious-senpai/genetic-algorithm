import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ga.vrpdfd import SolutionJSON


def wrap_double_quotes(text: Any) -> str:
    return f"\"{text}\""


def sdvrp_results() -> Dict[str, Tuple[float, float]]:
    sd_results: Dict[str, List[float]] = {}
    with open("problems/vrpdfd/results/sdvrp-summary.csv", "r", encoding="utf-8", newline="") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",", quotechar="\"")
        csvlines = iter(csvreader)
        next(csvlines)  # Skip header
        for csvline in csvlines:
            problem = csvline[0].removesuffix(".txt")
            result = float(csvline[6])

            try:
                sd_results[problem].append(result)
            except KeyError:
                sd_results[problem] = [result]

    sd_summary: Dict[str, Tuple[float, float]] = {}
    for problem, sd_result in sd_results.items():
        sd_summary[problem] = (sum(sd_result) / len(sd_result), max(sd_result))

    return sd_summary


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
    "SDVRP average",
    "SDVRP max",
    "Improved to avg [%]",
    "Improved to max [%]",
)
sd_summary = sdvrp_results()
with open(summary_dir / "vrpdfd-summary.csv", "w") as csvfile:
    csvfile.write(",".join(field_names) + "\n")
    for index, file in enumerate(sorted(os.listdir(summary_dir))):
        if file.startswith("output-") and file.endswith(".json"):
            with open(summary_dir / file, "r", encoding="utf-8") as f:
                data: SolutionJSON = json.load(f)

            sd_avg, sd_max = sd_summary[data["problem"]]
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
                sd_avg,
                sd_max,
                wrap_double_quotes(f"=ROUND(100 * (H{index + 2} - P{index + 2}) / ABS(P{index + 2}), 4)"),
                wrap_double_quotes(f"=ROUND(100 * (H{index + 2} - Q{index + 2}) / ABS(Q{index + 2}), 4)"),
            ]

            csvfile.write(",".join(map(str, fields)) + "\n")
