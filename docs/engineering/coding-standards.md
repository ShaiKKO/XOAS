# XOAS Coding and Engineering Standards

**Status:** Approved design; mandatory for new first-party code.

**Approval:** User / architecture authority, 2026-08-28.

**Enforcement state:** The contract is active for review, but its automated toolchain is not yet implemented.
Do not claim automated enforcement until the pinned tools, repository configuration, CI checks, and protected-branch rules are installed and verified.

**Decision record:** [`../adr/IDR-0001-engineering-quality-system.md`](../adr/IDR-0001-engineering-quality-system.md).

## 1. Purpose

XOAS requires production-grade source whose correctness, intent, numerical constraints, and ownership boundaries remain understandable under long-term compiler and research development.
Mechanical consistency is automated wherever mature tools can enforce it.
Semantic clarity, architecture discipline, and useful documentation remain review obligations rather than being replaced by a linter score.

This standard is derived from the [LLVM Coding Standards](https://llvm.org/docs/CodingStandards.html), with explicit XOAS deviations recorded below.
It does not import LLVM rules that would change XOAS architecture without a separate decision.

## 2. Scope and source classes

### 2.1 Handwritten first-party code

All XOAS-owned C++, CMake, Python, schemas, tests, and supporting scripts follow the complete applicable standard and pass the configured quality gates.

### 2.2 Generated code

Generated source is owned by its generator, not edited by hand.
It must be deterministic for identical canonical inputs and generator versions, carry provenance and a do-not-edit notice, pass formatting and compilation checks, and satisfy the numerical, ABI, compatibility, and differential-test obligations of its artifact class.
Generated source is exempt from hand-authored Doxygen coverage and ordinary handwritten identifier style only where the generator contract documents the exception.

### 2.3 Vendored and third-party code

Vendored code is isolated from first-party enforcement and included as a system dependency where supported.
Do not reformat or patch third-party source merely to satisfy XOAS style.
Any necessary patch is minimal, retained separately, attributed, licensed, tested, and version-pinned.
Warnings originating from first-party use of a third-party API remain XOAS defects.

## 3. Identifier rules

Use descriptive names that communicate semantics and ownership.
Avoid abbreviations unless they are established mathematical, ISA, or project terminology and remain unambiguous in context.

| Entity | Required form | Example |
|---|---|---|
| Class, struct, enum, concept, and type alias | `UpperCamelCase` | `ContributionGraph` |
| Template type parameter | `UpperCamelCase` | `ScalarType` |
| Function and method | `lowerCamelCase` verb phrase | `verifyCoverage()` |
| Local variable and parameter | `lowerCamelCase` noun | `outputRow` |
| Private data member | `lowerCamelCase_` | `targetFeatures_` |
| Namespace | lowercase, concise | `xoas::structure` |
| Macro | `UPPER_SNAKE_CASE` | `XOAS_ASSERT` |
| Compile-time constant | `UpperCamelCase` | `MaximumVectorWidth` |
| Enumerator | `UpperCamelCase` | `NumericalMode::Contracted` |

XOAS deliberately uses lower-camel variables instead of LLVM's upper-camel variable convention so values are visually distinct from types and private members have a consistent suffix.

The following identifiers are prohibited in first-party code:

- any identifier containing `__`;
- any identifier beginning with an underscore followed by an uppercase letter;
- any global-namespace identifier beginning with an underscore;
- Hungarian notation;
- placeholder names such as `tmp`, `data`, `thing`, or numbered variants when a semantic name is possible;
- single-letter names outside a tiny, conventional mathematical or index scope.

C++ reserves double-underscore and other implementation identifiers; violating that boundary is not an LLVM-inspired style choice for an ordinary application.

IR and artifact names must identify their ownership level.
Problem, Structure, Reduction, Bilinear, Schedule, and Machine concepts must not use interchangeable generic names that hide a boundary crossing.

## 4. Documentation and comments

Comments are professional English prose with correct capitalization and punctuation.
They explain contracts, intent, rationale, invariants, or constraints rather than narrating syntax.

### 4.1 Required Doxygen documentation

Use LLVM-style `///` Doxygen blocks for:

- every handwritten source and public header through a `\file` purpose block;
- every non-trivial class or struct;
- every public class, method, and non-member interface;
- private interfaces whose contract, invariant, or failure behavior is non-obvious.

Public documentation explains the relevant subset of:

- purpose and observable behavior;
- preconditions and postconditions;
- ownership and lifetime;
- aliasing and mutation;
- failure and diagnostic behavior;
- numerical mode, ordering, and floating-point constraints;
- target or compatibility requirements;
- complexity, allocation, scratch, or code-size effects when material.

Do not repeat a declaration's spelling or document information already obvious from a precise name and signature.
Place public API documentation at its declaration and do not duplicate it in the implementation.

### 4.2 Implementation comments

Use `//` comments rarely and only to explain non-obvious reasons such as:

- why a numerically tempting transformation is illegal;
- why a traversal or layout is required by target behavior;
- why an invariant permits an otherwise surprising operation;
- why a compatibility, fallback, or provenance check cannot be removed;
- why a deliberate implementation differs from the obvious form.

`/*ParameterName=*/` annotations are permitted for otherwise ambiguous boolean, null, zero, or numeric call arguments.

The following are prohibited on protected `main`:

- comments that restate the next statement;
- commented-out code;
- decorative separator noise that does not establish a real section boundary;
- jokes, conversational fragments, or review dialogue;
- bare future-work, repair-later, or workaround debt markers;
- stale claims about performance, hardware, or future work.

Track unfinished work in the milestone ledger, an approved plan, an issue, or a decision record rather than leaving anonymous debt in production source.

### 4.3 Generated-file header

Every generated source artifact includes a stable header naming:

- the generator and version;
- the canonical problem or plan digest;
- the numerical contract;
- required target features;
- the generation timestamp only when it is excluded from deterministic content identity;
- a clear instruction not to edit the file by hand.

## 5. Formatting and mechanical source rules

The future `.clang-format` is based on the pinned LLVM style and records every XOAS override explicitly.

- C++ source uses spaces, two-space indentation, and an 80-column target.
- Tabs and trailing whitespace are prohibited.
- Includes are minimal and ordered: matching public header first, XOAS private headers, external project headers, then system headers, with each group sorted.
- Headers are self-sufficient and may not rely on transitive includes.
- Header guards are derived from the repository include path and checked mechanically.
- C++ casts replace C-style casts except in a separately justified compatibility boundary.
- `using namespace std;` is prohibited.
- Early returns and named predicates are preferred when they reduce nesting and cognitive state.
- Formatting-only churn is isolated from semantic changes.

Markdown documentation uses one sentence per line for new prose where practical.
Existing documents are not mass-reflowed as an incidental change.

## 6. Compiler and static-analysis policy

The initial enforcement implementation uses one explicitly pinned Clang/LLVM major version on the primary development environment and in CI.
Tool versions, binary provenance, enabled checks, and configuration digests are recorded.

### 6.1 Compiler diagnostics

First-party C++ builds with at least:

- `-Wall`;
- `-Wextra`;
- `-Wpedantic`;
- `-Werror`;
- an explicit, reviewed set of additional high-signal diagnostics supported by the pinned compiler.

Do not use `-Weverything` as the policy surface.
Compiler upgrades must not silently enable experimental diagnostics, force mass suppressions, or change the accepted language contract.

Warning flags are applied through one repository-owned interface target or equivalent central mechanism.
Directory-wide or source-wide suppression requires a reviewed implementation decision.

### 6.2 clang-tidy

The repository owns an explicit `.clang-tidy` manifest rather than enabling every available check by wildcard.
The initial set covers applicable `bugprone`, `clang-analyzer`, `performance`, `portability`, `readability`, and selected modern C++ checks, including:

- identifier naming;
- reserved identifiers;
- header guards and include hygiene;
- narrowing, lifetime, ownership, and suspicious control flow;
- needless copies and performance traps;
- misleading or mismatched argument comments.

Every configured diagnostic is an error in required checks.
The exact list is frozen only after the pinned toolchain is provisioned and its checks are reviewed against representative XOAS fixtures.

### 6.3 Suppressions

A suppression must:

1. name one exact diagnostic;
2. cover the narrowest expression or line possible;
3. explain why compliant source is less correct, less portable, or impossible;
4. link a decision or issue when the exception is durable;
5. retain a regression test when behavior is involved.

Bare `NOLINT`, broad warning disabling, unexplained `clang-format off`, and suppression solely to make a gate green are prohibited.

## 7. Testing and dynamic analysis

The quality system does not replace the repository test taxonomy in root `AGENTS.md`.
It makes the applicable tests mandatory for merge.

- Debug and optimized configurations must compile warning-free.
- AddressSanitizer and UndefinedBehaviorSanitizer run with fail-fast behavior on supported first-party tests.
- Assertions check internal invariants; user-controlled invalid input receives a normal diagnostic path rather than an assertion-only failure.
- Critical behavior has named positive, negative, boundary, and failure-path tests.
- Coverage is retained as review evidence but is not reduced to a gameable repository-wide percentage gate.
- A test skip affecting required evidence is a failure unless a time-bounded approved exception explains the unavailable platform or dependency.

The use of C++ exceptions and RTTI is deliberately not decided by this standard.
M1 must resolve their error-model, ABI, binary-size, and IR implications through a separate IDR before public interfaces rely on either mechanism.

## 8. Documentation enforcement

Doxygen is configured to treat malformed documentation and undocumented public first-party interfaces as errors.
Generated and vendored paths are excluded according to section 2.

Automation verifies documentation structure, but review owns semantic quality.
A syntactically valid comment that merely repeats the declaration does not satisfy this standard.

## 9. Quality gates

| Change class | Required evidence before merge |
|---|---|
| Documentation or configuration | Formatting, links, schema/config validation, secret scan, and placeholder scan |
| Handwritten C++ | Format, warning-clean debug/optimized builds, unit/property tests, clang-tidy, Doxygen, and ASan/UBSan |
| IR or semantic logic | All C++ gates plus invalid-input, invariant, round-trip, and numerical-contract tests |
| Code generation | All semantic gates plus deterministic regeneration, generated-source compilation, differential tests, provenance, and artifact inspection |
| Runtime or cache | Compatibility, invalidation, fallback, serialization, and corrupted-artifact rejection tests |
| Performance claim | Every correctness gate first, then the locked benchmark protocol and retained raw evidence |

The implementation exposes stable CMake quality targets, including equivalents of `format-check`, `tidy`, `docs-check`, `test`, `asan-ubsan`, and one aggregate `quality` target.
Exact names and commands become authoritative only when implemented, verified, and added to root `AGENTS.md`.

## 10. CI and protected-main policy

Protected `main` requires all configured quality checks before merge.
Short-lived branches may use the primary checkout; a linked worktree is not required.

Each pull request records:

- controlling requirement;
- scope and non-goals;
- architecture, IR, numerical, identity, compatibility, and benchmark impact;
- exact verification commands and results;
- generated artifacts or performance evidence when applicable;
- requested exception or follow-up decision, if any.

Public API, architecture, numerical, identity, compatibility, benchmark, and gate changes require explicit owner approval in addition to automated checks.

GitHub-hosted runners are the initial required-check lane.
Installing a self-hosted Actions runner on `gpu-2` would grant persistent remote workflow execution on the primary environment and requires a separate security decision.
CI quality results are not Target 0 performance evidence.

## 11. Development environment

The user designated `gpu-2` as XOAS's primary development environment on 2026-08-28.
No alternative server is currently designated; an AMD desktop may be evaluated later.

This designation authorizes development use but does not qualify `gpu-2` for Target 0 measurement evidence.
Target qualification remains controlled by [`../architecture/proposals/AR-0001-target-0-host-qualification.md`](../architecture/proposals/AR-0001-target-0-host-qualification.md).

The pinned quality toolchain must run identically on `gpu-2` and the required CI lane to the extent the host operating environments permit.
Any platform-specific difference is explicit and cannot silently weaken a required check.

## 12. Toolchain upgrades and exceptions

A toolchain upgrade is a reviewed change with:

- old and new tool identities;
- configuration diff;
- enabled/removed diagnostic diff;
- clean repository-wide verification;
- explicit disposition of every new finding;
- no mass automated source rewrite hidden inside an unrelated change.

Temporary gate exceptions are time-bounded, owned, justified, and visible in the milestone ledger or an IDR.
Permanent exceptions require evidence that the general rule is wrong for the affected boundary.

## 13. Definition of compliance

A change complies only when:

- its applicable automated checks pass on the exact reviewed commit;
- its documentation and names communicate the intended contract;
- all suppressions satisfy section 6.3;
- generated and third-party boundaries are classified correctly;
- no known contract deviation is hidden by formatting, comments, or tooling configuration;
- required review and protected-branch checks complete.

Passing automation is necessary but not sufficient.
Review may reject technically formatted code that is needlessly complex, weakly named, poorly factored, numerically ambiguous, or inconsistent with the approved IR boundaries.
