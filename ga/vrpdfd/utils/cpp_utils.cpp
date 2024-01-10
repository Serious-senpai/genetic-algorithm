#include <algorithm>
#include <deque>
#include <map>
#include <set>
#include <vector>
#ifdef DEBUG
#include <iostream>
#endif

#include <lemon/network_simplex.h>
#include <lemon/smart_graph.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "../../utils/helpers.hpp"

namespace py = pybind11;
const double TOLERANCE = 1e-5;
typedef std::pair<std::vector<std::set<unsigned>>, std::vector<std::vector<std::set<unsigned>>>> individual;
typedef std::pair<std::vector<std::map<unsigned, double>>, std::vector<std::vector<std::map<unsigned, double>>>> solution;

struct Customer
{
    const double low, high, w, x, y;
    static double total_low, total_high;
    static std::vector<Customer> customers;
    static std::vector<std::vector<double>> distances;
    static std::vector<std::vector<unsigned>> nearests;

    Customer(double low, double high, double w, double x, double y) : low(low), high(high), w(w), x(x), y(y) {}

    std::pair<double, double> location() const
    {
        return {x, y};
    }
};

std::vector<Customer> Customer::customers;
std::vector<std::vector<double>> Customer::distances;
std::vector<std::vector<unsigned>> Customer::nearests;

double Customer::total_low = 0.0, Customer::total_high = 0.0;

