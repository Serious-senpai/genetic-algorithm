#pragma once

#include "config.hpp"

namespace py = pybind11;

void strip_customers(std::set<unsigned> &path)
{
    auto iter = path.begin();
    while (iter != path.end())
    {
        if (*iter != 0 && Customer::customers[*iter].low == 0)
        {
            iter = path.erase(iter);
        }
        else
        {
            iter++;
        }
    }
}

py::object educate(const py::object &py_individual)
{
    py::object py_result = py_individual;

    const auto [truck_paths, drone_paths] = get_paths(py_individual);
    /*
    const auto py_decoded = py_individual.attr("decode")();
    const bool feasibility = feasible(py_individual);
    // unused: auto truck_paths = py::cast<std::vector<std::vector<std::pair<unsigned, volume_t>>>>(py_decoded.attr("truck_paths"));
    const auto encoded_drone_paths = py::cast<std::vector<std::vector<std::vector<std::pair<unsigned, volume_t>>>>>(py_decoded.attr("drone_paths"));

    {
        auto [new_truck_paths, new_drone_paths] = copy(truck_paths, drone_paths);
        for (unsigned drone = 0; drone < encoded_drone_paths.size(); drone++)
        {
            for (unsigned path = 0; path < encoded_drone_paths[drone].size(); path++)
            {
                if (encoded_drone_paths[drone][path].size() > 3)
                {
                    unsigned remove_customer = 0;
                    volume_t remove_volume = -1;
                    for (unsigned i = 1; i < encoded_drone_paths[drone][path].size() - 1; i++)
                    {
                        auto &[customer, volume] = encoded_drone_paths[drone][path][i];
                        if (volume < remove_volume || remove_volume == -1)
                        {
                            remove_customer = customer;
                            remove_volume = volume;
                        }
                    }

                    new_drone_paths[drone][path].erase(remove_customer);
                }
            }
        }

        auto py_new_individual = from_cache(new_truck_paths, new_drone_paths, false);

        if (feasible(py_new_individual))
        {
            py_result = feasibility ? std::min(py_result, py_new_individual) : py_new_individual;
        }
        else if (!feasibility)
        {
            py_result = std::min(py_result, py_new_individual);
        }
    }

    std::vector<bool> exists(Customer::customers.size());

    for (auto &path : truck_paths)
    {
        for (auto customer : path)
        {
            exists[customer] = true;
        }
    }
    for (auto &paths : drone_paths)
    {
        for (auto &path : paths)
        {
            for (auto customer : path)
            {
                exists[customer] = true;
            }
        }
    }

    std::vector<unsigned> new_path = {0};
    for (unsigned customer = 1; customer < Customer::customers.size(); customer++)
    {
        if (!exists[customer])
        {
            new_path.push_back(customer);
        }
    }

    auto py_new_path = py_frozenset(new_path.begin(), new_path.end());
    for (unsigned drone = 0; drone < drone_paths.size(); drone++)
    {
        py_result = std::min(py_result, py_individual.attr("append_drone_path")(drone, py_new_path));
    }

    auto flattened_paths = py::cast<std::vector<py::frozenset>>(py_individual.attr("flatten")());
    for (unsigned i = 0; i < flattened_paths.size(); i++)
    {
        auto old_path = flattened_paths[i];

        std::set<unsigned> extended(new_path.begin(), new_path.end());
        for (auto c : old_path)
        {
            extended.insert(py::cast<unsigned>(c));
        }
        flattened_paths[i] = py_frozenset(extended.begin(), extended.end());

        py_result = std::min(py_result, py_individual.attr("reconstruct")(flattened_paths));
        flattened_paths[i] = old_path;
    }
    */

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

        py_result = std::min(py_result, from_cache(new_truck_paths, new_drone_paths));
    }

    return py_result;
}
