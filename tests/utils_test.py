import itertools
from typing import Sequence

from ga import utils


def check_valid_flow(flows: Sequence[Sequence[float]]) -> None:
    size = len(flows)
    total_out = [0.0] * size
    total_in = [0.0] * size
    for first, second in itertools.product(range(size), range(size)):
        assert flows[first][second] >= 0.0
        total_out[first] += flows[first][second]
        total_in[second] += flows[first][second]

    for index in range(size):
        if index > 0 and index < size - 1:
            assert total_out[index] == total_in[index]


def test_maximum_flow() -> None:
    result, flows = utils.maximum_flow(
        size=6,
        capacities=[
            [0, 7, 0, 0, 4, 0],
            [0, 0, 5, 3, 0, 0],
            [0, 0, 0, 0, 0, 8],
            [0, 0, 3, 0, 0, 5],
            [0, 3, 0, 2, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ],
        neighbors=[
            {1, 4},
            {2, 3},
            {5},
            {2, 5},
            {1, 3},
            set(),
        ],
        source=0,
        sink=5,
    )

    print(flows)
    assert result == 10
    check_valid_flow(flows)


def test_maximum_weighted_flow() -> None:
    result, flows = utils.maximum_weighted_flow(
        size=6,
        capacities=[
            [0, 7, 0, 0, 4, 0],
            [0, 0, 5, 3, 0, 0],
            [0, 0, 0, 0, 0, 8],
            [0, 0, 3, 0, 0, 5],
            [0, 3, 0, 2, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ],
        neighbors=[
            {1, 4},
            {2, 3},
            {5},
            {2, 5},
            {1, 3},
            set(),
        ],
        flow_weights=[
            [0, 2, 0, 0, 1, 0],
            [0, 0, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 1],
            [0, 0, 1, 0, 0, 1],
            [0, 1, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ],
        source=0,
        sink=5,
    )

    print(flows)
    assert result == 41
    assert sum(flows[0]) == 10
    check_valid_flow(flows)


def test_flows_with_answers_as_demands() -> None:
    flows = utils.flows_with_demands(
        size=6,
        demands=[
            [0, 6, 0, 0, 4, 0],
            [0, 0, 5, 3, 0, 0],
            [0, 0, 0, 0, 0, 8],
            [0, 0, 3, 0, 0, 2],
            [0, 2, 0, 2, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ],
        capacities=[
            [0, 7, 0, 0, 4, 0],
            [0, 0, 5, 3, 0, 0],
            [0, 0, 0, 0, 0, 8],
            [0, 0, 3, 0, 0, 5],
            [0, 3, 0, 2, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ],
        neighbors=[
            {1, 4},
            {2, 3},
            {5},
            {2, 5},
            {1, 3},
            set(),
        ],
        source=0,
        sink=5,
    )

    assert flows is not None

    print(flows)
    assert sum(flows[0]) == 10
    check_valid_flow(flows)


def test_weird_round() -> None:
    assert utils.weird_round(1.234, 2) == 1.24
    assert utils.weird_round(2.3301, 2) == 2.34
