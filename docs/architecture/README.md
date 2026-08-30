# XOAS Architecture Index

This index lists architecture and evidence documents that actually exist. Planned documents are not authoritative until they are added, reviewed, and entered here.

## Authority order

1. The user's latest explicit instruction.
2. Approved or locked architecture/specification documents and approved architecture proposals.
3. [`../exact_instance_matrix_kernel_synthesizer_build_plan.md`](../exact_instance_matrix_kernel_synthesizer_build_plan.md).
4. Repository and scoped `AGENTS.md` files.
5. Accepted implementation plans and implementation decision records.
6. Existing code and tests as evidence of current behavior.

If two sources conflict, stop work affected by the conflict, quote the exact sections or interfaces, identify work that remains independent, and obtain the appropriate architecture decision. This index records status; it does not promote a draft to approved authority.

## Controlling architecture

| Document                                                                                                                 | State                                                                                                               | Scope                                                                              | Update trigger                                |
| ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------- |
| [`../exact_instance_matrix_kernel_synthesizer_build_plan.md`](../exact_instance_matrix_kernel_synthesizer_build_plan.md) | Approved execution authority by the user's 2026-08-28 handoff; front-matter label remains historically unreconciled | Full research architecture, milestone dependencies, gates, IR boundaries, Target 0 | Approved architecture change                  |
| [`000-charter.md`](000-charter.md)                                                                                       | M0 locked contract; M0 gate remains open until its acceptance record closes                                         | Product mission, v0 claim, Target 0, non-goals, numerical boundary, falsification  | Approved scope, semantics, or gate change     |
| [`050-benchmark-protocol.md`](050-benchmark-protocol.md)                                                                 | M0 locked measurement contract; not yet exercised by a harness                                                      | Eligibility, environment, sampling, statistics, lifecycle, holdout, and claim rules | Approved protocol revision or evidence-driven correction |

## Architecture proposals

| Document | State | Requested decision |
|---|---|---|
| [`proposals/AR-0001-target-0-host-qualification.md`](proposals/AR-0001-target-0-host-qualification.md) | Approved — Option 2; replacement candidate designated | `gpu-2` is development-only; qualify the designated physical AMD host before measurement use |
| [`proposals/AR-0002-amd-target-baseline-admission.md`](proposals/AR-0002-amd-target-baseline-admission.md) | Approved — Option 1 | Add AOCL-BLAS as an AMD-vendor comparator without removing existing applicable baselines |

Approved proposals override the affected sections of lower-authority documents only to the extent their requested decision says so. Rejected and superseded proposals remain evidence and must be labeled accordingly.

## Implementation decisions

| Document | State | Decision |
|---|---|---|
| [`../adr/IDR-0001-engineering-quality-system.md`](../adr/IDR-0001-engineering-quality-system.md) | Accepted and implemented; enforced on protected `main` | LLVM-derived source standard, pinned Clang-native gates, protected `main`, generated/vendor boundaries, and staged rollout |
| [`../adr/IDR-0002-target0-qualification-tool-deployment.md`](../adr/IDR-0002-target0-qualification-tool-deployment.md) | Accepted; native deployment/cross-host verification passed at `a312aa2`, integrated by PR #4 at `a51a7f9` | Separate `gpu-2` quality and physical native-build authority, closed dual-build evidence bundle, replica verification, and no campaign authority |
| [`../adr/IDR-0003-target0-qualification-campaign-runner.md`](../adr/IDR-0003-target0-qualification-campaign-runner.md) | Accepted; implementation at `db0eb87`, attempt 1 retained as `restoration_failure`, and test-first source repair verified through `c9af373`; physical repair proof and redeployment remain open | Closed two-phase qualification campaign, exact identity/statistical evidence, and dedicated privileged-PMU boundary |
| [`../adr/IDR-0004-wineth-quality-toolchain.md`](../adr/IDR-0004-wineth-quality-toolchain.md) | Accepted and verified at clean `93f164c` | Isolated Python 3.12.3, Doxygen 1.9.8, and ShellCheck 0.9.0 quality lane on `wineth-ubuntu`; no measurement or qualification authority |

Use the next unused `../adr/IDR-####-short-title.md` number for a durable, semantics-neutral implementation decision.

## Implementation plans

