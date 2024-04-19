#pragma once

#include "config.hpp"

const unsigned TRUCK_TRADE_LIMIT = 4u;
const unsigned DRONE_TRADE_LIMIT = 4u;

struct extra_info
{
    const py::object py_individual;
    const unsigned trucks_count;
    const unsigned drones_count;
    const std::vector<std::set<unsigned int>> truck_paths;
    const std::vector<std::vector<std::set<unsigned int>>> drone_paths;
    const std::set<unsigned> in_truck_paths;
    const std::set<unsigned> in_drone_paths;
    const std::set<unsigned> in_truck_paths_only;
    const std::set<unsigned> in_drone_paths_only;
    const std::set<unsigned> absent;

    static extra_info from_individual(const py::object &py_individual);
};

extra_info extra_info::from_individual(const py::object &py_individual)
{
    const auto [truck_paths, drone_paths] = get_paths(py_individual);

    unsigned trucks_count = truck_paths.size(),
             drones_count = drone_paths.size();

    std::set<unsigned> in_truck_paths = {0}, in_drone_paths = {0};
    for (unsigned i = 0; i < trucks_count; i++)
    {
        for (auto customer : truck_paths[i])
        {
            in_truck_paths.insert(customer);
        }
    }
    for (unsigned i = 0; i < drones_count; i++)
    {
        for (unsigned j = 0; j < drone_paths[i].size(); j++)
        {
            for (auto customer : drone_paths[i][j])
            {
                in_drone_paths.insert(customer);
            }
        }
    }

    std::set<unsigned> in_both;
    for (auto customer : in_truck_paths)
    {
        if (in_drone_paths.count(customer))
        {
            in_both.insert(customer);
        }
    }

    std::set<unsigned> in_truck_paths_only;
    for (auto c : in_truck_paths)
    {
        if (!in_both.count(c))
        {
            in_truck_paths_only.insert(c);
        }
    }

    std::set<unsigned> in_drone_paths_only;
    for (auto c : in_drone_paths)
    {
        if (!in_both.count(c))
        {
            in_drone_paths_only.insert(c);
        }
    }

    std::set<unsigned> absent;
    for (unsigned customer = 1; customer < Customer::customers.size(); customer++)
    {
        if (!in_truck_paths.count(customer) && !in_drone_paths.count(customer))
        {
            absent.insert(customer);
        }
    }

    return extra_info{
        py_individual, trucks_count, drones_count, truck_paths, drone_paths,
        in_truck_paths, in_drone_paths, in_truck_paths_only, in_drone_paths_only, absent};
}

void local_search_1(
    const extra_info &extra,
    std::pair<std::optional<py::object>, py::object> &result)
{
    auto mutable_truck_paths = extra.truck_paths;
    for (unsigned truck = 0; truck < extra.trucks_count; truck++)
    {
        // Temporary modify the individual
        mutable_truck_paths[truck].insert(extra.absent.begin(), extra.absent.end());

        py::object py_new_individual = from_cache(mutable_truck_paths, extra.drone_paths);

        if (feasible(py_new_individual))
        {
            result.first = std::min(result.first.value_or(py_new_individual), py_new_individual);
        }
        result.second = std::min(result.second, py_new_individual);

        // Restore the individual
        for (auto c : extra.absent)
        {
            mutable_truck_paths[truck].erase(c);
        }
    }
}

void local_search_2(
    const extra_info &extra,
    std::pair<std::optional<py::object>, py::object> &result)
{
    std::vector<unsigned> new_path(extra.absent.begin(), extra.absent.end());
    new_path.push_back(0);

    auto py_new_path = py_frozenset(new_path.begin(), new_path.end());
    auto mutable_drone_paths = extra.drone_paths;
    for (unsigned drone = 0; drone < extra.drones_count; drone++)
    {
        for (unsigned path = 0; path < extra.drone_paths[drone].size(); path++)
        {
            // Temporary modify the individual
            mutable_drone_paths[drone][path].insert(extra.absent.begin(), extra.absent.end());

            py::object py_new_individual = from_cache(extra.truck_paths, mutable_drone_paths);

            if (feasible(py_new_individual))
            {
                result.first = std::min(result.first.value_or(py_new_individual), py_new_individual);
            }
            result.second = std::min(result.second, py_new_individual);

            // Restore the individual
            for (auto c : extra.absent)
            {
                mutable_drone_paths[drone][path].erase(c);
            }
        }

        py::object py_new_individual = append_drone_path(extra.py_individual, drone, py_new_path);

        if (feasible(py_new_individual))
        {
            result.first = std::min(result.first.value_or(py_new_individual), py_new_individual);
        }
        result.second = std::min(result.second, py_new_individual);
    }
}

