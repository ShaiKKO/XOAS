# Engineering Quality Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn XOAS's approved LLVM-derived coding standard into reproducible local and hosted-CI gates, prove each gate with compliant and intentionally non-compliant fixtures, and protect `main` with the verified check set.

**Architecture:** Build one repository-owned CMake quality surface around the exact tool identities recorded by the completed `gpu-2` toolchain plan. Keep the harness separate from future product modules: fixtures live under `tests/quality`, reusable build policy lives under `cmake/quality`, and public commands are exposed through presets and stable aggregate targets. Every gate is tested both for acceptance and intended rejection before it becomes required in GitHub-hosted CI. The workflow installs locked tools on `ubuntu-24.04`, pins every action to a commit SHA, and never uses `gpu-2` as a runner. Branch protection is applied only after all required contexts pass on the exact pushed commit.

**Tech Stack:** C++23, CMake and CTest, Ninja, Clang/clang-tidy/clang-format/compiler-rt/LLVM coverage tools, Doxygen, Graphviz, ShellCheck, Python 3.12 only for JSON Schema validation and repository audit orchestration, GitHub Actions on `ubuntu-24.04`, and GitHub branch-protection APIs.

**Spec:** [`docs/engineering/coding-standards.md`](../../engineering/coding-standards.md), [`docs/adr/IDR-0001-engineering-quality-system.md`](../../adr/IDR-0001-engineering-quality-system.md), [`AGENTS.md`](../../../AGENTS.md), and the verified `toolchains/gpu-2-development-toolchain-v1.lock.json` produced by the prerequisite plan.

## Global Constraints

- Do not begin this plan until the `gpu-2` toolchain lock state is `installed_verified`, its schema passes, and its exact commit is on `origin/main`.
- Work in the primary checkout. A linked worktree is optional only if concrete concurrent overlap or recovery risk arises.
- This plan implements engineering infrastructure only. It must not add Problem, Structure, Reduction, Bilinear, Schedule, or Machine IR code; a kernel generator; a runtime; or a benchmark claim.
- Use the versioned LLVM major and exact tool identities from the verified lock. A version substitution requires a reviewed lock update, not an ad hoc workflow edit.
- Keep handwritten, generated, and vendored source policies distinct. Negative fixtures must be isolated from the passing build and cannot create a broad exclusion for first-party source.
- Do not decide exceptions, RTTI, public ABI, license-header text, numerical reassociation, or target/cache identity in this plan.
- Use professional `///` Doxygen blocks for fixture files, non-trivial fixture classes, and public fixture interfaces. Use `//` only for non-obvious rationale.
- Never hand-edit a generated fixture output; update its deterministic fixture generator.
- Do not install a self-hosted Actions runner or treat CI timing as Target 0 evidence.
- Do not weaken a diagnostic, exclusion, sanitizer, documentation rule, or required check merely to get a green run. Stop, show the exact failure, and use the IDR exception process if the approved rule is wrong.
- Preserve losing negative-fixture evidence in the test log, but do not retain sanitizer binaries or temporary build trees in Git.
- Do not activate branch protection until required contexts have completed successfully and their exact names are known.

---

## Task 1: Establish the Quality Harness Contract and Red Tests

**Files:**

- Create: `CMakeLists.txt`
- Create: `CMakePresets.json`
- Create: `tests/quality/CMakeLists.txt`
- Create: `tests/quality/README.md`
- Create: `tests/quality/contracts/expected-gates.json`
- Create: `schemas/quality-gates-v1.schema.json`
- Create: `cmake/quality/README.md`

- [x] **Step 1: Verify the prerequisite lock**

Run the schema validator and binary/version checks published by the completed provisioning plan. Require:

```text
state = installed_verified
build_ready = true
target0_measurement_qualified = false
```

Expected: exact package, binary, hash, and schema checks pass on `gpu-2`.

- [x] **Step 2: Write the gate contract before implementations**

Create `schemas/quality-gates-v1.schema.json` and a conforming `tests/quality/contracts/expected-gates.json` as closed records listing these stable local gates:

```text
format-check
warnings
tidy
docs-check
test
asan-ubsan
repository-policy
quality
```

