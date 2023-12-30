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

#include "../../utils/helpers.cpp"

namespace py = pybind11;

struct Customer
{
    const double low, high, w;
    static double total_low;

    Customer(double low, double high, double w) : low(low), high(high), w(w) {}
};

std::vector<Customer> customers;
double Customer::total_low = 0.0;

void set_customers(const std::vector<double> &low, const std::vector<double> &high, const std::vector<double> &w)
{
    unsigned size = low.size();
    if (size != high.size() || size != w.size())
    {
        throw std::runtime_error("low, high and w must have the same size");
    }

    customers.clear();
    Customer::total_low = 0.0;
    for (unsigned i = 0; i < size; i++)
    {
        customers.emplace_back(low[i], high[i], w[i]);
        Customer::total_low += low[i];
    }
}

unsigned sum(const std::vector<unsigned> &v)
{
    unsigned s = 0;
    for (auto i : v)
    {
        s += i;
    }

    return s;
}

std::pair<
    std::vector<std::map<unsigned, double>>,
    std::vector<std::vector<std::map<unsigned, double>>>>
paths_from_flow(
    const unsigned truck_paths_count,
    const std::vector<unsigned> &drone_paths_count,
    const std::vector<std::vector<double>> &flows,
    const std::vector<std::set<unsigned>> &neighbors)
{
#ifdef DEBUG
    std::cout << "Building solution from flow:" << std::endl;
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

std::pair<
    std::vector<std::map<unsigned, double>>,
    std::vector<std::vector<std::map<unsigned, double>>>>
paths_from_flow_chained(
    const std::vector<std::set<unsigned>> &truck_paths,
    const std::vector<std::vector<std::set<unsigned>>> &drone_paths,
    const double truck_capacity,
    const double drone_capacity)
{
    unsigned trucks_count = truck_paths.size(),
             drones_count = drone_paths.size(),
             customers_count = customers.size() - 1;
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
                    network_capacities[i][network_customer] = 1.0e+9;
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
                    network_capacities[i][network_customer] = 1.0e+9;
                    network_neighbors[i].insert(network_customer);
                }
            }
        }

        network_neighbors[network_source].insert(i);
    }

    for (unsigned i = network_customers_offset; i < network_sink; i++)
    {
        unsigned customer = i - network_customers_offset + 1;
        network_demands[i][network_sink] = customers[customer].low;
        network_capacities[i][network_sink] = customers[customer].high;
        network_neighbors[i].insert(network_sink);
        network_flow_weights[i][network_sink] = customers[customer].w;
    }

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

    double capacity_sum = 0;
    for (auto neighbor : network_neighbors[network_source])
    {
        capacity_sum += network_capacities[network_source][neighbor];
    }
    solver.stSupply(nodes[network_source], nodes[network_sink], capacity_sum);
    if (solver.run() == lemon::NetworkSimplex<lemon::SmartDigraph, double, double>::INFEASIBLE)
    {
        double l = Customer::total_low, r = capacity_sum;
        while (r - l > 1e-7)
        {
            double m = (l + r) / 2;

            solver.stSupply(nodes[network_source], nodes[network_sink], m);
            if (solver.run() == lemon::NetworkSimplex<lemon::SmartDigraph, double, double>::INFEASIBLE)
            {
                r = m;
            }
            else
            {
                l = m;
            }
        }
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

    return paths_from_flow(trucks_count, drone_paths_count, flows, network_neighbors);
}

PYBIND11_MODULE(cpp_utils, m)
{
    m.def(
        "set_customers", &set_customers,
        py::arg("low"), py::arg("high"), py::arg("w"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "paths_from_flow", &paths_from_flow,
        py::arg("truck_paths_count"), py::arg("drone_paths_count"), py::arg("flows"), py::arg("neighbors"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "paths_from_flow_chained", &paths_from_flow_chained,
        py::arg("truck_paths"), py::arg("drone_paths"), py::arg("truck_capacity"), py::arg("drone_capacity"),
        py::call_guard<py::gil_scoped_release>());
}
