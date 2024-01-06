#pragma once

#include <algorithm>
#include <chrono>
#include <ctime>
#include <map>
#include <random>
#include <stdexcept>
#include <string>

#include <lemon/maps.h>
#include <pybind11/pybind11.h>

namespace py = pybind11;

template <typename K, typename V>
class LemonMap : lemon::MapBase<K, V>
{
private:
    std::map<K, V> data;

public:
    typedef K Key;
    typedef V Value;

    void set(const K &key, const V &value)
    {
        data[key] = value;
    }

    const V &operator[](const K &key) const
    {
        return data.at(key);
    }

    bool empty() const
    {
        return data.empty();
    }
};

class Timer
{
private:
    const double _limit;
    const double _start;

public:
    Timer(const double seconds_limit) : _limit(seconds_limit), _start((double)std::clock() / (double)CLOCKS_PER_SEC) {}

    bool timeup() const
    {
        return elapsed() >= _limit;
    }

    double elapsed() const
    {
        return (double)std::clock() / (double)CLOCKS_PER_SEC - _start;
    }
};

template <typename... Args>
std::string format(const std::string &format, Args... args)
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

std::mt19937 rng(std::chrono::steady_clock::now().time_since_epoch().count());

double random_double(const double l, const double r)
{
    std::uniform_real_distribution<double> unif(l, r);
    return unif(rng);
}

unsigned random_int(const unsigned l, const unsigned r)
{
    std::uniform_int_distribution<unsigned> unif(l, r);
    return unif(rng);
}

void rotate_to_first(std::vector<unsigned> &path, const unsigned first)
{
    auto first_iter = std::find(path.begin(), path.end(), first);
    if (first_iter == path.end())
    {
        throw std::invalid_argument(format("First city %d not found in path", first));
    }

    std::rotate(path.begin(), first_iter, path.end());
}

double sqrt_impl(const double value)
{
    if (value < 0)
    {
        throw std::out_of_range(format("Attempted to calculate square root of %lf", value));
    }

    if (value == 0.0)
    {
        return 0.0;
    }

    double low = 0.0, high = value;
    while (high - low > 1.0e-9)
    {
        double mid = (low + high) / 2;
        if (mid * mid < value)
        {
            low = mid;
        }
        else
        {
            high = mid;
        }
    }

    return high;
}

template <typename T>
const T &min(const T &_x, const T &_y, const T &_z)
{
    return std::min(_x, std::min(_y, _z));
}

double round(const double value, const unsigned precision)
{
    double factor = std::pow(10, precision);
    return std::round(value * factor) / factor;
}

double weird_round(const double value, const unsigned precision)
{
    double factor = std::pow(10, precision);
    return std::ceil(value * factor) / factor;
}

template <typename T>
py::tuple py_tuple(const std::vector<T> &__v)
{
    py::tuple __t(__v.size());
    for (unsigned __i = 0; __i < __v.size(); __i++)
    {
        __t[__i] = __v[__i];
    }

    return __t;
}

template <typename T>
py::frozenset py_frozenset(const std::set<T> &__s)
{
    py::set __ps;
    for (const auto &__e : __s)
    {
        __ps.add(__e);
    }
    return py::frozenset(__ps);
}