void local_search_3(
    const extra_info &extra,
    std::pair<std::optional<py::object>, py::object> &result)
{
    for (auto customer : extra.in_truck_paths)
    {
        for (unsigned drone = 0; drone < extra.drones_count; drone++)
        {
            auto new_drone_paths = extra.drone_paths;

            new_drone_paths[drone].push_back({0, customer});
            py::object py_new_individual = from_cache(extra.truck_paths, new_drone_paths);
            if (feasible(py_new_individual))
            {
                result.first = std::min(result.first.value_or(py_new_individual), py_new_individual);
            }
            result.second = std::min(result.second, py_new_individual);

            new_drone_paths[drone].push_back({0, customer});
            py::object py_new_new_individual = from_cache(extra.truck_paths, new_drone_paths);

            while (py_new_new_individual < py_new_individual && feasible(py_new_new_individual))
            {
                py_new_individual = py_new_new_individual;
                new_drone_paths[drone].push_back({0, customer});
                py_new_new_individual = from_cache(extra.truck_paths, new_drone_paths);

                result.first = std::min(result.first.value_or(py_new_individual), py_new_individual); // Feasibility guaranteed
                result.second = std::min(result.second, py_new_individual);
            }
        }
    }
}

void local_search_4(
    const extra_info &extra,
    std::pair<std::optional<py::object>, py::object> &result)
{
    auto mutable_drone_paths = extra.drone_paths;
    for (unsigned drone = 0; drone < extra.drones_count; drone++)
    {
        for (unsigned path = 0; path < extra.drone_paths[drone].size(); path++)
        {
            if (extra.drone_paths[drone][path].size() < 3) // Require at least 3 elements: the depot and 2+ customers
            {
                continue;
            }

            // Split
            for (auto customer : extra.drone_paths[drone][path])
            {
                if (customer != 0)
                {
                    // Temporary modify the individual
                    mutable_drone_paths[drone][path].erase(customer);
                    mutable_drone_paths[drone].push_back({0, customer});

                    py::object py_new_individual = from_cache(extra.truck_paths, mutable_drone_paths);

                    if (feasible(py_new_individual))
                    {
                        result.first = std::min(result.first.value_or(py_new_individual), py_new_individual);
                    }
                    result.second = std::min(result.second, py_new_individual);

                    // Restore the individual
                    mutable_drone_paths[drone][path].insert(customer);
                    mutable_drone_paths[drone].pop_back();
                }
            }
        }
    }
}

