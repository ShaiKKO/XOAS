# IDR-0001: LLVM-Derived Engineering Quality System

**Status:** Accepted design; development toolchain verified; enforcement implementation pending

**Written-spec approval:** Approved by the user on 2026-08-28.

**Decision date:** 2026-08-28

**Decision owner:** User / architecture authority

**Normative standard:** [`../engineering/coding-standards.md`](../engineering/coding-standards.md)

## Context

XOAS is beginning from an evidence-first architecture with no product source or build system.
The project will generate and execute numerical code whose correctness depends on explicit IR ownership, numerical legality, target compatibility, and reproducible artifacts.
Permissive or informal source practices would make those obligations harder to audit and preserve.

The user requested a very high programming standard, an LLVM-like style, professional Doxygen blocks for files/classes/public interfaces, rare rationale-focused implementation comments, and an enforced rather than aspirational system.

## Decision

XOAS adopts an LLVM-derived source style and a Clang-native enforcement stack.

The design includes:

- standards-safe naming rather than libc++-style reserved implementation identifiers;
- `UpperCamelCase` types, `lowerCamelCase` functions/variables, and trailing-underscore private members;
- LLVM-style `///` Doxygen documentation and sparse rationale-focused `//` comments;
- separate policies for handwritten, generated, and vendored code;
- pinned `clang-format`, compiler diagnostics, `clang-tidy`, Doxygen, ASan, and UBSan;
- central CMake quality targets reproduced locally and in CI;
- protected `main` with required GitHub-hosted quality checks;
- narrow, named, justified suppressions only;
- evidence-based tests rather than a gameable global coverage percentage;
- a separate future decision for C++ exceptions and RTTI.

`gpu-2` is the primary development environment.
The quality-system designation does not qualify it as the Target 0 measurement host.

### Verified development-toolchain realization

The first implementation prerequisite is closed by [`../toolchain/gpu-2-development-toolchain-v1.md`](../toolchain/gpu-2-development-toolchain-v1.md) and its machine-readable [`../../toolchains/gpu-2-development-toolchain-v1.lock.json`](../../toolchains/gpu-2-development-toolchain-v1.lock.json).
Its stable configuration SHA-256 is `bf49239db2f78403ee592c1d1ddfaebdd7d9597433b6d39bbcfc7d0c4427347a`.

The verified realization selects:

- versioned LLVM/Clang 21.1.8 commands from the authenticated LLVM Noble 21 archive, without a project-managed global Clang alternative;
- Ubuntu Noble CMake 3.28.3, Ninja 1.11.1, and Doxygen 1.9.8;
- the host Ubuntu `libstdc++` headers/runtime for provisioning and quality probes only;
- exact entry-package versions, a complete 102-package installation closure, executable hashes, and ten behavioral probes;
- APT holds for the eight versioned LLVM entry packages, with explicit version-drift review for Ubuntu packages.

This realization does not decide XOAS's public ABI, exception model, or RTTI policy.
It does not install benchmark baselines, qualify `gpu-2` for Target 0 measurement, authorize GPU work, or create a self-hosted runner.

## Alternatives considered

### LLVM-native quality gates

Selected.
This approach aligns with the approved Clang-first C++23 direction, provides mature mechanical enforcement, and can run locally and in hosted CI without creating a custom analysis subsystem.

### Hermetic container or Nix environment first

Deferred.
Hermetic packaging can strengthen reproducibility later, but introducing it before the first build/test system would add infrastructure without changing the source contract.

### Bespoke XOAS linter

Rejected as the initial approach.
Custom checks add compiler-adjacent maintenance and are justified only after evidence shows a recurring rule that existing Clang tooling and review cannot enforce reliably.

### Literal LLVM conventions

Rejected where they conflict with ordinary C++ application constraints or XOAS clarity.
In particular, double-underscore identifiers are reserved to the implementation, and LLVM's upper-camel variable convention is replaced with lower-camel values to distinguish them from types.

## Consequences

### Benefits

- New code begins under one explicit style rather than accumulating migrations.
- Review focuses more on semantics because formatting and common defect classes are automated.
- Generated artifacts have a distinct, testable quality contract.
- Tool and policy upgrades are auditable.
- Protected-main checks turn standards into an enforceable merge gate.

### Costs

- The primary environment and CI require pinned tool installation and maintenance.
- Warning-clean and sanitizer-clean changes may take more effort initially.
- Doxygen coverage and strict naming require discipline at API design time.
- Hosted CI and branch protection require separate repository configuration.

### Risks

- Overly broad clang-tidy or warning sets can create noise and suppression pressure.
- Documentation checks can reward empty prose unless review enforces semantic usefulness.
- Toolchain drift can create unrelated churn if versions are not pinned.
- A self-hosted runner on the primary server would add unacceptable remote-execution authority unless separately approved and secured.

