#include <algorithm>
#include <map>
#include <set>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "../../utils/helpers.cpp"
#include "../../utils/maximum_weighted_flow.cpp"

namespace py = pybind11;

struct Customer
{
    const double low, high, w;

    Customer(double low, double high, double w) : low(low), high(high), w(w) {}
};

std::vector<Customer> customers;

void set_customers(const std::vector<double> &low, const std::vector<double> &high, const std::vector<double> &w)
{
    customers.clear();
    for (unsigned i = 0; i < low.size(); i++)
    {
        customers.emplace_back(low[i], high[i], w[i]);
    }
}

unsigned sum(const std::vector<unsigned> &v)
{
    unsigned s = 0;
    for (auto i : v)
    {
        s += i;
    }

    return s;
}

std::pair<
    std::vector<std::map<unsigned, double>>,
    std::vector<std::vector<std::map<unsigned, double>>>>
paths_from_flow(
    const unsigned truck_paths_count,
    const std::vector<unsigned> &drone_paths_count,
    const std::vector<std::vector<double>> &flows,
    const std::vector<std::set<unsigned>> &neighbors)
{
    unsigned customers_count = customers.size() - 1,
             network_trucks_offset = 1,
             network_drones_offset = network_trucks_offset + truck_paths_count,
             network_customers_offset = network_trucks_offset + truck_paths_count + sum(drone_paths_count),
             network_sink = network_customers_offset + customers_count;

    std::vector<std::map<unsigned, double>> truck_paths;
    for (unsigned network_truck = network_trucks_offset; network_truck < network_drones_offset; network_truck++)
    {
        truck_paths.emplace_back();
        auto path = --truck_paths.end();
        path->emplace(0, 0.0);

        for (auto network_customer : neighbors[network_truck])
        {
            unsigned customer = network_customer - network_customers_offset + 1;
            path->emplace(customer, flows[network_truck][network_customer]);
        }
    }

    std::vector<std::vector<std::map<unsigned, double>>> drone_paths(drone_paths_count.size());
    for (unsigned network_drone = network_drones_offset; network_drone < network_customers_offset; network_drone++)
    {
        unsigned drone = 0, from_offset = network_drone - network_drones_offset;
        while (from_offset >= drone_paths_count[drone])
        {
            from_offset -= drone_paths_count[drone];
            drone++;
        }

        drone_paths[drone].emplace_back();
        auto path = --drone_paths[drone].end();
        path->emplace(0, 0.0);

        for (auto network_customer : neighbors[network_drone])
        {
            unsigned customer = network_customer - network_customers_offset + 1;
            path->emplace(customer, flows[network_drone][network_customer]);
        }
    }

    std::vector<double> total_weights(customers.size());
    for (unsigned customer = 1; customer < customers.size(); customer++)
    {
        total_weights[customer] = flows[network_customers_offset + customer - 1][network_sink];
    }

    std::vector<unsigned> senders, receivers;
    for (unsigned customer = 1; customer < customers.size(); customer++)
    {
        if (total_weights[customer] > customers[customer].low)
        {
            senders.push_back(customer);
        }
        else if (total_weights[customer] < customers[customer].low)
        {
            receivers.push_back(customer);
        }
    }

    std::sort(
        senders.begin(), senders.end(),
        [](unsigned i, unsigned j)
        { return customers[i].w < customers[j].w; });
    std::sort(
        receivers.begin(), receivers.end(),
        [](unsigned i, unsigned j)
        { return customers[i].w > customers[j].w; });

    std::vector<std::set<std::vector<std::map<unsigned, double>>::iterator>> in_path(customers.size());
    for (unsigned i = 0; i < truck_paths.size(); i++)
    {
        for (auto &[customer, _] : truck_paths[i])
        {
            in_path[customer].insert(truck_paths.begin() + i);
        }
    }
    for (unsigned i = 0; i < drone_paths.size(); i++)
    {
        for (unsigned j = 0; j < drone_paths[i].size(); j++)
        {
            for (auto &[customer, _] : drone_paths[i][j])
            {
                in_path[customer].insert(drone_paths[i].begin() + j);
            }
        }
    }

    // Rearrange delivery volumes
    for (auto receiver : receivers)
    {
        for (auto sender : senders)
        {
            if (total_weights[sender] > customers[sender].low)
            {
                for (auto &path_iter : in_path[sender])
                {
                    if (path_iter->count(receiver))
                    {
                        double original_sender = path_iter->at(sender),
                               original_receiver = path_iter->at(receiver),
                               transfer = min(
                                   original_sender,
                                   total_weights[sender] - customers[sender].low,
                                   customers[receiver].low - total_weights[receiver]);

                        path_iter->insert_or_assign(sender, original_sender - transfer);
                        path_iter->insert_or_assign(receiver, original_receiver + transfer);

                        total_weights[sender] -= transfer;
                        total_weights[receiver] += transfer;
                    }
                }
            }
        }
    }

    return {truck_paths, drone_paths};
}

