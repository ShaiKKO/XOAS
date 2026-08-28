# Target 0 Corpus Policy

**Policy ID:** `xoas-target0-corpus-v0`

**Status:** Frozen M0 definition. Materialized support digests and parser validation remain M1 work.

## Purpose

The corpus tests the narrow Target 0 claim without allowing the benchmark set to drift toward favorable results. It contains:

- deterministic synthetic structures spanning the build-plan envelope;
- visible application-derived support for engineering and product-class evaluation;
- a frozen application-derived holdout whose measurements cannot shape the compiler;
- explicit smoke, design-training, proof-target, and product-class roles.

The corpus supplies support, shapes, runtime-value seeds, reuse classes, and tuning objectives. It does not supply compile-time `A` values.

## Manifests

- [`../../benchmarks/manifests/synthetic-target-v0.json`](../../benchmarks/manifests/synthetic-target-v0.json)
- [`../../benchmarks/manifests/application-target-v0.json`](../../benchmarks/manifests/application-target-v0.json)
- [`../../benchmarks/manifests/holdout-v0.json`](../../benchmarks/manifests/holdout-v0.json)

Manifests are append-only once used for tuning evidence. A semantic change creates a new version and retains the prior file.

## Deterministic PRNG contract

Synthetic support and ordinary finite runtime values use `PCG-XSL-RR 128/64`, the `pcg64` reference implementation from [`imneme/pcg-cpp`](https://github.com/imneme/pcg-cpp) pinned at commit `428802d1a5634f96bcd0705fab379ff0113bcf13`.

Each stochastic stream is constructed from two unsigned 128-bit values:

- the case's 32-lowercase-hex seed is the initial state seed;
- the stream selector is the first 128 bits of SHA-256 over the exact UTF-8 bytes `XOAS/v0/stream/<case_id>/<stream_role>` after substituting the manifest case ID and one role named below;
- hex is interpreted as one big-endian integer at the manifest boundary and passed as the numeric 128-bit value to the pinned `pcg64(initial_state, stream_selector)` constructor;
- unsigned arithmetic follows the pinned reference implementation.

The stream roles are `support`, `lhs-values`, `rhs-values`, and `row-order`. Independent roles never reuse state.

### Unbiased bounded draw

For exclusive upper bound `b` with `1 <= b < 2^64`:

1. compute `threshold = (-b) mod b` in unsigned 64-bit arithmetic;
2. draw `r` from `pcg64` until `r >= threshold`;
3. return `r mod b`.

No floating-point sampling participates in support generation.

### Sampling without replacement

To select `q` elements from ordered candidates `v[0..p)`:

1. for `i` from `0` through `q-1`, draw `j = i + bounded(p - i)`;
2. swap `v[i]` and `v[j]`;
3. select the first `q` elements.

Candidate order is always specified below. Final coordinates are deduplicated and sorted lexicographically by `(row, column)`.

## Synthetic support algorithms

Coordinates are zero-based pairs `(i,k)` with `0 <= i < M` and `0 <= k < K`. Linear coordinate `x` maps to `(x / K, x mod K)` using integer division.

### `random_exact`

Create candidates `0..M*K-1`, sample exactly `target_coordinate_count` without replacement, map to coordinates, and sort.

### `banded`

For every row `i`, include every valid `k` satisfying `-half_bandwidth <= k-i <= half_bandwidth`. No random draws are consumed.

### `diagonal_offsets`

For every offset in the manifest's ordered offset list and every row `i`, include `(i, i+offset)` when the column is in range. Union, deduplicate, and sort. No random draws are consumed.

### `block_sparse_exact`

Require `M` divisible by `block_rows` and `K` divisible by `block_columns`. Enumerate block IDs in row-major block-grid order, select exactly `selected_block_count` without replacement, and include every coordinate in each selected block.

### `repeated_rows`

Generate `signature_count` distinct column sets. Each set samples exactly `entries_per_signature` columns from `0..K-1`; if a set duplicates an earlier signature, continue drawing until distinct. Build a balanced signature-ID list by repeating `0..signature_count-1` until it has `M` entries, then Fisher-Yates shuffle it with the `row-order` stream. Row `i` receives its assigned signature.

### `power_law_rows_v1`

Create row ranks `0..M-1` and Fisher-Yates shuffle them with the `row-order` stream. For rank `r`, set:

`degree(r) = max(min_degree, floor(max_degree / (r + 1)))`

Require `degree(r) <= K`. Sample that many columns without replacement for the row. This is an integer, exponent-1 heavy-tail construction; the family name does not imply a statistically fitted real-world power law.

### `mixed_band_block_scatter_v1`

1. Generate a banded set with the declared half-bandwidth.
2. Enumerate declared-size blocks in row-major block-grid order and remove any block containing a coordinate already in the band.
3. Select the declared number of remaining blocks without replacement and add their full coordinates.
4. Enumerate every matrix coordinate not yet present, sample the declared scatter count without replacement, add it, and sort.

The v0 mixed case has an exact coordinate count because blocks overlapping the band are rejected before selection.

## Runtime finite-value generation

Ordinary performance inputs are generated once outside timing and shared logically across all implementations.

For each present `A` coordinate in canonical row-major order and each dense `B` element in row-major order:

1. draw `u = bounded(2001) - 1000` as a signed integer;
2. if `u == 0`, replace it with `1`;
3. convert to `float32` and divide by `128.0f`.

The resulting finite nonzero values are exactly representable binary fractions before arithmetic. `A` values remain runtime data and may differ between compatible invocations; the benchmark merely freezes one deterministic buffer per run for paired fairness.

Special values, cancellation, wide magnitudes, signed zeros, subnormals, NaNs, and infinities belong to the M2 numerical verification suites and are never inferred from ordinary performance seeds.

## Application-source authority and normalization

The application structures come from the [NIST Matrix Market Harwell-Boeing collection](https://math.nist.gov/MatrixMarket/data/Harwell-Boeing/). Each manifest pins the download URL, compressed bytes, compressed SHA-256, decompressed SHA-256, Matrix Market header, stored coordinate count, and normalization facts.

Normalization is exact:

1. decompress the pinned artifact;
2. require the declared Matrix Market coordinate header and dimensions;
3. convert one-based indices to zero-based indices;
4. treat every stored coordinate as structurally present, regardless of its numeric field;
5. for `symmetric`, add `(column,row)` for every off-diagonal stored coordinate;
6. reject out-of-range coordinates and duplicate normalized coordinates;
7. sort lexicographically by `(row,column)`;
8. assert the manifest's normalized coordinate count;
9. discard source numeric values from the compiled instance and generate runtime values using the case seed.

This rule is intentionally visible for `ARC130`: the upstream file stores 1,282 coordinates, 245 of which have numeric value zero. All 1,282 coordinates remain present support. NIST's page reports numerical nonzeros separately; XOAS does not substitute that count for stored structure.

## Partition and role rules

### Smoke

Small cases validate parsing, generation, canonicalization, oracle, compilation, and benchmark plumbing. Smoke results never support performance claims.

### Design training

Visible synthetic cases may shape transforms, features, bounded schedule ranges, and pruning rules. Every design choice influenced by their evidence is recorded.

### Proof target

The initial proof candidates are frozen before generated-kernel performance exists:

- `syn-proof-repeated-m128-k128-n16-s4-d12`;
- `syn-proof-banded-m192-k192-n32-hb4`;
- `app-west0067-n16-r1e7`.

A proof-gate claim requires the lower `95%` paired-speedup confidence bound to reach `2.0` against the fastest applicable generic baseline on at least one of them. All three results are published once run.

### Product class

The product-class aggregate is the six synthetic cases whose IDs begin `syn-product-` plus all six cases in `application-target-v0.json`. Unless an approved preregistration narrows this set before tuning measurements exist, the geometric mean includes every supported case and reports unsupported/fallback outcomes explicitly.

### Holdout

`ARC130` and `ASH85` cases are frozen in `holdout-v0.json`. Their source identities are public, but their measurements may not influence:

- transformations or structural families;
- cost-model features;
- schedule values/ranges;
- code-size or family-admission thresholds;
- baseline configuration policy;
- proof/product corpus membership.

Holdout measurements are authorized only by the M7 acceptance procedure. Early inspection creates an unblinding incident, invalidates the affected claim, and requires a versioned replacement frozen before further design work.

## Reuse and tuning classes

The manifests use expected invocation counts `10^3`, `10^7`, and `10^9` to cover low, medium, and very high reuse while keeping the corpus finite. Benchmarks do not literally execute the expected count; they measure execution and compute lifecycle totals/break-even under the protocol.

Tuning budgets are per case and include search plus candidate compilation. M0 values are:

- smoke: `1,000 ms`;
- design training: `60,000 ms`;
- proof target: `300,000 ms`;
- product class or holdout: `600,000 ms`.

Analysis time remains separately reported even when the tuning-budget accounting groups it differently in later APIs.

## Falsification and anti-cherry-picking rules

- Do not add a case to a claimed aggregate after seeing that it wins.
- Do not remove, resize, re-seed, or relabel a losing case without a versioned architecture decision and preserved original evidence.
- Application support is based on stored coordinates, not a threshold applied to values.
- No source matrix value becomes a compile-time constant in Target 0.
- A case that selects fallback remains in aggregate reporting according to the preregistered statistical policy.
- A failed corpus materially narrows or rejects the claim; it does not authorize broader machinery.

## Materialization gate

M1 must implement and test a manifest parser and support materializer that reproduces every declared coordinate count, emits canonical support bytes, records content digests, rejects duplicate/out-of-range/malformed sources, and passes cross-platform golden vectors for the pinned PCG streams. Until then, these manifests are frozen specifications rather than executable fixtures.