For each, record the change classes it covers, expected positive fixtures, expected negative fixtures, and whether CI requires it. Mark implementation state `red` initially.

- [x] **Step 3: Add a failing CMake contract check**

Create a minimal top-level project that enables C++23 and CTest but does not yet define the quality targets. Add a configure-time test which compares declared target names with `expected-gates.json`.

Run:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target quality
```

Expected: configuration succeeds, then the build fails because `quality` does not exist. Retain that expected failure in `tests/quality/README.md`.

- [x] **Step 4: Lock source classifications**

Document exact roots:

```text
handwritten: include, src, tests except classified fixtures, cmake, tools
generated: tests/quality/fixtures/generated/output only
vendored: tests/quality/fixtures/vendor only
```

State that future real generated or vendored roots require an IDR or reviewed standard update. A filename or comment alone cannot reclassify first-party source.

- [x] **Step 5: Verify documentation and JSON syntax**

```bash
python3 - <<'PY'
import json
from pathlib import Path
from jsonschema import Draft202012Validator

schema = json.loads(Path("schemas/quality-gates-v1.schema.json").read_text())
contract = json.loads(
    Path("tests/quality/contracts/expected-gates.json").read_text()
)
Draft202012Validator.check_schema(schema)
Draft202012Validator(schema).validate(contract)
PY
python3 -m json.tool tests/quality/contracts/expected-gates.json >/dev/null
git diff --check
```

**Commit boundary:** `build: establish quality gate contracts`

---

## Task 2: Implement Non-Mutating Format and Editor Policy

**Files:**

- Create: `.clang-format`
- Create: `.editorconfig`
- Create: `cmake/quality/FormatCheck.cmake`
- Create: `tests/quality/fixtures/format/compliant.cpp`
- Create: `tests/quality/fixtures/format/noncompliant.cpp.in`
- Modify: `CMakeLists.txt`
- Modify: `tests/quality/CMakeLists.txt`
- Modify: `tests/quality/contracts/expected-gates.json`

- [x] **Step 1: Write the negative formatter test**

Add a CTest case that copies `noncompliant.cpp.in` into the build tree, runs the configured `clang-format-21 --dry-run --Werror`, and requires failure with a replacement diagnostic. The source-tree fixture remains unchanged.

Run:

```bash
ctest --preset dev-debug -R quality-format-negative --output-on-failure
```

Expected before the checker exists: test fails because no formatter command is wired.

- [x] **Step 2: Encode the approved style explicitly**

Base `.clang-format` on LLVM and explicitly set XOAS overrides including two-space indentation, 80-column limit, spaces-only indentation, include sorting, and no short-form compaction that harms public API documentation. Do not depend on defaults for a durable XOAS deviation.

Use `.editorconfig` to enforce UTF-8, LF, final newline, trailing-whitespace removal, two-space C/C++/CMake indentation, and four-space Python indentation. Exclude only exact generated/vendor fixture roots from mutation advice.

- [x] **Step 3: Implement the non-mutating tracked-file checker**

`FormatCheck.cmake` must obtain tracked handwritten C/C++ paths from `git ls-files`, reject an unexpected path classification, and invoke the locked formatter only with `--dry-run --Werror`. It must never call in-place formatting.

Expose `format-check` and an optional developer-only `format` target. CI may call only `format-check`.

- [x] **Step 4: Prove negative, positive, and non-mutation behavior**

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target format-check
ctest --preset dev-debug -R 'quality-format-(negative|positive|nonmutation)' \
  --output-on-failure
git diff --exit-code
```

Expected: compliant tracked source passes, copied noncompliant input fails for formatting, and no tracked file changes.

- [x] **Step 5: Mark only the format gate green**

Update its contract state and evidence commands; leave every other unimplemented gate red.

**Commit boundary:** `build: enforce LLVM-derived formatting`

---

## Task 3: Centralize C++23 Diagnostics and Build Presets

**Files:**

- Create: `cmake/quality/XoasWarnings.cmake`
- Create: `tests/quality/fixtures/compiler/compliant.h`
- Create: `tests/quality/fixtures/compiler/compliant.cpp`
- Create: `tests/quality/fixtures/compiler/warning-negative.cpp.in`
- Modify: `CMakeLists.txt`
- Modify: `CMakePresets.json`
- Modify: `tests/quality/CMakeLists.txt`
- Modify: `tests/quality/contracts/expected-gates.json`

