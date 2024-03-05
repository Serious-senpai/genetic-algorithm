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
    vrpdfd.ProblemConfig.quick_setup("6.5.1")
    solution = vrpdfd.VRPDFDIndividual(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 5, 1, 6]),),
        drone_paths=(
            (
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 1]),
                frozenset([0, 2]),
                frozenset([0, 4]),
                frozenset([0, 4]),
                frozenset([0, 3, 6]),
            ),
        ),
    ).decode()

    check_solution(solution, expected=-25847.199999999997)
    assert utils.isclose(solution.revenue, 29825.0)
    assert utils.isclose(solution.truck_cost, 3233.8)
    assert utils.isclose(solution.drone_cost, 744.0)


def test_decode_6_5_4() -> None:
    vrpdfd.ProblemConfig.quick_setup("6.5.4")
    solution = vrpdfd.VRPDFDIndividual(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 5, 3, 2]),),
        drone_paths=(
            (
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
            ),
        ),
    ).decode()

    check_solution(solution, expected=-18352.8)
    assert utils.isclose(solution.revenue, 23775.0)
    assert utils.isclose(solution.truck_cost, 4816.2)
    assert utils.isclose(solution.drone_cost, 606.0)


def test_decode_6_10_1() -> None:
    vrpdfd.ProblemConfig.quick_setup("6.10.1")
    solution = vrpdfd.VRPDFDIndividual(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 1, 2, 4, 5]),),
        drone_paths=(
            (
                frozenset([0, 6]),
                frozenset([0, 2]),
                frozenset([0, 2]),
                frozenset([0, 2]),
                frozenset([0, 2]),
                frozenset([0, 2]),
                frozenset([0, 3]),
            ),
        ),
    ).decode()

    check_solution(solution, expected=-8418.2)
    assert utils.isclose(solution.revenue, 16700.0)
    assert utils.isclose(solution.truck_cost, 7304.799999999999)
    assert utils.isclose(solution.drone_cost, 976.9999999999999)


def test_decode_6_10_2() -> None:
    vrpdfd.ProblemConfig.quick_setup("6.10.2")
    solution = vrpdfd.VRPDFDIndividual(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 1, 2, 3, 4, 5]),),
        drone_paths=(
            (
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 6]),
                frozenset([0, 2]),
            ),
        ),
    ).decode()

    check_solution(solution, expected=-5366.0)
    assert utils.isclose(solution.revenue, 14825.0)
    assert utils.isclose(solution.truck_cost, 8556.0)
    assert utils.isclose(solution.drone_cost, 903.0)


def test_decode_6_20_3() -> None:
    vrpdfd.ProblemConfig.quick_setup("6.20.3")
    solution = vrpdfd.VRPDFDIndividual(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 1, 4, 5, 6]),),
        drone_paths=(
            (
                frozenset([0, 2]),
                frozenset([0, 2]),
                frozenset([0, 3]),
                frozenset([0, 3]),
            ),
        ),
    ).decode()

    check_solution(solution, expected=-4431.5999999999985)
    assert utils.isclose(solution.revenue, 24875.0)
    assert utils.isclose(solution.truck_cost, 18464.399999999998)
    assert utils.isclose(solution.drone_cost, 1979.0)


def test_decode_10_5_3() -> None:
    vrpdfd.ProblemConfig.quick_setup("10.5.3")
    solution = vrpdfd.VRPDFDIndividual(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 2, 3, 5, 6]),),
        drone_paths=(
            (
                frozenset([0, 9]),
                frozenset([0, 9]),
                frozenset([0, 9, 1]),
                frozenset([0, 9, 10]),
                frozenset([0, 7, 8]),
            ),
        ),
    ).decode()

    check_solution(solution, expected=-15428.55)
    assert utils.isclose(solution.revenue, 19775.0)
    assert utils.isclose(solution.truck_cost, 3620.2000000000003)
    assert utils.isclose(solution.drone_cost, 726.25)


def test_decode_10_20_1() -> None:
    vrpdfd.ProblemConfig.quick_setup("10.20.1")
    solution = vrpdfd.VRPDFDIndividual(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 2, 3, 4, 6, 8, 9, 10]),),
        drone_paths=(
            (
                frozenset([0, 5]),
                frozenset([0, 5]),
                frozenset([0, 5]),
                frozenset([0, 5]),
                frozenset([0, 7]),
            ),
        ),
    ).decode()

    check_solution(solution, expected=371.0)
    assert utils.isclose(solution.revenue, 18125.0)
    assert utils.isclose(solution.truck_cost, 16099.999999999998)
    assert utils.isclose(solution.drone_cost, 2396.0)


def test_decode_12_20_4() -> None:
    vrpdfd.ProblemConfig.quick_setup("12.20.4")
    solution = vrpdfd.VRPDFDIndividual(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 1, 3, 6, 8, 9, 12]),),
        drone_paths=(
            (
                frozenset([0, 2]),
                frozenset([0, 2]),
                frozenset([0, 2]),
                frozenset([0, 2]),
                frozenset([0, 2]),
                frozenset([0, 4]),
                frozenset([0, 5]),
            ),
        ),
    ).decode()

    check_solution(solution, expected=4610.4)
    assert utils.isclose(solution.revenue, 11825.0)
    assert utils.isclose(solution.truck_cost, 13404.4)
    assert utils.isclose(solution.drone_cost, 3031.0)


def test_decode_20_20_3() -> None:
    vrpdfd.ProblemConfig.quick_setup("20.20.3")
    solution = vrpdfd.VRPDFDIndividual(
        solution_cls=vrpdfd.VRPDFDSolution,
        truck_paths=(frozenset([0, 1, 2, 3, 5, 8, 9, 10, 12, 13, 14, 15]),),
        drone_paths=(
            (
                frozenset([0, 16]),
                frozenset([0, 16]),
                frozenset([0, 16]),
                frozenset([0, 18]),
                frozenset([0, 20]),
                frozenset([0, 20]),
                frozenset([0, 20]),
                frozenset([0, 16, 20]),
            ),
        ),
    ).decode()

    check_solution(solution, expected=1070.4500000000007)
    assert utils.isclose(solution.revenue, 28675.0)
    assert utils.isclose(solution.truck_cost, 26689.2)
    assert utils.isclose(solution.drone_cost, 3056.25)
