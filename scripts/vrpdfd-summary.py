import json
import os
from pathlib import Path
from typing import Any

from ga.vrpdfd import SolutionJSON


def wrap_double_quotes(text: Any) -> str:
    return f"\"{text}\""


summary_dir = Path("vrpdfd-summary")
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
    "I hit/miss/cached",
    "T hit/miss/cached",
)


summary_dir.mkdir(parents=True, exist_ok=True)
with open(summary_dir / "vrpdfd-summary.csv", "w") as csvfile:
    csvfile.write(",".join(field_names) + "\n")
    for file in sorted(os.listdir(summary_dir)):
        if file.startswith("output-") and file.endswith(".json"):
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
                "/".join(
                    map(
                        str,
                        [
                            data["cache_info"]["individual"]["hit"],
                            data["cache_info"]["individual"]["miss"],
                            data["cache_info"]["individual"]["cached"],
                        ],
                    ),
                ),
                "/".join(
                    map(
                        str,
                        [
                            data["cache_info"]["tsp"]["hit"],
                            data["cache_info"]["tsp"]["miss"],
                            data["cache_info"]["tsp"]["cached"],
                        ],
                    ),
                ),
            ]

            csvfile.write(",".join(map(str, fields)) + "\n")
