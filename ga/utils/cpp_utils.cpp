#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "maximum_flow.cpp"
#include "tsp_solver.cpp"
#include "weighted_random.cpp"

namespace py = pybind11;

PYBIND11_MODULE(cpp_utils, m)
{
    m.def("maximum_flow", &maximum_flow, py::kw_only(), py::arg("size"), py::arg("capacities"), py::arg("neighbors"), py::arg("source"), py::arg("sink"));
    m.def("tsp_solver", &tsp_solver, py::arg("cities"));
    m.def("weighted_random", &weighted_random, py::arg("weights"), py::kw_only(), py::arg("count") = 1);
}
