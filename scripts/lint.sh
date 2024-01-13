echo "Running clang-tidy"
params="-O3 -Wall -std=c++17 -fPIC $(python3-config --includes) -I extern/pybind11/include -I extern/lemon-1.3.1"
for file in $(find ga/ -type f -name "*.cpp")
do
    clang-tidy $file -- $params &
done
wait

echo "Running autopep8"
autopep8 --exclude extern -aaair .

echo "Running mypy"
mypy .

echo "Running flake8"
flake8 .

echo "Running pyright"
pyright .

echo "Converting all line endings"
find . -type f -exec dos2unix {} \; > /dev/null 2>&1
