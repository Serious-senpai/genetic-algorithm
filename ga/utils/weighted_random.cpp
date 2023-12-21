#pragma once

#include <set>
#include <stdexcept>
#include <vector>

#include "helpers.cpp"

std::vector<unsigned> weighted_random(const std::vector<double> &weights, const unsigned count = 1)
{
    unsigned n = weights.size();
    if (count > n)
    {
        throw std::invalid_argument(format("Argument count exceeded the number of weights (%d > %d)", count, weights.size()));
    }

    double sum_weight = 0.0;
    for (auto weight : weights)
    {
        sum_weight += weight;
        if (weight < 0.0)
        {
            throw std::invalid_argument(format("Received weight %lf < 0.0", weight));
        }
    }

    std::set<unsigned> results;

    unsigned limit = std::min(count, n - count);
    while (results.size() < limit)
    {
        double value = random_double(0.0, sum_weight);
        for (unsigned index = 0; index < n; index++)
        {
            if (!results.count(index))
            {
                value -= weights[index];
                if (value <= 0.0)
                {
                    results.insert(index);
                    sum_weight -= weights[index];
                    break;
                }
            }
        }
    }

    if (limit == count)
    {
        return std::vector<unsigned>(results.begin(), results.end());
    }

    std::vector<unsigned> returns;
    for (unsigned index = 0; index < n; index++)
    {
        if (!results.count(index))
        {
            returns.push_back(index);
        }
    }

    return returns;
}
