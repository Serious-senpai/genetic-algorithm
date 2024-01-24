#pragma once

#include "config.hpp"

const unsigned TRUCK_TRADE_LIMIT = 5u;
const unsigned DRONE_TRADE_LIMIT = 5u;

std::pair<std::optional<py::object>, py::object> local_search(const py::object &py_individual)
{
    auto paths = get_paths(py_individual);
    auto truck_paths = paths.first;
    auto drone_paths = paths.second;

    py::object py_result_any = py_individual;
    std::optional<py::object> py_result_feasible;
    if (feasible(py_individual))
    {
        py_result_feasible = py_individual;
    }

    unsigned trucks_count = truck_paths.size(),
             drones_count = drone_paths.size();

#ifdef DEBUG
    unsigned counter = 0;
    std::cout << "Local search for " << trucks_count << " truck(s) and " << drones_count << " drone(s)" << std::endl;
#endif

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

    // Attempt to add absent customers
    std::vector<unsigned> absent;
    for (unsigned customer = 1; customer < Customer::customers.size(); customer++)
    {
        if (!in_truck_paths.count(customer) && !in_drone_paths.count(customer))
        {
            absent.push_back(customer);
        }
    }

    for (unsigned truck = 0; truck < trucks_count; truck++)
    {
        auto [new_truck_paths, new_drone_paths] = copy(truck_paths, drone_paths);
        new_truck_paths[truck].insert(absent.begin(), absent.end());

        py::object py_new_individual = from_cache(new_truck_paths, new_drone_paths);
#ifdef DEBUG
        counter++;
#endif

        if (feasible(py_new_individual))
        {
            py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
        }
        py_result_any = std::min(py_result_any, py_new_individual);
    }

    std::vector<unsigned> new_path = absent;
    new_path.push_back(0);

    auto py_new_path = py_frozenset(new_path.begin(), new_path.end());
    for (unsigned drone = 0; drone < drones_count; drone++)
    {
        for (unsigned path = 0; path < drone_paths[drone].size(); path++)
        {
            auto [new_truck_paths, new_drone_paths] = copy(truck_paths, drone_paths);
            new_drone_paths[drone][path].insert(absent.begin(), absent.end());

            py::object py_new_individual = from_cache(new_truck_paths, new_drone_paths);
#ifdef DEBUG
            counter++;
#endif

            if (feasible(py_new_individual))
            {
                py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
            }
            py_result_any = std::min(py_result_any, py_new_individual);
        }

        py::object py_new_individual = py_individual.attr("append_drone_path")(drone, py_new_path);
#ifdef DEBUG
        counter++;
#endif

        if (feasible(py_new_individual))
        {
            py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
        }
        py_result_any = std::min(py_result_any, py_new_individual);
    }

    // Remove elements in both sets
    std::set<unsigned> in_both;
    for (auto customer : in_truck_paths)
    {
        if (in_drone_paths.count(customer))
        {
            in_both.insert(customer);
        }
    }

    auto remove_intersection = [&in_both](std::set<unsigned> &customers)
    {
        for (auto iter = customers.begin(); iter != customers.end();)
        {
            if (in_both.count(*iter))
            {
                iter = customers.erase(iter);
            }
            else
            {
                iter++;
            }
        }
    };
    remove_intersection(in_truck_paths);
    remove_intersection(in_drone_paths);

    std::vector<unsigned> in_truck_paths_vector(in_truck_paths.begin(), in_truck_paths.end()),
        in_drone_paths_vector(in_drone_paths.begin(), in_drone_paths.end());

    // Brute-force swap
    std::vector<std::vector<double>> improved_ratio(2);
    improved_ratio[0].resize(in_truck_paths_vector.size(), -1);
    improved_ratio[1].resize(in_drone_paths_vector.size(), -1);

    {
        // Calculate improved ratios
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

        for (unsigned truck_i = 0; truck_i < in_truck_paths_vector.size(); truck_i++)
        {
            double total_ratio = 0.0;
            for (unsigned truck = 0; truck < trucks_count; truck++)
            {
                bool erased = truck_paths[truck].erase(in_truck_paths_vector[truck_i]);
                total_ratio += path_order(truck_paths[truck]).first / truck_paths_distance[truck];

                if (erased)
                {
                    truck_paths[truck].insert(in_truck_paths_vector[truck_i]);
                }
            }

            improved_ratio[0][truck_i] = total_ratio / trucks_count;
        }

        unsigned total_drone_paths = 0;
        for (unsigned drone = 0; drone < drones_count; drone++)
        {
            total_drone_paths += drone_paths[drone].size();
        }

        for (unsigned drone_i = 0; drone_i < in_drone_paths_vector.size(); drone_i++)
        {
            double total_ratio = 0.0;
            for (unsigned drone = 0; drone < drones_count; drone++)
            {
                for (unsigned path = 0; path < drone_paths[drone].size(); path++)
                {

                    bool erased = drone_paths[drone][path].erase(in_drone_paths_vector[drone_i]);
                    total_ratio += path_order(drone_paths[drone][path]).first / drone_paths_distance[drone][path];

                    if (erased)
                    {
                        drone_paths[drone][path].insert(in_drone_paths_vector[drone_i]);
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
    for (unsigned i = 0; i < in_truck_paths_vector.size(); i++)
    {
        improved_ratio_map[in_truck_paths_vector[i]] = improved_ratio[0][i];
    }
    for (unsigned i = 0; i < in_drone_paths_vector.size(); i++)
    {
        improved_ratio_map[in_drone_paths_vector[i]] = improved_ratio[1][i];
    }
    std::sort(
        in_truck_paths_vector.begin(), in_truck_paths_vector.end(),
        [&improved_ratio_map](unsigned a, unsigned b)
        {
            return improved_ratio_map[a] < improved_ratio_map[b];
        });
    std::sort(
        in_drone_paths_vector.begin(), in_drone_paths_vector.end(),
        [&improved_ratio_map](unsigned a, unsigned b)
        {
            return improved_ratio_map[a] < improved_ratio_map[b];
        });

    while (in_truck_paths_vector.size() > TRUCK_TRADE_LIMIT)
    {
        in_truck_paths_vector.pop_back();
    }
    while (in_drone_paths_vector.size() > DRONE_TRADE_LIMIT)
    {
        in_drone_paths_vector.pop_back();
    }

    unsigned truck_trade = in_truck_paths_vector.size(),
             drone_trade = in_drone_paths_vector.size();

    for (unsigned bitmask = 1; bitmask < (1u << (truck_trade + drone_trade)); bitmask++)
    {
        auto [new_truck_paths, new_drone_paths] = copy(truck_paths, drone_paths);
        std::vector<unsigned> truck_comb, drone_comb;
        for (unsigned i = 0; i < truck_trade; i++)
        {
            if (bitmask & (1u << (i + drone_trade)))
            {
                unsigned customer = in_truck_paths_vector[i];
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
                unsigned customer = in_drone_paths_vector[i];
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
#ifdef DEBUG
        counter++;
#endif

        if (feasible(py_new_individual))
        {
            py_result_feasible = std::min(py_result_feasible.value_or(py_new_individual), py_new_individual);
        }
        py_result_any = std::min(py_result_any, py_new_individual);
    }

#ifdef DEBUG
    std::cout << "Explored " << counter << " neighbors" << std::endl;
#endif

    return std::make_pair(py_result_feasible, py_result_any);
}
