#pragma once

#include "config.hpp"

const unsigned TRUCK_TRADE_LIMIT = 4u;
const unsigned DRONE_TRADE_LIMIT = 4u;

std::pair<std::optional<py::object>, py::object> local_search(const py::object &py_individual)
{
    const auto [truck_paths, drone_paths] = get_paths(py_individual);
    const auto [decoded_truck_paths, decoded_drone_paths] = get_decoded_paths(py_individual.attr("decode")());

    std::vector<volume_t> volumes(Customer::customers.size());
    for (auto &path : decoded_truck_paths)
    {
        for (auto &[customer, volume] : path)
        {
            volumes[customer] += volume;
        }
    }
    for (auto &paths : decoded_drone_paths)
    {
        for (auto &path : paths)
        {
            for (auto &[customer, volume] : path)
            {
                volumes[customer] += volume;
            }
        }
    }

    py::object py_result_any = py_individual;
    std::optional<py::object> py_result_feasible;
    if (feasible(py_individual))
    {
        py_result_feasible = py_individual;
    }

    unsigned trucks_count = truck_paths.size(),
             drones_count = drone_paths.size();

#ifdef DEBUG
    std::cout << "Local search for " << trucks_count << " truck(s) and " << drones_count << " drone(s)" << std::endl;
#endif

    /*
    {
        auto [new_truck_paths, new_drone_paths] = copy(truck_paths, drone_paths);
        for (auto &path : new_truck_paths)
        {
            strip_customers(path);
        }
        for (auto &paths : new_drone_paths)
        {
            for (auto &path : paths)
            {
                strip_customers(path);
            }
        }

        auto py_new_individual = from_cache(new_truck_paths, new_drone_paths);

        if (feasible(py_new_individual))
        {
            py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
        }
        py_result_any = std::min(py_result_any, py_new_individual);
    }
    */

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

    std::vector<unsigned> absent;
    for (unsigned customer = 1; customer < Customer::customers.size(); customer++)
    {
        if (!in_truck_paths.count(customer) && !in_drone_paths.count(customer))
        {
            absent.push_back(customer);
        }
    }

    /*
    // FEATURE REQUEST #1. Replicate drone paths with the highest profit
    for (unsigned drone = 0; drone < drones_count; drone++)
    {
        std::vector<std::pair<unsigned, double>> profits;
        for (unsigned path = 0; path < decoded_drone_paths[drone].size(); path++)
        {
            profits.emplace_back(path, drone_path_profit(decoded_drone_paths[drone][path]));
        }

        std::sort(
            profits.begin(), profits.end(),
            [](const std::pair<unsigned int, double> &a, const std::pair<unsigned int, double> &b)
            { return a.second > b.second; });

        for (auto &[path, profit] : profits)
        {
            if (profit < 0.0)
            {
                break;
            }

            volume_t available = 0;
            std::vector<unsigned> new_path;
            for (auto &[customer, _] : decoded_drone_paths[drone][path])
            {
                available += Customer::customers[customer].high - volumes[customer];
                new_path.push_back(customer);
            }

            if (available < Customer::drone_capacity)
            {
                continue;
            }

            auto py_new_path = py_frozenset(new_path.begin(), new_path.end());
            while (available >= Customer::drone_capacity)
            {
                available -= Customer::drone_capacity;
                py::object py_new_individual = append_drone_path(py_individual, drone, py_new_path);

                if (feasible(py_new_individual))
                {
                    py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
                }
                py_result_any = std::min(py_result_any, py_new_individual);
            }

            break;
        }
    }
    */

    // Add absent customers to truck paths
    {
        auto mutable_truck_paths = truck_paths;
        for (unsigned truck = 0; truck < trucks_count; truck++)
        {
            // Temporary modify the individual
            mutable_truck_paths[truck].insert(absent.begin(), absent.end());

            py::object py_new_individual = from_cache(mutable_truck_paths, drone_paths);

            if (feasible(py_new_individual))
            {
                py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
            }
            py_result_any = std::min(py_result_any, py_new_individual);

            // Restore the individual
            for (auto c : absent)
            {
                mutable_truck_paths[truck].erase(c);
            }
        }
    }

    // Add absent customers to drone paths
    {
        std::vector<unsigned> new_path = absent;
        new_path.push_back(0);

        auto py_new_path = py_frozenset(new_path.begin(), new_path.end());
        auto mutable_drone_paths = drone_paths;
        for (unsigned drone = 0; drone < drones_count; drone++)
        {
            for (unsigned path = 0; path < drone_paths[drone].size(); path++)
            {
                // Temporary modify the individual
                mutable_drone_paths[drone][path].insert(absent.begin(), absent.end());

                py::object py_new_individual = from_cache(truck_paths, mutable_drone_paths);

                if (feasible(py_new_individual))
                {
                    py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
                }
                py_result_any = std::min(py_result_any, py_new_individual);

                // Restore the individual
                for (auto c : absent)
                {
                    mutable_drone_paths[drone][path].erase(c);
                }
            }

            py::object py_new_individual = append_drone_path(py_individual, drone, py_new_path);

            if (feasible(py_new_individual))
            {
                py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
            }
            py_result_any = std::min(py_result_any, py_new_individual);
        }
    }

    // FEATURE REQUEST #4.1. Push customers from truck paths to new drone paths
    for (auto customer : in_truck_paths)
    {
        for (unsigned drone = 0; drone < drones_count; drone++)
        {
            auto new_drone_paths = drone_paths;

            new_drone_paths[drone].push_back({0, customer});
            py::object py_new_individual = from_cache(truck_paths, new_drone_paths);
            if (feasible(py_new_individual))
            {
                py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
            }
            py_result_any = std::min(py_result_any, py_new_individual);

            new_drone_paths[drone].push_back({0, customer});
            py::object py_new_new_individual = from_cache(truck_paths, new_drone_paths);

            while (py_new_new_individual < py_new_individual && feasible(py_new_new_individual))
            {
                py_new_individual = py_new_new_individual;
                new_drone_paths[drone].push_back({0, customer});
                py_new_new_individual = from_cache(truck_paths, new_drone_paths);

                py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual); // Feasibility guaranteed
                py_result_any = std::min(py_result_any, py_new_individual);
            }
        }
    }

    // FEATURE REQUEST #3. Split/Remove drone paths serving more than 1 customer
    {
        auto mutable_drone_paths = drone_paths;
        for (unsigned drone = 0; drone < drones_count; drone++)
        {
            for (unsigned path = 0; path < drone_paths[drone].size(); path++)
            {
                if (drone_paths[drone][path].size() < 3) // Require at least 3 elements: the depot and 2+ customers
                {
                    continue;
                }

                // Split
                for (auto customer : drone_paths[drone][path])
                {
                    if (customer != 0)
                    {
                        // Temporary modify the individual
                        mutable_drone_paths[drone][path].erase(customer);
                        mutable_drone_paths[drone].push_back({0, customer});

                        py::object py_new_individual = from_cache(truck_paths, mutable_drone_paths);

                        if (feasible(py_new_individual))
                        {
                            py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
                        }
                        py_result_any = std::min(py_result_any, py_new_individual);

                        // Restore the individual
                        mutable_drone_paths[drone][path].insert(customer);
                        mutable_drone_paths[drone].pop_back();
                    }
                }

                // Remove
                {
                    // Temporary modify the individual
                    auto temp = mutable_drone_paths[drone][path];
                    mutable_drone_paths[drone][path] = {0};

                    py::object py_new_individual = from_cache(truck_paths, mutable_drone_paths);

                    if (feasible(py_new_individual))
                    {
                        py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
                    }
                    py_result_any = std::min(py_result_any, py_new_individual);

                    // Restore the individual
                    mutable_drone_paths[drone][path] = temp;
                }
            }
        }
    }

    /*
    // FEATURE REQUEST #4.2. Remove a customer from a drone path
    {
        auto mutable_drone_paths = drone_paths;
        for (unsigned drone = 0; drone < drones_count; drone++)
        {
            for (unsigned path = 0; path < drone_paths[drone].size(); path++)
            {
                for (auto customer : drone_paths[drone][path])
                {
                    if (customer != 0 && in_both.count(customer))
                    {
                        // Temporary remove customer from path
                        mutable_drone_paths[drone][path].erase(customer);

                        py::object py_new_individual = from_cache(truck_paths, mutable_drone_paths);

                        if (feasible(py_new_individual))
                        {
                            py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
                        }
                        py_result_any = std::min(py_result_any, py_new_individual);

                        // Restore the individual
                        mutable_drone_paths[drone][path].insert(customer);
                    }
                }
            }
        }
    }
    */

    std::vector<unsigned> in_truck_paths_only_vector(in_truck_paths_only.begin(), in_truck_paths_only.end()),
        in_drone_paths_only_vector(in_drone_paths_only.begin(), in_drone_paths_only.end());

    // Calculate improved ratios
    std::vector<std::vector<double>> improved_ratio(2);
    improved_ratio[0].resize(in_truck_paths_only_vector.size(), -1);
    improved_ratio[1].resize(in_drone_paths_only_vector.size(), -1);

    {
        std::vector<double> truck_paths_distance;
        for (auto &path : truck_paths)
        {
            truck_paths_distance.push_back(path_order(path).first);
        }

        std::vector<std::vector<double>> drone_paths_distance(drones_count);
        for (unsigned drone = 0; drone < drones_count; drone++)
        {
            for (auto &path : drone_paths[drone])
            {
                drone_paths_distance[drone].push_back(path_order(path).first);
            }
        }

        auto mutable_truck_paths = truck_paths;
        for (unsigned truck_i = 0; truck_i < in_truck_paths_only_vector.size(); truck_i++)
        {
            double total_ratio = 0.0;
            for (unsigned truck = 0; truck < trucks_count; truck++)
            {
                bool erased = mutable_truck_paths[truck].erase(in_truck_paths_only_vector[truck_i]);
                total_ratio += path_order(mutable_truck_paths[truck]).first / truck_paths_distance[truck];

                if (erased)
                {
                    mutable_truck_paths[truck].insert(in_truck_paths_only_vector[truck_i]);
                }
            }

            improved_ratio[0][truck_i] = total_ratio / trucks_count;
        }

        unsigned total_drone_paths = 0;
        for (unsigned drone = 0; drone < drones_count; drone++)
        {
            total_drone_paths += drone_paths[drone].size();
        }

        auto mutable_drone_paths = drone_paths;
        for (unsigned drone_i = 0; drone_i < in_drone_paths_only_vector.size(); drone_i++)
        {
            double total_ratio = 0.0;
            for (unsigned drone = 0; drone < drones_count; drone++)
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

    /*
    // FEATURE REQUEST #2. Insert customers from truck paths to new drone paths
    for (unsigned bitmask = 1; bitmask < (1u << truck_trade); bitmask++)
    {
        auto [new_truck_paths, new_drone_paths] = copy(truck_paths, drone_paths);
        for (unsigned i = 0; i < truck_trade; i++)
        {
            if (bitmask & (1u << i))
            {
                unsigned customer = in_truck_paths_only_vector[i];
                for (auto &path : new_truck_paths)
                {
                    path.erase(customer);
                }
                for (unsigned drone = 0; drone < drones_count; drone++)
                {
                    new_drone_paths[drone].push_back({0, customer});
                }
            }
        }

        py::object py_new_individual = from_cache(new_truck_paths, new_drone_paths);

        if (feasible(py_new_individual))
        {
            py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
        }
        py_result_any = std::min(py_result_any, py_new_individual);
    }
    */

    // Brute-force swap
    for (unsigned bitmask = 1; bitmask < (1u << (truck_trade + drone_trade)); bitmask++)
    {
        auto new_truck_paths = truck_paths;
        auto new_drone_paths = drone_paths;
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

        /*
        for (auto customer : absent)
        {
            for (auto &path : new_truck_paths)
            {
                path.insert(customer);
            }
            for (auto &paths : new_drone_paths)
            {
                for (auto &path : paths)
                {
                    path.insert(customer);
                }
            }
        }
        */

        py::object py_new_individual = from_cache(new_truck_paths, new_drone_paths);

        if (feasible(py_new_individual))
        {
            py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
        }
        py_result_any = std::min(py_result_any, py_new_individual);
    }

    /*
    if (py_result_feasible.has_value())
    {
        auto py_result_feasible_educated = educate(py_result_feasible.value());
        if (feasible(py_result_feasible_educated))
        {
            py_result_feasible = py_result_feasible_educated;
        }
    }
    */

    return std::make_pair(py_result_feasible, py_result_any);
}
