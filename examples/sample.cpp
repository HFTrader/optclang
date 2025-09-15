#include <iostream>
#include <vector>
#include <algorithm>

int main() {
    std::vector<int> numbers = {5, 2, 8, 1, 9, 3};
    
    // This code has optimization opportunities
    int sum = 0;
    for (int i = 0; i < numbers.size(); ++i) {
        sum += numbers[i];
    }
    
    // Dead code that should be eliminated
    int unused_var = 42;
    if (false) {
        std::cout << "This will never execute" << std::endl;
    }
    
    // Sort the vector
    std::sort(numbers.begin(), numbers.end());
    
    std::cout << "Sum: " << sum << std::endl;
    std::cout << "Sorted numbers: ";
    for (const auto& num : numbers) {
        std::cout << num << " ";
    }
    std::cout << std::endl;
    
    return 0;
}
