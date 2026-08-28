# Target 0 Benchmark and Evidence Protocol

**Protocol ID:** `xoas-benchmark-protocol-v1`

**Status:** Locked M0 measurement contract. No performance result exists yet.

**Applies to:** Single-threaded `float32`, contiguous row-major Target 0 candidates and applicable baselines.

## Purpose

This protocol defines when an XOAS timing result is reproducible evidence and when it is only diagnostic data. Correctness, legality, compatibility, performance, and lifecycle cost are separate gates. A completed timing loop proves none of the others.

Every retained run must conform to [`../../schemas/benchmark-result-v1.schema.json`](../../schemas/benchmark-result-v1.schema.json) once that schema exists. The human-readable JSON record is evidence interchange; M1 will define canonical semantic identities.

## Evidence classes

### `smoke`

Validates harness mechanics, adapter invocation, affinity, raw-sample retention, and result serialization. It may use one process and reduced samples. It makes no performance claim and cannot close a research gate.

### `search`

Ranks or prunes verified candidates during a bounded tuning run. It uses paired interleaving and at least three fresh processes, but it may use fewer reboot campaigns than a gate run. Search data may influence the selected candidate only within the preregistered search space. It cannot be cited as holdout or gate evidence.

### `gate`

Supports a proof, product-class, regression, go/no-go, or scope-narrowing claim. A gate run follows every requirement below, uses frozen manifests, and retains raw data and artifacts. Repeating until a favorable result appears invalidates the claim unless every attempt is retained and the stopping rule was preregistered.

## Required preregistration

Before compiling candidates for a gate claim, freeze a manifest that identifies:

- exact corpus cases and visible/holdout role;
- target manifest and compatibility digest;
- numerical mode and comparison policy;
- admitted baselines and bounded configurations;
- candidate families and schedule/search bounds;
- compiler/search-rule versions;
- expected invocation classes and lifecycle objective;
- sample, process, reboot, confidence, noise-floor, and stopping rules;
- proof/product threshold being tested;
- bootstrap seed and input seeds.

Changing a load-bearing item creates a new preregistration version. The old run remains evidence.

## Candidate eligibility before timing

An implementation may enter the timed phase only when all applicable checks pass outside the timed region:

1. problem and manifest validation;
2. exact support normalization and digest verification;
3. active numerical-contract validation;
4. structural legality, complete contribution coverage, and duplicate detection for generated plans;
5. successful compile/load and ABI check;
6. target/ISA/OS/ABI compatibility validation;
7. differential comparison with the independent oracle on required finite and special-value cases;
8. guard-page and allowed alignment checks where generated memory accesses are involved;
9. fallback availability and correctness;
10. implementation-specific setup success.

Failed and inapplicable candidates receive result records with the reason and retained diagnostics. They are not assigned synthetic slow timings.

## Target and environment qualification

### Identity capture

Capture at run time:

- CPU vendor, family, model, stepping, model name, microcode, and exposed ISA flags;
- socket, NUMA, core, hardware-thread, and SMT-sibling topology;
- L1 data/instruction, L2, and LLC hierarchy;
- memory size and page configuration;
- OS distribution, kernel, libc, and virtualization/container boundary;
- clock source and timer implementation;
- compiler, linker, standard library, and loaded baseline libraries with file hashes;
- target manifest digest, repository commit, tree state, and relevant artifact hashes;
- observable governor, frequency range/current state, turbo/boost, power limits, thermal state, and throttling indicators;
- PMU access policy and available events.

Unavailable facts are represented explicitly as unavailable with a reason. They are never omitted or guessed.

### Affinity and interference

- Bind the benchmark process and benchmark thread to one preregistered physical core.
- Bind memory to the preregistered NUMA node or record why single-node first-touch is the accepted equivalent.
- No candidate or baseline may create worker threads. Verify effective thread count during a smoke run and spot-check gate processes.
- Keep the selected core's SMT sibling offline, isolated, or demonstrably idle under the accepted target decision. If the host cannot provide that control, record the limitation and do not promote the run to gate evidence without explicit acceptance.
- Record system load and unexpected context switches. Do not silently delete a slow sample because the machine was busy.
- Run gate campaigns during an exclusive-use window under the target qualification decision.

### Frequency and thermal state

Use a fixed performance policy when the host exposes safe controls. Otherwise record the observable state before and after every process and characterize the resulting noise before gate use. Warm the CPU to a declared steady state without including warm-up in samples. Record temperature/throttling telemetry where available.

## Build and artifact controls

For every implementation retain:

