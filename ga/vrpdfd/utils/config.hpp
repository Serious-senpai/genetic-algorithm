#pragma once

#include <algorithm>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <vector>
#ifdef DEBUG
#include <iostream>
#endif

#include "../../utils/helpers.hpp"
#include "../../utils/lru_cache.hpp"
#include "../../utils/tsp_solver.hpp"

typedef int volume_t;
typedef std::pair<std::vector<std::set<unsigned>>, std::vector<std::vector<std::set<unsigned>>>> individual;
typedef std::pair<std::vector<std::map<unsigned, volume_t>>, std::vector<std::vector<std::map<unsigned, volume_t>>>> solution;

struct Customer
{
    const volume_t low, high, w;
    const double x, y;
    const std::pair<double, double> location;
    static volume_t total_low, total_high;
    static std::vector<Customer> customers;
    static std::vector<std::vector<double>> distances;
    static std::vector<std::vector<unsigned>> nearests;

    Customer(volume_t low, volume_t high, volume_t w, double x, double y)
        : low(low), high(high), w(w), x(x), y(y),
          location(std::make_pair(x, y)) {}
};

struct Vehicle
{
    const volume_t capacity;
    const double distance_limit, cost_coefficient;
    static Vehicle *truck, *drone;

    Vehicle(volume_t capacity, double distance_limit, double cost_coefficient)
        : capacity(capacity),
          distance_limit(distance_limit),
          cost_coefficient(cost_coefficient) {}
};

volume_t Customer::total_low, Customer::total_high;
std::vector<Customer> Customer::customers;
std::vector<std::vector<double>> Customer::distances;
std::vector<std::vector<unsigned>> Customer::nearests;

Vehicle *Vehicle::truck = nullptr, *Vehicle::drone = nullptr;

lru_cache<std::set<unsigned>, std::pair<double, std::vector<unsigned>>> path_order_cache(100000);

void setup_path_cache(unsigned capacity)
{
    path_order_cache.clear();
    path_order_cache.capacity = capacity;
}

void setup(
    const std::vector<volume_t> &low,
    const std::vector<volume_t> &high,
    const std::vector<volume_t> &w,
    const std::vector<double> &x,
    const std::vector<double> &y,
    const double truck_distance_limit,
    const double drone_distance_limit,
    const double truck_capacity,
    const double drone_capacity,
    const double truck_cost_coefficient,
    const double drone_cost_coefficient)
{
    unsigned size = low.size();
    if (size != high.size() || size != w.size() || size != x.size() || size != y.size())
    {
        throw std::runtime_error("low, high, w, x and y must have the same size");
    }

    if (low[0] != 0 || high[0] != 0 || w[0] != 0)
    {
        throw std::runtime_error("The first customer must be the depot");
    }

    Customer::customers.clear();
    Customer::total_low = Customer::total_high = 0.0;
    for (unsigned i = 0; i < size; i++)
    {
        Customer::customers.emplace_back(low[i], high[i], w[i], x[i], y[i]);
        Customer::total_low += low[i];
        Customer::total_high += high[i];
    }

    Customer::distances.clear();
    Customer::distances.resize(size, std::vector<double>(size, 0.0));
    for (unsigned i = 0; i < size; i++)
    {
        for (unsigned j = i; j < size; j++)
        {
            Customer::distances[i][j] = Customer::distances[j][i] = distance(
                Customer::customers[i].x - Customer::customers[j].x,
                Customer::customers[i].y - Customer::customers[j].y);
        }
    }

    Customer::nearests.clear();
    for (unsigned i = 0; i < size; i++)
    {
        std::vector<unsigned> all(size);
        std::iota(all.begin(), all.end(), 0);
        std::sort(
            all.begin(), all.end(),
            [i](unsigned a, unsigned b)
            {
                return Customer::distances[i][a] < Customer::distances[i][b];
            });

        Customer::nearests.push_back(all);
    }

    if (Vehicle::truck != nullptr)
    {
        delete Vehicle::truck;
    }
    Vehicle::truck = new Vehicle(truck_capacity, truck_distance_limit, truck_cost_coefficient);

    if (Vehicle::drone != nullptr)
    {
        delete Vehicle::drone;
    }
    Vehicle::drone = new Vehicle(drone_capacity, drone_distance_limit, drone_cost_coefficient);

    // Clear path cache
    setup_path_cache(path_order_cache.capacity);
}

