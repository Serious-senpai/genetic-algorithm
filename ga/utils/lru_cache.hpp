#pragma once

#include <list>
#include <map>
#include <optional>
#include <string>
#include <type_traits>
#include <unordered_map>

namespace std
{ // https://stackoverflow.com/a/51915825
    template <typename T, typename = std::void_t<>>
    struct is_hashable : std::false_type
    {
    };

    template <typename T>
    struct is_hashable<T, std::void_t<decltype(std::declval<std::hash<T>>()(std::declval<T>()))>> : std::true_type
    {
    };
};

template <typename K, typename V>
class lru_cache
{
private:
    std::list<std::pair<K, V>> items_list;
    typename std::conditional<
        std::is_hashable<K>::value,
        std::unordered_map<K, typename std::list<std::pair<K, V>>::iterator>,
        std::map<K, typename std::list<std::pair<K, V>>::iterator>>::type items_map;

public:
    unsigned capacity,
        hit = 0,
        miss = 0,
        cached = 0;

    lru_cache(unsigned capacity) : capacity(capacity) {}

    std::optional<V> get(const K &key)
    {
        // Fetch iterator
        auto map_iter = items_map.find(key);
        if (map_iter == items_map.end())
        {
            miss++;
            return std::nullopt;
        }

        hit++;

        // Move to front
        auto list_iter = map_iter->second;
        auto kv_pair = *list_iter;
        items_list.erase(list_iter);
        items_list.push_front(kv_pair);
        items_map[key] = items_list.begin();

        return kv_pair.second;
    }

    void set(const K &key, const V &value)
    {
        cached++;

        auto map_iter = items_map.find(key);
        if (map_iter != items_map.end())
        {
            // Already in cache
            auto list_iter = map_iter->second;
            items_list.erase(list_iter);
        }

        items_list.push_front(std::make_pair(key, value));
        items_map[key] = items_list.begin();

        while (items_map.size() > capacity)
        {
            auto last = items_list.end();
            last--;
            items_map.erase(last->first);
            items_list.pop_back();
        }
    }

    unsigned size()
    {
        return items_map.size();
    }

    void clear()
    {
        hit = miss = cached = 0;
        items_list.clear();
        items_map.clear();
    }

    std::map<std::string, unsigned> to_json()
    {
        std::map<std::string, unsigned> json;
        json["capacity"] = capacity;
        json["hit"] = hit;
        json["miss"] = miss;
        json["cached"] = cached;

        return json;
    }
};