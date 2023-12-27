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
    solution = vrpdfd.VRPDFDIndividual(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 5, 1, 6]),),
        drone_paths=[
            [
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 2]),
                frozenset([0, 4]),
                frozenset([0, 4]),
                frozenset([0, 3, 6]),
            ],
        ],
    ).decode()

    print(solution.truck_distances)
    assert utils.isclose(solution.revenue, 29825.0)
    assert utils.isclose(solution.truck_cost, 3233.8)
    assert utils.isclose(solution.drone_cost, 744.0)
    check_solution(solution, expected=-25847.199999999997)


def test_decode_6_5_4() -> None:
    vrpdfd.ProblemConfig.get_config("6.5.4").initial_fine_coefficient = 10 ** 3
    vrpdfd.ProblemConfig.context = "6.5.4"
    solution = vrpdfd.VRPDFDIndividual.from_cache(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 5, 3, 2]),),
        drone_paths=[
            [
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
            ),
        ),
    ).decode()

    print(solution.truck_distances)
    assert utils.isclose(solution.revenue, 23775.0)
    assert utils.isclose(solution.truck_cost, 4816.2)
    assert utils.isclose(solution.drone_cost, 606.0)
    check_solution(solution, expected=-18352.8)


def test_decode_6_10_2() -> None:
    vrpdfd.ProblemConfig.get_config("6.10.2").initial_fine_coefficient = 10 ** 3
    vrpdfd.ProblemConfig.context = "6.10.2"
    solution = vrpdfd.VRPDFDIndividual.from_cache(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 2, 5, 3, 4, 1]),),
        drone_paths=[
            [
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 2]),
            ],
        ],
    ).decode()

    print(solution.truck_distances)
    assert utils.isclose(solution.revenue, 14825.0)
    assert utils.isclose(solution.truck_cost, 8556.0)
    assert utils.isclose(solution.drone_cost, 903.0)
    check_solution(solution, expected=-5366.0)