| Document | State | Scope |
|---|---|---|
| [`../superpowers/plans/2026-08-28-gpu-2-development-toolchain.md`](../superpowers/plans/2026-08-28-gpu-2-development-toolchain.md) | Executed and verified at `ce1d27d` | Reversible exact-version provisioning and verification of the primary development toolchain; excludes baselines and measurement qualification |
| [`../superpowers/plans/2026-08-28-engineering-quality-gates.md`](../superpowers/plans/2026-08-28-engineering-quality-gates.md) | Executed and enforced through protected-main merge `6516866`; command/status activation verified | Local quality fixtures/targets, pinned hosted CI, and protected `main`; excludes product/compiler implementation |
| [`../superpowers/plans/2026-08-29-amd-target0-host-qualification.md`](../superpowers/plans/2026-08-29-amd-target0-host-qualification.md) | Tasks 1–4 complete; Task 5 attempt 1 retained as restoration rejection; source repair verified through `c9af373`; physical validation and Tasks 5–7 remain open | Physical AMD host tooling, source-built baselines, reversible controls, reboot-separated qualification, and M0 decision |
| [`../superpowers/plans/2026-08-29-target0-qualification-tool-deployment.md`](../superpowers/plans/2026-08-29-target0-qualification-tool-deployment.md) | Tasks 0–9 executed; implementation subject `a312aa2`, compact evidence bound | Native probe build/authentication, closed bundle, cross-host replica verification, durable decision, and deployment handoff |
| [`../superpowers/plans/2026-08-29-target0-qualification-campaign-runner.md`](../superpowers/plans/2026-08-29-target0-qualification-campaign-runner.md) | Tasks 1–9 complete; Task 10 attempt 1 retained as `restoration_failure`; source repair verified through `c9af373`; fresh deployment and a new approved attempt remain open | Closed campaign contract, dedicated privileged-PMU boundary, exact-commit verification, campaign one, and stop-before-reboot handoff |

An implementation plan does not change architecture authority. Its execution must preserve the controlling specification and record exact commits and evidence.

## Milestone control and acceptance

| Document                                                                             | State                       | Purpose                                                   |
| ------------------------------------------------------------------------------------ | --------------------------- | --------------------------------------------------------- |
| [`../milestones/status.md`](../milestones/status.md)                                 | Canonical live ledger       | Current frontier, gate state, dependencies, evidence gaps |
| [`../milestones/M0-implementation-plan.md`](../milestones/M0-implementation-plan.md) | Active                      | Exact M0 files, checks, evidence, and commit boundaries   |
| [`../milestones/M0-acceptance.md`](../milestones/M0-acceptance.md)                   | Open acceptance record; gate OPEN | M0 traceability, commands, evidence gaps, review, and gate decision |

## Repository operating evidence

| Document                                                                                                                     | State                            | Purpose                                                                            |
| ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | ---------------------------------------------------------------------------------- |
| [`../../AGENTS.md`](../../AGENTS.md)                                                                                         | Active operating manual          | Repository-wide engineering rules; never overrides architecture                    |
| [`../engineering/coding-standards.md`](../engineering/coding-standards.md)                                                   | Approved normative standard; local, hosted, and protected-main automation active | Source naming/comments, quality gates, suppression policy, review, and CI authority |
| [`../toolchain/gpu-2-development-toolchain-v1.md`](../toolchain/gpu-2-development-toolchain-v1.md)                           | Installed and behaviorally verified on `gpu-2` | Non-secret provisioning pre-state, source authentication, rollback, and probe evidence |
| [`../../toolchains/gpu-2-development-toolchain-v1.lock.json`](../../toolchains/gpu-2-development-toolchain-v1.lock.json)     | Exact installed lock; `build_ready=true`; Target 0 qualification false | Versioned package closure, executable identities, probe evidence, and stable configuration digest |
| [`../../schemas/development-toolchain-v1.schema.json`](../../schemas/development-toolchain-v1.schema.json)                   | Draft 2020-12 lock schema | Closed machine-readable development-toolchain evidence contract |
| [`../targets/target0-amd-ryzen9-7900x-v1.md`](../targets/target0-amd-ryzen9-7900x-v1.md)                                   | Candidate unqualified; exact support closure and baseline stack installed and verified | Non-secret physical-host boundary, package/source/artifact identities, blockers, and remaining qualification gates |
| [`../../toolchains/target0-amd-ryzen9-7900x-v1.lock.json`](../../toolchains/target0-amd-ryzen9-7900x-v1.lock.json)           | Installed and schema-valid at `9d44f64`; live 288-file identity verified against Task 4 subject `16d698d` | Full package pre-state/closure, source locks, build/test commands, validations, artifact hashes, and rollback boundary |
| [`../../schemas/target0-toolchain-lock-v1.schema.json`](../../schemas/target0-toolchain-lock-v1.schema.json)               | Draft 2020-12 closed provisioning-lock schema | Target, repository, APT, executable, source, license, validation, installed-artifact, and rollback contract |
| [`../../schemas/target0-qualification-tool-bundle-v1.schema.json`](../../schemas/target0-qualification-tool-bundle-v1.schema.json) | Draft 2020-12 closed deployment-bundle schema; synthetic and accepted native instances validate | Checkout, source, compiler/linker, reproducible build, ELF/runtime, compatibility, and non-claiming bundle contract |
| [`../../schemas/target0-qualification-campaign-v1.schema.json`](../../schemas/target0-qualification-campaign-v1.schema.json) | Draft 2020-12 closed campaign schema; synthetic example and generated fixture campaigns validate | Preflight, five-process statistics, PMU evidence, acceptance thresholds, and inventory binding |
| [`../../benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json`](../../benchmarks/evidence/target0-amd-ryzen9-7900x-v1/qualification-tools-v1.json) | Accepted non-claiming native deployment receipt at `a312aa2`; external bundles retained | Canonical source/toolchain/build/runtime evidence plus companion inventory, executable, boot, and replica digests |
| [`../engineering/main-branch-protection-v1.json`](../engineering/main-branch-protection-v1.json)                             | Applied and independently verified; published by PR #1 at `6516866` | Exact pre-state, required App-bound checks, request digest, response digest, operator, and reversal |
| [`../repository_discovery_and_project_understanding_report.md`](../repository_discovery_and_project_understanding_report.md) | Point-in-time discovery snapshot | Verified repository, development-host, toolchain, and evidence state at 2026-08-28 |