- [x] **Step 1: Write a compiler-warning failure test**

Compile the copied negative fixture through a CMake script using the same interface policy intended for first-party targets. Require a selected high-signal warning to be promoted to an error. Confirm the test is red before adding the interface target.

- [x] **Step 2: Add one repository-owned warnings interface**

Define `xoas_warnings` as the sole first-party warning-policy target. Start with:

```text
-Wall
-Wextra
-Wpedantic
-Werror
-Wcast-align
-Wconversion
-Wdouble-promotion
-Wextra-semi
-Wformat=2
-Wimplicit-fallthrough
-Wnon-virtual-dtor
-Wold-style-cast
-Woverloaded-virtual
-Wshadow
-Wsign-conversion
-Wundef
-Wzero-as-null-pointer-constant
```

Probe every additional flag with the locked Clang and omit only an unsupported flag with recorded evidence. Do not add global suppression flags.

- [x] **Step 3: Configure exact debug and release presets**

Use Ninja, `clang-21`, `clang++-21`, and `ld.lld-21`. Require C++23 without compiler extensions and export `compile_commands.json`. Keep build roots below `build/` and make preset inheritance explicit.

- [x] **Step 4: Prove header self-sufficiency and both build types**

Build the public fixture header as the first include in its source and in a one-header translation unit. Run:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target warnings
ctest --preset dev-debug -R quality-compiler --output-on-failure
cmake --preset dev-release
cmake --build --preset dev-release --target warnings
ctest --preset dev-release -R quality-compiler-positive --output-on-failure
```

Expected: negative warning fixture fails for the intended diagnostic; documented compliant fixture passes warning-free in debug and release.

- [x] **Step 5: Update the warning contract evidence**

Record the exact accepted flag list and compiler identity digest. Mark `warnings` green only after both configurations pass.

**Commit boundary:** `build: centralize strict C++ diagnostics`

---

## Task 4: Freeze and Enforce the Explicit clang-tidy Manifest

**Files:**

- Create: `.clang-tidy`
- Create: `cmake/quality/TidyCheck.cmake`
- Create: `tests/quality/fixtures/tidy/reserved-identifier.cpp.in`
- Create: `tests/quality/fixtures/tidy/identifier-naming.cpp.in`
- Create: `tests/quality/fixtures/tidy/performance.cpp.in`
- Create: `tests/quality/fixtures/tidy/compliant.cpp`
- Modify: `CMakeLists.txt`
- Modify: `tests/quality/CMakeLists.txt`
- Modify: `tests/quality/contracts/expected-gates.json`
- Modify: `docs/adr/IDR-0001-engineering-quality-system.md`

- [x] **Step 1: Inventory checks from the locked binary**

Run `clang-tidy-21 --list-checks -checks='*'` and save the reviewed supported-check inventory in the IDR evidence section. Do not enable an unavailable, renamed, or experimental diagnostic by assumption.

- [x] **Step 2: Write independent negative fixtures**

Create isolated build-tree copies proving at least:

- reserved double-underscore identifier rejection;
- XOAS type/function/value/member naming;
- one needless-copy or equivalent performance trap;
- suspicious argument or control-flow detection;
- header-guard/include-hygiene behavior.

Run the test group before `.clang-tidy` exists and retain the expected failures.

- [x] **Step 3: Create the explicit check manifest**

Begin with `Checks: '-*'`, then enumerate each admitted diagnostic by full name. Cover the supported high-signal checks in the approved `clang-analyzer`, `bugprone`, `performance`, `portability`, `readability`, selected `modernize`, `misc`, and LLVM header-guard families. Do not use a category-wide wildcard as the final policy.

Configure identifier naming for:

```text
Types and non-trivial classes: UpperCamelCase
Functions and methods: lowerCamelCase
Local variables and parameters: lowerCamelCase
Constants and enumeration constants: UpperCamelCase
Private data members: lowerCamelCase with one trailing underscore
Namespaces: lower_snake_case
Macros: UPPER_SNAKE_CASE
```

Set `WarningsAsErrors: '*'` and a repository-anchored header filter.

- [x] **Step 4: Implement tracked handwritten-source traversal**

`TidyCheck.cmake` must consume the debug compilation database, process only tracked handwritten C/C++ paths, and reject any unclassified source. Exclude generated/vendor fixture roots exactly. Expose `tidy`.

- [x] **Step 5: Prove each rule and the aggregate target**

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target tidy
ctest --preset dev-debug -R quality-tidy --output-on-failure
```

