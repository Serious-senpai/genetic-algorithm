#pragma once

#include <algorithm>
#include <set>
#include <vector>

#include "jaccard_distance.hpp"
#include "helpers.hpp"

std::vector<unsigned> crowding_distance_sort(const std::vector<std::vector<std::set<unsigned>>> &sets, const unsigned k = 2)
{
    unsigned n = sets.size();
    if (k >= n)
    {
        throw std::invalid_argument(format("k = %d >= n = %d", k, n));
    }

    std::vector<std::vector<double>> distances(n, std::vector<double>(n, 0.0));
    for (unsigned i = 0; i < n; i++)
    {
        for (unsigned j = 1; j < n; j++)
        {
            double distance = 0.0;

            unsigned compare_size = std::min(sets[i].size(), sets[j].size());
            for (unsigned k = 0; k < compare_size; k++)
            {
                distance += jaccard_distance(sets[i][k], sets[j][k]);
            }
            for (unsigned k = compare_size; k < sets[i].size(); k++)
            {
                distance += sets[i][k].size();
            }
            for (unsigned k = compare_size; k < sets[j].size(); k++)
            {
                distance += sets[j][k].size();
            }

            distances[i][j] = distances[j][i] = distance;
        }
    }

    std::vector<double> nearest_sums(n, 0.0);
    for (unsigned i = 0; i < n; i++)
    {
        std::vector<double> nearest(distances[i]);
        std::sort(nearest.begin(), nearest.end());

        for (unsigned j = 1; j <= k; j++) // The nearest set is the set itself, so we start from 1
        {
            nearest_sums[i] += nearest[j];
        }
    }

    std::vector<unsigned> sorted;
    for (unsigned i = 0; i < n; i++)
    {
        sorted.push_back(i);
    }
    std::sort(
        sorted.begin(), sorted.end(),
        [&nearest_sums](const unsigned &a, const unsigned &b)
        { return nearest_sums[a] > nearest_sums[b]; });

    return sorted;
}