- exact source/plan identity and compiler command;
- compiler/linker version and executable path hash;
- object/shared-library/executable hash and size;
- generated source or lower IR where applicable;
- disassembly for generated candidates and code-generating baselines;
- library version, loaded file identity, dispatch controls, and thread controls;
- setup/prepack/JIT state and persistent byte counts;
- warnings and failed build attempts relevant to the search.

Generated source, object, metadata, and disassembly are review artifacts. Do not hand-edit a generated file; change the generator or plan.

## Deterministic inputs

- Support comes from the frozen case manifest.
- Present `A` values and dense `B` values are generated from fixed versioned PRNG algorithms and seeds.
- A listed coordinate remains structurally present even when a generated value is `+0` or `-0`.
- Input buffers are initialized outside timed regions and reused or regenerated according to the preregistered cache-state scenario.
- Each implementation receives byte-identical logical values. Format conversion must be verified and accounted separately.
- The output starts in the state required by overwrite semantics. `beta=0` or equivalent must not read an uninitialized `C` as a semantic input.

## Clock and calibration

Use a monotonic raw/high-resolution clock whose implementation is recorded. On x86, a TSC-derived clock is acceptable only after invariant/synchronization behavior is established for the target.

For each implementation and case:

1. estimate a single-call duration after warm-up;
2. choose an integer iteration count that makes one timed sample at least `20 ms` and at most `200 ms` where practical;
3. use the same iteration count for paired candidate/baseline implementations when doing so does not push either outside `10 ms` to `400 ms`; otherwise retain per-implementation counts and normalize by invocations;
4. freeze iteration counts before retained timed rounds;
5. record calibration trials separately from raw gate samples.

Timer overhead must be measured in a harness smoke test and remain below `0.1%` of the minimum retained sample duration.

## Warm-up

Before retained samples in each fresh process:

- invoke every implementation in randomized order for at least five calibration-sized samples;
- require the last three normalized durations for each implementation to lie within `5%` of their median, or continue up to 20 warm-up samples;
- if stability is not reached, mark that process invalid with all warm-up data retained; do not time until stable;
- touch all input, output, prepack, and code paths required by the declared warm-cache scenario;
- run one untimed oracle check after warm-up.

Warm-up is never mixed into timed statistics.

## Interleaved timed sampling

A **round** contains exactly one retained sample for every eligible implementation in the comparison set.

- Generate a deterministic pseudorandom permutation of implementation order for each round from the preregistered order seed.
- Execute implementations in that order with no unrelated work between them.
- Retain campaign, reboot, process, round, within-round order, implementation ID, iteration count, elapsed nanoseconds, and checksum for every sample.
- Use at least 30 retained rounds per fresh process for a gate run.
- Use five fresh processes per reboot campaign.
- Use two gate campaigns separated by a verified reboot, for at least ten process-level observations and 300 samples per implementation.
- A product-class corpus may split cases across sessions, but every case uses the same registered process/round minimum.
- Search runs use at least 15 rounds in each of three fresh processes.
- Smoke runs use at least five rounds in one process.

Each sample overwrites `C` for the declared iteration count. Immediately after stopping the timer, consume a deterministic checksum from `C` through a compiler-visible observation mechanism and record it. Checksum computation is outside the timed interval. Compare the final logical output with the oracle outside timing at least once per implementation per fresh process.

## Sample invalidation and outliers

Do not remove a sample because its duration is inconvenient or statistically extreme.

Invalidate only under a preregistered objective failure, such as:

- process affinity changed or could not be verified;
- implementation returned an error or crashed;
- output/checksum/canary verification failed;
- iteration count or timer record is corrupt;
- an explicitly monitored thermal or host reset threshold was crossed;
- the process created forbidden worker threads;
- the target identity changed.

Retain the invalid sample, failure reason, and process context. Replace the entire affected fresh process run, not an individual slow round. Gate stopping occurs only after the preregistered number of valid processes or the preregistered failure limit is reached.

## Primary statistics

All durations are normalized to nanoseconds per invocation before summarization.

### Per implementation

1. Compute the median normalized duration within each fresh process.
2. The run point estimate is the median of process medians.
3. Report process-level median absolute deviation and interquartile range.
4. Retain minimum and maximum for diagnostics but never use the minimum as the claimed performance.

### Paired comparison

For each matched round, compute:

`speedup = baseline_ns_per_invocation / candidate_ns_per_invocation`

Compute a median paired speedup within each process, then the median across process medians.

Generate a two-level percentile bootstrap confidence interval by resampling fresh processes with replacement and then paired rounds with replacement inside each selected process. Use `10,000` bootstrap replicates, the preregistered `PCG-XSL-RR 128/64` seed, and a two-sided `95%` interval.