Expected: compliant fixture passes; every negative fixture fails for its named diagnostic; no bare or broad suppression is present.

- [x] **Step 6: Freeze the manifest decision**

Record the exact check list, locked clang-tidy identity, exclusions, and unsupported candidate disposition in IDR-0001. Mark `tidy` green.

**Commit boundary:** `build: enforce explicit clang-tidy policy`

---

## Task 5: Enforce Professional Public Documentation

**Files:**

- Create: `Doxyfile.in`
- Create: `cmake/quality/DocumentationCheck.cmake`
- Create: `tests/quality/fixtures/docs/compliant.h`
- Create: `tests/quality/fixtures/docs/undocumented-public.h.in`
- Create: `tests/quality/fixtures/docs/malformed.h.in`
- Modify: `CMakeLists.txt`
- Modify: `tests/quality/CMakeLists.txt`
- Modify: `tests/quality/contracts/expected-gates.json`

- [ ] **Step 1: Write undocumented and malformed failure tests**

Each test copies one negative header into a build-tree Doxygen input root and requires nonzero exit with the corresponding warning class. Confirm both tests fail before the policy is wired.

- [ ] **Step 2: Configure Doxygen warnings as errors**

Require documented files, non-trivial classes, and public interfaces; reject malformed commands and undocumented public members. Set extraction so absent documentation remains visible. Exclude only the exact generated/vendor fixture roots. Keep HTML output in the build tree.

- [ ] **Step 3: Add the compliant documentation fixture**

Use `///` blocks with `@file`, purpose, preconditions, parameter semantics, return semantics, and one non-obvious invariant. Avoid comments that merely repeat declarations.

