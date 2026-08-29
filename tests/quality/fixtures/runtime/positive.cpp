/// \file
/// Provides sanitizer-policy acceptance behavior for the quality harness.

#include <array>
#include <numeric>

/// Runs deterministic, allocation-free sanitizer acceptance behavior.
///
/// \returns Zero when the checked accumulation produces the expected value.
int main() {
  constexpr std::array<int, 4> Values{1, 2, 3, 4};
  const int Sum = std::accumulate(Values.begin(), Values.end(), 0);
  return Sum == 10 ? 0 : 1;
}