std::map<std::string, unsigned> path_cache_info()
{
    return path_order_cache.to_json();
}

std::pair<double, std::vector<unsigned>> path_order(const std::set<unsigned> &path)
{
    auto cached = path_order_cache.get(path);
    if (cached.has_value())
    {
        return cached.value();
    }

    std::vector<std::pair<double, double>> coordinates;
    std::vector<unsigned> path_vector(path.begin(), path.end()); // depot at customers[0]
    for (auto customer : path_vector)
    {
        coordinates.push_back(Customer::customers[customer].location);
    }

    auto result = tsp_solver(coordinates);
    std::vector<unsigned> result_path(path_vector.size() + 1);
    for (unsigned i = 1; i < path_vector.size(); i++) // Let first and last elements be the depot
    {
        result_path[i] = path_vector[result.second[i]];
    }

    result.second = result_path;
    path_order_cache.set(path, result);

    return result;
}

individual get_paths(const py::object &py_individual)
{
    auto truck_paths = py::cast<std::vector<std::set<unsigned>>>(py_individual.attr("truck_paths"));
    auto drone_paths = py::cast<std::vector<std::vector<std::set<unsigned>>>>(py_individual.attr("drone_paths"));

    return std::make_pair(truck_paths, drone_paths);
}

std::pair<
    std::vector<std::vector<std::pair<unsigned int, volume_t>>>,
    std::vector<std::vector<std::vector<std::pair<unsigned int, volume_t>>>>>
get_decoded_paths(const py::object &py_solution)
{
    auto truck_paths = py::cast<std::vector<std::vector<std::pair<unsigned, volume_t>>>>(py_solution.attr("truck_paths"));
    auto drone_paths = py::cast<std::vector<std::vector<std::vector<std::pair<unsigned, volume_t>>>>>(py_solution.attr("drone_paths"));

    return std::make_pair(truck_paths, drone_paths);
}

bool feasible(const py::object &py_individual)
{
    return py::cast<bool>(py_individual.attr("feasible")());
}

template <typename _PathContainer>
py::tuple truck_paths_cast(const std::vector<_PathContainer> &truck_paths)
{
    py::tuple py_truck_paths(truck_paths.size());
    for (unsigned i = 0; i < truck_paths.size(); i++)
    {
        py_truck_paths[i] = py_frozenset(truck_paths[i].begin(), truck_paths[i].end());
    }

    return py_truck_paths;
}

template <typename _PathContainer>
py::tuple drone_paths_cast(const std::vector<std::vector<_PathContainer>> &drone_paths)
{
    py::tuple py_drone_paths(drone_paths.size());
    for (unsigned i = 0; i < drone_paths.size(); i++)
    {
        py::tuple py_drone_paths_i(drone_paths[i].size());
        for (unsigned j = 0; j < drone_paths[i].size(); j++)
        {
            py_drone_paths_i[j] = py_frozenset(drone_paths[i][j].begin(), drone_paths[i][j].end());
        }

        py_drone_paths[i] = py_drone_paths_i;
    }

    return py_drone_paths;
}

py::object from_cache(
    const std::vector<std::set<unsigned int>> &new_truck_paths,
    const std::vector<std::vector<std::set<unsigned int>>> &new_drone_paths)
{
    auto py_VRPDFDSolution = py::module::import("ga.vrpdfd").attr("VRPDFDSolution"),
         py_from_cache = py::module::import("ga.vrpdfd").attr("VRPDFDIndividual").attr("from_cache");

    auto result = py_from_cache(
        py::arg("solution_cls") = py_VRPDFDSolution,
        py::arg("truck_paths") = truck_paths_cast(new_truck_paths),
        py::arg("drone_paths") = drone_paths_cast(new_drone_paths));

    return result;
}

py::object append_drone_path(
    const py::object &py_individual,
    const unsigned drone,
    const py::frozenset &py_new_path)
{
    return py_individual.attr("append_drone_path")(drone, py_new_path);
}

double drone_path_profit(const std::vector<std::pair<unsigned, volume_t>> &path)
{
    double revenue = 0.0;
    for (auto &[customer, volume] : path)
    {
        revenue += Customer::customers[customer].w * volume;
    }

    double cost = 0.0;
    for (unsigned i = 0; i < path.size() - 1; i++)
    {
        cost += Customer::distances[path[i].first][path[i + 1].first];
    }
    cost *= Vehicle::drone->cost_coefficient;

    return revenue - cost;
}