For multiple baselines, compare the candidate with the fastest correct applicable baseline for each case. Baseline selection is based on each baseline's registered process-median estimate, with selection and uncertainty recorded. Also publish every individual baseline comparison.

### Winner, loser, and tie

The practical noise floor is `2%` for v1 unless a stricter preregistered target characterization replaces it.

- Candidate winner: paired-speedup lower confidence bound is greater than `1.02`.
- Baseline winner: paired-speedup upper confidence bound is less than `1 / 1.02`.
- Tie: neither winner rule is met, including when the interval crosses parity or the effect remains inside the noise floor.
- Invalid/inconclusive: protocol, correctness, compatibility, or environment gate failed.

Do not select a candidate as a runtime plan when it ties or loses against the fastest fallback. A tie may remain a research result.

## Research-gate decisions

The general winner rule is weaker than the research thresholds. Gate claims use the confidence bound:

- **Proof gate:** at least one preregistered nontrivial workload has a paired-speedup lower `95%` confidence bound of at least `2.0` versus the fastest applicable generic baseline.
- **Product-class aggregate:** bootstrap the geometric mean across the frozen target subset, preserving case/process hierarchy; its lower `95%` bound must be at least `1.5`.
- **Real-structure requirement:** at least one preregistered application-derived case has a paired-speedup lower `95%` bound of at least `2.0`.

Every workload remains in the published table. A passing aggregate does not erase losses, ties, unsupported cases, or fallback selections.

## Hardware counters and disassembly

Counters are explanatory evidence, not a substitute for elapsed time.

- Collect cycles and instructions when trustworthy PMU access exists.
- Collect available L1/L2/LLC miss, branch miss, stall, and vector evidence in separate counter runs if multiplexing would perturb primary timing.
- Record event names, raw encodings where relevant, kernel/perf version, multiplex scaling, and permission failures.
- If PMU access is unavailable, set status to unavailable and retain the error. Do not estimate counters from wall time.
- Inspect generated disassembly for ISA requirements, spills, unexpected calls/branches, and code size.

## Lifecycle and break-even accounting

Report separately:

- analysis;
- candidate generation and search;
- source/IR emission;
- compilation/linking or JIT;
- format conversion, handle inspection/optimization, packing, and prepack;
- per-invocation execution;
- scratch, prepack, object, and executable code bytes.

For expected invocation count `R`:

`T_total(R) = T_analysis + T_search + T_compile + T_prepack + R * T_execute`

Use the actual baseline setup model in the corresponding baseline total. Break-even is the smallest nonnegative integer `R` for which the generated plan's supported lifecycle estimate is below the fastest compatible fallback's estimate. Report no finite break-even when the generated execution time is not faster.

## Holdout governance

- Holdout identities and provenance may be public for reproducibility, but their measurements may not influence transformation design, features, schedule ranges, thresholds, or admission.
- Run the frozen holdout only at the milestone authorized by the build plan.
- If holdout measurements are inspected early, record an unblinding incident, invalidate the affected claim, and freeze a versioned replacement before further tuning.
- Never move a difficult visible case into holdout or remove a difficult holdout after results are known.

## Required result and artifact retention

Each run retains:

- conforming result JSON and preregistration manifest;
- ordered raw samples, calibration, warm-up, and invalid records;
- correctness inputs/results and failure seeds;
- exact target/environment snapshot;
- source/plan/schedule records;
- compiler commands, logs, objects, executables, and disassembly;
- library identities and setup records;
- statistical program/version, seed, and output;
- failed, losing, tied, and unsupported configurations;
- checksum evidence and reproduction command;
- explicit performance-claim boolean and gate decision.

Artifacts use content digests and repository-relative or content-store URIs. Credentials and host access coordinates are never stored.

## Prohibited claims

- No claim from a smoke or search run.
- No benchmark of an unverified or incompatible candidate.
- No comparison only with a naive loop when a serious baseline applies.
- No best-of-minimum timing headline.
- No dropped losing/failed evidence.
- No post-result changes to thresholds, corpus, sample count, or outlier policy.
- No extrapolated PMU values.
- No claim tied only to an uncommitted dirty tree.
- No “Target 0 closed” statement without the exact commit, target manifest, raw evidence, and acceptance record.

## Reproduction boundary

M2 must provide a one-command runner that consumes a frozen manifest and writes a new immutable run directory without overwriting prior evidence. Until that executable exists, this protocol is a locked design contract rather than an executed benchmark capability.