std::pair<
    std::vector<std::map<unsigned, double>>,
    std::vector<std::vector<std::map<unsigned, double>>>>
paths_from_flow_chained(
    const std::vector<std::set<unsigned>> &truck_paths,
    const std::vector<std::vector<std::set<unsigned>>> &drone_paths,
    const double truck_capacity,
    const double drone_capacity)
{
    unsigned trucks_count = truck_paths.size(),
             drones_count = drone_paths.size(),
             customers_count = customers.size() - 1;
    std::vector<unsigned> drone_paths_count(drones_count);
    for (unsigned i = 0; i < drones_count; i++)
    {
        drone_paths_count[i] = drone_paths[i].size();
    }

    unsigned network_trucks_offset = 1,
             network_drones_offset = network_trucks_offset + trucks_count,
             network_customers_offset = network_trucks_offset + trucks_count + sum(drone_paths_count),
             network_source = 0, network_sink = network_customers_offset + customers_count,
             network_size = network_sink + 1;

    std::vector<std::vector<double>> network_capacities(network_size, std::vector<double>(network_size, 0.0)),
        network_flow_weights(network_size, std::vector<double>(network_size, 0.0));
    std::vector<std::set<unsigned>> network_neighbors(network_size);

    for (unsigned i = 1; i < network_customers_offset; i++)
    {
        if (i < network_trucks_offset + trucks_count)
        {
            network_capacities[network_source][i] = truck_capacity;

            unsigned truck = i - network_trucks_offset;
            for (auto customer : truck_paths[truck])
            {
                if (customer != 0)
                {
                    unsigned network_customer = network_customers_offset + customer - 1;
                    network_capacities[i][network_customer] = 1.0e+9;
                    network_neighbors[i].insert(network_customer);
                }
            }
        }
        else
        {
            network_capacities[network_source][i] = drone_capacity;

            unsigned drone = 0, from_offset = i - network_drones_offset;
            while (from_offset >= drone_paths_count[drone])
            {
                from_offset -= drone_paths_count[drone];
                drone++;
            }

            for (auto customer : drone_paths[drone][from_offset])
            {
                if (customer != 0)
                {
                    unsigned network_customer = network_customers_offset + customer - 1;
                    network_capacities[i][network_customer] = 1.0e+9;
                    network_neighbors[i].insert(network_customer);
                }
            }
        }

        network_neighbors[network_source].insert(i);
    }

    for (unsigned i = network_customers_offset; i < network_sink; i++)
    {
        unsigned customer = i - network_customers_offset + 1;
        network_capacities[i][network_sink] = customers[customer].high;
        network_neighbors[i].insert(network_sink);
        network_flow_weights[i][network_sink] = customers[customer].w;
    }

    auto [_, flows] = maximum_weighted_flow(
        network_size,
        network_capacities, network_neighbors, network_flow_weights,
        network_source, network_sink);

    return paths_from_flow(trucks_count, drone_paths_count, flows, network_neighbors);
}

PYBIND11_MODULE(cpp_utils, m)
{
    m.def(
        "set_customers", &set_customers,
        py::arg("low"), py::arg("high"), py::arg("w"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "paths_from_flow", &paths_from_flow,
        py::arg("truck_paths_count"), py::arg("drone_paths_count"), py::arg("flows"), py::arg("neighbors"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "paths_from_flow_chained", &paths_from_flow_chained,
        py::arg("truck_paths"), py::arg("drone_paths"), py::arg("truck_capacity"), py::arg("drone_capacity"),
        py::call_guard<py::gil_scoped_release>());
}
