from typing import Optional

from ga import utils, vrpdfd


def check_solution(solution: Optional[vrpdfd.VRPDFDSolution], *, expected: float) -> None:
    assert solution is not None

    print(solution)
    solution.assert_feasible()
    if not utils.isclose(solution.cost, expected):
        message = f"Optimal {expected}, got {solution.cost}"
        raise ValueError(message)


def test_decode_6_5_1() -> None:
    vrpdfd.ProblemConfig.reset_singleton("6.5.1")
    solution = vrpdfd.VRPDFDIndividual(
        cls=vrpdfd.VRPDFDSolution,
        truck_paths=[frozenset([0, 6, 3, 2, 5, 1])],
        drone_paths=[
            [
                frozenset([0, 4]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
            ],
        ],
    ).decode()

    # MILP reported -31375.726216108575, seems like it doesn't know how to solve TSP lol
    check_solution(solution, expected=-31376.164803417923)


def test_decode_6_5_2() -> None:
    vrpdfd.ProblemConfig.reset_singleton("6.5.2")
    solution = vrpdfd.VRPDFDIndividual(
        cls=vrpdfd.VRPDFDSolution,
        truck_paths=[frozenset([0, 1, 2, 5, 4])],
        drone_paths=[
            [
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 3]),
                frozenset([0, 1]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
            ],
        ],
    ).decode()
    check_solution(solution, expected=-17105.399401003662)


def test_decode_10_5_3() -> None:
    vrpdfd.ProblemConfig.reset_singleton("10.5.3")
    solution = vrpdfd.VRPDFDIndividual(
        cls=vrpdfd.VRPDFDSolution,
        truck_paths=[frozenset([0, 2, 3, 6, 9, 10, 1, 7, 8, 5, 0])],
        drone_paths=[
            [
                frozenset([0, 5]),
                frozenset([0, 5]),
                frozenset([0, 5]),
                frozenset([0, 5]),
                frozenset([0, 5]),
                frozenset([0, 5]),
                frozenset([0, 5]),
                frozenset([0, 5]),
                frozenset([0, 5]),
                frozenset([0, 5]),
            ],
        ],
    ).decode()
    check_solution(solution, expected=-22063.12298397885)


def test_decode_100_20_1() -> None:
    vrpdfd.ProblemConfig.reset_singleton("100.20.1")
    solution = next(iter(vrpdfd.VRPDFDIndividual.initial(solution_cls=vrpdfd.VRPDFDSolution, size=1))).decode()

    print(solution)
    solution.assert_feasible()
