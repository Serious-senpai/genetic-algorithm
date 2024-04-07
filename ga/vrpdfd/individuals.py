from __future__ import annotations

import itertools
import random
from collections import deque
from math import ceil
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

from tqdm import tqdm
if TYPE_CHECKING:
    from typing_extensions import Self

from .config import ProblemConfig
from .errors import PopulationInitializationException
from .utils import decode, educate, local_search
from ..abc import SingleObjectiveIndividual
from ..utils import LRUCache, weighted_random, weighted_random_choice
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
        "__stuck_penalty",
        "__decoded",
        "__educated",
        "__local_searched",
        "truck_paths",
        "drone_paths",
    )
    genetic_algorithm_last_improved: ClassVar[int] = 0
    genetic_algorithm_result: ClassVar[Optional[VRPDFDIndividual]] = None
    cache: ClassVar[LRUCache[Tuple[Tuple[FrozenSet[int], ...], Tuple[Tuple[FrozenSet[int], ...], ...]], VRPDFDIndividual]] = LRUCache(10000)
    if TYPE_CHECKING:
        __cls: Final[Type[VRPDFDSolution]]
        __stuck_penalty: float
        __decoded: Optional[VRPDFDSolution]
        __educated: Optional[VRPDFDIndividual]
        __local_searched: Optional[Tuple[Optional[VRPDFDIndividual], VRPDFDIndividual]]
        truck_paths: Final[Tuple[FrozenSet[int], ...]]
        drone_paths: Final[Tuple[Tuple[FrozenSet[int], ...], ...]]

    def __init__(
        self,
        *,
        solution_cls: Type[VRPDFDSolution],
        truck_paths: Tuple[FrozenSet[int], ...],
        drone_paths: Tuple[Tuple[FrozenSet[int], ...], ...],
        decoded: Optional[VRPDFDSolution] = None,
        local_searched: Optional[Tuple[Optional[VRPDFDIndividual], VRPDFDIndividual]] = None,
    ) -> None:
        self.__cls = solution_cls
        self.__stuck_penalty = 1.0
        self.__decoded = decoded
        self.__educated = None
        self.__local_searched = local_searched
        self.truck_paths = truck_paths
        self.drone_paths = drone_paths

    @classmethod
    def from_cache(
        cls,
        *,
        solution_cls: Type[VRPDFDSolution],
        truck_paths: Tuple[FrozenSet[int], ...],
        drone_paths: Sequence[Sequence[FrozenSet[int]]],
        decoded: Optional[VRPDFDSolution] = None,
        local_searched: Optional[Tuple[Optional[VRPDFDIndividual], VRPDFDIndividual]] = None,
    ) -> VRPDFDIndividual:
        tuplized_drone_paths = tuple(tuple(filter(lambda path: len(path) > 1, sorted(paths, key=tuple))) for paths in drone_paths)
        hashed = truck_paths, tuplized_drone_paths

        try:
            return cls.cache[hashed]

        except KeyError:
            unique = cls(
                solution_cls=solution_cls,
                truck_paths=truck_paths,
                drone_paths=tuplized_drone_paths,
                decoded=decoded,
                local_searched=local_searched,
            ).decode().encode(create_new=True)  # ensure uniqueness

            try:
                result = cls.cache[unique.truck_paths, unique.drone_paths]
            except KeyError:
                result = unique

            cls.cache[hashed] = cls.cache[unique.truck_paths, unique.drone_paths] = result
            return result

    @property
    def cls(self) -> Type[VRPDFDSolution]:
        return self.__cls

    @overload
    @staticmethod
    def calculate_distance(path: Sequence[int], /) -> float: ...

    @overload
    @staticmethod
    def calculate_distance(path: FrozenSet[int], /) -> float: ...

    @staticmethod
    def calculate_distance(path: Union[Sequence[int], FrozenSet[int]], /) -> float:
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

        return VRPDFDIndividual.from_cache(
            solution_cls=self.cls,
            truck_paths=tuple(truck_paths),
            drone_paths=drone_paths,
        )

    def append_drone_path(self, drone: int, path: FrozenSet[int]) -> VRPDFDIndividual:
        drone_paths = list(map(list, self.drone_paths))
        drone_paths[drone].append(path)
        return VRPDFDIndividual.from_cache(
            solution_cls=self.cls,
            truck_paths=self.truck_paths,
            drone_paths=drone_paths,
        )

    def append_drone_paths(self, *, drones: Sequence[int], paths: Sequence[FrozenSet[int]]) -> VRPDFDIndividual:
        drone_paths = list(map(list, self.drone_paths))
        for drone, path in zip(drones, paths, strict=True):
            drone_paths[drone].append(path)

        return VRPDFDIndividual.from_cache(
            solution_cls=self.cls,
            truck_paths=self.truck_paths,
            drone_paths=drone_paths,
        )

    def feasible(self) -> bool:
        decoded = self.decode()
        return decoded.feasible()

    @property
    def cost(self) -> float:
        decoded = self.decode()
        return decoded.cost

    @property
    def penalized_cost(self) -> float:
        return self.cost + self.__stuck_penalty

    def bump_stuck_penalty(self) -> None:
        config = ProblemConfig.get_config()
        self.__stuck_penalty *= config.stuck_penalty_increase_rate or 1.0
        self.__stuck_penalty = min(self.__stuck_penalty, 10 ** 9)

    def decode(self) -> VRPDFDSolution:
        if self.__decoded is None:
            config = ProblemConfig.get_config()

            truck_paths_mapping, drone_paths_mapping = decode(
                self.truck_paths,
                self.drone_paths,
            )

            truck_paths: List[List[Tuple[int, int]]] = []
            truck_distance = 0.0
            for truck, path in enumerate(self.truck_paths):
                truck_paths.append([])
                distance, ordered = config.path_order(path)
                truck_distance += distance

                for customer in ordered:
                    weight = round(truck_paths_mapping[truck][customer], 4)
                    if customer == 0 or weight > 0.0:
                        truck_paths[-1].append((customer, weight))

            drone_paths: List[List[List[Tuple[int, int]]]] = []
            drone_distance = 0.0
            for drone, paths in enumerate(self.drone_paths):
                drone_paths.append([])
                for path_index, path in enumerate(paths):
                    drone_paths[-1].append([])
                    distance, ordered = config.path_order(path)
                    drone_distance += distance

                    for customer in ordered:
                        weight = round(drone_paths_mapping[drone][path_index][customer], 4)
                        if customer == 0 or weight > 0.0:
                            drone_paths[-1][-1].append((customer, weight))

                    if len(drone_paths[-1][-1]) == 2:
                        drone_paths[-1].pop()

            self.__decoded = self.cls(
                truck_paths=tuple(map(tuple, truck_paths)),
                drone_paths=tuple(tuple(map(tuple, paths)) for paths in drone_paths),
                truck_distance=truck_distance,
                drone_distance=drone_distance,
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

        self_paths_first_index = frozenset(first)
        other_paths_second_index = frozenset(second)

        self_paths[first_index] = self_paths_first_index
        other_paths[second_index] = other_paths_second_index

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
                        new_path = paths[path_index].difference([customer])
                        paths[path_index] = new_path
                        break

                return self.reconstruct(paths)

            def add_customer(paths: List[FrozenSet[int]]) -> VRPDFDIndividual:
                distances = [self.calculate_distance(path) for path in paths]
                path_index = weighted_random_choice([1 / d if d > 0.0 else 10 ** 6 for d in distances])

                for customer in random_customers:
                    if customer not in paths[path_index]:
                        new_path = paths[path_index].union([customer])
                        paths[path_index] = new_path
                        break

                return self.reconstruct(paths)

            def append_path(_: List[FrozenSet[int]]) -> VRPDFDIndividual:
                customer = random_customers[0]
                for customer in random_customers:
                    if 2 * config.distances[0][customer] <= config.drone.speed * config.drone.time_limit:
                        break

                drone = random.randint(0, config.drones_count - 1)
                path = frozenset([0, customer])

                return self.append_drone_path(drone, path)

            factories = (
                remove_customer,
                add_customer,
                append_path,
            )
            factory = random.choice(factories)
            return factory(self.flatten())

        return self

    def educate(self) -> VRPDFDIndividual:
        if self.__educated is None:
            self.__educated = educate(self)

        return self.__educated

    @property
    def local_searched(self) -> bool:
        return self.__local_searched is not None

    def local_search(self, *, prioritize_feasible: bool = False) -> VRPDFDIndividual:
        if self.__local_searched is None:
            self.__local_searched = local_search(self)

        feasible, any = self.__local_searched
        if prioritize_feasible and feasible is not None:
            return feasible
        else:
            return any

    @classmethod
    def before_generation_hook(
        cls,
        *,
        generation: int,
        last_improved: int,
        result: VRPDFDIndividual,
        population: Set[VRPDFDIndividual],
        verbose: bool,
    ) -> None:
        result.cls.tune_fine_coefficients(population)

    @classmethod
    def after_generation_hook(
        cls,
        *,
        generation: int,
        last_improved: int,
        result: VRPDFDIndividual,
        population: Set[VRPDFDIndividual],
        verbose: bool,
    ) -> None:
        cls.genetic_algorithm_last_improved = last_improved
        cls.genetic_algorithm_result = result
        config = ProblemConfig.get_config()

        if config.logger is not None:
            best = min(population)
            worst = max(population)
            average_cost = sum(individual.cost for individual in population) / len(population)
            feasible_count = len(list(filter(lambda i: i.feasible(), population)))

            decoded = set(individual.decode() for individual in population)
            violations = (
                sum(s.violation[0] for s in decoded) / len(decoded),
                sum(s.violation[1] for s in decoded) / len(decoded),
            )

            config.logger.write(
                ",".join(
                    map(
                        str,
                        (
                            generation + 1,
                            result.cost,
                            best.cost,
                            worst.cost,
                            average_cost,
                            feasible_count,
                            *result.cls.fine_coefficient,
                            *violations,
                        ),
                    ),
                ),
            )
            config.logger.write("\n")

        if (
            config.reset_after is not None
            and generation != last_improved
            and (generation - last_improved) % config.reset_after == 0
        ):
            if config.logger is not None:
                config.logger.write("\"Increasing stuck penalty and applying local search\"\n")

            for individual in population:
                individual.bump_stuck_penalty()

            if result not in population:
                population.pop()
                population.add(result)

            local_searched = set(filter(lambda i: i.local_searched, population))
            not_local_searched = list(population.difference(local_searched))

            original_size = len(population)
            population.clear()
            population.update(local_searched)

            not_local_searched.sort()
            assert config.local_search_batch is not None
            to_local_search = set(
                map(
                    not_local_searched.__getitem__,
                    weighted_random(
                        [1 + 1 / (index + 1) for index in range(len(not_local_searched))],
                        count=min(config.local_search_batch, len(not_local_searched)),
                    ),
                ),
            )
            population.update(i for i in not_local_searched if i not in to_local_search)

            individuals: Union[tqdm[VRPDFDIndividual], Set[VRPDFDIndividual]] = to_local_search
            if verbose:
                individuals = tqdm(individuals, desc=f"Local search (#{generation + 1})", ascii=" █", colour="red")

            for individual in individuals:
                # 2-layer local search
                for states in itertools.product((True, False), repeat=2):
                    current = individual
                    for state in states:
                        current = current.local_search(prioritize_feasible=state)

                    population.add(current)

            population_sorted = sorted(population, key=lambda i: i.penalized_cost)
            population.clear()
            population.update(population_sorted[:original_size])

    @classmethod
    def selection(cls, *, population: FrozenSet[Self], size: int) -> Set[Self]:
        population_sorted = sorted(population, key=lambda i: i.penalized_cost)

        feasible = list(filter(lambda i: i.feasible(), population_sorted))
        infeasible = deque(filter(lambda i: not i.feasible(), population_sorted))

        while len(feasible) > size // 2 and len(feasible) + len(infeasible) > size:
            feasible.pop()

        while len(feasible) < size:
            feasible.append(infeasible.popleft())

        return set(feasible)

    @classmethod
    def parents_selection(cls, *, population: FrozenSet[Self]) -> Tuple[Self, Self]:
        population_sorted = sorted(population, key=lambda i: i.penalized_cost)
        first, second = weighted_random([1 + 1 / (2 * index + 1) for index in range(len(population))], count=2)
        return population_sorted[first], population_sorted[second]

    @classmethod
    def initial(cls, *, solution_cls: Type[VRPDFDSolution], size: int) -> Set[VRPDFDIndividual]:
        config = ProblemConfig.get_config()

        results: Set[VRPDFDIndividual] = set()
        all_customers = frozenset(range(len(config.customers)))
        try:
            for paths_per_drone in range(size // 3):
                results.add(
                    cls.from_cache(
                        solution_cls=solution_cls,
                        truck_paths=tuple(all_customers for _ in range(config.trucks_count)),
                        drone_paths=tuple(tuple(all_customers for _ in range(paths_per_drone)) for _ in range(config.drones_count)),
                    )
                )

            distances_to_port = [config.distances[0][customer] for customer in range(len(config.customers))]
            customers_sorted = sorted(range(1, len(config.customers)), key=distances_to_port.__getitem__)
            nearest = customers_sorted[:len(customers_sorted) // 2]
            furthest = customers_sorted[len(customers_sorted) // 2:]

            required_drone_paths = {customer: ceil(config.customers[customer].low / config.drone.capacity) for customer in nearest}
            truck_paths = frozenset([0, *furthest])
            all_drone_paths = [frozenset([0, customer]) for customer in nearest for _ in range(1 + required_drone_paths[customer])]

            for _ in range(size // 3):
                if len(results) == size:
                    break

                drone_paths: List[List[FrozenSet[int]]] = [[] for _ in range(config.drones_count)]
                for drone_path in all_drone_paths:
                    drone = random.randint(0, config.drones_count - 1)
                    drone_paths[drone].append(drone_path)

                results.add(
                    cls.from_cache(
                        solution_cls=solution_cls,
                        truck_paths=tuple(truck_paths for _ in range(config.trucks_count)),
                        drone_paths=drone_paths,
                    )
                )

            def merge_drone_paths(original: VRPDFDIndividual) -> VRPDFDIndividual:
                paths = original.flatten()

                drone_paths = paths[config.trucks_count:]
                try:
                    first, second = weighted_random([config.distances[0][sorted(path)[-1]] for path in drone_paths], count=2)
                except ValueError:
                    return original.mutate()

                drone_paths[first] = drone_paths[first].union(drone_paths[second])
                drone_paths[second] = frozenset([0])

                return original.reconstruct(paths[:config.trucks_count] + drone_paths)

            while len(results) < size:
                array = list(results)
                base = random.choice(array)
                results.add(merge_drone_paths(base))

            return results

        except BaseException as e:
            raise PopulationInitializationException(e) from e

    def __str__(self) -> str:
        def convert(paths: Tuple[FrozenSet[int], ...]) -> List[List[int]]:
            return [sorted(path) for path in paths]

        return f"VRPDFDIndividual(truck_paths={convert(self.truck_paths)!r}, drone_paths={list(map(convert, self.drone_paths))!r}, cost={self.cost})"

    def __repr__(self) -> str:
        return f"VRPDFDIndividual(solution_cls=VRPDFDSolution, truck_paths={self.truck_paths!r}, drone_paths={self.drone_paths!r})"

    def __hash__(self) -> int:
        return hash((self.truck_paths, self.drone_paths))
