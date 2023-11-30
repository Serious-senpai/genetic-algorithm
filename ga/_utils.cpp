#include <vector>
#include <random>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

template <typename... Args>
std::string string_format(const std::string &format, Args... args)
{
    // https://stackoverflow.com/a/26221725
    int size_s = std::snprintf(nullptr, 0, format.c_str(), args...) + 1; // Extra space for '\0'
    if (size_s <= 0)
    {
        throw std::runtime_error("Error during formatting.");
    }
    auto size = static_cast<size_t>(size_s);
    std::unique_ptr<char[]> buf(new char[size]);
    std::snprintf(buf.get(), size, format.c_str(), args...);
    return std::string(buf.get(), buf.get() + size - 1); // We don't want the '\0' inside
}

template <typename T>
T sum(std::vector<T> &array)
{
    unsigned n = array.size();
    if (n == 1)
    {
        return array[0];
    }

    if (n > 1)
    {
        T result = array[0] + array[1];
        for (unsigned index = 2; index < n; index++)
        {
            result += array[index];
        }

        return result;
    }

    throw std::length_error("Attempted to calculate sum of empty array");
}

std::vector<int> weighted_random(std::vector<double> &weights, unsigned count = 1)
{
    unsigned n = weights.size();
    if (count > n)
    {
        throw std::range_error(string_format("count exceeded the number of weights (%d > %d)", count, weights.size()));
    }

    std::set<int> results;
    double sum_weight = sum(weights);
    std::default_random_engine re;
    while (results.size() < count)
    {
        std::uniform_real_distribution<double> unif(0, sum_weight);
        double value = unif(re);
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

    return std::vector<int>(results.begin(), results.end());
}

PYBIND11_MODULE(_utils, m)
{
    m.def("weighted_random", &weighted_random, py::arg("weights"), py::arg("count") = 1);
}