void set_customers(
    const std::vector<double> &low,
    const std::vector<double> &high,
    const std::vector<double> &w,
    const std::vector<double> &x,
    const std::vector<double> &y)
{
    unsigned size = low.size();
    if (size != high.size() || size != w.size() || size != x.size() || size != y.size())
    {
        throw std::runtime_error("low, high, w, x and y must have the same size");
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
}

solution paths_from_flow(
    const unsigned truck_paths_count,
    const std::vector<unsigned> &drone_paths_count,
    const std::vector<std::vector<double>> &flows,
    const std::vector<std::set<unsigned>> &neighbors)
{
#ifdef DEBUG
    std::cout << "Building paths from flow" << std::endl;
    for (unsigned i = 0; i < flows.size(); i++)
    {
        for (unsigned j = 0; j < flows[i].size(); j++)
        {
            std::cout << flows[i][j] << " ";
        }
        std::cout << std::endl;
    }
#endif

    unsigned network_trucks_offset = 1,
             network_drones_offset = network_trucks_offset + truck_paths_count,
             network_customers_offset = network_trucks_offset + truck_paths_count + sum(drone_paths_count);

    std::vector<std::map<unsigned, double>> truck_paths;
    for (unsigned network_truck = network_trucks_offset; network_truck < network_drones_offset; network_truck++)
    {
        truck_paths.emplace_back();
        auto path = --truck_paths.end();
        path->emplace(0, 0.0);

        for (auto network_customer : neighbors[network_truck])
        {
            unsigned customer = network_customer - network_customers_offset + 1;
            path->emplace(customer, flows[network_truck][network_customer]);
        }
    }

    std::vector<std::vector<std::map<unsigned, double>>> drone_paths(drone_paths_count.size());
    for (unsigned network_drone = network_drones_offset; network_drone < network_customers_offset; network_drone++)
    {
        unsigned drone = 0, from_offset = network_drone - network_drones_offset;
        while (from_offset >= drone_paths_count[drone])
        {
            from_offset -= drone_paths_count[drone];
            drone++;
        }

        drone_paths[drone].emplace_back();
        auto path = --drone_paths[drone].end();
        path->emplace(0, 0.0);

        for (auto network_customer : neighbors[network_drone])
        {
            unsigned customer = network_customer - network_customers_offset + 1;
            path->emplace(customer, flows[network_drone][network_customer]);
        }
    }

    return {truck_paths, drone_paths};
}

std::vector<std::vector<double>> __solve_flow(
    const std::vector<std::vector<double>> &network_demands,
    const std::vector<std::vector<double>> &network_capacities,
    const std::vector<std::vector<double>> &network_flow_weights,
    const std::vector<std::set<unsigned>> &network_neighbors,
    const unsigned network_source,
    const unsigned network_sink)
{
    unsigned network_size = network_neighbors.size();

#ifdef DEBUG
    std::cout << "Solving flow with network size " << network_size << std::endl;
    std::cout << "network_demands:" << std::endl;
    for (unsigned i = 0; i < network_size; i++)
    {
        for (unsigned j = 0; j < network_size; j++)
        {
            std::cout << network_demands[i][j] << " ";
        }
        std::cout << std::endl;
    }

    std::cout << "network_capacities:" << std::endl;
    for (unsigned i = 0; i < network_size; i++)
    {
        for (unsigned j = 0; j < network_size; j++)
        {
            std::cout << network_capacities[i][j] << " ";
        }
        std::cout << std::endl;
    }

    std::cout << "network_flow_weights:" << std::endl;
    for (unsigned i = 0; i < network_size; i++)
    {
        for (unsigned j = 0; j < network_size; j++)
        {
            std::cout << network_flow_weights[i][j] << " ";
        }
        std::cout << std::endl;
    }

    std::cout << "network_neighbors:" << std::endl;
    for (unsigned i = 0; i < network_size; i++)
    {
        std::cout << i << ": ";
        for (auto neighbor : network_neighbors[i])
        {
            std::cout << neighbor << " ";
        }
        std::cout << std::endl;
    }
#endif

    lemon::SmartDigraph graph;
    std::vector<lemon::SmartDigraph::Node> nodes;
    for (unsigned i = 0; i < network_size; i++)
    {
        nodes.push_back(graph.addNode());
    }

    std::vector<std::map<unsigned, lemon::SmartDigraph::Arc>> arcs_mapping(network_size);
    LemonMap<lemon::SmartDigraph::Arc, double> demands_map, capacities_map, flow_weights_map;
    for (unsigned i = 0; i < network_size; i++)
    {
        for (auto neighbor : network_neighbors[i])
        {
            auto arc = graph.addArc(nodes[i], nodes[neighbor]);

            arcs_mapping[i][neighbor] = arc;
            demands_map.set(arc, network_demands[i][neighbor]);
            capacities_map.set(arc, network_capacities[i][neighbor]);
            flow_weights_map.set(arc, -network_flow_weights[i][neighbor]); // we aim to maximize weighted flow
        }
    }

    lemon::NetworkSimplex<lemon::SmartDigraph, double, double> solver(graph);
    solver.lowerMap(demands_map);
    solver.upperMap(capacities_map);
    solver.costMap(flow_weights_map);

    double total_out = 0;
    for (auto neighbor : network_neighbors[network_source])
    {
        total_out += network_capacities[network_source][neighbor];
    }

    solver.stSupply(nodes[network_source], nodes[network_sink], total_out);
    if (solver.run() == lemon::NetworkSimplex<lemon::SmartDigraph, double, double>::INFEASIBLE)
    {
#ifdef DEBUG
        std::cout << "Unable to find a feasible flow with " << total_out << std::endl;
#endif

        double total_demands = 0;
        for (unsigned i = 0; i < network_size; i++)
        {
            for (auto neighbor : network_neighbors[i])
            {
                total_demands += network_demands[i][neighbor];
            }
        }

        double l = total_demands, r = total_out;
        while (r - l > TOLERANCE)
        {
            double m = (l + r) / 2;

            solver.stSupply(nodes[network_source], nodes[network_sink], m);
            if (solver.run() == lemon::NetworkSimplex<lemon::SmartDigraph, double, double>::INFEASIBLE)
            {
#ifdef DEBUG
                std::cout << "Total flow " << m << " INFEASIBLE" << std::endl;
#endif
                r = m;
            }
            else
            {
#ifdef DEBUG
                std::cout << "Total flow " << m << " OK" << std::endl;
#endif
                l = m;
            }
        }

        solver.stSupply(nodes[network_source], nodes[network_sink], l);
        solver.run();
    }

    LemonMap<lemon::SmartDigraph::Arc, double> flows_mapping;
    solver.flowMap(flows_mapping);

    std::vector<std::vector<double>> flows(network_size, std::vector<double>(network_size, 0.0));
    for (unsigned i = 0; i < network_size; i++)
    {
        for (auto neighbor : network_neighbors[i])
        {
            flows[i][neighbor] = flows_mapping[arcs_mapping[i][neighbor]];
        }
    }

#ifdef DEBUG
    std::cout << "Found flow with cost = " << solver.totalCost() << std::endl;
    std::cout << "Resulting flow:" << std::endl;
    for (unsigned i = 0; i < network_size; i++)
    {
        for (unsigned j = 0; j < network_size; j++)
        {
            std::cout << flows[i][j] << " ";
        }
        std::cout << std::endl;
    }
#endif

    return flows;
}

solution paths_from_flow_chained(
    const std::vector<std::set<unsigned>> &truck_paths,
    const std::vector<std::vector<std::set<unsigned>>> &drone_paths,
    const double truck_capacity,
    const double drone_capacity)
{
    unsigned trucks_count = truck_paths.size(),
             drones_count = drone_paths.size(),
             customers_count = Customer::customers.size() - 1;
    std::vector<unsigned> drone_paths_count(drones_count);
    for (unsigned i = 0; i < drones_count; i++)
    {
        drone_paths_count[i] = drone_paths[i].size();
    }

    unsigned network_trucks_offset = 1,
             network_drones_offset = network_trucks_offset + trucks_count,
             network_customers_offset = network_trucks_offset + trucks_count + sum(drone_paths_count),
             network_source = 0, network_sink = network_customers_offset + customers_count,
             network_size = network_sink + 1;

    std::vector<std::vector<double>> network_demands(network_size, std::vector<double>(network_size, 0.0)),
        network_capacities(network_size, std::vector<double>(network_size, 0.0)),
        network_flow_weights(network_size, std::vector<double>(network_size, 0.0));
    std::vector<std::set<unsigned>> network_neighbors(network_size);

    for (unsigned i = 1; i < network_customers_offset; i++)
    {
        if (i < network_trucks_offset + trucks_count)
        {
            network_capacities[network_source][i] = truck_capacity;

            unsigned truck = i - network_trucks_offset;
            for (auto customer : truck_paths[truck])
            {
                if (customer != 0)
                {
                    unsigned network_customer = network_customers_offset + customer - 1;
                    network_capacities[i][network_customer] = Customer::total_high;
                    network_neighbors[i].insert(network_customer);
                }
            }
        }
        else
        {
            network_capacities[network_source][i] = drone_capacity;

            unsigned drone = 0, from_offset = i - network_drones_offset;
            while (from_offset >= drone_paths_count[drone])
            {
                from_offset -= drone_paths_count[drone];
                drone++;
            }

            for (auto customer : drone_paths[drone][from_offset])
            {
                if (customer != 0)
                {
                    unsigned network_customer = network_customers_offset + customer - 1;
                    network_capacities[i][network_customer] = Customer::total_high;
                    network_neighbors[i].insert(network_customer);
                }
            }
        }

        network_neighbors[network_source].insert(i);
    }

    for (unsigned i = network_customers_offset; i < network_sink; i++)
    {
        unsigned customer = i - network_customers_offset + 1;
        network_demands[i][network_sink] = Customer::customers[customer].low;
        network_capacities[i][network_sink] = Customer::customers[customer].high;
        network_neighbors[i].insert(network_sink);
        network_flow_weights[i][network_sink] = Customer::customers[customer].w;
    }

    auto flows = __solve_flow(
             network_demands,
             network_capacities,
             network_flow_weights,
             network_neighbors,
             network_source,
             network_sink),
         last_flow = flows;

    while (true)
    {
        for (unsigned i = 0; i < network_size; i++)
        {
            for (unsigned j = 0; j < network_size; j++)
            {
                network_demands[i][j] -= last_flow[i][j];
                network_capacities[i][j] -= last_flow[i][j];

                network_demands[i][j] = std::max(0.0, network_demands[i][j]);
                network_capacities[i][j] = std::max(0.0, network_capacities[i][j]);
            }
        }

#ifdef DEBUG
        std::cout << "Extending flow" << std::endl;
#endif

        double extend_flow = 0.0;
        last_flow = __solve_flow(
            network_demands,
            network_capacities,
            network_flow_weights,
            network_neighbors,
            network_source,
            network_sink);
        for (unsigned i = 0; i < network_size; i++)
        {
            for (unsigned j = 0; j < network_size; j++)
            {
                extend_flow += last_flow[i][j];
                flows[i][j] += last_flow[i][j];
            }
        }

#ifdef DEBUG
        std::cout << "Flow extended by " << extend_flow << std::endl;
#endif

        if (extend_flow < TOLERANCE)
        {
            break;
        }
    }

    return paths_from_flow(trucks_count, drone_paths_count, flows, network_neighbors);
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

bool feasible(const py::object &individual)
{
    return py::cast<bool>(individual.attr("feasible")());
}

py::object local_search(
    const std::vector<std::vector<unsigned>> &truck_paths,
    const std::vector<std::vector<std::vector<unsigned>>> &drone_paths)
{
    py::object py_VRPDFDSolution = py::module::import("ga.vrpdfd.solutions").attr("VRPDFDSolution"),
               py_from_cache = py::module::import("ga.vrpdfd.individuals").attr("VRPDFDIndividual").attr("from_cache"),
               py_self = py_from_cache(
                   py::arg("solution_cls") = py_VRPDFDSolution,
                   py::arg("truck_paths") = truck_paths_cast(truck_paths),
                   py::arg("drone_paths") = drone_paths_cast(drone_paths)),
               py_result = py_self;

    unsigned trucks_count = truck_paths.size(),
             drones_count = drone_paths.size();

#ifdef DEBUG
    std::cout << "Local search for " << trucks_count << " truck(s) and " << drones_count << " drone(s)" << std::endl;
#endif

    auto copy = [&truck_paths, drone_paths]()
    {
        std::vector<std::set<unsigned>> new_truck_paths;
        for (auto &path : truck_paths)
        {
            new_truck_paths.push_back(std::set<unsigned>(path.begin(), path.end()));
        }

        std::vector<std::vector<std::set<unsigned>>> new_drone_paths;
        for (auto &paths : drone_paths)
        {
            std::vector<std::set<unsigned>> new_paths;
            for (auto &path : paths)
            {
                new_paths.push_back(std::set<unsigned>(path.begin(), path.end()));
            }

            new_drone_paths.push_back(new_paths);
        }

        return std::make_pair(new_truck_paths, new_drone_paths);
    };

    std::set<unsigned> in_truck_paths = {0}, in_drone_paths = {0};
    for (unsigned i = 0; i < trucks_count; i++)
    {
        for (auto customer : truck_paths[i])
        {
            in_truck_paths.insert(customer);
        }
    }
    for (unsigned i = 0; i < drones_count; i++)
    {
        for (unsigned j = 0; j < drone_paths[i].size(); j++)
        {
            for (auto customer : drone_paths[i][j])
            {
                in_drone_paths.insert(customer);
            }
        }
    }

    // Attempt to add absent customers
    std::vector<unsigned> absent;
    for (unsigned customer = 1; customer < Customer::customers.size(); customer++)
    {
        if (!in_truck_paths.count(customer) && !in_drone_paths.count(customer))
        {
            absent.push_back(customer);
        }
    }

    for (unsigned truck = 0; truck < trucks_count; truck++)
    {
        auto [new_truck_paths, new_drone_paths] = copy();
        new_truck_paths[truck].insert(absent.begin(), absent.end());

        py_result = std::min(
            py_result,
            py_from_cache(
                py::arg("solution_cls") = py_VRPDFDSolution,
                py::arg("truck_paths") = truck_paths_cast(new_truck_paths),
                py::arg("drone_paths") = drone_paths_cast(new_drone_paths)));
    }

    std::vector<unsigned> new_path = absent;
    new_path.push_back(0);

    auto py_new_path = py_frozenset(new_path.begin(), new_path.end());
    for (unsigned drone = 0; drone < drones_count; drone++)
    {
        for (unsigned path = 0; path < drone_paths[drone].size(); path++)
        {
            auto [new_truck_paths, new_drone_paths] = copy();
            new_drone_paths[drone][path].insert(absent.begin(), absent.end());

            py_result = std::min(
                py_result,
                py_from_cache(
                    py::arg("solution_cls") = py_VRPDFDSolution,
                    py::arg("truck_paths") = truck_paths_cast(new_truck_paths),
                    py::arg("drone_paths") = drone_paths_cast(new_drone_paths)));
        }

        py_result = std::min(py_result, py_self.attr("append_drone_path")(drone, py_new_path));
    }

    // Remove elements in both sets
    std::set<unsigned> in_both;
    for (auto customer : in_truck_paths)
    {
        if (in_drone_paths.count(customer))
        {
            in_both.insert(customer);
        }
    }

    auto remove_intersection = [&in_both](std::set<unsigned> &customers)
    {
        for (auto iter = customers.begin(); iter != customers.end();)
        {
            if (in_both.count(*iter))
            {
                iter = customers.erase(iter);
            }
            else
            {
                iter++;
            }
        }
    };
    remove_intersection(in_truck_paths);
    remove_intersection(in_drone_paths);

    // Swap all customers in truck paths with all customers in drone paths
    {
        auto [new_truck_paths, new_drone_paths] = copy();
        for (auto &path : new_truck_paths)
        {
            for (auto customer : in_truck_paths)
            {
                path.erase(customer);
                path.insert(in_drone_paths.begin(), in_drone_paths.end());
            }
        }
        for (auto &paths : new_drone_paths)
        {
            for (auto &path : paths)
            {
                for (auto customer : in_drone_paths)
                {
                    path.erase(customer);
                    path.insert(in_truck_paths.begin(), in_truck_paths.end());
                }
            }
        }

        py_result = std::min(
            py_result,
            py_from_cache(
                py::arg("solution_cls") = py_VRPDFDSolution,
                py::arg("truck_paths") = truck_paths_cast(new_truck_paths),
                py::arg("drone_paths") = drone_paths_cast(new_drone_paths)));
    }

    std::vector<unsigned> in_truck_paths_vector(in_truck_paths.begin(), in_truck_paths.end()),
        in_drone_paths_vector(in_drone_paths.begin(), in_drone_paths.end());

    // Brute-force swap
    for (unsigned truck_i = 0; truck_i < in_truck_paths_vector.size(); truck_i++)
    {
        for (unsigned truck_j = truck_i; truck_j < in_truck_paths_vector.size(); truck_j++) // truck_i = truck_j -> Only swap 1 customer from truck paths
        {
            for (unsigned drone_i = 0; drone_i < in_drone_paths_vector.size(); drone_i++)
            {
                for (unsigned drone_j = drone_i; drone_j < in_drone_paths_vector.size(); drone_j++) // drone_i = drone_j -> Only swap 1 customer from drone paths
                {
                    auto [new_truck_paths, new_drone_paths] = copy();

                    for (auto &path : new_truck_paths)
                    {
                        path.erase(in_truck_paths_vector[truck_i]);
                        path.erase(in_truck_paths_vector[truck_j]);
                        path.insert(in_drone_paths_vector[drone_i]);
                        path.insert(in_drone_paths_vector[drone_j]);
                    }

                    for (auto &paths : new_drone_paths)
                    {
                        for (auto &path : paths)
                        {
                            path.erase(in_drone_paths_vector[drone_i]);
                            path.erase(in_drone_paths_vector[drone_j]);
                            path.insert(in_truck_paths_vector[truck_i]);
                            path.insert(in_truck_paths_vector[truck_j]);
                        }
                    }

                    py::object py_new_individual = py_from_cache(
                        py::arg("solution_cls") = py_VRPDFDSolution,
                        py::arg("truck_paths") = truck_paths_cast(new_truck_paths),
                        py::arg("drone_paths") = drone_paths_cast(new_drone_paths));

                    py_result = std::min(py_result, py_new_individual);
                }
            }
        }
    }

    return py_result.attr("educate")();
}

PYBIND11_MODULE(cpp_utils, m)
{
    m.def(
        "set_customers", &set_customers,
        py::arg("low"), py::arg("high"), py::arg("w"), py::arg("x"), py::arg("y"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "paths_from_flow", &paths_from_flow,
        py::arg("truck_paths_count"), py::arg("drone_paths_count"), py::arg("flows"), py::arg("neighbors"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "paths_from_flow_chained", &paths_from_flow_chained,
        py::arg("truck_paths"), py::arg("drone_paths"), py::arg("truck_capacity"), py::arg("drone_capacity"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "local_search", &local_search,
        py::arg("truck_paths"), py::arg("drone_paths")); // Do not release the GIL
}
