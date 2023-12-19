#pragma once

#include <algorithm>
#include <vector>

#include "helpers.cpp"

double pow_2(double x)
{
    return x * x;
}

std::pair<double, std::vector<unsigned>> fake_tsp_solver(std::vector<std::pair<double, double>> &cities, unsigned first = 0)
{
    unsigned n = cities.size();

    std::vector<unsigned> result(n);
    for (unsigned i = 0; i < n; i++)
    {
        result[i] = i;
    }

    std::shuffle(result.begin(), result.end(), rng);
    unsigned first_index = std::find(result.begin(), result.end(), first) - result.begin();
    std::swap(result[0], result[first_index]);

    double distance = 0.0;
    for (unsigned i = 0; i < n; i++)
    {
        unsigned current = result[i], next = result[(i + 1) % n];
        distance += sqrt_impl(pow_2(cities[current].first - cities[next].first) + pow_2(cities[current].second - cities[next].second));
    }

    return {distance, result};
}