- [ ] **Step 4: Expose and prove `docs-check`**

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target docs-check
ctest --preset dev-debug -R quality-docs --output-on-failure
```

Expected: compliant docs pass; undocumented and malformed copies fail; generated/vendor exclusions do not hide the handwritten fixture.

- [ ] **Step 5: Mark documentation enforcement green**

Record Doxygen identity, configuration hash, exclusion roots, and passing evidence.

**Commit boundary:** `build: enforce public API documentation`

---

## Task 6: Add Unit and Fail-Fast Sanitizer Gates

**Files:**

- Create: `cmake/quality/XoasSanitizers.cmake`
- Create: `tests/quality/fixtures/runtime/positive.cpp`
- Create: `tests/quality/fixtures/runtime/address-negative.cpp.in`
- Create: `tests/quality/fixtures/runtime/undefined-negative.cpp.in`
- Create: `cmake/quality/ExpectRuntimeFailure.cmake`
- Modify: `CMakeLists.txt`
- Modify: `CMakePresets.json`
- Modify: `tests/quality/CMakeLists.txt`
- Modify: `tests/quality/contracts/expected-gates.json`

- [ ] **Step 1: Write the sanitizer negative tests first**

Create copied build-tree inputs for one deterministic heap-use-after-free and one deterministic signed-overflow case. The harness must assert nonzero exit and match `AddressSanitizer` or UndefinedBehaviorSanitizer's runtime diagnostic, not merely mark any failure as success.

- [ ] **Step 2: Add target-scoped sanitizer policy**

Create one interface target applying AddressSanitizer plus UndefinedBehaviorSanitizer with frame pointers and no recovery. Do not apply sanitizers globally or to vendored fixtures.

- [ ] **Step 3: Add the sanitizer preset and aggregate**

Configure a separate build tree with Clang/LLD and fail-fast environment:

```text
ASAN_OPTIONS=abort_on_error=1:halt_on_error=1:detect_leaks=1
UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1
```

Expose `asan-ubsan`; keep intentional negative binaries outside the passing CTest default set and invoke them through named harness tests.

- [ ] **Step 4: Prove positive and negative behavior**

```bash
cmake --preset asan-ubsan
cmake --build --preset asan-ubsan --target asan-ubsan
ctest --preset asan-ubsan -R quality-sanitizer --output-on-failure
```

Expected: positive fixture passes, both negative fixtures are detected for the intended reasons, and no skipped required test appears.

- [ ] **Step 5: Mark test and sanitizer contracts green**

Record exact compiler-rt package identity, runtime options, and results.

**Commit boundary:** `test: enforce fail-fast sanitizer gates`

---

## Task 7: Enforce Repository Policy and Source Classification

**Files:**

- Create: `cmake/quality/RepositoryPolicy.cmake`
- Create: `cmake/quality/MarkdownLinks.cmake`
- Create: `tests/quality/fixtures/policy/secret-negative.txt.in`
- Create: `tests/quality/fixtures/policy/unfinished-marker-negative.txt.in`
- Create: `tests/quality/fixtures/generated/generate.cmake`
- Create: `tests/quality/fixtures/generated/input.json`
- Create: `tests/quality/fixtures/vendor/README.md`
- Modify: `.gitignore`
- Modify: `CMakeLists.txt`
- Modify: `tests/quality/CMakeLists.txt`
- Modify: `tests/quality/contracts/expected-gates.json`

- [ ] **Step 1: Write policy negative tests**

Pass copied build-tree content containing a synthetic credential pattern and a prohibited unfinished-work marker into the checker. Require each to fail for the named rule. Ensure the synthetic value cannot authenticate anywhere and is excluded from source-tree secret scans by using an encoded fixture input decoded only below `build/`.

- [ ] **Step 2: Implement deterministic local Markdown-link validation**

Validate relative links and anchors for tracked Markdown without network access. Reject missing files, path traversal outside the repository, malformed local targets, and orphaned plan/spec links. Treat external links as syntactically checked references; external reachability remains a separate research audit.

- [ ] **Step 3: Implement repository policy checks**

Expose `repository-policy` covering:

- `git diff --check`;
- JSON syntax and all repository schemas with `Draft202012Validator`;
- tracked-file secret-pattern scan;
- prohibited unfinished-work marker scan;
- local Markdown links;
- unexpected generated or vendored classification;
- tracked build output and executable artifact rejection;
- ShellCheck for tracked shell files.

Use exact allowlists only for synthetic encoded fixtures and normative prose that names a prohibited concept. An allowlist entry requires path, rule, and rationale.

- [ ] **Step 4: Prove deterministic generation and vendor isolation**

Generate the classified output twice from the same input and compare bytes and SHA-256. Prove the output carries generator identity and a do-not-edit notice. Prove the vendor fixture is excluded from first-party formatting/tidy/docs while the adjacent handwritten fixture is not.

- [ ] **Step 5: Run all policy tests**

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target repository-policy
ctest --preset dev-debug -R quality-policy --output-on-failure
```

Expected: all positive repository checks pass, each negative copy fails for its intended rule, and the source tree remains unchanged.

- [ ] **Step 6: Mark repository policy green**

Record exact exclusions and rule identities in the gate contract.

**Commit boundary:** `build: enforce repository evidence policy`

---

## Task 8: Close the Aggregate Local Quality Surface

**Files:**

- Modify: `CMakeLists.txt`
- Modify: `CMakePresets.json`
- Modify: `tests/quality/CMakeLists.txt`
- Modify: `tests/quality/contracts/expected-gates.json`
- Modify: `tests/quality/README.md`

- [ ] **Step 1: Add the failing aggregate dependency test**

Require `quality` to fail if any gate contract remains red or any target is absent. Confirm the test is red before connecting all dependencies.

- [ ] **Step 2: Wire stable aggregate targets**

Make `quality` depend on non-mutating format, warnings, tidy, docs, passing CTest, sanitizer verification, and repository policy. Prevent cyclic builds by using explicit stamp outputs where a gate configures another preset.

- [ ] **Step 3: Run the entire surface from a clean build root**

