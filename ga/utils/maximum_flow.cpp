#pragma once

#include <deque>
#include <set>
#include <stdexcept>
#include <vector>

#include "helpers.cpp"

double __flow(
    unsigned size,
    std::vector<std::vector<double>> &capacities,
    std::vector<std::set<unsigned>> &neighbors,
    unsigned source,
    unsigned sink,
    std::vector<unsigned> &parents)
{
    std::fill(parents.begin(), parents.end(), size);
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
                    return next_flow;
                }

                queue.push_back({neighbor, next_flow});
            }
        }
    }

    return 0.0;
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
        for (unsigned j = 0; j < size; j++)
        {
            complete_capacities[i][j] += capacities[i][j];
            complete_capacities[j][i] -= capacities[i][j];
        }
    }

    double result = 0.0;
    std::vector<unsigned> parents(size);
    while (double new_flow = __flow(size, complete_capacities, neighbors, source, sink, parents))
    {
        unsigned current = sink;
        while (current != source)
        {
            unsigned previous = parents[current];
            complete_capacities[previous][current] -= new_flow;
            complete_capacities[current][previous] += new_flow;
            current = previous;
        }

        result += new_flow;
    }

    std::vector<std::vector<double>> results(size, std::vector<double>(size));
    for (unsigned i = 0; i < size; i++)
    {
        for (auto j : neighbors[i])
        {
            results[i][j] = capacities[i][j] - complete_capacities[i][j];
        }
    }

    return {result, results};
}

std::pair<double, std::vector<std::vector<double>>> maximum_flow(
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

    return maximum_flow_no_checking(size, capacities, neighbors, source, sink);
}