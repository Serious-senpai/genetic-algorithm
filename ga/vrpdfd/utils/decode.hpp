#pragma once

#include <lemon/network_simplex.h>
#include <lemon/smart_graph.h>

#include "config.hpp"
#include "paths_from_flow.hpp"
#include "../../utils/helpers.hpp"

std::vector<std::vector<volume_t>> __solve_flow(
    const std::vector<std::vector<volume_t>> &network_demands,
    const std::vector<std::vector<volume_t>> &network_capacities,
    const std::vector<std::vector<volume_t>> &network_flow_weights,
    const std::vector<std::set<unsigned>> &network_neighbors,
    const unsigned network_source,
    const unsigned network_sink)
{
    unsigned network_size = network_neighbors.size();

    lemon::SmartDigraph graph;
    std::vector<lemon::SmartDigraph::Node> nodes;
    for (unsigned i = 0; i < network_size; i++)
    {
        nodes.push_back(graph.addNode());
    }

    std::vector<std::map<unsigned, lemon::SmartDigraph::Arc>> arcs_mapping(network_size);
    LemonMap<lemon::SmartDigraph::Arc, volume_t> demands_map, capacities_map, flow_weights_map;
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

    typedef lemon::NetworkSimplex<lemon::SmartDigraph, volume_t, volume_t> NetworkSimplex;

    NetworkSimplex solver(graph);
    solver.lowerMap(demands_map);
    solver.upperMap(capacities_map);
    solver.costMap(flow_weights_map);

    volume_t total_out = 0;
    for (auto neighbor : network_neighbors[network_source])
    {
        total_out += network_capacities[network_source][neighbor];
    }

    solver.stSupply(nodes[network_source], nodes[network_sink], total_out);
    if (solver.run() == NetworkSimplex::INFEASIBLE)
    {
        volume_t l = Customer::total_low, r = total_out;
        while (r - l > 1)
        {
            volume_t m = (l + r) / 2;

            solver.stSupply(nodes[network_source], nodes[network_sink], m);
            if (solver.run() == NetworkSimplex::INFEASIBLE)
            {
                r = m;
            }
            else
            {
                l = m;
            }
        }

        solver.stSupply(nodes[network_source], nodes[network_sink], l);
        solver.run();
    }

    LemonMap<lemon::SmartDigraph::Arc, volume_t> flows_mapping;
    solver.flowMap(flows_mapping);

    std::vector<std::vector<volume_t>> flows(network_size, std::vector<volume_t>(network_size, 0));
    for (unsigned i = 0; i < network_size; i++)
    {
        for (auto neighbor : network_neighbors[i])
        {
            flows[i][neighbor] = flows_mapping[arcs_mapping[i][neighbor]];
        }
    }

    return flows;
}

solution decode(
    const std::vector<std::set<unsigned>> &truck_paths,
    const std::vector<std::vector<std::set<unsigned>>> &drone_paths,
    const volume_t truck_capacity,
    const volume_t drone_capacity)
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

    std::vector<std::vector<volume_t>> network_demands(network_size, std::vector<volume_t>(network_size, 0)),
        network_capacities(network_size, std::vector<volume_t>(network_size, 0)),
        network_flow_weights(network_size, std::vector<volume_t>(network_size, 0));
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
        network_sink);

    return paths_from_flow(trucks_count, drone_paths_count, flows, network_neighbors);
}
