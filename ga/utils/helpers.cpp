#pragma once

#include <chrono>
#include <random>
#include <stdexcept>
#include <string>

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

double _random_double(double l, double r)
{
    std::uniform_real_distribution<double> unif(l, r);
    return unif(rng);
}

unsigned _random_int(unsigned l, unsigned r)
{
    std::uniform_int_distribution<unsigned> unif(l, r);
    return unif(rng);
}

double sqrt_impl(double value)
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
