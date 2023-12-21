#pragma once

#include <deque>
#include <set>
#include <stdexcept>
#include <vector>

#include "helpers.cpp"
#include "maximum_flow.cpp"

std::pair<std::pair<double, double>, std::vector<unsigned>> __weighted_flow(
    const unsigned size,
    const std::vector<std::vector<double>> &capacities,
    const std::vector<std::set<unsigned>> &neighbors,
    const std::vector<std::vector<double>> &flow_weights,
    const unsigned source,
    const unsigned sink)
{
    double sink_flow = 0.0;
    std::vector<unsigned> parents(size, size);
    std::vector<double> max_total_weights(size, -1.0);

    std::deque<std::pair<std::pair<unsigned, std::set<unsigned>>, std::pair<double, double>>> queue = {{{source, {}}, {1.0e+9, 0.0}}};
    while (!queue.empty())
    {
        auto data = queue.front();
        queue.pop_front();

        unsigned current = data.first.first;
        std::set<unsigned> visited = data.first.second;
        visited.insert(current);

        double flow = data.second.first, total_weights = data.second.second;
        if (flow > 0.0)
        {
            for (auto neighbor : neighbors[current])
            {
                if (!visited.count(neighbor))
                {
                    double new_flow = std::min(flow, capacities[current][neighbor]),
                           new_total_weights = total_weights + flow_weights[current][neighbor];
                    if (new_flow > 0.0 && new_total_weights > max_total_weights[neighbor])
                    {
                        max_total_weights[neighbor] = new_total_weights;
                        parents[neighbor] = current;
                        if (neighbor == sink)
                        {
                            sink_flow = new_flow;
                        }
                        else
                        {
                            queue.push_back({{neighbor, visited}, {new_flow, new_total_weights}});
                        }
                    }
                }
            }
        }
    }

    return {{max_total_weights[sink] * sink_flow, sink_flow}, parents};
}

std::pair<double, std::vector<std::vector<double>>> maximum_weighted_flow_no_checking(
    const unsigned size,
    const std::vector<std::vector<double>> &capacities,
    const std::vector<std::set<unsigned>> &neighbors,
    const std::vector<std::vector<double>> &flow_weights,
    const unsigned source,
    const unsigned sink)
{
    std::vector<std::vector<double>> complete_capacities(size, std::vector<double>(size));
    for (unsigned i = 0; i < size; i++)
    {
        for (auto j : neighbors[i])
        {
            complete_capacities[i][j] = capacities[i][j];
            complete_capacities[j][i] = 0.0;
        }
    }

    std::vector<std::set<unsigned>> complete_neighbors(size);
    for (unsigned i = 0; i < size; i++)
    {
        for (auto j : neighbors[i])
        {
            complete_neighbors[i].insert(j);
            complete_neighbors[j].insert(i);
        }
    }

    std::vector<std::vector<double>> complete_flow_weights(size, std::vector<double>(size));
    for (unsigned i = 0; i < size; i++)
    {
        for (auto j : neighbors[i])
        {
            complete_flow_weights[i][j] = flow_weights[i][j];
            complete_flow_weights[j][i] = -flow_weights[i][j];
        }
    }

    double result = 0.0;
    std::vector<std::vector<double>> results(size, std::vector<double>(size));
    while (true)
    {
        auto propagate = __weighted_flow(size, complete_capacities, complete_neighbors, complete_flow_weights, source, sink);
        double new_weighted_flow = propagate.first.first, new_flow = propagate.first.second;
        if (new_flow == 0.0)
        {
            break;
        }

        auto parents = propagate.second;

        unsigned current = sink;
        while (current != source)
        {
            unsigned previous = parents[current];
            complete_capacities[previous][current] -= new_flow;
            complete_capacities[current][previous] += new_flow;

            results[previous][current] += new_flow;
            results[current][previous] -= new_flow; // results[current][previous] = -results[previous][current];

            current = previous;
        }

        result += new_weighted_flow;
    }

    for (unsigned i = 0; i < size; i++)
    {
        for (unsigned j = 0; j < size; j++)
        {
            results[i][j] = std::max(0.0, results[i][j]);
        }
    }

    return {result, results};
}

void check_constraints(
    const unsigned size,
    const std::vector<std::vector<double>> &capacities,
    const std::vector<std::set<unsigned>> &neighbors,
    const std::vector<std::vector<double>> &flow_weights,
    const unsigned source,
    const unsigned sink)
{
    check_constraints(size, capacities, neighbors, source, sink);
    for (unsigned i = 0; i < size; i++)
    {
        for (unsigned j = 0; j < size; j++)
        {
            if (neighbors[i].count(j) == 0 && flow_weights[i][j] > 0.0)
            {
                throw std::invalid_argument(format("flow_weights[%d][%d] = %lf, but edge (%d, %d) isn't present", i, j, flow_weights[i][j], i, j));
            }
        }
    }

    if (flow_weights.size() != size)
    {
        throw std::invalid_argument(format("Received flow_weights matrix with %d rows, expected %d", flow_weights.size(), size));
    }
    for (unsigned i = 0; i < size; i++)
    {
        if (flow_weights[i].size() != size)
        {
            throw std::invalid_argument(format("flow_weights[%d] has size %d, expected %d", i, flow_weights[i].size(), size));
        }

        for (unsigned j = 0; j < size; j++)
        {
            if (flow_weights[i][j] < 0.0)
            {
                throw std::invalid_argument(format("Negative flow_weights[%d][%d] = %lf is not supported", i, j, flow_weights[i][j]));
            }
        }
    }
}

std::pair<double, std::vector<std::vector<double>>> maximum_weighted_flow(
    unsigned size,
    std::vector<std::vector<double>> &capacities,
    std::vector<std::set<unsigned>> &neighbors,
    std::vector<std::vector<double>> &flow_weights,
    unsigned source,
    unsigned sink)
{
    check_constraints(size, capacities, neighbors, flow_weights, source, sink);
    return maximum_weighted_flow_no_checking(size, capacities, neighbors, flow_weights, source, sink);
}
