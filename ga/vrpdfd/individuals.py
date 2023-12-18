from __future__ import annotations

import itertools
import random
from typing import ClassVar, Final, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple, Type, Union, TYPE_CHECKING, final, overload

if TYPE_CHECKING:
    from typing_extensions import Self

from .config import ProblemConfig
from .errors import PopulationInitializationException
from ..abc import SingleObjectiveIndividual
from ..utils import maximum_weighted_flow, tsp_solver, weighted_flows_with_demands, weighted_random_choice
if TYPE_CHECKING:
    from .solutions import VRPDFDSolution


__all__ = ("VRPDFDIndividual",)


if TYPE_CHECKING:
    BaseIndividual = SingleObjectiveIndividual[VRPDFDSolution]

else:
    BaseIndividual = SingleObjectiveIndividual


@final
class VRPDFDIndividual(BaseIndividual):

    __slots__ = (
        "__cls",
        "__decoded",
        "__truck_distance",
        "__drone_distance",
        "__truck_distances",
        "__drone_distances",
        "truck_paths",
        "drone_paths",
    )
    genetic_algorithm_last_improved: ClassVar[int] = 0
    if TYPE_CHECKING:
        __cls: Final[Type[VRPDFDSolution]]
        __decoded: Optional[VRPDFDSolution]
        __truck_distance: Optional[float]
        __drone_distance: Optional[float]
        __truck_distances: Optional[Tuple[float, ...]]
        __drone_distances: Optional[Tuple[Tuple[float, ...], ...]]
        truck_paths: Final[Tuple[FrozenSet[int], ...]]
        drone_paths: Final[Tuple[Tuple[FrozenSet[int], ...], ...]]

    def __init__(
        self,
        *,
        cls: Type[VRPDFDSolution],
        truck_paths: Iterable[FrozenSet[int]],
        drone_paths: Iterable[Iterable[FrozenSet[int]]],
    ) -> None:
        self.__cls = cls
        self.__decoded = None
        self.__truck_distance = None
        self.__drone_distance = None
        self.__truck_distances = None
        self.__drone_distances = None
        self.truck_paths = tuple(truck_paths)
        self.drone_paths = tuple(tuple(path for path in paths if len(path) > 1) for paths in drone_paths)

    @property
    def cls(self) -> Type[VRPDFDSolution]:
        return self.__cls

    @overload
    @staticmethod
    def calculate_distance(path: Sequence[int]) -> float: ...

    @overload
    @staticmethod
    def calculate_distance(path: FrozenSet[int]) -> float: ...

    @staticmethod
    def calculate_distance(path: Union[Sequence[int], FrozenSet[int]]) -> float:
        config = ProblemConfig()
        if isinstance(path, frozenset):
            distance, _ = VRPDFDIndividual.path_order(path)
            return distance

        distance = 0.0
        for index in range(len(path) - 1):
            current = path[index]
            next = path[index + 1]
            distance += config.distances[current][next]

        return distance

    @staticmethod
    def path_order(path: FrozenSet[int]) -> Tuple[float, List[int]]:
        config = ProblemConfig()
        customers = tuple(path)
        locations = [config.customers[i].location for i in customers]
        distance, path_index = tsp_solver(locations, first=customers.index(0))

        ordered = list(map(customers.__getitem__, path_index))
        ordered.append(0)

        return distance, ordered

    def flatten(self) -> List[FrozenSet[int]]:
        return list(itertools.chain(self.truck_paths, itertools.chain(*self.drone_paths)))

    def reconstruct(self, flattened_paths: List[FrozenSet[int]]) -> VRPDFDIndividual:
        truck_paths: List[FrozenSet[int]] = flattened_paths[:len(self.truck_paths)]
        drone_paths: List[List[FrozenSet[int]]] = []
        drone_paths_iter = iter(flattened_paths[len(self.truck_paths):])
        for paths in self.drone_paths:
            drone_paths.append([])
            for _ in range(len(paths)):
                drone_paths[-1].append(next(drone_paths_iter))

        return VRPDFDIndividual(
            cls=self.cls,
            truck_paths=truck_paths,
            drone_paths=drone_paths,
        )

    def append_drone_path(self, drone: int, path: FrozenSet[int]) -> VRPDFDIndividual:
        drone_paths = list(map(list, self.drone_paths))
        drone_paths[drone].append(path)
        return VRPDFDIndividual(
            cls=self.cls,
            truck_paths=self.truck_paths,
            drone_paths=drone_paths,
        )

    @property
    def cost(self) -> float:
        decoded = self.decode()
        return decoded.cost

    def decode(self) -> VRPDFDSolution:
        if self.__decoded is None:
            config = ProblemConfig()

            network_size = 1 + (config.trucks_count + sum(map(len, self.drone_paths))) + config.customers_count + 1  # network with 4 layers
            network_source = 0
            network_sink = network_size - 1

            network_customers_offset = config.trucks_count + sum(map(len, self.drone_paths)) + 1

            network_demands = [[0.0] * network_size for _ in range(network_size)]
            network_capacities = [[0.0] * network_size for _ in range(network_size)]
            network_neighbors: List[Set[int]] = [set() for _ in range(network_size)]

            network_neighbors[network_source].update(range(1, network_customers_offset))
            total_flow = 0.0
            for network_route in range(1, network_customers_offset):
                capacity = config.truck.capacity if network_route < 1 + config.trucks_count else config.drone.capacity
                total_flow += capacity
                if network_route < 1 + config.trucks_count:
                    network_capacities[network_source][network_route] = network_demands[network_source][network_route] = capacity
                else:
                    network_capacities[network_source][network_route] = network_demands[network_source][network_route] = capacity

            for network_route, path in enumerate(self.truck_paths, start=1):
                for customer in path:
                    if customer != 0:
                        network_capacities[network_route][network_customers_offset + customer - 1] = 10 ** 6
                        network_neighbors[network_route].add(network_customers_offset + customer - 1)

            for network_route, path in enumerate(itertools.chain(*self.drone_paths), start=1 + config.trucks_count):
                for customer in path:
                    if customer != 0:
                        network_capacities[network_route][network_customers_offset + customer - 1] = 10 ** 6
                        network_neighbors[network_route].add(network_customers_offset + customer - 1)

            for customer, network_customer in enumerate(range(network_customers_offset, network_sink), start=1):
                network_demands[network_customer][network_sink] = config.customers[customer].low
                network_capacities[network_customer][network_sink] = config.customers[customer].high
                network_neighbors[network_customer].add(network_sink)

            network_flow_weights: List[List[float]] = [[0.0] * network_size for _ in range(network_size)]
            for customer in range(1, len(config.customers)):
                network_weight = config.customers[customer].w
                network_flow_weights[network_customers_offset + customer - 1][network_sink] = network_weight

            _, flows = maximum_weighted_flow(
                size=network_size,
                capacities=network_capacities,
                neighbors=network_neighbors,
                flow_weights=network_flow_weights,
                source=network_source,
                sink=network_sink,
            )

            total_weights = [0.0] * len(config.customers)
            truck_paths: List[List[Tuple[int, float]]] = []
            for route, path in enumerate(self.truck_paths, start=1):
                _, cycle = self.path_order(path)

                truck_paths.append([])
                for customer in cycle:
                    if customer == 0:
                        truck_paths[-1].append((0, 0.0))
                    else:
                        weight = flows[route][network_customers_offset + customer - 1]
                        truck_paths[-1].append((customer, weight))
                        total_weights[customer] += weight

            flatten_drone_paths: List[List[Tuple[int, float]]] = []
            for route, path in enumerate(itertools.chain(*self.drone_paths), start=1 + config.trucks_count):
                flatten_drone_paths.append([])
                _, cycle = self.path_order(path)

                for customer in cycle:
                    if customer == 0:
                        flatten_drone_paths[-1].append((0, 0.0))
                    else:
                        weight = flows[route][network_customers_offset + customer - 1]
                        flatten_drone_paths[-1].append((customer, weight))
                        total_weights[customer] += weight

            drone_paths: List[List[List[Tuple[int, float]]]] = []
            flatten_drone_paths_iter = iter(flatten_drone_paths)
            for paths in self.drone_paths:
                drone_paths.append([])
                for _ in range(len(paths)):
                    drone_paths[-1].append(next(flatten_drone_paths_iter))

            # Rearrange paths to achieve lower bounds
            for customer in range(1, len(config.customers)):
                if config.customers[customer].low > total_weights[customer]:
                    patched = False
                    for c in reversed(config.customers_by_profit):
                        if c == customer:
                            continue

                        for complete_path in itertools.chain(truck_paths, itertools.chain(*drone_paths)):
                            index_customer = -1
                            for index, (_c, _) in enumerate(complete_path):
                                if _c == customer:
                                    index_customer = index
                                    break

                            if index_customer > -1:
                                for index, (_c, weight) in enumerate(complete_path):
                                    if _c == c:
                                        d = min(
                                            weight,
                                            config.customers[customer].low - total_weights[customer],
                                            total_weights[c] - config.customers[c].low,
                                        )

                                        complete_path[index_customer] = (customer, complete_path[index_customer][1] + d)
                                        complete_path[index] = (_c, weight - d)

                                        total_weights[customer] += d
                                        total_weights[c] -= d

                                        if config.customers[customer].low == total_weights[customer]:
                                            patched = True
                                            break

                            if patched:
                                break

                        if patched:
                            break

                    if not patched:
                        break

            self.__decoded = self.cls(
                truck_paths=tuple(map(tuple, truck_paths)),
                drone_paths=tuple(tuple(map(tuple, paths)) for paths in drone_paths),
            )

        return self.__decoded

    def crossover(self, other: Self) -> List[VRPDFDIndividual]:
        # flatten paths into a single array
        self_paths = self.flatten()
        other_paths = other.flatten()

        # The following procedure can be applied multiple times
        # TODO: Figure out a better random method
        first_index = random.choice(range(len(self_paths)))
        second_index = random.choice(range(len(other_paths)))
        first = {0}
        second = {0}
        sets = (first, second)

        for customer in itertools.chain(self_paths[first_index], other_paths[second_index]):
            random.choice(sets).add(customer)

        self_paths[first_index] = frozenset(first)
        other_paths[second_index] = frozenset(second)

        return [self.reconstruct(self_paths), other.reconstruct(other_paths)]

    def mutate(self) -> VRPDFDIndividual:
        config = ProblemConfig()

        if random.random() < config.mutation_rate:
            random_customers = list(range(1, len(config.customers)))
            random.shuffle(random_customers)

            def remove_customer() -> VRPDFDIndividual:
                paths = self.flatten()
                distances = [self.calculate_distance(path) for path in paths]
                path_index = weighted_random_choice(distances)
                for customer in random_customers:
                    if customer in paths[path_index]:
                        paths[path_index] = paths[path_index].difference([customer])
                        break

                return self.reconstruct(paths)

            def add_customer() -> VRPDFDIndividual:
                paths = self.flatten()
                distances = [self.calculate_distance(path) for path in paths]
                path_index = weighted_random_choice([1 / d if d > 0.0 else 10 ** 9 for d in distances])
                for customer in random_customers:
                    if customer not in paths[path_index]:
                        paths[path_index] = paths[path_index].union([customer])
                        break

                return self.reconstruct(paths)

            def append_path() -> VRPDFDIndividual:
                paths = self.flatten()
                result = self.reconstruct(paths)
                return result.append_drone_path(random.randint(0, config.drones_count - 1), frozenset([0, random_customers[0]]))

            factories = (
                remove_customer,
                add_customer,
                append_path,
            )
            factory = random.choice(factories)
            return factory()

        return self

    @property
    def truck_distances(self) -> Tuple[float, ...]:
        if self.__truck_distances is None:
            self.__truck_distances = tuple(map(self.calculate_distance, self.truck_paths))

        return self.__truck_distances

    @property
    def truck_distance(self) -> float:
        if self.__truck_distance is None:
            self.__truck_distance = sum(self.truck_distances)

        return self.__truck_distance

    @property
    def drone_distances(self) -> Tuple[Tuple[float, ...], ...]:
        if self.__drone_distances is None:
            self.__drone_distances = tuple(tuple(map(self.calculate_distance, paths)) for paths in self.drone_paths)

        return self.__drone_distances

    @property
    def drone_distance(self) -> float:
        if self.__drone_distance is None:
            self.__drone_distance = sum(map(sum, self.drone_distances))

        return self.__drone_distance

    @classmethod
    def after_generation_hook(cls, generation: int, last_improved: int, result: VRPDFDIndividual) -> None:
        cls.genetic_algorithm_last_improved = last_improved

    @classmethod
    def initial(cls, *, solution_cls: Type[VRPDFDSolution], size: int) -> Set[VRPDFDIndividual]:
        config = ProblemConfig()

        results: Set[VRPDFDIndividual] = set()
        try:
            # Solve flows with demands problem with 4 layers: source - routes - customers - sink
            paths_per_drone = 1
            while True:
                network_size = 1 + (config.trucks_count + config.drones_count * paths_per_drone) + config.customers_count + 1  # network with 4 layers
                network_source = 0
                network_sink = network_size - 1

                network_customers_offset = config.trucks_count + config.drones_count * paths_per_drone + 1

                network_demands = [[0.0] * network_size for _ in range(network_size)]
                network_capacities = [[0.0] * network_size for _ in range(network_size)]

                for network_route in range(1, network_customers_offset):
                    if network_route < 1 + config.trucks_count:
                        network_capacities[network_source][network_route] = config.truck.capacity
                    else:
                        network_capacities[network_source][network_route] = config.drone.capacity

                for network_route, network_customer in itertools.product(range(1, network_customers_offset), range(network_customers_offset, network_sink)):
                    network_capacities[network_route][network_customer] = 10 ** 9

                for customer, network_customer in enumerate(range(network_customers_offset, network_sink), start=1):
                    network_demands[network_customer][network_sink] = config.customers[customer].low
                    network_capacities[network_customer][network_sink] = config.customers[customer].high

                network_neighbors: List[Set[int]] = [set() for _ in range(network_size)]
                network_neighbors[network_source].update(range(1, network_customers_offset))

                for network_route in range(1, network_customers_offset):
                    network_neighbors[network_route].update(range(network_customers_offset, network_sink))

                for network_customer in range(network_customers_offset, network_sink):
                    network_neighbors[network_customer].add(network_sink)

                network_flow_weights: List[List[float]] = [[0.0] * network_size for _ in range(network_size)]
                for customer in range(1, len(config.customers)):
                    network_weight = config.customers[customer].w
                    network_flow_weights[network_customers_offset + customer - 1][network_sink] = network_weight

                packed = weighted_flows_with_demands(
                    size=network_size,
                    demands=network_demands,
                    capacities=network_capacities,
                    neighbors=network_neighbors,
                    flow_weights=network_flow_weights,
                    source=network_source,
                    sink=network_sink,
                )
                if packed is None:
                    paths_per_drone += 1
                    continue

                _, flows = packed

                truck_paths = [{0} for _ in range(config.trucks_count)]
                drone_paths = [[{0}, {0}] for _ in range(config.drones_count)]
                customer_demands = [customer.low for customer in config.customers]
                for vehicle, network_route in zip(itertools.chain(range(config.trucks_count), range(config.drones_count)), range(1, network_customers_offset)):
                    if network_route < 1 + config.trucks_count:
                        path = truck_paths[vehicle]
                        capacity = config.truck.capacity
                    else:
                        path = drone_paths[vehicle][(network_route - config.trucks_count - 1) // config.drones_count]
                        capacity = config.drone.capacity

                    for customer, network_customer in enumerate(range(network_customers_offset, network_sink), start=1):
                        deliver = min(customer_demands[customer], flows[network_route][network_customer])
                        if deliver > 0.0:
                            capacity -= deliver
                            customer_demands[customer] -= deliver
                            path.add(customer)

                    for customer in sorted(path, key=customer_demands.__getitem__):
                        deliver = min(capacity, customer_demands[customer])
                        capacity -= deliver
                        customer_demands[customer] -= deliver
                        if capacity == 0.0:
                            break

                results.add(
                    cls(
                        cls=solution_cls,
                        truck_paths=map(frozenset, truck_paths),
                        drone_paths=(map(frozenset, paths) for paths in drone_paths),
                    )
                )

                while len(results) < size:
                    array = list(results)
                    base = random.choice(array)
                    results.add(base.mutate())

                return results

        except BaseException as e:
            raise PopulationInitializationException(e) from e

    def __repr__(self) -> str:
        return f"VRPDFDIndividual(truck_paths={self.truck_paths!r}, drone_paths={self.drone_paths!r})"

    def __hash__(self) -> int:
        return hash((self.truck_paths, self.drone_paths))
