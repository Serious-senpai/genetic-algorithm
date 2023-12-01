#include "maximum_flow.cpp"
#include "weighted_random.cpp"

PYBIND11_MODULE(utils, m)
{
    m.def("maximum_flow", &maximum_flow, py::arg("size"), py::arg("capacities"), py::arg("neighbors"), py::arg("source"), py::arg("sink"));
    m.def("weighted_random", &weighted_random, py::arg("weights"), py::arg("count") = 1);
}
