#ifndef XOAS_TESTS_QUALITY_FIXTURES_DOCS_COMPLIANT_H
#define XOAS_TESTS_QUALITY_FIXTURES_DOCS_COMPLIANT_H

/// \file
/// Declares documentation-policy acceptance interfaces for the quality harness.

namespace xoas::quality {

/// Holds an immutable fixture value used to prove public documentation policy.
///
/// The stored value remains unchanged for the object's lifetime.
class DocumentedValue final {
public:
  /// Constructs a fixture value without allocation.
  ///
  /// \param value The immutable value to retain.
  explicit DocumentedValue(int value) : value_(value) {
  }

  /// Reads the retained value without mutation.
  ///
  /// \returns The value supplied at construction.
  [[nodiscard]] int value() const {
    return value_;
  }

private:
  int value_;
};

} // namespace xoas::quality

#endif // XOAS_TESTS_QUALITY_FIXTURES_DOCS_COMPLIANT_H
