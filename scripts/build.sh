params="-O3 -Wall -shared -std=c++17 -fPIC $(python3-config --includes) -I extern/pybind11/include"
extension=$(python3-config --extension-suffix)

g++ $params ga/utils/cpp_utils.cpp -o ga/utils/cpp_utils$extension
