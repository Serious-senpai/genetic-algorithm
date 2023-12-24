g++ --version

params="-O3 -Wall -shared -std=c++17 -fPIC $(python3-config --includes) -I extern/pybind11/include"
extension=$(python3-config --extension-suffix)

if [ "$1" == "debug" ]
then
    params="$params -D DEBUG"
    echo "Building in debug mode"
fi

g++ $params ga/utils/cpp_utils.cpp -o ga/utils/cpp_utils$extension
echo "Built ga/utils/cpp_utils$extension"

g++ $params ga/vrpdfd/utils/cpp_utils.cpp -o ga/vrpdfd/utils/cpp_utils$extension
echo "Built ga/vrpdfd/utils/cpp_utils$extension"