void local_search_5(
    const extra_info &extra,
    std::pair<std::optional<py::object>, py::object> &result)
{
    std::vector<unsigned> in_truck_paths_only_vector(extra.in_truck_paths_only.begin(), extra.in_truck_paths_only.end()),
        in_drone_paths_only_vector(extra.in_drone_paths_only.begin(), extra.in_drone_paths_only.end());

    // Calculate improved ratios
    std::vector<std::vector<double>> improved_ratio(2);
    improved_ratio[0].resize(in_truck_paths_only_vector.size(), -1);
    improved_ratio[1].resize(in_drone_paths_only_vector.size(), -1);

    {
        std::vector<double> truck_paths_distance;
        for (auto &path : extra.truck_paths)
        {
            truck_paths_distance.push_back(path_order(path).first);
        }

        std::vector<std::vector<double>> drone_paths_distance(extra.drones_count);
        for (unsigned drone = 0; drone < extra.drones_count; drone++)
        {
            for (auto &path : extra.drone_paths[drone])
            {
                drone_paths_distance[drone].push_back(path_order(path).first);
            }
        }

        auto mutable_truck_paths = extra.truck_paths;
        for (unsigned truck_i = 0; truck_i < in_truck_paths_only_vector.size(); truck_i++)
        {
            double total_ratio = 0.0;
            for (unsigned truck = 0; truck < extra.trucks_count; truck++)
            {
                bool erased = mutable_truck_paths[truck].erase(in_truck_paths_only_vector[truck_i]);
                total_ratio += path_order(mutable_truck_paths[truck]).first / truck_paths_distance[truck];

                if (erased)
                {
                    mutable_truck_paths[truck].insert(in_truck_paths_only_vector[truck_i]);
                }
            }

            improved_ratio[0][truck_i] = total_ratio / extra.trucks_count;
        }

        unsigned total_drone_paths = 0;
        for (unsigned drone = 0; drone < extra.drones_count; drone++)
        {
            total_drone_paths += extra.drone_paths[drone].size();
        }

        auto mutable_drone_paths = extra.drone_paths;
        for (unsigned drone_i = 0; drone_i < in_drone_paths_only_vector.size(); drone_i++)
        {
            double total_ratio = 0.0;
            for (unsigned drone = 0; drone < extra.drones_count; drone++)
            {
                for (unsigned path = 0; path < mutable_drone_paths[drone].size(); path++)
                {
                    bool erased = mutable_drone_paths[drone][path].erase(in_drone_paths_only_vector[drone_i]);
                    total_ratio += path_order(mutable_drone_paths[drone][path]).first / drone_paths_distance[drone][path];

                    if (erased)
                    {
                        mutable_drone_paths[drone][path].insert(in_drone_paths_only_vector[drone_i]);
                    }
                }
            }

            improved_ratio[1][drone_i] = total_ratio / total_drone_paths;
        }
    }

#ifdef DEBUG
    std::cout << "Improved ratio:" << std::endl;
    for (unsigned i = 0; i < 2; i++)
    {
        for (auto r : improved_ratio[i])
        {
            std::cout << r << " ";
        }
        std::cout << std::endl;
    }
#endif

    // Sort customers according to improved ratios
    std::map<unsigned, double> improved_ratio_map;
    for (unsigned i = 0; i < in_truck_paths_only_vector.size(); i++)
    {
        improved_ratio_map[in_truck_paths_only_vector[i]] = improved_ratio[0][i];
    }
    for (unsigned i = 0; i < in_drone_paths_only_vector.size(); i++)
    {
        improved_ratio_map[in_drone_paths_only_vector[i]] = improved_ratio[1][i];
    }
    std::sort(
        in_truck_paths_only_vector.begin(), in_truck_paths_only_vector.end(),
        [&improved_ratio_map](unsigned a, unsigned b)
        {
            return improved_ratio_map[a] < improved_ratio_map[b];
        });
    std::sort(
        in_drone_paths_only_vector.begin(), in_drone_paths_only_vector.end(),
        [&improved_ratio_map](unsigned a, unsigned b)
        {
            return improved_ratio_map[a] < improved_ratio_map[b];
        });

    while (in_truck_paths_only_vector.size() > TRUCK_TRADE_LIMIT)
    {
        in_truck_paths_only_vector.pop_back();
    }
    while (in_drone_paths_only_vector.size() > DRONE_TRADE_LIMIT)
    {
        in_drone_paths_only_vector.pop_back();
    }

    const unsigned truck_trade = in_truck_paths_only_vector.size(),
                   drone_trade = in_drone_paths_only_vector.size();

    // Brute-force swap
    for (unsigned bitmask = 1; bitmask < (1u << (truck_trade + drone_trade)); bitmask++)
    {
        auto new_truck_paths = extra.truck_paths;
        auto new_drone_paths = extra.drone_paths;
        std::vector<unsigned> from_truck, from_drone;
        for (unsigned i = 0; i < truck_trade; i++)
        {
            if (bitmask & (1u << (i + drone_trade)))
            {
                unsigned customer = in_truck_paths_only_vector[i];
                from_truck.push_back(customer);
                for (auto &path : new_truck_paths)
                {
                    path.erase(customer);
                }
                for (auto &paths : new_drone_paths)
                {
                    for (auto &path : paths)
                    {
                        path.insert(customer);
                    }
                }
            }
        }
        for (unsigned i = 0; i < drone_trade; i++)
        {
            if (bitmask & (1u << i))
            {
                unsigned customer = in_drone_paths_only_vector[i];
                from_drone.push_back(customer);
                for (auto &path : new_truck_paths)
                {
                    path.insert(customer);
                }
                for (auto &paths : new_drone_paths)
                {
                    for (auto &path : paths)
                    {
                        path.erase(customer);
                    }
                }
            }
        }

        py::object py_new_individual = from_cache(new_truck_paths, new_drone_paths);

        if (feasible(py_new_individual))
        {
            result.first = std::min(result.first.value_or(py_new_individual), py_new_individual);
        }
        result.second = std::min(result.second, py_new_individual);
    }
}

typedef std::function<void(const extra_info &, std::pair<std::optional<py::object>, py::object> &)> local_search_t;
const std::vector<local_search_t> operations = {local_search_1, local_search_2, local_search_3, local_search_4, local_search_5};

std::pair<std::optional<py::object>, py::object> local_search(const py::object &py_individual)
{
    py::object py_result_any = py_individual;
    std::optional<py::object> py_result_feasible;
    if (feasible(py_individual))
    {
        py_result_feasible = py_individual;
    }

    std::map<py::object, extra_info> cache;
    auto get_extra = [&cache](const py::object &py_individual)
    {
        try
        {
            return cache.at(py_individual);
        }
        catch (std::out_of_range &e)
        {
            auto extra = extra_info::from_individual(py_individual);
            cache.insert(std::make_pair(py_individual, extra));
            return extra;
        }
    };

    auto result = std::make_pair(py_result_feasible, py_result_any);

    for (auto &operation : operations)
    {
        operations[0](get_extra(result.first.has_value() ? *result.first : result.second), result);

        bool improved = true;
        while (improved)
        {
            auto old_result = result.first;
            operation(get_extra(result.first.has_value() ? *result.first : result.second), result);

            if (!old_result.has_value())
            {
                improved = result.first.has_value();
            }
            else
            {
                improved = *result.first < *old_result;
            }
        }
    }

    return result;
}
