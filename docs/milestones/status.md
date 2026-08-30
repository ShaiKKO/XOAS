# Milestone Status Ledger

**Snapshot date:** 2026-08-30

**Controlling program:** [Exact-Instance Matrix Kernel Synthesizer build plan](../exact_instance_matrix_kernel_synthesizer_build_plan.md)

**Gate authority:** The build plan plus approved architecture decisions and the user's latest explicit instructions.

This is the canonical frontier ledger. Update it whenever a milestone changes state, a gate is reviewed, or evidence is invalidated. Never substitute a percentage estimate for a gate status.

## Status vocabulary

- **Not started:** No accepted implementation or required evidence exists.
- **In progress:** Some scoped work or evidence exists, but the exit gate is open.
- **Implemented but unevidenced:** Implementation exists, but required verification or acceptance evidence is missing.
- **Gate closed:** The exit gate has an exact tested commit, retained evidence, and recorded acceptance.

## Current frontier

M0 is the earliest open milestone. The repository-discovery checkpoint was performed before the first commit; `main` now contains the published foundation and prior-art checkpoints, but M0 is not closed.

M0 Task 1 is closed at commit `60044e8`; Task 2 prior-art/baseline policy at `30616bc`; Task 3 benchmark contract at `00afbf7`; Task 4 corpus policy/manifests at `8a7032b`; Task 5 candidate-target capture/proposal at `6e6adf3`; and Task 6 manual integration at verified subject `3d635d3`. AR-0001 Option 2 is approved and integrated at `6904d49e4978f48d9ca3c5db29fac59bbc3233c6`; the `gpu-2` development toolchain is verified at `ce1d27df6fda8b3d91dacadb6afbc6a2c83509c5`; the engineering-quality system is published through protected-main merge `6516866b4266a7418fb62997acd664c74fc23ec3`. The AMD qualification architecture and plan are published through `60c4eeb`; its deterministic process contract is implemented at `8a247a2`, fixture-verified capture/session tooling at `864f7fa`, real-checkout capture repair at `b7371ae`, physical-host pre-state/provisioning lock at `ee57ff5`, and verified baseline stack at `9d44f64`. Qualification-tool implementation subject `a312aa2bbbb403b31ffb67cf40200da063527a4f` passed the complete `gpu-2` quality contract and produced matching accepted physical and `gpu-2` bundles; the canonical non-claiming receipt and digest bindings were integrated through protected-main PR #4 at `a51a7f9`. Campaign-runner implementation is committed through `db0eb87`; exact quality subject `7b486e1` passed the complete `gpu-2` contract. On 2026-08-29 the user designated a physical AMD Ryzen 9 7900X Linux host as the replacement Target 0 measurement candidate and approved AR-0002 Option 1, admitting AOCL-BLAS. Task 4 provisioning was executed against clean subject `16d698d`; evidence head `9b28162` passed pinned Debug and Release quality aggregates. Replacement bundle and preflight then passed at source `1141713c`; campaign-one attempt 1 was retained with closed `restoration_failure` SHA-256 `e6458e2dac1097fa5649371c0815403708c7985da0b80d2ebf5c8b049efc5868` after CPU 2 EPP failed to restore. Bounded recovery returned the physical host to exact pre-state. The support closure, baseline stack, qualification-tool deployment, and campaign implementation quality are verified, while measurement qualification remains open.

On 2026-08-30, IDR-0004's isolated quality-toolchain supplement closed the
physical repository-quality gap. Clean `93f164c` passed Debug 50/50 twice,
Release 50/50 twice, and sanitizer 3/3 on `wineth-ubuntu`.

The named M0 document, policy, schema, corpus, and candidate-capture
deliverables exist and passed the Task 6 checks. AR-0001 Option 2, AR-0002
Option 1, and the engineering-quality specification are approved. `gpu-2` is
development-only; the replacement Target 0 candidate is designated but not
qualified. Qualification-plan Tasks 1–4, the exact support closure, three
versioned baseline libraries, and qualification-tool deployment are closed.
Campaign-runner Tasks 1–7 are closed through exact quality subject `7b486e1`.
Attempt 1 at source `1141713c` rejected before PMU on EPP restoration, and
bounded recovery restored exact pre-state. Replacement Task 9 at repaired
source `a396f64` independently accepted CPU 1/sibling 13. Its separately
authorized Task 10 attempt ran exactly once: all five primary processes and
six restorations passed, required PMU counters ran at full scale, and
publication failed because the target user could not traverse the root-owned
`pmu/` parent. That root is terminal. Red `cc826f2` and repair `0a30b24`
address only this traversal defect; complete quality, review, and integration
remain open.

The test-first source repair is now verified. Red subjects `485eb6b` and
`c68474c` exposed the exact canonical-byte, restoration-order, and non-finite
classification defects. Exact repair through `c9af373` restores sibling,
governor, then EPP; emits canonical native process and Bash restoration
records; and maps noncanonical or non-finite bytes to the closed rejection
classes in both runner and fresh verifier. Complete Debug and Release 50/50
suites, isolated sanitizer 3/3, and repository policy passed on
`wineth-ubuntu`; follow-up independent review reported no remaining critical,
important, or minor finding. This closes
source and fixture quality only.