Delete only the validated XOAS `build/` subdirectories via the repository cleanup command, then run:

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target quality
cmake --preset dev-release
cmake --build --preset dev-release --target warnings
ctest --preset dev-release --output-on-failure
```

Expected: all gates pass, all intended negative probes were observed by their harnesses, and no tracked file changes.

- [ ] **Step 4: Mark the aggregate contract green**

Record commands, wall-clock cost, exact lock ID, and build-tree cleanup boundary. Do not make a performance claim from gate duration.

**Commit boundary:** `build: close aggregate local quality gates`

---

## Task 9: Reproduce the Gates in Pinned GitHub-Hosted CI

**Files:**

- Create: `.github/workflows/quality.yml`
- Create: `toolchains/github-actions-v1.lock.json`
- Create: `schemas/github-actions-lock-v1.schema.json`
- Modify: `tests/quality/contracts/expected-gates.json`
- Modify: `docs/adr/IDR-0001-engineering-quality-system.md`

- [ ] **Step 1: Resolve and record immutable action identities**

Use the GitHub API to resolve each admitted official action release to one 40-character commit SHA. The initial workflow should require only checkout unless a demonstrated need adds another action. Define `schemas/github-actions-lock-v1.schema.json` and record repository, release tag, commit SHA, verification state, purpose, and retrieval time in the conforming `toolchains/github-actions-v1.lock.json`.

Do not use a floating major tag in workflow `uses:` fields.

- [ ] **Step 2: Add least-privilege workflow policy**

Use:

- `ubuntu-24.04` hosted runners only;
- `permissions: contents: read`;
- concurrency cancellation scoped to workflow and ref;
- Bash fail-fast steps;
- no repository secrets;
- no cache or artifact upload until separately justified;
- exact APT source key fingerprint and package versions from the verified toolchain lock;
- versioned compiler tools and no global alternatives.

- [ ] **Step 3: Define stable required job names**

Create exactly these required contexts:

```text
quality / repository-policy
quality / static-quality
quality / debug-build-and-test
quality / release-build-and-test
quality / sanitizers
```

Each job must run its local equivalent rather than duplicate policy in YAML. CI formatter checks remain non-mutating.

- [ ] **Step 4: Validate workflow syntax and local parity**

Run the repository policy target, parse the YAML with the locked PyYAML module, validate the action lock against its schema, verify every `uses:` value ends in a locked 40-character SHA, and compare job names against the gate contract. Run the complete local `quality` target again on `gpu-2`.

- [ ] **Step 5: Commit and push CI before protection**

```bash
git add .github/workflows/quality.yml \
  schemas/github-actions-lock-v1.schema.json \
  toolchains/github-actions-v1.lock.json \
  tests/quality/contracts/expected-gates.json \
  docs/adr/IDR-0001-engineering-quality-system.md
