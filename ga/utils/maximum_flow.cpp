#pragma once

#include <deque>
#include <set>
#include <stdexcept>
#include <vector>

#include "helpers.cpp"

std::pair<double, std::vector<unsigned>> __flow(
    unsigned size,
    std::vector<std::vector<double>> &capacities,
    std::vector<std::set<unsigned>> &neighbors,
    unsigned source,
    unsigned sink)
{
    std::vector<unsigned> parents(size, size);
    std::deque<std::pair<unsigned, double>> queue = {{source, 1.0e+18}};
    while (!queue.empty())
    {
        auto data = queue.front();
        queue.pop_front();

        unsigned current = data.first;
        double flow = data.second;

        for (auto neighbor : neighbors[current])
        {
            if (parents[neighbor] == size && capacities[current][neighbor] > 0.0)
            {
                parents[neighbor] = current;
                double next_flow = std::min(flow, capacities[current][neighbor]);
                if (neighbor == sink)
                {
                    return {next_flow, parents};
                }

                queue.push_back({neighbor, next_flow});
            }
        }
    }

    return {0.0, {}};
}

std::pair<double, std::vector<std::vector<double>>> maximum_flow_no_checking(
    unsigned size,
    std::vector<std::vector<double>> &capacities,
    std::vector<std::set<unsigned>> &neighbors,
    unsigned source,
    unsigned sink)
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

    double result = 0.0;
    std::vector<std::vector<double>> results(size, std::vector<double>(size));
    while (true)
    {
        auto propagate = __flow(size, complete_capacities, complete_neighbors, source, sink);
        double new_flow = propagate.first;
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

        result += new_flow;
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
    unsigned size,
    std::vector<std::vector<double>> &capacities,
    std::vector<std::set<unsigned>> &neighbors,
    unsigned source,
    unsigned sink)
{
    if (capacities.size() != size)
    {
        throw std::invalid_argument(format("Received capacities matrix with %d rows, expected %d", capacities.size(), size));
    }
    for (unsigned i = 0; i < size; i++)
    {
        if (capacities[i].size() != size)
        {
            throw std::invalid_argument(format("capacities[%d] has size %d, expected %d", i, capacities[i].size(), size));
        }

        for (unsigned j = 0; j < size; j++)
        {
            if (neighbors[i].count(j) == 0 && capacities[i][j] > 0.0)
            {
                throw std::invalid_argument(format("capacities[%d][%d] = %lf, but edge (%d, %d) isn't present", i, j, capacities[i][j], i, j));
            }
        }
    }

    if (neighbors.size() != size)
    {
        throw std::invalid_argument(format("Received neighbors list with %d sets, expected %d", capacities.size(), size));
    }
    for (unsigned i = 0; i < size; i++)
    {
        for (auto neighbor : neighbors[i])
        {
            if (neighbor < 0 || neighbor > size - 1 || neighbor == source)
            {
                throw std::invalid_argument(format("Node %d has invalid neighbor %d", i, neighbor));
            }
        }
    }
    if (neighbors[sink].size() > 0)
    {
        throw std::invalid_argument(format("Sink mustn't have any outgoing edges, currently %d", neighbors[sink].size()));
    }
}

std::pair<double, std::vector<std::vector<double>>> maximum_flow(
    unsigned size,
    std::vector<std::vector<double>> &capacities,
    std::vector<std::set<unsigned>> &neighbors,
    unsigned source,
    unsigned sink)
{
    check_constraints(size, capacities, neighbors, source, sink);
    return maximum_flow_no_checking(size, capacities, neighbors, source, sink);
}