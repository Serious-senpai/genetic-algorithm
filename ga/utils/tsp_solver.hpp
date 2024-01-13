#pragma once

#include <optional>
#include <vector>

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wregister"

#include <lemon/full_graph.h>
#include <lemon/insertion_tsp.h>
#include <lemon/opt2_tsp.h>
#include <lemon/path.h>

#pragma GCC diagnostic pop

#include "helpers.hpp"

const unsigned HELD_KARP_LIMIT = 17;

std::pair<double, unsigned> __held_karp_solve(
    const unsigned bitmask,
    const unsigned city,
    const std::vector<std::vector<double>> &distances,
    std::vector<std::vector<std::pair<double, unsigned>>> &dp,
    const unsigned level = 0)
{
    if (dp[bitmask][city].first != -1.0)
    {
        return dp[bitmask][city];
    }

    if (bitmask & (1u << city))
    {
        return dp[bitmask][city] = __held_karp_solve(bitmask - (1u << city), city, distances, dp);
    }

    if (bitmask & 1)
    {
        return dp[bitmask][city] = __held_karp_solve(bitmask - 1, city, distances, dp);
    }

    unsigned n = distances.size();
    std::pair<double, unsigned> result = {-1.0, n};
    for (unsigned i = 1; i < n; i++)
    {
        if (bitmask & (1u << i))
        {
            auto before = __held_karp_solve(bitmask - (1u << i), i, distances, dp, level + 1);
            double d = before.first + distances[i][city];
            if (d < result.first || result.first == -1.0)
            {
                result = {d, i};
            }
        }
    }

    return dp[bitmask][city] = result;
}

std::pair<double, std::vector<unsigned>> __held_karp(const std::vector<std::vector<double>> &distances, const unsigned first)
{
    // https://en.wikipedia.org/wiki/Held-Karp_algorithm
    unsigned n = distances.size();
    std::vector<std::vector<std::pair<double, unsigned>>> dp(1u << n, std::vector<std::pair<double, unsigned>>(n, {-1.0, n}));
    for (unsigned end = 1; end < n; end++)
    {
        dp[0][end] = {distances[0][end], 0};
    }

    unsigned path_end = 0, bitmask = (1u << n) - 2;
    std::pair<double, unsigned> distance_end = {1.0e+9, -1};
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

    bitmask -= (1u << path_end);
    std::vector<unsigned> path = {0, path_end};
    while (bitmask > 0)
    {
        auto r = __held_karp_solve(bitmask, path_end, distances, dp);
        path_end = r.second;
        bitmask -= 1u << path_end;
        path.push_back(path_end);
    }

    rotate_to_first(path, first);
    return {distance_end.first, path};
}

std::pair<double, std::vector<unsigned>> tsp_solver(
    const std::vector<std::pair<double, double>> &cities,
    const unsigned first = 0,
    const std::optional<std::vector<unsigned>> &heuristic_hint = std::optional<std::vector<unsigned>>())
{
    unsigned n = cities.size();
    if (n == 0)
    {
        throw std::invalid_argument("Empty TSP map");
    }

    if (n == 1)
    {
        std::vector<unsigned> path = {0};
        rotate_to_first(path, first);
        return {0.0, path};
    }

    std::vector<std::vector<double>> distances(n, std::vector<double>(n, 0.0));
    for (unsigned i = 0; i < n; i++)
    {
        for (unsigned j = i + 1; j < n; j++)
        {
            double dx = cities[i].first - cities[j].first,
                   dy = cities[i].second - cities[j].second;
            distances[i][j] = distances[j][i] = distance(dx, dy);
        }
    }

    if (n == 2)
    {
        std::vector<unsigned> path = {0, 1};
        rotate_to_first(path, first);
        return {2 * distances[0][1], path};
    }

    if (n == 3)
    {
        std::vector<unsigned> path = {0, 1, 2};
        rotate_to_first(path, first);
        return {distances[0][1] + distances[1][2] + distances[2][0], path};
    }

    if (n <= HELD_KARP_LIMIT)
    {
        return __held_karp(distances, first);
    }
    else
    {
        lemon::Path<lemon::FullGraph> initial;
        lemon::FullGraph graph(n);
        LemonMap<lemon::FullGraph::Edge, double> costs;
        for (unsigned i = 0; i < n; i++)
        {
            for (unsigned j = 0; j < n; j++)
            {
                auto edge = graph.edge(graph(i), graph(j));
                costs.set(edge, distances[i][j]);
            }
        }

        if (heuristic_hint.has_value())
        {
            if (heuristic_hint.value().size() != n)
            {
                throw std::invalid_argument(format("Hint size %d does not match n = %d", heuristic_hint.value().size(), n));
            }

            for (unsigned i = 0; i < n; i++)
            {
                auto arc = graph.arc(graph(heuristic_hint.value()[i]), graph(heuristic_hint.value()[(i + 1) % n]));
                initial.addBack(arc);
            }
        }
        else
        {
            lemon::InsertionTsp<LemonMap<lemon::FullGraph::Edge, double>> tsp(graph, costs);
            tsp.run();

            tsp.tour(initial);
        }

        lemon::Opt2Tsp<LemonMap<lemon::FullGraph::Edge, double>> tsp(graph, costs);
        tsp.run(initial);

        std::vector<lemon::FullGraph::Node> path(n);
        tsp.tourNodes(path.begin());

        std::vector<unsigned> result;
        for (auto node : path)
        {
            result.push_back(graph.id(node));
        }

        double result_cost = 0.0;
        for (unsigned i = 0; i < n; i++)
        {
            result_cost += distances[result[i]][result[(i + 1) % n]];
        }

        rotate_to_first(result, first);
        return {result_cost, result};
    }
}
