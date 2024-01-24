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
#include <pybind11/stl.h>

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

unsigned sum(const std::vector<unsigned> &v)
{
    unsigned __sum = 0;
    for (auto __i : v)
    {
        __sum += __i;
    }
    return __sum;
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

    double low = 0.0, high = std::max(1.0, value);
    while (high - low > 1.0e-6)
    {
        double mid = (low + high) / 2.0;
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

double distance(const double dx, const double dy)
{
    return weird_round(sqrt_impl(dx * dx + dy * dy), 2);
}

double distance(
    const std::pair<double, double> &first,
    const std::pair<double, double> &second)
{
    return distance(first.first - second.first, first.second - second.second);
}

template <typename T>
class Combination
{
private:
    const int _k;
    const std::vector<T> _data;

    std::vector<unsigned> _state;
    bool _done = false;

    bool _shift(const int index)
    {
        if (index < 0)
        {
            return false;
        }

        _state[index]++;
        if (_state[index] == (index == _k - 1 ? _data.size() : _state[index + 1]))
        {
            _state[index]--;
            bool shiftable = _shift(index - 1);
            if (shiftable)
            {
                _state[index] = _state[index - 1] + 1;
            }

            return shiftable;
        }

        return true;
    }

public:
    Combination(const std::vector<T> &data, const unsigned k) : _k(k), _data(data), _state(std::vector<unsigned>(k))
    {
        if (k > data.size())
        {
            _done = true;
        }
        else
        {
            for (unsigned i = 0; i < k; i++)
            {
                _state[i] = i;
            }
        }
    }

    std::vector<T> read()
    {
        if (_done)
        {
            throw std::runtime_error("Attempted to read from exhausted combination");
        }

        std::vector<T> result;
        for (auto index : _state)
        {
            result.push_back(_data[index]);
        }

        return result;
    }

    bool next()
    {
        if (_done)
        {
            return false;
        }

        bool shiftable = _shift(_k - 1);
        if (!shiftable)
        {
            _done = true;
        }

        return shiftable;
    }

    bool done()
    {
        return _done;
    }
};

template <typename _ForwardIterator>
py::tuple py_tuple(const _ForwardIterator &first, const _ForwardIterator &last)
{
    unsigned __size = std::distance(first, last);
    py::tuple __t(__size);

    auto iter = first;
    for (unsigned __i = 0; __i < __size; __i++)
    {
        __t[__i] = *iter;
        iter++;
    }

    return __t;
}

template <typename _ForwardIterator>
py::frozenset py_frozenset(const _ForwardIterator &first, const _ForwardIterator &last)
{
    py::set __ps;
    for (auto __i = first; __i != last; __i++)
    {
        __ps.add(*__i);
    }
    return py::frozenset(__ps);
}