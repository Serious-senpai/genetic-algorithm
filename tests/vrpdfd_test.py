from typing import Optional

from ga import utils, vrpdfd


def check_solution(solution: Optional[vrpdfd.VRPDFDSolution], *, expected: Optional[float] = None) -> None:
    assert solution is not None

    print(solution)
    solution.assert_feasible()
    if expected is not None and not utils.isclose(solution.cost, expected):
        message = f"Optimal {expected}, got {solution.cost}"
        raise ValueError(message)


def test_decode_6_5_1() -> None:
    vrpdfd.ProblemConfig.get_config("6.5.1").initial_fine_coefficient = 10 ** 3
    vrpdfd.ProblemConfig.context = "6.5.1"
    solution = vrpdfd.VRPDFDIndividual.from_cache(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 6, 3, 2, 5, 1]),),
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
    vrpdfd.ProblemConfig.get_config("6.5.2").initial_fine_coefficient = 10 ** 3
    vrpdfd.ProblemConfig.context = "6.5.2"
    solution = vrpdfd.VRPDFDIndividual.from_cache(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 1, 2, 5, 4]),),
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


def test_decode_6_5_3() -> None:
    vrpdfd.ProblemConfig.get_config("6.5.3").initial_fine_coefficient = 10 ** 3
    vrpdfd.ProblemConfig.context = "6.5.3"
    solution = vrpdfd.VRPDFDIndividual.from_cache(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 6, 5, 1, 4, 3]),),
        drone_paths=[
            [
                frozenset([0, 2]),
                frozenset([0, 2]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
            ],
        ],
    ).decode()
    check_solution(solution, expected=-14901.444958783168)


def test_decode_10_5_3() -> None:
    vrpdfd.ProblemConfig.get_config("10.5.3").initial_fine_coefficient = 10 ** 3
    vrpdfd.ProblemConfig.context = "10.5.3"
    solution = vrpdfd.VRPDFDIndividual.from_cache(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 2, 3, 6, 9, 10, 1, 7, 8, 5, 0]),),
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


def test_decode_50_10_1() -> None:
    vrpdfd.ProblemConfig.get_config("50.10.1").initial_fine_coefficient = 10 ** 3
    vrpdfd.ProblemConfig.context = "50.10.1"
    solution = next(iter(vrpdfd.VRPDFDIndividual.initial(solution_cls=vrpdfd.VRPDFDSolution, size=1))).decode()

    print(solution)
    solution.assert_feasible()


def test_decode_100_20_1() -> None:
    vrpdfd.ProblemConfig.get_config("100.20.1").initial_fine_coefficient = 10 ** 3
    vrpdfd.ProblemConfig.context = "100.20.1"
    solution = next(iter(vrpdfd.VRPDFDIndividual.initial(solution_cls=vrpdfd.VRPDFDSolution, size=1))).decode()

    print(solution)
    solution.assert_feasible()


def test_decode_100_40_1() -> None:
    vrpdfd.ProblemConfig.get_config("100.40.1").initial_fine_coefficient = 10 ** 3
    vrpdfd.ProblemConfig.context = "100.40.1"
    solution = vrpdfd.VRPDFDIndividual.from_cache(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(
            frozenset({0, 1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17}),
            frozenset({0, 33, 32, 35, 36, 37, 39, 20, 21, 22, 23, 24, 25, 27, 29, 30, 31}),
            frozenset({0, 41, 44, 45, 48, 50, 51, 54, 55, 56, 57, 59, 60, 64, 67, 68, 69, 70, 71}),
            frozenset({0, 72, 74, 75, 80, 81, 82, 83, 84, 85, 86, 88, 89, 90, 91, 92, 93}),
            frozenset({0, 96, 97, 99, 36, 37, 93, 86, 29, 94, 95}),
        ),
        drone_paths=(
            (),
            (
                frozenset({0, 17}),
                frozenset({0, 76, 55}),
                frozenset({0, 60}),
            ), (
                frozenset({0, 17}),
            ), (
                frozenset({0, 95}),
            ), (
                frozenset({0, 13}),
            ),
        ),
    ).decode()
    check_solution(solution)  # Cannot expect a specific cost since TSP solver result is random