git commit -m "ci: reproduce locked engineering quality gates"
git push origin main
```

- [ ] **Step 6: Require a green exact commit**

Use `gh run list` and `gh run view` to require all five named contexts to succeed for `git rev-parse HEAD`. If any job fails, diagnose and correct it through the same local gate; do not proceed to branch protection.

**Commit boundary:** `ci: reproduce locked engineering quality gates`

---

## Task 10: Protect main with the Verified Required Checks

**Files:**

- Create: `docs/engineering/main-branch-protection-v1.json`
- Create: `schemas/branch-protection-v1.schema.json`
- Modify: `docs/adr/IDR-0001-engineering-quality-system.md`

- [ ] **Step 1: Capture the live pre-state**

Use read-only GitHub API calls to record repository visibility, default branch, administrative permission, current protection state, and the exact successful check contexts. Exclude tokens and HTTP authorization metadata.

Expected initial state from planning discovery: public repository, `main` default, owner has admin permission, and `main` is unprotected. Recheck at execution because this state can drift.

- [ ] **Step 2: Write the desired closed protection record**

Define `schemas/branch-protection-v1.schema.json`, then create a conforming closed record containing:

- strict required status checks with the five exact contexts;
- required pull-request path with zero required external approvals for the current single-owner project;
- stale-review dismissal if reviews are later supplied;
- conversation resolution;
- force pushes disabled;
- branch deletion disabled;
- linear history required;
- no collaborator-dependent reviewer rule;
- owner responsibility for explicit semantic approval;
- captured pre-state and exact reversal API payload.

Do not claim the repository can enforce self-review as independent approval.

- [ ] **Step 3: Apply protection through one reviewed API request**

Use `gh api --method PUT` with the exact JSON file as input. Do not construct a mutable partial rule interactively. Require the response to match the desired contexts and booleans.

- [ ] **Step 4: Prove enforcement without destructive pushes**

Re-read the protection API and branch record. Confirm `protected: true`, all five contexts, force-push prohibition, deletion prohibition, and PR policy. Do not test by force-pushing or deleting a branch.

- [ ] **Step 5: Record the applied timestamp and commit identity**

Update the record and IDR with the exact CI commit, successful run IDs, protection response digest, and operator. Commit through the now-required pull-request path if protection prevents direct update.

**Commit boundary:** `docs: record protected-main quality controls`

---

## Task 11: Publish Verified Commands and Close the Enforcement Decision

**Files:**

- Modify: `AGENTS.md`
- Modify: `docs/engineering/coding-standards.md`
- Modify: `docs/adr/IDR-0001-engineering-quality-system.md`
- Modify: `docs/milestones/status.md`
- Modify: `docs/architecture/README.md`

- [ ] **Step 1: Replace planned-state language with exact verified commands**

Update root `AGENTS.md` with:

- exact toolchain-lock verification;
- debug/release configure, build, and CTest commands;
- `format-check`, `tidy`, `docs-check`, `asan-ubsan`, `repository-policy`, and `quality` commands;
- safe cleanup command and exact build-root boundary;
- test taxonomy and required gates by change class;
- hosted-CI context names and protected-main behavior;
- generated/vendor classification and exception path.

Do not include commands that were not executed successfully.

- [ ] **Step 2: Update enforcement status**

Mark the standard automated only after local and hosted results pass. Mark IDR-0001 enforcement implemented only after protection is verified. Keep exceptions/RTTI, license-header text, M0 measurement qualification, baselines, and product implementation open.

- [ ] **Step 3: Run full final verification on the exact review commit**

```bash
cmake --preset dev-debug
cmake --build --preset dev-debug --target quality
cmake --preset dev-release
cmake --build --preset dev-release --target warnings
ctest --preset dev-release --output-on-failure
git diff --check
git status --short --branch
```

Then require the five hosted contexts to pass for the same commit or the resulting pull-request merge commit, and verify branch protection again.

- [ ] **Step 4: Inspect generated and retained artifacts**

Inspect the generated fixture source, Doxygen warnings log, compile commands, sanitizer harness logs, CTest results, action lock, and branch-protection record. Confirm build artifacts are ignored and no credential or network access datum is tracked.

- [ ] **Step 5: Commit through protected main and report exact evidence**

Use the required pull-request/check path. Report:

- exact tested source and merge commits;
- local commands and results;
- hosted run IDs and five context outcomes;
- toolchain and configuration digests;
- branch-protection response digest;
- remaining open decisions and M0 blockers.

**Commit boundary:** `docs: activate enforced engineering quality system`

---

## Acceptance Evidence

This plan is complete only when:

- every stable local gate exists and its compliant and non-compliant fixtures prove intended behavior;
- debug and release compile warning-free under the central C++23 policy;
- clang-format checking is non-mutating;
- clang-tidy uses a fully enumerated reviewed manifest and treats findings as errors;
- Doxygen rejects undocumented and malformed public documentation;
- ASan and UBSan detect their named negative probes and the positive suite passes;
- generated and vendored exclusions are exact and cannot hide adjacent handwritten source;
- repository policy validates whitespace, schemas, local links, secret patterns, unfinished-work markers, ShellCheck, and tracked artifacts;
- the aggregate `quality` target passes on `gpu-2` with the verified lock;
- the same policy passes in five pinned GitHub-hosted contexts on the exact commit;
- `main` requires those contexts and disallows force pushes and deletion;
- root `AGENTS.md` contains exact verified commands and no fictional path;
- no self-hosted runner, product compiler code, baseline claim, or Target 0 performance claim was introduced.

Completion closes IDR-0001's enforcement implementation gate only. M0 and AR-0001 remain governed by their independent measurement-host, baseline, schema, and review evidence.
