#pragma once

#include <list>
#include <map>
#include <optional>
#include <string>
#include <type_traits>
#include <unordered_map>

namespace std
{
    // https://stackoverflow.com/a/51915825
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
    std::list<std::pair<K, V>> _items_list;
    typedef typename std::conditional<
        std::is_hashable<K>::value,
        std::unordered_map<K, typename std::list<std::pair<K, V>>::iterator>,
        std::map<K, typename std::list<std::pair<K, V>>::iterator>>::type map_t;

    map_t _items_map;

public:
    unsigned capacity,
        hit = 0,
        miss = 0,
        cached = 0;

    lru_cache(unsigned capacity) : capacity(capacity) {}

    typename map_t::const_iterator map_cbegin()
    {
        return _items_map.cbegin();
    }

    typename map_t::const_iterator map_cend()
    {
        return _items_map.cend();
    }

    typename std::list<std::pair<K, V>>::const_iterator list_cbegin()
    {
        return _items_list.cbegin();
    }

    typename std::list<std::pair<K, V>>::const_iterator list_cend()
    {
        return _items_list.cend();
    }

    std::optional<V> get(const K &key)
    {
        // Fetch iterator
        auto map_iter = _items_map.find(key);
        if (map_iter == _items_map.end())
        {
            miss++;
            return std::nullopt;
        }

        hit++;

        // Move to front
        auto list_iter = map_iter->second;
        auto kv_pair = *list_iter;
        _items_list.erase(list_iter);
        _items_list.push_front(kv_pair);
        _items_map[key] = _items_list.begin();

        return kv_pair.second;
    }

    void set(const K &key, const V &value)
    {
        cached++;

        auto map_iter = _items_map.find(key);
        if (map_iter != _items_map.end())
        {
            // Already in cache
            auto list_iter = map_iter->second;
            _items_list.erase(list_iter);
        }

        _items_list.push_front(std::make_pair(key, value));
        _items_map[key] = _items_list.begin();

        while (_items_map.size() > capacity)
        {
            auto last = _items_list.end();
            last--;
            _items_map.erase(last->first);
            _items_list.pop_back();
        }
    }

    unsigned size()
    {
        return _items_map.size();
    }

    void clear()
    {
        hit = miss = cached = 0;
        _items_list.clear();
        _items_map.clear();
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