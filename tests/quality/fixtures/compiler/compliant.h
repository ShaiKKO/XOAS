#ifndef XOAS_TESTS_QUALITY_FIXTURES_COMPILER_COMPLIANT_H
#define XOAS_TESTS_QUALITY_FIXTURES_COMPILER_COMPLIANT_H

/// \file
/// Declares warning-policy acceptance interfaces for the quality harness.

namespace xoas::quality {

/// Doubles a small fixture value without narrowing or allocation.
///
/// \param value A value whose doubled result is representable as `int`.
/// \returns Twice `value`.
[[nodiscard]] int doubleFixtureValue(int value);

} // namespace xoas::quality

#endif // XOAS_TESTS_QUALITY_FIXTURES_COMPILER_COMPLIANT_H