The standard mitigates these risks through explicit check selection, warnings-as-errors, reviewed upgrades, narrow suppressions, and semantic review.

## Architecture and semantic impact

This decision does not change Target 0, numerical modes, public ABI, canonical identity, cache invalidation, benchmark thresholds, or IR boundaries.
It strengthens how future implementations demonstrate conformance to those contracts.

Exceptions and RTTI are excluded because their choice affects error propagation and ABI rather than source style.
M1 must resolve them through another IDR before public interfaces depend on either.

## Affected files and interfaces

This accepted design creates or updates only documentation and repository operating policy.

The later implementation is expected to add, subject to an approved implementation plan:

- `.clang-format`;
- `.clang-tidy`;
- `.editorconfig`;
- Doxygen configuration;
- CMake quality modules and presets;
- test/sanitizer targets;
- GitHub workflow definitions;
- protected-branch required checks;
- root `AGENTS.md` commands and change-class requirements.

These paths are planned, not implemented by this decision record.

## Verification design

The implementation is accepted only when:

1. the pinned tools run on `gpu-2` and the selected GitHub-hosted runner;
2. compliant and intentionally non-compliant fixtures prove every configured rule;
3. formatter checking is non-mutating in CI;
4. compiler and clang-tidy diagnostics fail required jobs;
5. undocumented public APIs and malformed Doxygen fail documentation checks;
6. generated and vendored exclusions are exact and cannot hide first-party code;
7. ASan and UBSan catch known-negative fixtures before those fixtures are excluded from the passing suite;
8. protected `main` requires the verified checks;
9. root `AGENTS.md` records exact commands and tool versions;
10. the implementation is bound to an exact reviewed commit.

## Rollout sequence

1. Accept this design and normative standard.
2. Record AR-0001 Option 2 and approve the reversible `gpu-2` development-toolchain plan. This prerequisite is closed.
3. Pin, provision, and behaviorally verify the initial Clang/LLVM, CMake, Ninja, Doxygen, and analysis tool versions on `gpu-2`. Closed by the development-toolchain v1 record and lock.
4. Write a test-driven implementation plan for formatter, diagnostics, tidy, documentation, sanitizer, and CI fixtures.
5. Implement the smallest quality harness before or with the first authorized M1 source slice.
6. Verify protected-main checks before merging production C++.

This decision does not authorize product/compiler implementation before M0 closes.

## Reversal and migration

Changing naming, documentation syntax, source classification, protected-main authority, or the core enforcement stack requires a superseding IDR with migration cost and repository-wide evidence.
A tool-version upgrade that preserves this design may update the standard and configuration through an ordinary reviewed implementation decision.

Do not mass-reformat or rename unrelated existing code during migration.
Separate mechanical transformations from semantic changes.

## Open implementation inputs

The following remain deliberately unresolved for the enforcement implementation:

- exact additional warning and clang-tidy check manifests;
- GitHub workflow runner image and action digests;
- license/SPDX header text;
- exceptions and RTTI policy;
- whether a future self-hosted runner is justified.

An unresolved version is not permission to use an unpinned latest tool in production enforcement.

## Enforcement evidence

### Clang-Tidy 21 inventory and manifest

The locked `clang-tidy-21` binary reports 582 supported checks.
Its executable SHA-256 is
`1bc7e7d6a046528a574a82f7d5e7ec9c4d5ff11f1611a07df99040aa6d012f73`.
The normalized supported-check inventory has SHA-256
`a4a217e7f9ddd872009a497a087c1188cd0824a1a684a44e84fb8b514cc0251d`
and is retained in the operator-private quality evidence on `gpu-2`.

The initial repository manifest begins from `-*` and admits every check by its
full name.
It covers explicit core analyzer checks plus reviewed `bugprone`, `performance`,
`portability`, `readability`, selected `modernize`, `misc`, and LLVM header
policy checks.
Category wildcards, alpha diagnostics, platform-specific Objective-C checks,
embedded-CERT profiles, and checks that imply an exception/RTTI decision are
not admitted.
Target-specific SIMD diagnostics are also omitted because Target 0 intentionally
permits explicit ISA code once that implementation stage is authorized.
The proposed `clang-analyzer-cplusplus.SmartPtr` spelling was rejected by
`--verify-config`; the locked inventory exposes only the non-diagnostic
`clang-analyzer-cplusplus.SmartPtrModeling` checker, so neither is admitted.

`llvm-header-guard` is admitted and retained as an isolated upstream behavior
fixture, but Clang-Tidy 21 derives its suggested guard from the canonical
absolute host path.
That produces machine-specific `HOME_UBUNTU_...` names on `gpu-2` and different
names on hosted CI, contradicting XOAS's repository-relative guard contract.
The aggregate invocation therefore disables exactly `llvm-header-guard` and
replaces it with the tested `xoas-portable-header-guard` check, which derives
`XOAS_...` from the tracked repository path.
No other configured diagnostic is suppressed by the aggregate.

