from __future__ import annotations

import itertools
import random
from typing import (
    ClassVar,
    Final,
    FrozenSet,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    TYPE_CHECKING,
    final,
    overload,
)

if TYPE_CHECKING:
    from typing_extensions import Self

from .config import ProblemConfig
from .errors import PopulationInitializationException
from .utils import paths_from_flow_chained
from ..abc import SingleObjectiveIndividual
from ..utils import flows_with_demands, weighted_random_choice
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
        "__hash",
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
        __hash: Final[int]
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
        solution_cls: Type[VRPDFDSolution],
        truck_paths: Tuple[FrozenSet[int], ...],
        drone_paths: Tuple[Tuple[FrozenSet[int], ...], ...],
    ) -> None:
        self.__cls = solution_cls
        self.__hash = hash((frozenset(truck_paths), frozenset(frozenset(paths) for paths in drone_paths)))
        self.__decoded = None
        self.__truck_distance = None
        self.__drone_distance = None
        self.__truck_distances = None
        self.__drone_distances = None
        self.truck_paths = truck_paths
        self.drone_paths = drone_paths

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
        config = ProblemConfig.get_config()
        if isinstance(path, frozenset):
            distance, _ = config.path_order(path)
            return distance

        distance = 0.0
        for index in range(len(path) - 1):
            current = path[index]
            next = path[index + 1]
            distance += config.distances[current][next]

        return distance

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
            solution_cls=self.cls,
            truck_paths=tuple(truck_paths),
            drone_paths=tuple(map(tuple, drone_paths)),
        )

    def append_drone_path(self, drone: int, path: FrozenSet[int]) -> VRPDFDIndividual:
        drone_paths = list(map(list, self.drone_paths))
        drone_paths[drone].append(path)
        return VRPDFDIndividual(
            solution_cls=self.cls,
            truck_paths=self.truck_paths,
            drone_paths=tuple(map(tuple, drone_paths)),
        )

    def feasible(self) -> bool:
        decoded = self.decode()
        return decoded.fine == 0.0

    @property
    def cost(self) -> float:
        decoded = self.decode()
        return decoded.cost

    def decode(self) -> VRPDFDSolution:
        if self.__decoded is None:
            config = ProblemConfig.get_config()

            truck_paths_mapping, drone_paths_mapping = paths_from_flow_chained(
                self.truck_paths,
                self.drone_paths,
                truck_capacity=config.truck.capacity,
                drone_capacity=config.drone.capacity,
            )

            truck_paths: List[List[Tuple[int, float]]] = []
            for truck, path in enumerate(self.truck_paths):
                truck_paths.append([])
                _, ordered = config.path_order(path)

                for customer in ordered:
                    weight = truck_paths_mapping[truck][customer]
                    if customer == 0 or weight > 0.0:
                        truck_paths[-1].append((customer, weight))

            drone_paths: List[List[List[Tuple[int, float]]]] = []
            for drone, paths in enumerate(self.drone_paths):
                drone_paths.append([])
                for path_index, path in enumerate(paths):
                    drone_paths[-1].append([])
                    _, ordered = config.path_order(path)

                    for customer in ordered:
                        weight = drone_paths_mapping[drone][path_index][customer]
                        if customer == 0 or weight > 0.0:
                            drone_paths[-1][-1].append((customer, weight))

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
        config = ProblemConfig.get_config()

        assert config.mutation_rate is not None
        if random.random() < config.mutation_rate:
            random_customers = list(range(1, len(config.customers)))
            random.shuffle(random_customers)

            def remove_customer(paths: List[FrozenSet[int]]) -> VRPDFDIndividual:
                distances = [self.calculate_distance(path) for path in paths]
                path_index = weighted_random_choice(distances)
                for customer in random_customers:
                    if customer in paths[path_index]:
                        paths[path_index] = paths[path_index].difference([customer])
                        break

                return self.reconstruct(paths)

            def add_customer(paths: List[FrozenSet[int]]) -> VRPDFDIndividual:
                distances = [self.calculate_distance(path) for path in paths]
                path_index = weighted_random_choice([1 / d if d > 0.0 else 10 ** 9 for d in distances])
                for customer in random_customers:
                    if customer not in paths[path_index]:
                        paths[path_index] = paths[path_index].union([customer])
                        break

                return self.reconstruct(paths)

            def append_path(paths: List[FrozenSet[int]]) -> VRPDFDIndividual:
                result = self.reconstruct(paths)
                customer = random_customers[0]
                for customer in random_customers:
                    if 2 * config.distances[0][customer] <= config.drone.speed * config.drone.time_limit:
                        break

                return result.append_drone_path(random.randint(0, config.drones_count - 1), frozenset([0, customer]))

            factories = (
                remove_customer,
                add_customer,
                append_path,
            )
            factory = random.choice(factories)
            return factory(self.flatten())

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
    def after_generation_hook(cls, generation: int, last_improved: int, result: VRPDFDIndividual, population: FrozenSet[VRPDFDIndividual]) -> None:
        cls.genetic_algorithm_last_improved = last_improved
        for individual in population:
            individual.decode().bump_fine_coefficient()

        config = ProblemConfig.get_config()
        if config.logger is not None:
            config.logger.write(f"After generation #{generation + 1}:\nCost,Fine coefficient,Feasible,Individual\n")
            config.logger.write(
                "\n".join(f"{i.cost},{i.decode().fine_coefficient},{int(i.feasible())},\"{i}\"" for i in sorted(population, key=lambda x: x.cost))
            )
            config.logger.write("\n")

    @classmethod
    def initial(cls, *, solution_cls: Type[VRPDFDSolution], size: int) -> Set[VRPDFDIndividual]:
        config = ProblemConfig.get_config()

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

                flows = flows_with_demands(
                    size=network_size,
                    demands=network_demands,
                    capacities=network_capacities,
                    neighbors=network_neighbors,
                    source=network_source,
                    sink=network_sink,
                )
                if flows is None:
                    paths_per_drone += 1
                    continue

                truck_paths = [{0} for _ in range(config.trucks_count)]
                drone_paths = [[{0} for _ in range(paths_per_drone)] for _ in range(config.drones_count)]
                for vehicle, network_route in zip(
                    list(range(config.trucks_count)) + list(range(config.drones_count)) * paths_per_drone,
                    range(1, network_customers_offset),
                    strict=True,
                ):
                    if network_route < 1 + config.trucks_count:
                        path = truck_paths[vehicle]
                        capacity = config.truck.capacity
                    else:
                        path = drone_paths[vehicle][(network_route - config.trucks_count - 1) // config.drones_count]
                        capacity = config.drone.capacity

                    for customer, network_customer in enumerate(range(network_customers_offset, network_sink), start=1):
                        deliver = flows[network_route][network_customer]
                        if deliver > 0.0:
                            capacity -= deliver
                            path.add(customer)

                results.add(
                    cls(
                        solution_cls=solution_cls,
                        truck_paths=tuple(map(frozenset, truck_paths)),
                        drone_paths=tuple(tuple(map(frozenset, paths)) for paths in drone_paths),
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
        return self.__hash
