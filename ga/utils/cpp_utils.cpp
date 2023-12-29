#include <optional>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "crowding_distance.cpp"
#include "fake_tsp_solver.cpp"
#include "flows_with_demands.cpp"
#include "jaccard_distance.cpp"
#include "maximum_flow.cpp"
#include "maximum_weighted_flow.cpp"
#include "tsp_solver.cpp"
#include "weighted_random.cpp"

namespace py = pybind11;

PYBIND11_MODULE(cpp_utils, m)
{
    m.def(
        "crowding_distance_sort", &crowding_distance_sort,
        py::arg("sets"), py::kw_only(), py::arg("k") = 2,
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "fake_tsp_solver", &fake_tsp_solver,
        py::arg("cities"), py::kw_only(), py::arg("first") = 0, py::arg("heuristic_hint") = std::optional<std::vector<unsigned>>(),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "flows_with_demands", &flows_with_demands,
        py::kw_only(), py::arg("size"), py::arg("demands"), py::arg("capacities"), py::arg("neighbors"), py::arg("source"), py::arg("sink"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "jaccard_distance", &jaccard_distance,
        py::arg("first"), py::arg("second"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "maximum_flow", &maximum_flow,
        py::kw_only(), py::arg("size"), py::arg("capacities"), py::arg("neighbors"), py::arg("source"), py::arg("sink"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "maximum_weighted_flow", &maximum_weighted_flow,
        py::kw_only(), py::arg("size"), py::arg("capacities"), py::arg("neighbors"), py::arg("flow_weights"), py::arg("source"), py::arg("sink"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "tsp_solver", &tsp_solver,
        py::arg("cities"), py::kw_only(), py::arg("first") = 0, py::arg("heuristic_hint") = std::optional<std::vector<unsigned>>(),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "weighted_random", &weighted_random,
        py::arg("weights"), py::kw_only(), py::arg("count") = 1,
        py::call_guard<py::gil_scoped_release>());
}