## Research and benchmark evidence

| Document | State | Purpose |
|---|---|---|
| [`../experiments/prior-art-matrix.md`](../experiments/prior-art-matrix.md) | M0 reviewed-source matrix; executable reproduction remains later work | Capability boundary, closest prior systems, constrained XOAS differentiator |
| [`../experiments/baseline-matrix.md`](../experiments/baseline-matrix.md) | M0 admission policy; host availability remains open | Serious baseline candidates, configuration search, cost accounting, disqualification |
| [`../../schemas/benchmark-result-v1.schema.json`](../../schemas/benchmark-result-v1.schema.json) | M0 JSON Schema draft 2020-12 contract; schema and synthetic example fully validated on `gpu-2` | Immutable result, environment, raw-sample, lifecycle, artifact, and decision fields |
| [`../../benchmarks/manifests/benchmark-result-v1.example.json`](../../benchmarks/manifests/benchmark-result-v1.example.json) | Explicitly synthetic, non-claiming example | Demonstrates the result shape; never benchmark evidence |
| [`../experiments/corpus-policy.md`](../experiments/corpus-policy.md) | Frozen M0 corpus/generation policy; materializer remains M1 work | Deterministic support/value generation, source normalization, partitions, holdout governance |
| [`../../benchmarks/manifests/synthetic-target-v0.json`](../../benchmarks/manifests/synthetic-target-v0.json) | Frozen, not materialized | 25 visible smoke/design/proof/product synthetic cases |
| [`../../benchmarks/manifests/application-target-v0.json`](../../benchmarks/manifests/application-target-v0.json) | Frozen sources, not materialized | Six visible NIST-derived product cases, including one proof target |
| [`../../benchmarks/manifests/holdout-v0.json`](../../benchmarks/manifests/holdout-v0.json) | Frozen and not measured; measurements sealed until M7 | Six NIST-derived holdout cases and early-access invalidation rule |
| [`../../benchmarks/manifests/target-gpu-2-candidate.json`](../../benchmarks/manifests/target-gpu-2-candidate.json) | Development-host capture with verified toolchain; not qualified for measurement | Non-secret CPU/OS/topology/timer/PMU/toolchain evidence and qualification blockers |
| [`../../benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json`](../../benchmarks/manifests/target0-amd-ryzen9-7900x-v1.json) | Physical Target 0 candidate with verified provisioning; explicitly unqualified and non-claiming | Closed host capture, installed baseline disposition, and every remaining qualification gate |

No qualified Target 0 manifest exists. The historical `gpu-2` candidate
manifest cannot satisfy plan or runtime compatibility. The physical AMD
candidate now has a repository manifest plus an installed, artifact-verified
support/baseline lock, but no controlled qualification campaign has run.

Performance results do not become architectural authority. They may motivate a proposal, support a gate decision, or falsify a claim.

## Ownership and maintenance

The head engineering and integration agent maintains this index whenever an architecture document, decision record, milestone plan, acceptance record, or controlling evidence path is created, approved, superseded, or invalidated. Every status change must be traceable to a review, exact commit, or explicit user decision.
