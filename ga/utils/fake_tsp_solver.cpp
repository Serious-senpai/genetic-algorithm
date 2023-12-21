#pragma once

#include <algorithm>
#include <vector>

#include "helpers.cpp"

double pow_2(const double x)
{
    return x * x;
}

std::pair<double, std::vector<unsigned>> fake_tsp_solver(const std::vector<std::pair<double, double>> &cities, const unsigned first = 0)
{
    unsigned n = cities.size();

    std::vector<unsigned> result(n);
    for (unsigned i = 0; i < n; i++)
    {
        result[i] = i;
    }

    std::shuffle(result.begin(), result.end(), rng);
    rotate_to_first(result, first);

    double distance = 0.0;
    for (unsigned i = 0; i < n; i++)
    {
        unsigned current = result[i], next = result[(i + 1) % n];
        distance += sqrt_impl(pow_2(cities[current].first - cities[next].first) + pow_2(cities[current].second - cities[next].second));
    }

    return {distance, result};
}
