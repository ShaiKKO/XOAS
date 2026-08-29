# IDR-0001: LLVM-Derived Engineering Quality System

**Status:** Accepted design; enforcement implementation pending

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
2. Resolve AR-0001's remaining Target 0 measurement decision and approve a reversible provisioning plan for `gpu-2`.
3. Pin and provision the initial Clang/LLVM, CMake, Ninja, Doxygen, and analysis tool versions.
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

The following remain deliberately unresolved until the primary environment is provisioned and inspected:

- exact Clang/LLVM, CMake, Ninja, Doxygen, and Python formatter versions;
- exact additional warning and clang-tidy check manifests;
- GitHub workflow runner image and action digests;
- license/SPDX header text;
- exceptions and RTTI policy;
- whether a future self-hosted runner is justified.

An unresolved version is not permission to use an unpinned latest tool in production enforcement.
