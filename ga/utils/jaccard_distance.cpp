#pragma once

#include <algorithm>
#include <set>

double jaccard_distance(const std::set<unsigned> &first, const std::set<unsigned> &second)
{
    std::set<unsigned> intersection;
    std::set_intersection(first.begin(), first.end(), second.begin(), second.end(), std::inserter(intersection, intersection.begin()));

    std::set<unsigned> union_set;
    std::set_union(first.begin(), first.end(), second.begin(), second.end(), std::inserter(union_set, union_set.begin()));

    return 1.0 - (double)intersection.size() / (double)union_set.size();
}
