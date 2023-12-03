#pragma once

#include <vector>

#include "helpers.cpp"

const unsigned HELD_KARP_LIMIT = 17;

std::pair<double, unsigned> __held_karp_solve(
    unsigned bitmask,
    unsigned city,
    std::vector<std::vector<double>> &distances,
    std::vector<std::vector<std::pair<double, unsigned>>> &dp, unsigned level = 0)
{
    if (dp[bitmask][city].first != -1.0)
    {
        return dp[bitmask][city];
    }

    if (bitmask & (1 << city))
    {
        return dp[bitmask][city] = __held_karp_solve(bitmask - (1 << city), city, distances, dp);
    }

    if (bitmask & 1)
    {
        return dp[bitmask][city] = __held_karp_solve(bitmask - 1, city, distances, dp);
    }

    unsigned n = distances.size();
    std::pair<double, unsigned> result = {-1.0, n};
    for (unsigned i = 1; i < n; i++)
    {
        if (bitmask & (1 << i))
        {
            auto before = __held_karp_solve(bitmask - (1 << i), i, distances, dp, level + 1);
            double d = before.first + distances[i][city];
            if (d < result.first || result.first == -1.0)
            {
                result = {d, i};
            }
        }
    }

    return dp[bitmask][city] = result;
}

std::pair<double, std::vector<unsigned>> __held_karp(std::vector<std::vector<double>> &distances)
{
    // https://en.wikipedia.org/wiki/Held-Karp_algorithm
    unsigned n = distances.size();
    std::vector<std::vector<std::pair<double, unsigned>>> dp(1 << n, std::vector<std::pair<double, unsigned>>(n, {-1.0, n}));
    for (unsigned end = 1; end < n; end++)
    {
        dp[0][end] = {distances[0][end], 0};
    }

    unsigned path_end = -1, bitmask = (1 << n) - 2;
    std::pair<double, unsigned> distance_end = {1.0e+18, -1};
    for (unsigned end = 1; end < n; end++)
    {
        auto r = __held_karp_solve(bitmask, end, distances, dp);
        r.first += distances[0][end];
        if (r < distance_end)
        {
            distance_end = r;
            path_end = end;
        }
    }

    bitmask -= (1 << path_end);
    std::vector<unsigned> path = {0, path_end};
    while (bitmask > 0)
    {
        auto r = __held_karp_solve(bitmask, path_end, distances, dp);
        path_end = r.second;
        bitmask -= 1 << path_end;
        path.push_back(path_end);
    }

    return {distance_end.first, path};
}

std::pair<double, std::vector<unsigned>> tsp_solver(std::vector<std::pair<double, double>> &cities)
{
    unsigned n = cities.size();
    if (n == 0)
    {
        throw std::invalid_argument("Empty TSP map");
    }

    if (n == 1)
    {
        return {0.0, {0}};
    }

    std::vector<std::vector<double>> distances(n, std::vector<double>(n, 0.0));
    for (unsigned i = 0; i < n; i++)
    {
        for (unsigned j = i + 1; j < n; j++)
        {
            double dx = cities[i].first - cities[j].first,
                   dy = cities[i].second - cities[j].second;
            distances[i][j] = distances[j][i] = sqrt_impl(dx * dx + dy * dy);
        }
    }

    if (n == 2)
    {
        return {2 * distances[0][1], {0, 1}};
    }

    if (n == 3)
    {
        return {distances[0][1] + distances[1][2] + distances[2][0], {0, 1, 2}};
    }

    if (n <= HELD_KARP_LIMIT)
    {
        return __held_karp(distances);
    }
    else
    {
        throw std::invalid_argument(format("Not yet supported n = %d > %d", n, HELD_KARP_LIMIT));
    }
}