At clean merged source `a396f642d5c2ec6ed670cc2341170ec7d9f1a886`,
one bounded restoration-only physical session passed around `/usr/bin/true`.
The controller returned 0, the canonical record reported exact restoration,
and an independent live audit matched sibling, governor, EPP, and boost. The
restoration-record SHA-256 is
`5b6e2cefbac4c8c96f5228139978f776d55aff0dcffb9dc9fb19812cb50236e7`.
A fresh physical-native bundle at the same source passed preparation and fresh
physical verification. Its bundle-manifest, inventory, executable, and
normalized executable-identity SHA-256 values are
`15d58e20bbab593bd902782b917b79ba98a03cf1e79c784fbff2c450d23a99a0`,
`44d6ee1eec9791974098ce74c81647d1690bd0aef2bd54822e47635ebad1bbaf`,
`db82cd647e880b1780c2a5fb9d10f87398b184f35d4e84de9b6855db07fec015`,
and `753890dc53185727326bc5dba2585a59ed60bdf0465623dec3fb58bf63b388b3`.
The complete bundle was copied byte-for-byte to `gpu-2`, where a fresh verifier
at the same exact source accepted matching manifest, inventory, executable,
and normalized executable-identity digests. The replacement read-only
preflight then accepted with SHA-256
`08a3253b44a2bc1c0dc89abd3463c20def73e0fc313ac468441b9ce65c31935e`
and deterministic CPU 1/sibling 13 selection SHA-256
`718350bb2ff003000e1ed7ffd1f331fe0c52671cd56d21f3a5dde307bcead803`.
Independent replay and separate review closed Task 9 with no finding. No host
control or PMU phase occurred during preflight. The one authorized attempt at
that source retained five valid primary processes, 150 samples, six exact
restorations, required cycles/instructions at 100 percent running, and terminal
PMU `process_schema_failure` rejection SHA-256
`0330baaba84c9cef592204e65f95391d8597f55cdd3fe8e182153ec9a6405ba1`.
It produced no acceptance or campaign manifest, optional PMU phase, controlled
reboot, qualification, or performance claim. The 49-file external root is
immutable. A future attempt is not defined until the PMU traversal repair
passes complete quality/integration and a new bundle, replica, reviewed
preflight, immutable root, and separate authority exist. Accepted campaign
one, reboot authority, the M0/M2 baseline numerical-admission dependency, and
independent final M0 review/acceptance remain open.

Load-bearing infrastructure boundary before the reference-target manifest can be locked:

- Qualify the designated physical AMD x86-64 Linux host: PMU events, power/frequency observability, exclusivity, topology, reboot identity, toolchain, admitted baselines, and noise under the locked protocol.

## Milestone table

| Milestone | State | Implementing commits | Evidence | Open gate items |
|---|---|---|---|---|
| M0 — Charter, prior-art map, benchmark protocol | In progress | Foundation through `a396f64`; PMU traversal red `cc826f2`; repair `0a30b24` | M0 documents, target support, baselines, quality enforcement, campaign runner, restoration proof, bundle/replica, and reviewed preflight exist; attempt 1 is a terminal restoration rejection; attempt 2 retained five valid processes, 150 samples, six exact restorations, full-scale required counters, and a terminal PMU publication rejection; no accepted campaign, controlled reboot, qualification, or performance claim | Close repair quality/review/protected-main integration; define no future attempt until a new bundle, replica, preflight, review, root, and authority exist; resolve the M0/M2 numerical-admission dependency and deferred JITSpMM license; independent final M0 review/acceptance |
| M1 — Core types and canonical identity | Not started | None | None | M0 gate must close first |
| M2 — Reference semantics and honest baselines | Not started | None | None | M1 gate and target/baseline setup |
| M3 — Contribution graph and scalar code generation | Not started | None | None | M2 gate |
| M4 — Reduction IR and explicit CPU schedules | Not started | None | None | M3 gate |
| M5 — Empirical planner and plan cache | Not started | None | None | M4 gate |
| M6 — Structural motif discovery and hybrid kernels | Not started | None | None | M5 gate |
| M7 — Target 0 product-class proof | Not started | None | None | M6 proof gate and frozen subsets |
| M8 — Two-sided exact sparsity | Not started | None | None | M7 continuation decision |
| M9 — Constant-operand specialization | Not started | None | None | Earlier approved gates |
| M10 — Algebraic rewrite engine | Not started | None | None | Structural product-class gate and explicit numerical modes |
| M11 — Bilinear algorithm discovery | Not started | None | None | M10 and explicit later-program approval |
| M12 — Production runtime and JIT | Not started | None | None | Stable AOT planning and runtime architecture review |
| M13 — Parallel CPU and GPU expansion | Not started | None | None | Separate design review after CPU product-class gate |

## Dependency audit

- No product code, product tests, executable benchmark harness, generated kernel artifacts, database, or cached plans exist. The current CMake/test system is quality infrastructure only. An M0 benchmark-result schema and synthetic example exist as evidence contracts only.
- No later-milestone code currently depends on an open earlier gate.
- The only repository document present before discovery was the build plan; its front matter says “Proposed architectural program,” while the user's handoff treats the architecture as approved and locked for execution. The user instruction controls current work. The M0 architecture index and charter now record that authority distinction without editing the build plan's technical semantics.

## Gate-record requirements

Before changing a milestone to **Gate closed**, add or link an acceptance record containing:

- exact commit and clean/dirty state tested;
- controlling requirements and accepted deviations;
- exact configure, build, and verification commands;
- correctness and numerical evidence;
- generated source/object/disassembly evidence where applicable;
- raw benchmark manifests and statistical analysis where performance is claimed;
- baseline identities and configurations;
- target fingerprint and compatibility conditions;
- code size, compilation/tuning cost, scratch/prepack data, and break-even calls where applicable;
- independent review outcome;
- explicit go, no-go, or scope-narrowing decision.
