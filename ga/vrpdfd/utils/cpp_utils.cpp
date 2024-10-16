#include "config.hpp"
#include "decode.hpp"
#include "educate.hpp"
#include "local_search.hpp"
#include "paths_from_flow.hpp"

namespace py = pybind11;

PYBIND11_MODULE(cpp_utils, m)
{
    m.def(
        "setup", &setup,
        py::arg("low"), py::arg("high"), py::arg("w"), py::arg("x"), py::arg("y"),
        py::arg("truck_distance_limit"), py::arg("drone_distance_limit"),
        py::arg("truck_capacity"), py::arg("drone_capacity"),
        py::arg("truck_cost_coefficient"), py::arg("drone_cost_coefficient"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "setup_path_cache", &setup_path_cache,
        py::arg("capacity"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "path_cache_info", &path_cache_info,
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "path_order", &path_order,
        py::arg("path"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "decode", &decode,
        py::arg("truck_paths"), py::arg("drone_paths"),
        py::call_guard<py::gil_scoped_release>());
    m.def(
        "educate", &educate,
        py::arg("py_individual")); // Do not release the GIL
    m.def(
        "local_search", &local_search,
        py::arg("py_individual"), py::arg("py_updater")); // Do not release the GIL
    m.def(
        "paths_from_flow", &paths_from_flow,
        py::arg("truck_paths_count"), py::arg("drone_paths_count"), py::arg("flows"), py::arg("neighbors"),
        py::call_guard<py::gil_scoped_release>());
}
