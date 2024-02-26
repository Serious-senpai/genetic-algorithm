#include <optional>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "crowding_distance.hpp"
#include "fake_tsp_solver.hpp"
#include "flows_with_demands.hpp"
#include "jaccard_distance.hpp"
#include "lru_cache.hpp"
#include "maximum_flow.hpp"
#include "smallest_circle.hpp"
#include "tsp_solver.hpp"
#include "weighted_random.hpp"

namespace py = pybind11;

template <>
struct std::hash<py::object>
{
    std::size_t operator()(const py::object &object) const
    {
        return py::hash(object);
    }
};

template <>
struct std::equal_to<py::object>
{
    bool operator()(const py::object &first, const py::object &second) const
    {
        return first.equal(second);
    }
};

typedef lru_cache<py::object, py::object> py_lru_cache;

PYBIND11_MODULE(cpp_utils, m)
{
    m.def(
        "crowding_distance_sort", &crowding_distance_sort,
        py::arg("sets"), py::kw_only(), py::arg("k") = 2,
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "fake_tsp_solver", &fake_tsp_solver,
        py::arg("cities"), py::kw_only(), py::arg("first") = 0, py::arg("heuristic_hint") = std::nullopt,
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "flows_with_demands", &flows_with_demands,
        py::kw_only(), py::arg("size"), py::arg("demands"), py::arg("capacities"), py::arg("neighbors"), py::arg("source"), py::arg("sink"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "jaccard_distance", &jaccard_distance,
        py::arg("first"), py::arg("second"),
        py::call_guard<py::gil_scoped_release>());

    py::class_<py_lru_cache>(m, "LRUCache")
        .def_readwrite("capacity", &py_lru_cache::capacity)
        .def_readonly("hit", &py_lru_cache::hit)
        .def_readonly("miss", &py_lru_cache::miss)
        .def_readonly("cached", &py_lru_cache::cached)
        .def(py::init<unsigned>(), py::arg("capacity"))
        .def("get", &py_lru_cache::get, py::arg("key"))
        .def("set", &py_lru_cache::set, py::arg("key"), py::arg("value"))
        .def("to_json", &py_lru_cache::to_json)
        .def(
            "__getitem__",
            [](py_lru_cache &self, const py::object &key)
            {
                auto optional = self.get(key);
                if (optional.has_value())
                {
                    return *optional;
                }

                throw py::key_error(py::cast<std::string>(py::repr(key)));
            },
            py::arg("key"))
        .def(
            "__setitem__",
            [](py_lru_cache &self, const py::object &key, const py::object &value)
            {
                self.set(key, value);
            },
            py::arg("key"), py::arg("value"))
        .def(
            "__contains__",
            [](py_lru_cache &self, const py::object &key)
            {
                return self.get(key).has_value();
            },
            py::arg("key"));

    m.def(
        "maximum_flow", &maximum_flow,
        py::kw_only(), py::arg("size"), py::arg("capacities"), py::arg("neighbors"), py::arg("source"), py::arg("sink"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "smallest_circle", &smallest_circle,
        py::arg("points"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "tsp_solver", &tsp_solver,
        py::arg("cities"), py::kw_only(), py::arg("first") = 0, py::arg("heuristic_hint") = std::nullopt,
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "weighted_random", &weighted_random,
        py::arg("weights"), py::kw_only(), py::arg("count") = 1,
        py::call_guard<py::gil_scoped_release>());
}
