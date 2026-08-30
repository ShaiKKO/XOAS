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

The named M0 document, policy, schema, corpus, and candidate-capture deliverables now exist and passed the Task 6 checks. The user approved AR-0001 Option 2, AR-0002 Option 1, and the written engineering-quality specification. `gpu-2` is development-only. The replacement Target 0 candidate is designated but not qualified. The exact development toolchain is installed and behaviorally verified, full draft-2020-12 validation of the benchmark schema/example has passed, and the local/hosted quality system is enforced on protected `main`. Qualification-plan Tasks 1–4 are implemented: the physical host has a closed pre-state, exact 26-package support closure, three versioned source-built baseline libraries, complete installed-file hashes, upstream-test and loader evidence, and a schema-valid installed lock. Qualification-tool deployment is also closed: exact implementation `a312aa2` passed Debug 38/38, Release 38/38, and sanitizer 3/3 on `gpu-2`; the replacement physical dual build and five compatibility checks passed; fresh physical and replica verifiers matched all authoritative digests. Campaign-runner implementation Tasks 1–7 are closed through exact quality subject `7b486e1`: the campaign contract/schema, dedicated privileged-PMU boundary, preflight, five-process/PMU orchestration, deterministic finalization, fresh replay verifier, source-clean CLIs, complete Debug and Release 50/50 replays, and sanitizer 3/3 passed on `gpu-2`. Task 9 preflight passed, but Task 10 attempt 1 stopped during primary process 1 because the physical governor restore left EPP at `performance`; the runner rejected before PMU and bounded recovery restored exact pre-state.

The test-first source repair is now verified. Red subject `485eb6b` exposed the
exact canonical-byte and restoration-order defects. Exact repair
subject `93e9070` restores sibling, governor, then EPP; emits canonical native
process and Bash restoration records; and requires canonical bytes in both the
runner and fresh verifier. Complete Debug and Release 50/50 suites, isolated
sanitizer 3/3, and repository policy passed on `wineth-ubuntu`. This closes
source and fixture quality only. The next slice is physical restoration
verification plus a new exact-commit native bundle/replica and read-only
preflight. A separately authorized new attempt, accepted campaign one, reboot
authority, the M0/M2 baseline numerical-admission dependency, and independent
final M0 review/acceptance remain open. The incidental administrator reboot is
not campaign evidence.

Load-bearing infrastructure boundary before the reference-target manifest can be locked:

- Qualify the designated physical AMD x86-64 Linux host: PMU events, power/frequency observability, exclusivity, topology, reboot identity, toolchain, admitted baselines, and noise under the locked protocol.

## Milestone table

| Milestone | State | Implementing commits | Evidence | Open gate items |
|---|---|---|---|---|
| M0 — Charter, prior-art map, benchmark protocol | In progress | `60044e8` (foundation/charter); `30616bc` (prior art/baselines); `00afbf7` (benchmark contract); `8a7032b` (corpus); `6e6adf3` (candidate target/proposal); `3d635d3` (verified integration subject); `6904d49` (Option 2 decision); `ce1d27d` (verified development toolchain); `2c07fef` (aggregate local quality); `651b912` (authoritative hosted checks); `6516866` (protected-main evidence); `60c4eeb` (AMD qualification authority/plan); `8a247a2` (qualification process contract); `864f7fa` (capture/session controls); `b7371ae` (real-checkout capture repair); `ee57ff5` (physical pre-state and provisioning lock); `16d698d` (Task 4 execution subject); `9d44f64` (verified baseline stack); `a312aa2` (verified native qualification-tool deployment subject); `db0eb87` (campaign runner, fresh verifier, and source-clean execution); `7b486e1` (exact campaign quality evidence); `1141713` (replacement bundle and rejected physical attempt source); `485eb6b` (restoration/canonical-byte red tests); `93e9070` (verified source repair) | All named M0 documents/manifests exist; AR-0001 Option 2, AR-0002 Option 1, and engineering-quality design approved; physical AMD support closure and versioned baseline artifacts installed and verified; development toolchain and local/hosted/protected-main enforcement verified; replacement native bundle and preflight passed; campaign attempt 1 rejected on exact EPP restoration and bounded recovery restored pre-state; test-first source repair emits and requires canonical retained JSON and orders governor before EPP; exact repair passed full `wineth-ubuntu` quality; no PMU/reboot/qualification/performance claim | Physically verify repaired governor/EPP restoration; deploy and cross-verify a new exact-commit bundle/replica; pass a new read-only preflight before any separately authorized new campaign attempt; resolve the M0/M2 baseline numerical-admission dependency and deferred JITSpMM license before use; independent final review/acceptance |
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
