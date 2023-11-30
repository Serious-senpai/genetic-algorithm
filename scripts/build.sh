g++ -O3 -Wall -shared -std=c++11 -fPIC $(python3-config --includes) -I extern/pybind11/include ga/_utils.cpp -o ga/_utils$(python3-config --extension-suffix)