### Doxygen 1.9.8 policy

The locked Doxygen executable has SHA-256
`4ceed2d0bf847a5852838e0c2562f36dc364d482a1847e8780a8c1c9967739f7`.
The tracked `Doxyfile.in` has SHA-256
`3e2c67bbd7801e331b933faa6658e75dfc6ba62614b5faf805b1f4b9c54740b8`
and treats undocumented public interfaces, incomplete parameter documentation,
and malformed commands as errors.

The tracked-input collector excludes only
`tests/quality/fixtures/generated/output/` and
`tests/quality/fixtures/vendor/` from first-party documentation enforcement.
Isolated negative `.in` fixtures are not active C or C++ inputs.
Every selected handwritten file is also preflighted for a `/// \file` block,
and all HTML output and warning logs remain below the configured build tree.

### AddressSanitizer and UndefinedBehaviorSanitizer policy

The sanitizer build uses the locked Clang 21 compiler and compiler-rt package
`libclang-rt-21-dev` version
`1:21.1.8~++20251221032922+2078da43e25a-1~exp1~20251221153059.70`.
An interface target applies AddressSanitizer, UndefinedBehaviorSanitizer,
frame pointers, and no sanitizer recovery only to participating first-party
targets. It does not apply those flags globally or to vendored inputs.

The `asan-ubsan` preset fixes the fail-fast runtime contract to
`ASAN_OPTIONS=abort_on_error=1:halt_on_error=1:detect_leaks=1` and
`UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`. The negative harness
requires both a nonzero exit and the intended AddressSanitizer or
UndefinedBehaviorSanitizer diagnostic. A clean positive executable must pass
with leak detection enabled.

The original `gpu-2` provisioning capture recorded
`kernel.yama.ptrace_scope=2`, under which LeakSanitizer terminated with its
documented ptrace incompatibility. The user explicitly approved a persistent
development-host override on 2026-08-28. The root-owned mode `0644` file
`/etc/sysctl.d/90-xoas-lsan.conf` has SHA-256
`d36ae5ec5e8d2cbdf78a80b7b076629b7d71164e8bab7993be7aac4006b97188`
and sets `kernel.yama.ptrace_scope = 1`. This permits same-user process
inspection while retaining the ordinary ptrace relationship restriction; it
weakens the prior scope-2 administrative-only policy on this development host.
Remove that exact file and run `sudo sysctl --system` to restore the earlier
winning scope-2 policy from `/etc/sysctl.d/40-security_dev-sec.conf`.

This host policy is development infrastructure, not a Target 0 numerical or
measurement decision. The complete positive and two named negative sanitizer
tests must pass under the persistent setting before the sanitizer gate is
accepted.

### GitHub-hosted quality lock

The initial hosted lane uses only GitHub's `ubuntu-24.04` runner label and the
official `actions/checkout` action.
GitHub's API resolved release `v7.0.1` to commit
`3d3c42e5aac5ba805825da76410c181273ba90b1`; GitHub reports that commit's
signature verification as valid.
The workflow pins the commit SHA rather than the mutable release tag, grants
only `contents: read`, disables checkout credential persistence, and uses no
repository secret, cache, artifact upload, or self-hosted runner.

The conforming
[`../../toolchains/github-actions-v1.lock.json`](../../toolchains/github-actions-v1.lock.json)
binds that action identity, five required contexts, the exact development
toolchain lock ID, the LLVM archive fingerprint and file digests, and the exact
APT package versions installed on each ephemeral hosted runner.
The five contexts are `quality / repository-policy`,
`quality / static-quality`, `quality / debug-build-and-test`,
`quality / release-build-and-test`, and `quality / sanitizers`.
Hosted success and branch-protection enforcement remain separate gates until
the pushed revision completes and the live repository setting is verified.

Hosted run
[`33238861222`](https://github.com/ShaiKKO/XOAS/actions/runs/33238861222)
verified exact commit `99f3088fec5667aeda52756b39ff255ab4df4b96`.
All five required contexts concluded `success` on 2026-08-29.
The Debug runner recorded every step successful by `06:36:39Z`, while its
check context did not become terminal until `06:50:10Z`; Task 9 remained open
until that objective terminal result was available.

The exact manifest and identifier options are reviewable in the repository's
`.clang-tidy` file.
The accepted manifest enumerates 85 checks and has SHA-256
`a5772aebf276a6350c7f49a6ffa5569fdd5d4321a3334c152c60f6a639a577e3`.
The `--verify-config` gate rejects unavailable or misspelled diagnostics, and
the implementation tests the admitted rules against positive and isolated
negative fixtures before the manifest becomes required.
