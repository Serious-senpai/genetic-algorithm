params="-O3 -Wall -shared -std=c++11 -fPIC $(python3-config --includes) -I extern/pybind11/include"
extension=$(python3-config --extension-suffix)

g++ $params ga/utils/utils.cpp -o ga/utils/utils$extension
