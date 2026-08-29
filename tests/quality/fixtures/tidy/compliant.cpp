/// \file
/// Provides static-analysis acceptance input for the quality harness.

namespace xoas::quality {

/// Returns the non-negative form of a small fixture value.
///
/// \param value A value other than the minimum representable `int`.
/// \returns `value` when non-negative, otherwise its negation.
[[nodiscard]] constexpr int normalizeFixtureValue(int value) {
  return value < 0 ? -value : value;
}

static_assert(normalizeFixtureValue(-4) == 4);

} // namespace xoas::quality
